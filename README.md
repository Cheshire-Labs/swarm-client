# Orca Client Driver

WebSocket client for connecting local laboratory devices to the Orca Cloud orchestration system.

## Overview

The Orca Client Driver enables remote control of laboratory automation equipment through the Orca Cloud platform. This client software runs on computers physically connected to laboratory hardware (liquid handlers, robotic arms, centrifuges, shakers, sealers, etc.) and manages bidirectional communication with the Orca Cloud server via secure WebSocket connections.

**Key Features:**
- Secure WebSocket communication (WSS) with Orca Cloud
- Support for multiple device types via PyLabRobot backends
- Concurrent device operation management
- Automatic reconnection and error handling
- YAML-based configuration
- Comprehensive logging and audit trail

## Architecture

```
┌─────────────────────────────────────┐
│      Orca Cloud Platform            │
│    (Workflow Orchestration)         │
└──────────────┬──────────────────────┘
               │
               │ WebSocket (WSS/443)
               │ Outbound from client
               ▼
┌─────────────────────────────────────┐
│      Orca Client Driver             │
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

The client driver supports the following device categories through PyLabRobot backends:

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
git clone https://github.com/Cheshire-Labs/orca-client-driver.git
cd orca-client-driver

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# Install the client driver
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

Create a `config.yaml` file with your device setup:

```yaml
server:
  url: "wss://cloud.orca.io/ws"
  api_key: "${ORCA_API_KEY}"
  client_id: "my_lab_client"
  reconnect_interval: 5
  heartbeat_interval: 30

devices:
  - device_id: "shaker_1"
    type: "shaker"
    backend:
      driver: "plr"
      backend_type: "inheco"
      port: "COM3"

  - device_id: "centrifuge_1"
    type: "centrifuge"
    backend:
      driver: "plr"
      backend_type: "beckman"
      port: "COM4"

logging:
  level: "INFO"
  file: "orca_client.log"
  max_size_mb: 10
  backup_count: 3
```

### Environment Variables

Set your API key as an environment variable:

```bash
# Windows
set ORCA_API_KEY=your_api_key_here

# Linux/macOS
export ORCA_API_KEY=your_api_key_here
```

### Device-Specific Configuration

#### Liquid Handler (Hamilton Venus)

```yaml
- device_id: "hamilton_star"
  type: "liquid_handler"
  backend:
    driver: "venus"
    methods_folder: "C:\\Methods"
    run_control_path: "C:\\Program Files\\Hamilton\\Bin\\HxRun.exe"
    init_method: "Initialize.hsl"
    open_method: "Open.hsl"
    close_method: "Close.hsl"
```

#### Robotic Arm (PreciseFlex)

```yaml
- device_id: "arm_1"
  type: "transporter"
  backend:
    driver: "plr"
    backend_type: "precise_flex"
    ip: "192.168.1.100"
  teachpoints_file: "teachpoints.json"
```

## Usage

### Starting the Client

```bash
# Run with default config.yaml
orca-client-driver

# Run with custom config file
orca-client-driver --config /path/to/config.yaml

# Run with verbose logging
orca-client-driver --log-level DEBUG
```

### Testing Connection

Use simulation mode to test without hardware:

```yaml
devices:
  - device_id: "sim_shaker"
    type: "shaker"
    backend:
      driver: "sim"
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=orca_client_driver

# Run specific test file
pytest tests/test_client.py
```

### Code Quality

```bash
# Format code
black src/orca_client_driver

# Type checking
mypy src/orca_client_driver

# Linting
ruff check src/orca_client_driver
```

## Security

### Network Security

- **Outbound Connections Only**: The client initiates outbound WSS connections on port 443, making it firewall-friendly and eliminating the need for inbound port configuration
- **TLS Encryption**: All communication uses WebSocket Secure (WSS) with TLS 1.2+
- **Certificate Validation**: Server certificates are validated against trusted CA certificates

### Authentication

- **API Key-based**: Each client authenticates using a unique API key
- **Environment Variables**: API keys should be stored in environment variables, never in config files
- **Key Revocation**: API keys can be revoked remotely via the Orca Cloud dashboard

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

**Problem**: Client cannot connect to Orca Cloud

**Solutions**:
- Verify `ORCA_API_KEY` environment variable is set correctly
- Check internet connectivity and firewall settings (outbound port 443)
- Confirm server URL in config.yaml
- Review client logs for connection errors

### Device Communication Failures

**Problem**: Commands fail to execute on hardware

**Solutions**:
- Verify device is powered on and connected
- Check COM port or IP address in configuration
- Test device with manufacturer's software
- Review device-specific logs
- Ensure proper cable connections and drivers installed

### Configuration Problems

**Problem**: Client fails to start or load config

**Solutions**:
- Validate YAML syntax (use a YAML validator)
- Check file paths are correct and accessible
- Verify device backend types are supported
- Review error messages in console output

## Protocol and Message Format

The client communicates with Orca Cloud using JSON-formatted messages over WebSocket:

### Command Message (Cloud → Client)
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

### Response Message (Client → Cloud)
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

For full protocol documentation, see the [Protocol Reference](docs/protocol.md).

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Format code with `black`
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

All contributors must sign a Contributor License Agreement (CLA).

## License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0-only)**.

See the [LICENSE](LICENSE) file for the full license text.

**Key points about AGPL-3.0:**
- You are free to use, modify, and distribute this software
- If you modify and deploy this software (including network use), you must make your modifications available under AGPL-3.0
- Commercial use is permitted, but modifications must be shared
- No warranty is provided

## Support

- **Issue Tracker**: [GitHub Issues](https://github.com/Cheshire-Labs/orca-client-driver/issues)

## Acknowledgments

### PyLabRobot

This project uses [PyLabRobot](https://github.com/PyLabRobot/pylabrobot), an open-source, hardware-agnostic interface for liquid-handling robots and accessories. PyLabRobot was developed for the Sculpting Evolution Group at the MIT Media Lab.

If you use this software in academic research, please cite PyLabRobot:

> Wierenga, R.P., Golas, S.M., Ho, W., Coley, C.W., & Esvelt, K.M. (2023). PyLabRobot: An open-source, hardware-agnostic interface for liquid-handling robots and accessories. *Device*, 1(4), 100111. https://doi.org/10.1016/j.device.2023.100111

```bibtex
@article{wierenga2023pylabrobot,
  title={PyLabRobot: An open-source, hardware-agnostic interface for liquid-handling robots and accessories},
  author={Wierenga, Rick P. and Golas, Stefan M. and Ho, Wilson and Coley, Connor W. and Esvelt, Kevin M.},
  journal={Device},
  volume={1},
  number={4},
  pages={100111},
  year={2023},
  publisher={Elsevier},
  doi={10.1016/j.device.2023.100111}
}
```
