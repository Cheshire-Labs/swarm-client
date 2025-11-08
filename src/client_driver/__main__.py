"""Main entry point for the client driver CLI."""

import asyncio
import argparse
import sys
import logging
from pathlib import Path

from .config import load_config, setup_logging
from .devices import DeviceFactory, DeviceRegistry
from .executor import CommandExecutor
from .client import WebSocketClient

logger = logging.getLogger("cheshire_labs.client_driver")


async def async_main(args: argparse.Namespace) -> int:
    """Async main function.

    Args:
        args: Parsed command line arguments

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = load_config()
        logger.info(f"Loaded configuration for client: {config.client_id}")
        logger.info(f"Registered {len(config.devices)} device(s)")

        # Create device registry and factory
        registry = DeviceRegistry()
        factory = DeviceFactory()

        # Create and register all devices
        logger.info("Creating device drivers...")
        for device_config in config.devices:
            driver = factory.create_driver(device_config)
            registry.register(
                device_id=device_config.device_id,
                device_type=device_config.type,
                driver=driver,
                name=device_config.name
            )
            logger.info(f"  • {device_config.device_id} ({device_config.type}): {device_config.name}")

        # Initialize all devices (CRITICAL: fail fast if hardware unavailable)
        logger.info("Initializing devices...")
        await registry.initialize_all()
        logger.info("✓ All devices initialized successfully")

        # Create command executor
        executor = CommandExecutor(
            registry=registry,
            timeout=config.platform.command_timeout
        )

        # Create WebSocket client
        client = WebSocketClient(
            config=config,
            executor=executor,
            heartbeat_interval=config.platform.heartbeat_interval
        )

        # Start client (runs until stopped)
        logger.info(f"Connecting to Swarm platform: {config.platform.url}")
        await client.start()

        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = argparse.ArgumentParser(
        description="Cheshire Client Driver - Connect lab devices to Swarm platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  python -m client_driver

  # Run with verbose logging
  python -m client_driver --verbose

  # Run with custom config directory
  python -m client_driver --config-dir /path/to/config

Configuration:
  The client driver loads configuration from:
    1. Environment variables (SWARM_URL, SWARM_API_KEY, CLIENT_ID)
    2. JSON config file in ~/.cheshire-client-driver/config.json

  See README.md for configuration details.
        """
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        help="Custom configuration directory (default: ~/.cheshire-client-driver)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Log startup banner
    logger.info("=" * 60)
    logger.info("Cheshire Client Driver v0.1.0")
    logger.info("Connecting lab devices to Swarm platform")
    logger.info("=" * 60)

    # Run async main
    try:
        exit_code = asyncio.run(async_main(args))
        return exit_code
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        return 0


if __name__ == "__main__":
    sys.exit(main())
