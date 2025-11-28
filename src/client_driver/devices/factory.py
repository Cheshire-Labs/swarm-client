"""Device factory for creating driver instances from configuration.

# SHARED: May extract to shared package after MVP
"""

import logging
from typing import Any
from ..config.models import DeviceConfig
from cheshire_drivers import (
    BaseDriver,
    SimShakerDriver, SimCentrifugeDriver, SimSealerDriver,
    SimTransporterDriver, SimLiquidHandlerDriver,
    SimPlateWasherDriver, SimReaderDriver, SimDelidderDriver,
    PLRShakerBackendWrapper,
    PLRCentrifugeBackendWrapper,
    PLRSealerBackendWrapper,
    PLRTransporterBackendWrapper,
    Teachpoint,
)

logger = logging.getLogger("cheshire_labs.client_driver.factory")


class DeviceFactory:
    """Creates driver instances from configuration."""

    def create_driver(self, config: DeviceConfig) -> BaseDriver:
        """Create a driver based on configuration.

        Args:
            config: Device configuration

        Returns:
            Initialized driver instance

        Raises:
            ValueError: If driver type or device type is unknown
        """
        if config.driver.type == "sim":
            return self._create_sim_driver(config)
        elif config.driver.type == "plr":
            return self._create_plr_driver(config)
        elif config.driver.type == "venus":
            return self._create_venus_driver(config)
        else:
            raise ValueError(f"Unknown driver type: {config.driver.type}")

    def _create_sim_driver(self, config: DeviceConfig) -> BaseDriver:
        """Create simulation driver."""
        if config.type == "shaker":
            return SimShakerDriver(config.device_id)
        elif config.type == "centrifuge":
            return SimCentrifugeDriver(config.device_id)
        elif config.type == "sealer":
            return SimSealerDriver(config.device_id)
        elif config.type == "transporter":
            return SimTransporterDriver(config.device_id)
        elif config.type == "liquid_handler":
            return SimLiquidHandlerDriver(config.device_id)
        elif config.type == "plate_washer":
            return SimPlateWasherDriver(config.device_id)
        elif config.type == "reader":
            return SimReaderDriver(config.device_id)
        elif config.type == "delidder":
            return SimDelidderDriver(config.device_id)
        else:
            raise ValueError(f"Unknown device type for sim driver: {config.type}")

    def _create_plr_driver(self, config: DeviceConfig) -> BaseDriver:
        """Create PyLabRobot driver."""
        if not config.driver.backend:
            raise ValueError(f"PLR backend not specified for device {config.device_id}")

        backend = self._create_plr_backend(config)

        if config.type == "shaker":
            return PLRShakerBackendWrapper(backend)
        elif config.type == "centrifuge":
            return PLRCentrifugeBackendWrapper(backend)
        elif config.type == "sealer":
            return PLRSealerBackendWrapper(backend)
        elif config.type == "transporter":
            wrapper = PLRTransporterBackendWrapper(backend)
            # Load teachpoints if specified
            if config.driver.teachpoints_file:
                teachpoints = Teachpoint.load_teachpoints_from_file(config.driver.teachpoints_file)
                wrapper.load_teachpoints(teachpoints)
            return wrapper
        else:
            raise ValueError(f"Unknown device type for PLR driver: {config.type}")

    def _create_plr_backend(self, config: DeviceConfig) -> Any:
        """Instantiate PyLabRobot backend from config."""
        backend_class_name = config.driver.backend
        backend_class = self._get_plr_backend_class(backend_class_name)

        # Create backend based on connection type
        if config.driver.connection:
            if config.driver.connection.type == "serial":
                return backend_class(port=config.driver.connection.port)
            elif config.driver.connection.type == "tcp":
                return backend_class(
                    host=config.driver.connection.host,
                    port=config.driver.connection.tcp_port
                )
            elif config.driver.connection.type == "usb":
                return backend_class(device_path=config.driver.connection.port)
        else:
            # No connection config - instantiate with defaults
            return backend_class()

    def _get_plr_backend_class(self, backend_name: str) -> type:
        """Get PyLabRobot backend class by name.

        Args:
            backend_name: Name of backend class (e.g., 'InhecoThermoShake')

        Returns:
            Backend class

        Raises:
            ImportError: If backend not found
        """
        # Import PyLabRobot backends dynamically
        try:
            # Try shaker backends
            from pylabrobot.shaking.backend import ShakerBackend
            if hasattr(__import__('pylabrobot.shaking', fromlist=[backend_name]), backend_name):
                return getattr(__import__('pylabrobot.shaking', fromlist=[backend_name]), backend_name)

            # Try centrifuge backends
            from pylabrobot.centrifuge.backend import CentrifugeBackend
            if hasattr(__import__('pylabrobot.centrifuge', fromlist=[backend_name]), backend_name):
                return getattr(__import__('pylabrobot.centrifuge', fromlist=[backend_name]), backend_name)

            # Try sealer backends
            from pylabrobot.sealing.backend import SealerBackend
            if hasattr(__import__('pylabrobot.sealing', fromlist=[backend_name]), backend_name):
                return getattr(__import__('pylabrobot.sealing', fromlist=[backend_name]), backend_name)

            # Try arm backends
            from pylabrobot.arms.backend import ArmBackend
            if hasattr(__import__('pylabrobot.arms', fromlist=[backend_name]), backend_name):
                return getattr(__import__('pylabrobot.arms', fromlist=[backend_name]), backend_name)

            raise ImportError(f"PyLabRobot backend '{backend_name}' not found")

        except ImportError as e:
            logger.error(f"Failed to import PyLabRobot backend '{backend_name}': {e}")
            raise

    def _create_venus_driver(self, config: DeviceConfig) -> BaseDriver:
        """Create Venus driver (future implementation)."""
        raise NotImplementedError("Venus driver not yet implemented in client-driver")
