"""WebSocket protocol message definitions.

This module defines the message format for communication between the
client-driver and the Swarm platform.

IMPORTANT: This file must be kept in sync with the same file in swarm-backend.
Any changes to message structures must be coordinated between both repositories.
"""

from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional, List
from datetime import datetime


# Protocol version for compatibility checking
PROTOCOL_VERSION = "1.0.0"


class ConnectMessage(BaseModel):
    """Sent by client when connecting to platform.

    The client authenticates using an API key and provides a list of
    devices it can control.
    """
    protocol_version: str = PROTOCOL_VERSION
    api_key: str = Field(..., description="API key for authentication")
    devices: List[Dict[str, str]] = Field(
        ...,
        description="List of available devices with device_id, type, and name"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "protocol_version": "1.0.0",
                "api_key": "sk_test_1234567890",
                "devices": [
                    {"device_id": "shaker_1", "type": "shaker", "name": "Lab Shaker"},
                    {"device_id": "centrifuge_1", "type": "centrifuge", "name": "Eppendorf Centrifuge"}
                ]
            }
        }


class CommandMessage(BaseModel):
    """Command from server to client.

    The server sends commands to control specific devices. The command_id
    is used to match responses.
    """
    command_id: str = Field(..., description="Unique identifier for this command")
    device_id: str = Field(..., description="Target device identifier")
    command: str = Field(..., description="Command name (e.g., 'shake', 'centrifuge')")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Command-specific parameters"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "command_id": "cmd_1234567890",
                "device_id": "shaker_1",
                "command": "shake",
                "params": {
                    "speed": 500.0,
                    "duration": 30.0
                }
            }
        }


class ResponseMessage(BaseModel):
    """Response from client to server.

    Sent after executing a command. Includes the result or error information.
    """
    command_id: str = Field(..., description="ID of the command this responds to")
    success: bool = Field(..., description="Whether the command succeeded")
    result: Optional[Any] = Field(None, description="Result data if successful")
    error: Optional[str] = Field(None, description="Human-readable error message")
    error_type: Optional[str] = Field(None, description="Error type for programmatic handling")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "command_id": "cmd_1234567890",
                    "success": True,
                    "result": None,
                    "error": None,
                    "error_type": None
                },
                {
                    "command_id": "cmd_9876543210",
                    "success": False,
                    "result": None,
                    "error": "Device shaker_1 not found",
                    "error_type": "DeviceNotFoundError"
                }
            ]
        }


class StatusMessage(BaseModel):
    """Status update from client to server.

    Periodically sent to update server about device states.
    """
    devices: Dict[str, str] = Field(
        ...,
        description="Map of device_id to status (ready/busy/error)"
    )
    timestamp: float = Field(..., description="Unix timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "devices": {
                    "shaker_1": "ready",
                    "centrifuge_1": "busy",
                    "sealer_1": "error"
                },
                "timestamp": 1699459200.0
            }
        }


class HeartbeatMessage(BaseModel):
    """Heartbeat from client to server.

    Sent periodically to indicate the client is still connected.
    """
    timestamp: float = Field(..., description="Unix timestamp")
    uptime: float = Field(..., description="Client uptime in seconds")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 1699459200.0,
                "uptime": 3600.5
            }
        }


class MessageEnvelope(BaseModel):
    """Wrapper for all WebSocket messages.

    All messages sent over the WebSocket are wrapped in this envelope
    which specifies the message type.
    """
    type: Literal["connect", "command", "response", "status", "heartbeat"] = Field(
        ...,
        description="Message type discriminator"
    )
    payload: Dict[str, Any] = Field(..., description="Message payload")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "command",
                "payload": {
                    "command_id": "cmd_1234567890",
                    "device_id": "shaker_1",
                    "command": "shake",
                    "params": {"speed": 500.0, "duration": 30.0}
                }
            }
        }

    @classmethod
    def wrap_connect(cls, message: ConnectMessage) -> "MessageEnvelope":
        """Wrap a ConnectMessage in an envelope."""
        return cls(type="connect", payload=message.model_dump())

    @classmethod
    def wrap_command(cls, message: CommandMessage) -> "MessageEnvelope":
        """Wrap a CommandMessage in an envelope."""
        return cls(type="command", payload=message.model_dump())

    @classmethod
    def wrap_response(cls, message: ResponseMessage) -> "MessageEnvelope":
        """Wrap a ResponseMessage in an envelope."""
        return cls(type="response", payload=message.model_dump())

    @classmethod
    def wrap_status(cls, message: StatusMessage) -> "MessageEnvelope":
        """Wrap a StatusMessage in an envelope."""
        return cls(type="status", payload=message.model_dump())

    @classmethod
    def wrap_heartbeat(cls, message: HeartbeatMessage) -> "MessageEnvelope":
        """Wrap a HeartbeatMessage in an envelope."""
        return cls(type="heartbeat", payload=message.model_dump())

    def unwrap(self) -> ConnectMessage | CommandMessage | ResponseMessage | StatusMessage | HeartbeatMessage:
        """Unwrap the envelope to get the inner message."""
        if self.type == "connect":
            return ConnectMessage(**self.payload)
        elif self.type == "command":
            return CommandMessage(**self.payload)
        elif self.type == "response":
            return ResponseMessage(**self.payload)
        elif self.type == "status":
            return StatusMessage(**self.payload)
        elif self.type == "heartbeat":
            return HeartbeatMessage(**self.payload)
        else:
            raise ValueError(f"Unknown message type: {self.type}")
