"""Tests for command executor."""

import pytest
from swarm_client.executor import CommandExecutor
from swarm_client.protocol import CommandMessage
from swarm_client.devices import DeviceRegistry


@pytest.mark.asyncio
async def test_execute_valid_command(device_registry: DeviceRegistry):
    """Test executing a valid command."""
    executor = CommandExecutor(device_registry)

    cmd = CommandMessage(
        command_id="test_1",
        device_id="test_shaker",
        command="shake",
        params={"speed": 300.0, "duration": 5.0}
    )

    response = await executor.execute(cmd)

    assert response.success is True
    assert response.command_id == "test_1"
    assert response.error is None


@pytest.mark.asyncio
async def test_execute_device_not_found(device_registry: DeviceRegistry):
    """Test executing command on non-existent device."""
    executor = CommandExecutor(device_registry)

    cmd = CommandMessage(
        command_id="test_2",
        device_id="nonexistent",
        command="shake",
        params={}
    )

    response = await executor.execute(cmd)

    assert response.success is False
    assert response.error_type == "DeviceNotFoundError"
    assert "not found" in response.error.lower()


@pytest.mark.asyncio
async def test_execute_unsupported_command(device_registry: DeviceRegistry):
    """Test executing unsupported command."""
    executor = CommandExecutor(device_registry)

    cmd = CommandMessage(
        command_id="test_3",
        device_id="test_shaker",
        command="fly",  # Shakers can't fly
        params={}
    )

    response = await executor.execute(cmd)

    assert response.success is False
    assert response.error_type == "UnsupportedCommandError"


@pytest.mark.asyncio
async def test_execute_private_method(device_registry: DeviceRegistry):
    """Test that private methods are blocked."""
    executor = CommandExecutor(device_registry)

    cmd = CommandMessage(
        command_id="test_4",
        device_id="test_shaker",
        command="_private_method",
        params={}
    )

    response = await executor.execute(cmd)

    assert response.success is False
    assert response.error_type == "SecurityError"
    assert "private" in response.error.lower()


@pytest.mark.asyncio
async def test_execute_invalid_parameters(device_registry: DeviceRegistry):
    """Test executing command with invalid parameters."""
    executor = CommandExecutor(device_registry)

    cmd = CommandMessage(
        command_id="test_5",
        device_id="test_shaker",
        command="shake",
        params={"invalid_param": "value"}  # Missing required params
    )

    response = await executor.execute(cmd)

    assert response.success is False
    assert response.error_type == "ParameterError"
