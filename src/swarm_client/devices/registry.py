"""Device registry for managing driver instances.

# CLIENT-SPECIFIC: Simple device lookup for command execution
"""

import asyncio
import logging
from typing import Dict, Optional, List
from cheshire_drivers import BaseDriver

logger = logging.getLogger("swarm_client.registry")


class DeviceRegistry:
    """Manages device driver instances with locks."""

    def __init__(self):
        self._drivers: Dict[str, BaseDriver] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._device_types: Dict[str, str] = {}
        self._device_names: Dict[str, str] = {}

    def register(
        self,
        device_id: str,
        device_type: str,
        driver: BaseDriver,
        name: Optional[str] = None
    ):
        """Register a device driver.

        Args:
            device_id: Unique device identifier
            device_type: Device type (shaker, centrifuge, etc.)
            driver: Driver instance
            name: Optional human-readable name
        """
        self._drivers[device_id] = driver
        self._locks[device_id] = asyncio.Lock()
        self._device_types[device_id] = device_type
        self._device_names[device_id] = name or device_id

        # Attach lock to driver for convenience
        driver.lock = self._locks[device_id]

        logger.debug(f"Registered device: {device_id} ({device_type})")

    def get_driver(self, device_id: str) -> Optional[BaseDriver]:
        """Get driver by device ID.

        Args:
            device_id: Device identifier

        Returns:
            Driver instance or None if not found
        """
        return self._drivers.get(device_id)

    def get_device_type(self, device_id: str) -> Optional[str]:
        """Get device type by ID."""
        return self._device_types.get(device_id)

    def get_device_name(self, device_id: str) -> Optional[str]:
        """Get device name by ID."""
        return self._device_names.get(device_id)

    def get_all_device_ids(self) -> List[str]:
        """Get list of all registered device IDs."""
        return list(self._drivers.keys())

    def get_all_devices(self) -> Dict[str, Dict[str, str]]:
        """Get all devices with their metadata.

        Returns:
            Dict mapping device_id to {type, name}
        """
        return {
            device_id: {
                "type": self._device_types[device_id],
                "name": self._device_names[device_id]
            }
            for device_id in self._drivers.keys()
        }

    async def initialize_all(self):
        """Initialize all devices on startup.

        This is CRITICAL for beta - validates all hardware before connecting
        to platform. Fails fast with clear errors if any device is unreachable.

        Raises:
            RuntimeError: If any device fails to initialize
        """
        logger.info(f"Initializing {len(self._drivers)} devices...")
        errors = []

        for device_id, driver in self._drivers.items():
            try:
                logger.info(f"Initializing {device_id}...")
                await driver.initialize()
                logger.info(f"{device_id} initialized successfully")
            except Exception as e:
                error_msg = f"{device_id}: {e}"
                errors.append(error_msg)
                logger.error(f"Failed to initialize {device_id}: {e}", exc_info=True)

        if errors:
            logger.error("Device initialization failed:")
            for error in errors:
                logger.error(f"  • {error}")
            raise RuntimeError(
                f"Device initialization failed. Fix configuration and try again.\n"
                + "\n".join(f"  • {e}" for e in errors)
            )

        logger.info(f"All {len(self._drivers)} devices initialized successfully")

    async def cleanup_all(self):
        """Cleanup all devices on shutdown."""
        logger.info("Cleaning up devices...")
        for device_id, driver in self._drivers.items():
            try:
                if hasattr(driver, 'close'):
                    await driver.close()
                logger.debug(f"{device_id} cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up {device_id}: {e}")

        logger.info("Device cleanup complete")
