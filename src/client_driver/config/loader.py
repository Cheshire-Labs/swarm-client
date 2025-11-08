"""Configuration loader for client-driver.

Loads configuration from .env file (secrets) and config.json (devices).
"""

import os
import sys
import json
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

from .models import ClientConfig, PlatformConfig


def get_config_directory() -> Path:
    """Get platform-specific configuration directory.

    Returns:
        Windows: %USERPROFILE%\\.cheshire-client-driver
        macOS: ~/.cheshire-client-driver
        Linux: ~/.cheshire-client-driver
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("USERPROFILE", "C:\\Users\\Default"))
    else:
        base = Path.home()

    config_dir = base / ".cheshire-client-driver"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_client_config(config_path: Optional[str] = None) -> ClientConfig:
    """Load client configuration from .env and config.json.

    Args:
        config_path: Optional path to config.json. If None, uses default location.

    Returns:
        Validated ClientConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    config_dir = get_config_directory()

    # Load .env file for secrets
    env_file = config_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)

    # Load config.json for device definitions
    if config_path is None:
        config_path = str(config_dir / "config.json")

    if not Path(config_path).exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Create a config.json file at {config_dir / 'config.json'}"
        )

    with open(config_path, 'r') as f:
        config_data = json.load(f)

    # Build platform config from environment variables
    platform = PlatformConfig(
        url=os.getenv("SWARM_URL", ""),
        api_key=os.getenv("SWARM_API_KEY", ""),
        reconnect_backoff=[
            float(x) for x in os.getenv("SWARM_RECONNECT_BACKOFF", "1,2,4,8,16,30").split(",")
        ],
        heartbeat_interval=float(os.getenv("SWARM_HEARTBEAT_INTERVAL", "30")),
        command_timeout=float(os.getenv("SWARM_COMMAND_TIMEOUT", "60"))
    )

    # Validate required environment variables
    if not platform.url:
        raise ValueError(
            "SWARM_URL not found in environment.\n"
            f"Create a .env file at {env_file} with:\n"
            "SWARM_URL=wss://your-swarm-url\n"
            "SWARM_API_KEY=your-api-key"
        )

    if not platform.api_key:
        raise ValueError(
            "SWARM_API_KEY not found in environment.\n"
            f"Add SWARM_API_KEY to {env_file}"
        )

    # Combine platform config with device config
    return ClientConfig(
        platform=platform,
        devices=config_data.get("devices", [])
    )
