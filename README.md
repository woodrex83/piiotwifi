# piiotwifi

Refer to [cjimti/iotwifi](https://github.com/cjimti/iotwifi)

Python implementation of the IOT WiFi management system for lagacy Raspberry Pi, providing simultaneous AP (Access Point) and Station modes.

## Changes from Original Go Version

This Python version includes the following modifications:

- **Framework**: Uses Bottle instead of Gorilla Mux for HTTP API server
- **ARM64**: Use arm64v8 instead of arm32v6 as base image
- **Simplified API**: Removed `/scan` and `/kill` endpoints as requested
- **Maintained Functionality**: Preserves core AP+STA WiFi management capabilities

## API Endpoints

- `GET /status` - Get current WiFi connection status
- `POST /connect` - Connect to a WiFi network

## Requirements

- **Bullseye (deb11, not supported Bookworm or later)**
- Python 3.9-3.12
- Raspberry Pi with WiFi capability
- Root privileges for network interface management

## Installation and Usage

### Method 1: Docker (Recommended)

```bash
# Build the Python version
docker build -f Dockerfile.python -t piiotwifi .

# Run the container
docker run --rm --privileged --net host \
    -v $(pwd)/cfg/wificfg.json:/app/cfg/wificfg.json \
    piiotwifi
```

### Method 2: Direct Python Execution

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
sudo python3 main.py
```

## Configuration

The application uses the same JSON configuration format as the original Go version:

```json
{
  "dnsmasq_cfg": {
    "address": "/#/192.168.27.1",
    "dhcp_range": "192.168.27.100,192.168.27.150,1h",
    "vendor_class": "set:device,IoT"
  },
  "host_apd_cfg": {
    "ip": "192.168.27.1",
    "ssid": "iot-wifi-cfg-3",
    "wpa_passphrase": "iotwifipass",
    "channel": "6"
  },
  "wpa_supplicant_cfg": {
    "cfg_file": "/etc/wpa_supplicant/wpa_supplicant.conf"
  }
}
```

## Environment Variables

- `IOTWIFI_CFG` - Path to configuration file (default: `cfg/wificfg.json`)
- `IOTWIFI_PORT` - HTTP server port (default: `8080`)

## API Usage Examples

### Get WiFi Status

```bash
curl http://192.168.27.1:8080/status
```

### Connect to WiFi Network

```bash
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"ssid":"MyNetwork","psk":"mypassword"}' \
    http://192.168.27.1:8080/connect
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements.txt

# Run type checking
mypy *.py

# Run the application in debug mode
python3 main.py
```

### Code Style

This project follows Python best practices:

- Type hints for all function signatures
- Pydantic models for data validation
- Structured logging with JSON output
- Error handling with appropriate HTTP status codes

## Differences from Go Version

| Feature            | Go Version            | Python Version                  |
| ------------------ | --------------------- | ------------------------------- |
| HTTP Framework     | Gorilla Mux           | Bottle                          |
| Type System        | Go structs            | Python + Pydantic               |
| Validation         | Manual                | Pydantic automatic              |
| Endpoints          | 4 endpoints           | 2 endpoints (removed scan/kill) |
| Process Management | Channels + Goroutines | Threading + subprocess          |
| Logging            | Bunyan                | Python logging (JSON format)    |

The Python version maintains the same core WiFi management functionality while providing a more modern Python-based API with enhanced type safety and data validation.
