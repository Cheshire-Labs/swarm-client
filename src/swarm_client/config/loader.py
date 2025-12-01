"""Configuration loader for swarm-client.

Loads configuration from a single config.json file.
Environment variables can provide fallback values for platform settings.

Note: .env file loading is handled by __main__.py via --env flag.
If no --env flag specified, uses OS environment variables directly.
"""

import os
import json
import re
from pathlib import Path

from .models import ClientConfig, PlatformConfig


def _expand_env_vars(value: str) -> str:
    """Expand ${VAR} syntax from environment variables."""
    if not isinstance(value, str):
        return value
    pattern = r'\$\{([^}]+)\}'
    def replacer(match):
        var_name = match.group(1)
        return os.getenv(var_name, match.group(0))
    return re.sub(pattern, replacer, value)


def load_client_config(config_path: str) -> ClientConfig:
    """Load client configuration from config.json.

    Configuration priority (highest to lowest):
    1. Config file values (config.json)
    2. Environment variables (SWARM_URL, SWARM_API_KEY, etc.)
    3. Model defaults

    Args:
        config_path: Path to config.json file.

    Returns:
        Validated ClientConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If required fields (url, api_key) are missing
    """
    if not Path(config_path).exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            f"Create a config.json file in your working directory.\n"
            f"See examples/config.example.json for the expected format."
        )

    with open(config_path, 'r') as f:
        config_data = json.load(f)

    # Get platform config from file (or empty dict if not present)
    platform_data = config_data.get("platform", {})

    # Build platform config: file values override env vars, model provides defaults
    # Priority: config file (with ${VAR} expansion) > env var > model default
    url = _expand_env_vars(platform_data.get("url", "")) or os.getenv("SWARM_URL", "")
    api_key = _expand_env_vars(platform_data.get("api_key", "")) or os.getenv("SWARM_API_KEY", "")

    platform = PlatformConfig(
        url=url,
        api_key=api_key,
        # Optional fields - only pass if explicitly set, otherwise use model defaults
        **_optional_platform_fields(platform_data)
    )

    # Validate required fields
    if not platform.url:
        raise ValueError(
            "url is required.\n"
            "Add 'url' to the 'platform' section in config.json:\n"
            '  "platform": { "url": "wss://your-swarm-url", "api_key": "..." }\n'
            "Or set SWARM_URL environment variable."
        )

    if not platform.api_key:
        raise ValueError(
            "api_key is required.\n"
            "Add 'api_key' to the 'platform' section in config.json:\n"
            '  "platform": { "url": "...", "api_key": "your-api-key" }\n'
            "Or set SWARM_API_KEY environment variable."
        )

    # Build full config - let Pydantic validate the rest
    return ClientConfig(
        client_id=config_data.get("client_id", ""),
        site=config_data.get("site", ""),
        lab=config_data.get("lab", ""),
        workcell=config_data.get("workcell"),
        platform=platform,
        devices=config_data.get("devices", [])
    )


def _optional_platform_fields(platform_data: dict) -> dict:
    """Extract optional platform fields, only including those explicitly set.

    This allows the PlatformConfig model defaults to be used when fields aren't specified.
    """
    fields = {}

    if "reconnect_backoff" in platform_data:
        fields["reconnect_backoff"] = platform_data["reconnect_backoff"]
    elif os.getenv("SWARM_RECONNECT_BACKOFF"):
        fields["reconnect_backoff"] = [float(x) for x in os.getenv("SWARM_RECONNECT_BACKOFF").split(",")]

    if "heartbeat_interval" in platform_data:
        fields["heartbeat_interval"] = platform_data["heartbeat_interval"]
    elif os.getenv("SWARM_HEARTBEAT_INTERVAL"):
        fields["heartbeat_interval"] = float(os.getenv("SWARM_HEARTBEAT_INTERVAL"))

    if "command_timeout" in platform_data:
        fields["command_timeout"] = platform_data["command_timeout"]
    elif os.getenv("SWARM_COMMAND_TIMEOUT"):
        fields["command_timeout"] = float(os.getenv("SWARM_COMMAND_TIMEOUT"))

    return fields
