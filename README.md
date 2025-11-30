# Swarm Client

WebSocket client for connecting local laboratory devices to the Swarm device integration platform.

## Overview

The Swarm Client enables remote control of laboratory automation equipment through the Swarm platform. This client software runs on computers physically connected to laboratory hardware (liquid handlers, robotic arms, centrifuges, shakers, sealers, etc.) and manages bidirectional communication with the Swarm server via secure WebSocket connections.

**Key Features:**
- Secure WebSocket communication (WSS) with Swarm
- Support for multiple device types via PyLabRobot backends
- Concurrent device operation management
- Automatic reconnection and error handling
- JSON-based configuration
- Comprehensive logging and audit trail

## Architecture

```
┌─────────────────────────────────────┐
│        Swarm Platform               │
│    (Device Integration Gateway)     │
└──────────────┬──────────────────────┘
               │
               │ WebSocket (WSS/443)
               │ Outbound from client
               ▼
┌─────────────────────────────────────┐
│        Swarm Client                 │
│    (On-Premise Software)            │
├─────────────────────────────────────┤
│  - WebSocket Client                 │
│  - Command Executor                 │
│  - Device Drivers                   │
│  - Configuration Manager            │
└──────────────┬──────────────────────┘
               │
               │ USB/Serial/Network
               ▼
┌─────────────────────────────────────┐
│   Laboratory Hardware Devices       │
│  (Liquid Handlers, Arms, etc.)      │
└─────────────────────────────────────┘
```

## Supported Device Types

The client supports the following device categories through PyLabRobot backends:

- **Liquid Handlers**: Hamilton STAR, Hamilton Vantage (via Venus integration)
- **Robotic Arms**: PreciseFlex, Hudson Robotics, and other transporters
- **Shakers**: Inheco, Thermo Scientific, and compatible shakers
- **Centrifuges**: Beckman Coulter, Eppendorf, and compatible centrifuges
- **Sealers**: A4S, Thermo Scientific, and compatible plate sealers
- **Delids**: Brooks Delid systems
- **Custom Devices**: Extensible driver framework for additional hardware

## Installation

### Prerequisites

- **Python 3.10 or higher**
- **Operating System**: Windows 10+ (for Venus integration) or Linux/macOS (for other devices)
- **Hardware**: Computer with physical connections to laboratory devices
- **Network**: Outbound internet access on port 443 (HTTPS/WSS)

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/Cheshire-Labs/swarm-client.git
cd swarm-client

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install the client
pip install -e .
```

### Development Installation

For development with additional tooling:

```bash
pip install -e ".[dev]"
```

This includes pytest, mypy, black, and other development dependencies.

## Configuration

### Basic Configuration

Create a `config.json` file with your device setup:

```json
{
  "client_id": "my_lab_client",
  "site": "boston",
  "lab": "molbio",
  "platform": {
    "url": "wss://swarm.example.com/ws/devices",
    "api_key": "${SWARM_API_KEY}",
    "heartbeat_interval": 30,
    "command_timeout": 60
  },
  "devices": [
    {
      "device_id": "shaker_1",
      "type": "shaker",
      "name": "Inheco Thermoshake",
      "driver": {
        "type": "plr",
        "backend": "InhecoThermoShake",
        "connection": {
          "type": "serial",
          "port": "COM3"
        }
      }
    },
    {
      "device_id": "arm_1",
      "type": "transporter",
      "name": "PreciseFlex 400",
      "driver": {
        "type": "plr",
        "backend": "PreciseFlex400Backend",
        "connection": {
          "type": "tcp",
          "host": "192.168.1.100",
          "tcp_port": 5000
        }
      }
    }
  ]
}
```

### Environment Variables

Set your API key as an environment variable:

```bash
# Windows
set SWARM_API_KEY=sk_swarm_your_api_key_here

# Linux/macOS
export SWARM_API_KEY=sk_swarm_your_api_key_here
```

## Usage

### Starting the Client

```bash
# Run with default config
python -m swarm_client

# Run with custom config file
python -m swarm_client --config /path/to/config.json

# Run with verbose logging
python -m swarm_client --verbose
```

### Testing Connection

Use simulation mode to test without hardware:

```json
{
  "device_id": "sim_shaker",
  "type": "shaker",
  "name": "Simulated Shaker",
  "driver": {
    "type": "sim"
  }
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=swarm_client

# Run specific test file
pytest tests/test_protocol.py
```

### Code Quality

```bash
# Format code
black src/swarm_client

# Type checking
mypy src/swarm_client

# Linting
ruff check src/swarm_client
```

## Security

### Network Security

- **Outbound Connections Only**: The client initiates outbound WSS connections on port 443, making it firewall-friendly and eliminating the need for inbound port configuration
- **TLS Encryption**: All communication uses WebSocket Secure (WSS) with TLS 1.2+
- **Certificate Validation**: Server certificates are validated against trusted CA certificates

### Authentication

- **API Key-based**: Each client authenticates using a unique API key
- **Environment Variables**: API keys should be stored in environment variables, never in config files
- **Key Revocation**: API keys can be revoked remotely via the Swarm backend

### Audit Trail

All commands and responses are logged with:
- Client ID
- Device ID
- Command type and parameters
- Timestamp
- Success/failure status
- Error details (if applicable)

## Troubleshooting

### Connection Issues

**Problem**: Client cannot connect to Swarm

**Solutions**:
- Verify `SWARM_API_KEY` environment variable is set correctly
- Check internet connectivity and firewall settings (outbound port 443)
- Confirm server URL in config.json
- Review client logs for connection errors

### Device Communication Failures

**Problem**: Commands fail to execute on hardware

**Solutions**:
- Verify device is powered on and connected
- Check COM port or IP address in configuration
- Test device with manufacturer's software
- Review device-specific logs
- Ensure proper cable connections and drivers installed

## Protocol and Message Format

The client communicates with Swarm using JSON-formatted messages over WebSocket:

### Command Message (Swarm → Client)
```json
{
  "type": "command",
  "payload": {
    "command_id": "uuid",
    "device_id": "shaker_1",
    "command": "shake",
    "params": {
      "speed": 800,
      "duration": 60
    }
  }
}
```

### Response Message (Client → Swarm)
```json
{
  "type": "response",
  "payload": {
    "command_id": "uuid",
    "success": true,
    "result": null,
    "error": null
  }
}
```

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0-only)**.

See the [LICENSE](LICENSE) file for the full license text.

## Support

- **Issue Tracker**: [GitHub Issues](https://github.com/Cheshire-Labs/swarm-client/issues)

## Acknowledgments

### PyLabRobot

This project uses [PyLabRobot](https://github.com/PyLabRobot/pylabrobot), an open-source, hardware-agnostic interface for liquid-handling robots and accessories. PyLabRobot was developed for the Sculpting Evolution Group at the MIT Media Lab.

If you use this software in academic research, please cite PyLabRobot:

> Wierenga, R.P., Golas, S.M., Ho, W., Coley, C.W., & Esvelt, K.M. (2023). PyLabRobot: An open-source, hardware-agnostic interface for liquid-handling robots and accessories. *Device*, 1(4), 100111. https://doi.org/10.1016/j.device.2023.100111
