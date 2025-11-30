"""Tests for device registry."""

import pytest
from swarm_client.devices import DeviceRegistry, DeviceFactory
from swarm_client.config.models import DeviceConfig, DriverConfig


@pytest.mark.asyncio
async def test_register_device(device_factory: DeviceFactory, sim_shaker_config: DeviceConfig):
    """Test registering a device."""
    registry = DeviceRegistry()
    driver = device_factory.create_driver(sim_shaker_config)

    registry.register(
        device_id=sim_shaker_config.device_id,
        device_type=sim_shaker_config.type,
        driver=driver,
        name=sim_shaker_config.name
    )

    assert registry.get_driver("test_shaker") is not None
    assert registry.get_device_type("test_shaker") == "shaker"
    assert registry.get_device_name("test_shaker") == "Test Shaker"


@pytest.mark.asyncio
async def test_get_all_devices(device_registry: DeviceRegistry):
    """Test getting all registered devices."""
    devices = device_registry.get_all_devices()

    assert len(devices) == 2
    assert "test_shaker" in devices
    assert "test_centrifuge" in devices
    assert devices["test_shaker"]["type"] == "shaker"


@pytest.mark.asyncio
async def test_initialize_all_success(device_factory: DeviceFactory, sim_shaker_config: DeviceConfig):
    """Test successful initialization of all devices."""
    registry = DeviceRegistry()
    driver = device_factory.create_driver(sim_shaker_config)

    registry.register(
        device_id=sim_shaker_config.device_id,
        device_type=sim_shaker_config.type,
        driver=driver,
        name=sim_shaker_config.name
    )

    # Should not raise
    await registry.initialize_all()

    # Driver should be initialized
    assert driver.is_initialized


@pytest.mark.asyncio
async def test_cleanup_all(device_registry: DeviceRegistry):
    """Test cleanup of all devices."""
    # Should not raise
    await device_registry.cleanup_all()
