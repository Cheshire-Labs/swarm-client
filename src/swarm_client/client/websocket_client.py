"""WebSocket client for connecting to Swarm platform.

# CLIENT-SPECIFIC: Handles secure connection, message routing, and reconnection
"""

import asyncio
import logging
import json
import time
from typing import Optional, Callable, Awaitable, Dict
from urllib.parse import urlparse
import websockets
from websockets import ClientConnection

from ..protocol import (
    MessageEnvelope, ConnectMessage, CommandMessage, ResponseMessage,
    StatusMessage, HeartbeatMessage, PROTOCOL_VERSION
)
from ..executor import CommandExecutor
from ..config.models import ClientConfig

logger = logging.getLogger("swarm_client.client")


class WebSocketClient:
    """Manages WebSocket connection to Swarm platform with reconnection logic."""

    def __init__(
        self,
        config: ClientConfig,
        executor: CommandExecutor,
        heartbeat_interval: float = 20.0,
        reconnect_delay: float = 5.0,
        max_reconnect_delay: float = 60.0
    ):
        """Initialize WebSocket client.

        Args:
            config: Client configuration
            executor: Command executor for handling commands
            heartbeat_interval: Seconds between heartbeats
            reconnect_delay: Initial delay between reconnection attempts
            max_reconnect_delay: Maximum delay between reconnection attempts
        """
        self.config = config
        self.executor = executor
        self.heartbeat_interval = heartbeat_interval
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay

        self.ws: Optional[ClientConnection] = None
        self._connected = False
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._receive_task: Optional[asyncio.Task] = None
        self._start_time: float = time.time()  # Track uptime for heartbeats

        # Status callback for UI/logging
        self.on_status_change: Optional[Callable[[str], Awaitable[None]]] = None

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to platform."""
        return self._connected and self.ws is not None

    async def start(self) -> None:
        """Start the WebSocket client with automatic reconnection.

        This will keep trying to connect until explicitly stopped.
        """
        self._running = True
        current_delay = self.reconnect_delay

        while self._running:
            try:
                await self._connect_and_run()
                # Reset delay on successful connection
                current_delay = self.reconnect_delay

            except asyncio.CancelledError:
                logger.info("Client cancelled, stopping...")
                break

            except Exception as e:
                logger.error(f"Connection error: {e}", exc_info=True)
                if not self._running:
                    break

                # Exponential backoff for reconnection
                logger.info(f"Reconnecting in {current_delay}s...")
                await asyncio.sleep(current_delay)
                current_delay = min(current_delay * 2, self.max_reconnect_delay)

    async def stop(self) -> None:
        """Stop the WebSocket client and cleanup."""
        logger.info("Stopping WebSocket client...")
        self._running = False

        # Cancel tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        # Close connection
        if self.ws:
            await self.ws.close()
            self.ws = None

        self._connected = False
        logger.info("WebSocket client stopped")

    async def _connect_and_run(self) -> None:
        """Connect to platform and run until disconnected."""
        # Build WebSocket URL with API key
        url = f"{self.config.platform.url}?api_key={self.config.platform.api_key}"
        parsed = urlparse(self.config.platform.url)

        # Security: ws:// only allowed for localhost
        if parsed.scheme == "ws":
            if parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
                raise ValueError(
                    f"Insecure WebSocket (ws://) not allowed for remote hosts. "
                    f"Use wss:// for {parsed.hostname}"
                )
            ssl_context = None
        else:
            ssl_context = True

        logger.info(f"Connecting to Swarm platform: {self.config.platform.url}")

        async with websockets.connect(url, ssl=ssl_context) as ws:
            self.ws = ws
            logger.info("Connected to Swarm platform")

            # Send connection message
            await self._send_connect_message()

            # Wait for connection acknowledgment
            # (For MVP, we assume immediate connection)
            self._connected = True
            await self._notify_status("CONNECTED")

            # Start heartbeat and receive tasks
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Wait for either task to complete (indicates disconnection)
            done, pending = await asyncio.wait(
                [self._heartbeat_task, self._receive_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel remaining task
            for task in pending:
                task.cancel()

            self._connected = False
            await self._notify_status("DISCONNECTED")

    async def _send_connect_message(self) -> None:
        """Send initial connection message to platform."""
        msg = ConnectMessage(
            protocol_version=PROTOCOL_VERSION,
            api_key=self.config.platform.api_key,
            site=self.config.site,
            lab=self.config.lab,
            workcell=self.config.workcell,
            devices=self.config.devices_metadata()
        )
        envelope = MessageEnvelope(type="connect", payload=msg.model_dump())
        await self._send(envelope)
        logger.info(f"Sent connection message for client: {self.config.client_id} (site={self.config.site}, lab={self.config.lab})")

    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats to keep connection alive."""
        try:
            while self._connected:
                # Send heartbeat first, then sleep (ensures immediate heartbeat on connection)
                heartbeat = HeartbeatMessage(
                    timestamp=time.time(),  # Unix timestamp (float)
                    uptime=time.time() - self._start_time  # Seconds since start
                )
                envelope = MessageEnvelope(type="heartbeat", payload=heartbeat.model_dump())
                await self._send(envelope)
                logger.debug("Sent heartbeat")

                await asyncio.sleep(self.heartbeat_interval)

        except asyncio.CancelledError:
            logger.debug("Heartbeat loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Heartbeat error: {e}", exc_info=True)
            raise

    async def _receive_loop(self) -> None:
        """Receive and process messages from platform."""
        if self.ws is None:
            return
        try:
            async for message in self.ws:
                try:
                    # Parse envelope
                    data = json.loads(message)
                    envelope = MessageEnvelope.model_validate(data)

                    # Route based on message type
                    if envelope.type == "command":
                        await self._handle_command(envelope)
                    elif envelope.type == "heartbeat":
                        logger.debug("Received heartbeat")
                    else:
                        logger.warning(f"Unknown message type: {envelope.type}")

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)

        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
            raise
        except websockets.exceptions.ConnectionClosed:
            logger.info("Connection closed by platform")
            raise
        except Exception as e:
            logger.error(f"Receive error: {e}", exc_info=True)
            raise

    async def _handle_command(self, envelope: MessageEnvelope) -> None:
        """Handle command message from platform.

        Args:
            envelope: Message envelope with command payload
        """
        try:
            # Parse command
            cmd = CommandMessage.model_validate(envelope.payload)
            logger.info(f"Received command: {cmd.command} on {cmd.device_id}")

            # Execute command
            response = await self.executor.execute(cmd)

            # Send response
            response_envelope = MessageEnvelope(
                type="response",
                payload=response.model_dump()
            )
            await self._send(response_envelope)

            logger.info(f"Command {cmd.command_id} completed: {response.success}")

        except Exception as e:
            logger.error(f"Error handling command: {e}", exc_info=True)
            # Send error response if possible
            try:
                cmd_id = envelope.payload.get("command_id", "unknown")
                error_response = ResponseMessage(
                    command_id=cmd_id,
                    success=False,
                    result=None,
                    error=str(e),
                    error_type=type(e).__name__
                )
                error_envelope = MessageEnvelope(
                    type="response",
                    payload=error_response.model_dump()
                )
                await self._send(error_envelope)
            except Exception as send_error:
                logger.error(f"Failed to send error response: {send_error}")

    async def _send(self, envelope: MessageEnvelope) -> None:
        """Send message envelope to platform.

        Args:
            envelope: Message envelope to send
        """
        if not self.ws:
            raise RuntimeError("Not connected to platform")

        message = json.dumps(envelope.model_dump())
        await self.ws.send(message)

    async def _notify_status(self, status: str) -> None:
        """Notify status change callback.

        Args:
            status: New status (CONNECTED, DISCONNECTED, etc.)
        """
        logger.info(f"Status changed: {status}")
        if self.on_status_change:
            try:
                await self.on_status_change(status)
            except Exception as e:
                logger.error(f"Error in status callback: {e}", exc_info=True)

    async def send_status(self, device_statuses: Dict[str, str]) -> None:
        """Send device status update to platform.

        Args:
            device_statuses: Map of device_id to status (e.g., {"shaker_1": "ready", "centrifuge_1": "busy"})
        """
        if not self.is_connected:
            logger.warning(f"Cannot send status - not connected")
            return

        try:
            status_msg = StatusMessage(
                devices=device_statuses,
                timestamp=time.time()  # Unix timestamp (float)
            )
            envelope = MessageEnvelope(type="status", payload=status_msg.model_dump())
            await self._send(envelope)
            logger.debug(f"Sent status for {len(device_statuses)} devices")

        except Exception as e:
            logger.error(f"Error sending status: {e}", exc_info=True)

    async def send_device_status(self, device_id: str, status: str) -> None:
        """Send status update for a single device (convenience method).

        Args:
            device_id: Device identifier
            status: Status string (e.g., "ready", "busy", "error")
        """
        await self.send_status({device_id: status})
