"""Tests for protocol messages."""

import pytest
from datetime import datetime
from client_driver.protocol import (
    CommandMessage, ResponseMessage, MessageEnvelope,
    ConnectMessage, StatusMessage, HeartbeatMessage
)


def test_command_message():
    """Test command message creation and validation."""
    cmd = CommandMessage(
        command_id="cmd_123",
        device_id="device_1",
        command="shake",
        params={"speed": 300.0}
    )

    assert cmd.command_id == "cmd_123"
    assert cmd.device_id == "device_1"
    assert cmd.command == "shake"
    assert cmd.params["speed"] == 300.0


def test_response_message_success():
    """Test successful response message."""
    response = ResponseMessage(
        command_id="cmd_123",
        success=True,
        result={"status": "ok"}
    )

    assert response.success is True
    assert response.error is None
    assert response.result["status"] == "ok"


def test_response_message_error():
    """Test error response message."""
    response = ResponseMessage(
        command_id="cmd_123",
        success=False,
        result=None,
        error="Device not found",
        error_type="DeviceNotFoundError"
    )

    assert response.success is False
    assert response.error == "Device not found"
    assert response.error_type == "DeviceNotFoundError"


def test_message_envelope():
    """Test message envelope wrapping."""
    cmd = CommandMessage(
        command_id="cmd_123",
        device_id="device_1",
        command="shake",
        params={}
    )

    envelope = MessageEnvelope(
        type="command",
        payload=cmd.model_dump()
    )

    assert envelope.type == "command"
    assert envelope.payload["command_id"] == "cmd_123"


def test_connect_message():
    """Test connection message."""
    connect = ConnectMessage(
        protocol_version="1.0.0",
        api_key="test_api_key",
        site="boston",
        lab="molbio",
        devices=[
            {"device_id": "dev1", "type": "shaker", "name": "Shaker 1"},
            {"device_id": "dev2", "type": "centrifuge", "name": "Centrifuge 1"}
        ]
    )

    assert connect.api_key == "test_api_key"
    assert connect.site == "boston"
    assert connect.lab == "molbio"
    assert len(connect.devices) == 2
