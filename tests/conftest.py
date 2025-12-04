"""Pytest configuration and fixtures for swarm-client tests."""

import pytest
import asyncio
from typing import Dict, Any, AsyncGenerator

from swarm_client.devices import DeviceRegistry, DeviceFactory
from swarm_client.config.models import (
    DeviceConfig, DriverConfig, ConnectionConfig,
    PlatformConfig, ClientConfig
)


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sim_shaker_config() -> DeviceConfig:
    """Create a simulation shaker device config."""
    return DeviceConfig(
        device_id="test_shaker",
        type="shaker",
        name="Test Shaker",
        driver=DriverConfig(type="sim")
    )


@pytest.fixture
def sim_centrifuge_config() -> DeviceConfig:
    """Create a simulation centrifuge device config."""
    return DeviceConfig(
        device_id="test_centrifuge",
        type="centrifuge",
        name="Test Centrifuge",
        driver=DriverConfig(type="sim")
    )


@pytest.fixture
def platform_config() -> PlatformConfig:
    """Create a test platform config."""
    return PlatformConfig(
        url="wss://test.example.com/ws",
        api_key="test_api_key",
        heartbeat_interval=10.0,
        command_timeout=30.0
    )


@pytest.fixture
def client_config(
    platform_config: PlatformConfig,
    sim_shaker_config: DeviceConfig,
    sim_centrifuge_config: DeviceConfig
) -> ClientConfig:
    """Create a test client config with simulation devices."""
    return ClientConfig(
        client_id="test_client",
        site="test_site",
        lab="test_lab",
        platform=platform_config,
        devices=[sim_shaker_config, sim_centrifuge_config]
    )


@pytest.fixture
def device_factory() -> DeviceFactory:
    """Create a device factory."""
    return DeviceFactory()


@pytest.fixture
async def device_registry(
    device_factory: DeviceFactory,
    sim_shaker_config: DeviceConfig,
    sim_centrifuge_config: DeviceConfig
) -> AsyncGenerator[DeviceRegistry, None]:
    """Create a device registry with test devices."""
    registry = DeviceRegistry()

    # Register shaker
    shaker = device_factory.create_driver(sim_shaker_config)
    registry.register(
        device_id=sim_shaker_config.device_id,
        device_type=sim_shaker_config.type,
        driver=shaker,
        name=sim_shaker_config.name
    )

    # Register centrifuge
    centrifuge = device_factory.create_driver(sim_centrifuge_config)
    registry.register(
        device_id=sim_centrifuge_config.device_id,
        device_type=sim_centrifuge_config.type,
        driver=centrifuge,
        name=sim_centrifuge_config.name
    )

    # Initialize all
    await registry.initialize_all()

    yield registry

    # Cleanup
    await registry.cleanup_all()
