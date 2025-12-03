"""Command executor for routing string-based commands to device drivers.

# CLIENT-SPECIFIC: Uses string commands instead of typed actions
"""

import asyncio
import logging
from typing import Any, Dict

from cheshire_drivers.teachpoints import Teachpoint

from ..protocol import CommandMessage, ResponseMessage
from ..devices import DeviceRegistry

logger = logging.getLogger("swarm_client.executor")

# Commands that require teachpoint deserialization
TEACHPOINT_COMMANDS = {"pick_at_coords", "place_at_coords", "move_to_coords"}


class CommandExecutor:
    """Executes string-based commands on devices with validation and locking."""

    def __init__(self, registry: DeviceRegistry, timeout: float = 60.0):
        """Initialize command executor.

        Args:
            registry: Device registry for driver lookup
            timeout: Default command timeout in seconds
        """
        self.registry = registry
        self.timeout = timeout

    async def execute(self, cmd: CommandMessage) -> ResponseMessage:
        """Execute a command and return response.

        Args:
            cmd: Command message from platform

        Returns:
            Response message with result or error
        """
        logger.info(f"Executing: {cmd.command} on {cmd.device_id}")

        # Block private methods (security)
        if cmd.command.startswith('_'):
            logger.warning(f"Attempted to call private method: {cmd.command}")
            return self._error_response(
                cmd.command_id,
                f"Private methods are not allowed: {cmd.command}",
                "SecurityError"
            )

        # Get driver
        driver = self.registry.get_driver(cmd.device_id)
        if not driver:
            logger.error(f"Device not found: {cmd.device_id}")
            return self._error_response(
                cmd.command_id,
                f"Device {cmd.device_id} not found",
                "DeviceNotFoundError"
            )

        # Verify driver supports command
        if not hasattr(driver, cmd.command):
            logger.error(f"Device {cmd.device_id} does not support {cmd.command}")
            return self._error_response(
                cmd.command_id,
                f"Device {cmd.device_id} does not support command {cmd.command}",
                "UnsupportedCommandError"
            )

        # Verify method is async
        method = getattr(driver, cmd.command)
        if not asyncio.iscoroutinefunction(method):
            logger.error(f"Command {cmd.command} is not async on {cmd.device_id}")
            return self._error_response(
                cmd.command_id,
                f"Command {cmd.command} is not async",
                "NotAsyncError"
            )

        # Deserialize teachpoint for coordinate commands
        params = self._deserialize_params(cmd.command, cmd.params)

        # Execute with lock and timeout
        async with driver.lock:  # type: ignore[attr-defined]
            try:
                result = await asyncio.wait_for(
                    method(**params),
                    timeout=self.timeout
                )

                logger.debug(f"Command {cmd.command_id} completed successfully")
                return ResponseMessage(
                    command_id=cmd.command_id,
                    success=True,
                    result=result
                )

            except asyncio.TimeoutError:
                logger.error(f"Command {cmd.command_id} timed out after {self.timeout}s")
                return self._error_response(
                    cmd.command_id,
                    f"Command timed out after {self.timeout}s",
                    "TimeoutError"
                )
            except TypeError as e:
                logger.error(f"Invalid parameters for {cmd.command}: {e}")
                return self._error_response(
                    cmd.command_id,
                    f"Invalid parameters: {e}",
                    "ParameterError"
                )
            except Exception as e:
                logger.error(f"Command {cmd.command_id} failed: {e}", exc_info=True)
                return self._error_response(
                    cmd.command_id,
                    str(e),
                    type(e).__name__
                )

    def _error_response(
        self,
        command_id: str,
        error: str,
        error_type: str
    ) -> ResponseMessage:
        """Create error response message."""
        return ResponseMessage(
            command_id=command_id,
            success=False,
            result=None,
            error=error,
            error_type=error_type
        )

    def _deserialize_params(
        self,
        command: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deserialize complex objects in params before passing to driver.

        For teachpoint commands, converts the teachpoint dict to a Teachpoint object.
        """
        if command not in TEACHPOINT_COMMANDS:
            return params

        if "teachpoint" not in params:
            return params

        tp_dict = params["teachpoint"]
        teachpoint = Teachpoint.from_dict(tp_dict)
        return {**params, "teachpoint": teachpoint}
