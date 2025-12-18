# Swarm Client

WebSocket client for connecting local laboratory devices to the [Swarm](https://cheshirelabs.io/docs/swarm/intro) device integration platform.

## Overview

Swarm Client runs on computers physically connected to laboratory hardware and manages bidirectional communication with the Swarm platform via secure WebSocket connections. This enables remote control of lab devices through the Swarm API and MCP tools.

**Full documentation**: [cheshirelabs.io/docs/swarm/swarm-client](https://cheshirelabs.io/docs/swarm/swarm-client)

## Quick Start

### Prerequisites

- Python 3.10+
- [Swarm API key](https://cheshirelabs.io/docs/swarm/getting-started)

### Installation

```bash
git clone https://github.com/Cheshire-Labs/swarm-client.git
cd swarm-client
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -e .
```

### Configuration

Set your API key:

```bash
# Windows
set SWARM_API_KEY=sk_swarm_your_api_key_here

# Linux/macOS
export SWARM_API_KEY=sk_swarm_your_api_key_here
```

Create a `config.json` file. Here's a minimal example using simulation mode:

```json
{
  "client_id": "my-workstation",
  "site": "test",
  "lab": "simulation",
  "platform": {
    "url": "wss://swarm.cheshirelabs.io/ws/devices",
    "api_key": "${SWARM_API_KEY}"
  },
  "devices": [
    {
      "device_id": "sim-transporter",
      "type": "transporter",
      "name": "Simulated Arm",
      "driver": { "type": "sim" }
    }
  ]
}
```

For real hardware configuration, see the [configuration docs](https://cheshirelabs.io/docs/swarm/swarm-client).

### Run

```bash
python -m swarm_client --config config.json
# Add --verbose for debug logging
```

## Supported Devices

See [supported devices](https://cheshirelabs.io/docs/swarm/devices) for the full list of compatible hardware.

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/swarm_client

# Format code
black src/swarm_client
```

## Resources

- **Documentation**: [cheshirelabs.io/docs/swarm](https://cheshirelabs.io/docs/swarm/intro)
- **Troubleshooting**: [cheshirelabs.io/docs/swarm/troubleshooting](https://cheshirelabs.io/docs/swarm/troubleshooting)
- **Issues**: [GitHub Issues](https://github.com/Cheshire-Labs/swarm-client/issues)

## License

[AGPL-3.0-only](LICENSE)

## Acknowledgments

This project uses [PyLabRobot](https://github.com/PyLabRobot/pylabrobot), an open-source, hardware-agnostic interface for liquid-handling robots and accessories.

> Wierenga, R.P., Golas, S.M., Ho, W., Coley, C.W., & Esvelt, K.M. (2023). PyLabRobot: An open-source, hardware-agnostic interface for liquid-handling robots and accessories. *Device*, 1(4), 100111. https://doi.org/10.1016/j.device.2023.100111
