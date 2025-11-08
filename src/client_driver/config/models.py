"""Configuration models for client-driver.

Uses Pydantic for validation of JSON configuration files.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional, List


class ConnectionConfig(BaseModel):
    """Device connection configuration."""
    type: Literal["serial", "tcp", "usb"]
    port: Optional[str] = None           # Serial/USB port
    baudrate: Optional[int] = 9600       # Serial baudrate
    host: Optional[str] = None           # TCP host
    tcp_port: Optional[int] = None       # TCP port


class DriverConfig(BaseModel):
    """Driver configuration."""
    type: Literal["plr", "venus", "sim"]
    backend: Optional[str] = None        # PLR backend class name
    connection: Optional[ConnectionConfig] = None
    teachpoints_file: Optional[str] = None  # For transporters


class DeviceConfig(BaseModel):
    """Single device configuration."""
    device_id: str = Field(..., description="Unique device identifier")
    type: Literal["shaker", "centrifuge", "sealer", "transporter", "liquid_handler", "plate_washer", "reader", "delidder"]
    name: str = Field(..., description="Human-readable device name")
    driver: DriverConfig


class PlatformConfig(BaseModel):
    """Swarm platform connection configuration."""
    url: str = Field(..., description="WebSocket URL (wss://...)")
    api_key: str = Field(..., description="API key for authentication")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    reconnect_backoff: List[float] = Field(
        default=[1, 2, 4, 8, 16, 30],
        description="Reconnection backoff in seconds"
    )
    heartbeat_interval: float = Field(
        default=30.0,
        description="Heartbeat interval in seconds"
    )
    command_timeout: float = Field(
        default=60.0,
        description="Default command timeout in seconds"
    )


class ClientConfig(BaseModel):
    """Complete client configuration."""
    client_id: str = Field(..., description="Unique client identifier")
    platform: PlatformConfig
    devices: List[DeviceConfig]

    def devices_metadata(self) -> List[dict]:
        """Get device metadata for connection message.

        Returns:
            List of device metadata dicts
        """
        return [
            {
                "device_id": device.device_id,
                "type": device.type,
                "name": device.name
            }
            for device in self.devices
        ]
