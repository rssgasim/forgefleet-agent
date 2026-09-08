# ForgeFleet Agent for Windows

A production-ready local Windows application that acts as the bridge between the **ForgeFleet SaaS cloud platform** and physical **FlashForge 3D printers** located on the same local network.

## Architecture

```
                    Internet
                       │
                       ▼
              ┌─────────────────┐
              │  ForgeFleet SaaS│
              │   Cloud / API   │
              └────────┬────────┘
                       │
                 HTTPS / WSS
                       │
                       ▼
              ┌─────────────────┐
              │ ForgeFleet Agent│
              │     Windows     │
              └────────┬────────┘
                       │
                 Local Network
                 Ethernet / Wi-Fi
                       │
              ┌────────┴────────┐
              ▼                 ▼
       FlashForge AD5M    FlashForge AD5X
```

The Agent runs on a Windows computer inside the same LAN as the printers. The cloud platform never attempts to directly access private printer IP addresses. The Agent is responsible for all local network communication.

## Features

✅ **Real Hardware Support**
- FlashForge AD5M and AD5X printers
- Firmware 5.1.8+ compatible
- No mock printers or simulated data

✅ **Local Network Discovery**
- Automatic network interface detection (Ethernet, Wi-Fi)
- Dynamic subnet calculation
- Real FlashForge printer discovery
- Protocol-based validation (not just ping)

✅ **Printer Management**
- Real-time printer status
- Temperature monitoring
- Print progress tracking
- Error detection and reporting
- Adapter architecture for future printer models

✅ **Cloud Synchronization**
- Secure HTTPS/WebSocket connection to ForgeFleet
- Automatic heartbeat and reconnection
- Telemetry collection and transmission
- Command reception and execution
- Printer lifecycle management (CREATE, UPDATE, ONLINE, OFFLINE)

✅ **Persistent State**
- SQLite local database
- Offline operation capability
- Event queue for cloud sync
- Diagnostic logging

✅ **Windows Integration**
- Native Windows service support
- Automatic startup with Windows
- PowerShell installation/management scripts
- PyInstaller executable packaging

## Requirements

### Hardware
- Windows 10 or later
- Network connection (Ethernet or Wi-Fi)
- Access to local network containing FlashForge printers

### Software
- Python 3.11+ (for development)
- FlashForge printer on same LAN (AD5M or AD5X)
- Firmware 5.1.8 or compatible

## Installation

### From Executable (Recommended)

1. Download `ForgeFleet-Agent-Setup.exe` from Releases
2. Run the installer
3. Follow the installation wizard
4. The Agent will register as a Windows service and start automatically

### From Source

```bash
git clone https://github.com/rssgasim/forgefleet-agent.git
cd forgefleet-agent

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure (copy and edit)
copy .env.example .env
# Edit .env with your ForgeFleet API credentials

# Run as service
python -m src.forgefleet_agent.service.windows_service install
python -m src.forgefleet_agent.service.windows_service start
```

## Configuration

Create a `.env` file in the application directory:

```env
# ForgeFleet Cloud API
FORGEFLEET_API_URL=https://api.forgefleet.example.com
FORGEFLEET_AGENT_TOKEN=<your_agent_token>

# Agent Configuration
AGENT_NAME=ForgeFleet Agent
LOG_LEVEL=INFO

# Printer Discovery
DISCOVERY_TIMEOUT_SECONDS=5
TELEMETRY_INTERVAL_SECONDS=5

# Database
DATABASE_PATH=C:\ProgramData\ForgeFleet\agent.db
LOG_PATH=C:\ProgramData\ForgeFleet\logs
```

## Usage

### Windows Service Commands

```powershell
# Start the service
net start ForgeFleetAgent

# Stop the service
net stop ForgeFleetAgent

# Check status
Get-Service ForgeFleetAgent

# View logs
type C:\ProgramData\ForgeFleet\logs\forgefleet_agent.log
```

### Local Status Interface

The Agent provides a lightweight local UI accessible via:

```
http://localhost:9090
```

Shows:
- Agent connection status
- Cloud connection status
- Network interfaces
- Discovered and paired printers
- Real-time telemetry
- Action buttons (Scan, Sync, Restart, View Logs)

### Discovery Process

1. **Automatic Discovery** (Default)
   - Agent automatically scans the local network on startup and periodically
   - Detects FlashForge printers using native FlashForge discovery protocol
   - Validates printer presence and capabilities
   - Synchronizes with ForgeFleet Cloud

2. **Manual Discovery**
   - Use local UI "Scan Printers" button
   - Or API: `POST /agent/discover`

### Pairing Printers

Once discovered, printers must be paired with ForgeFleet:

```bash
curl -X POST http://localhost:9090/api/printers/pair \
  -H "Content-Type: application/json" \
  -d '{
    "printer_ip": "192.168.1.50",
    "workspace_id": "workspace_123"
  }'
```

## Telemetry

The Agent collects real printer telemetry every 5 seconds (configurable):

```json
{
  "printer_id": "AD5M-001234",
  "timestamp": "2024-01-15T10:30:45Z",
  "state": "PRINTING",
  "progress": 45.2,
  "nozzle_temperature": 220.5,
  "bed_temperature": 60.0,
  "current_file": "model.gcode",
  "print_start_time": "2024-01-15T09:45:00Z",
  "estimated_completion_time": "2024-01-15T11:15:00Z"
}
```

## Commands

The Agent supports the following commands from ForgeFleet:

- `DISCOVER_PRINTERS` - Initiate new printer discovery
- `REFRESH_STATUS` - Poll printer status immediately
- `REFRESH_TELEMETRY` - Collect and send telemetry
- `PAUSE_PRINT` - Pause active print job
- `RESUME_PRINT` - Resume paused print job
- `STOP_PRINT` - Stop active print job
- `START_PRINT` - Start a print job (requires file transfer)

All commands return: `command_id`, `printer_id`, `success`, `timestamp`, `error_code`, `error_message`

## Project Structure

```
forgefleet-agent/
│
├── src/
│   └── forgefleet_agent/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── logging.py
│       ├── database.py
│       │
│       ├── cloud/
│       │   ├── client.py
│       │   ├── websocket.py
│       │   ├── authentication.py
│       │   └── models.py
│       │
│       ├── network/
│       │   ├── interfaces.py
│       │   ├── subnet.py
│       │   ├── discovery.py
│       │   └── connectivity.py
│       │
│       ├── printers/
│       │   ├── adapter.py
│       │   ├── registry.py
│       │   ├── models.py
│       │   │
│       │   └── flashforge/
│       │       ├── base.py
│       │       ├── protocol.py
│       │       ├── discovery.py
│       │       ├── ad5m.py
│       │       └── ad5x.py
│       │
│       ├── telemetry/
│       │   ├── collector.py
│       │   └── normalizer.py
│       │
│       ├── commands/
│       │   ├── dispatcher.py
│       │   └── handlers.py
│       │
│       ├── ui/
│       │   ├── server.py
│       │   ├── handlers.py
│       │   └── static/
│       │       ├── index.html
│       │       └── style.css
│       │
│       └── service/
│           ├── runner.py
│           └── windows_service.py
│
├── tests/
│   ├── test_network.py
│   ├── test_discovery.py
│   ├── test_adapters.py
│   ├── test_cloud.py
│   └── test_synchronization.py
│
├── installer/
│   ├── installer.nsi
│   └── assets/
│
├── scripts/
│   ├── build_windows.ps1
│   ├── install_service.ps1
│   ├── start_service.ps1
│   ├── stop_service.ps1
│   └── uninstall_service.ps1
│
├── .env.example
├── requirements.txt
├── pyproject.toml
├── LICENSE
├── .gitignore
└── README.md
```

## Building from Source

### Prerequisites
- Python 3.11+
- Visual C++ Build Tools
- PyInstaller

### Build Steps

```powershell
# Clone repository
git clone https://github.com/rssgasim/forgefleet-agent.git
cd forgefleet-agent

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build executable
.\scripts\build_windows.ps1

# Output: dist/ForgeFleet-Agent.exe
```

### Creating Windows Installer

```powershell
# Install NSIS
# Then run:
makensis installer/installer.nsi

# Output: ForgeFleet-Agent-Setup.exe
```

## Testing

### Unit Tests

```bash
pytest tests/ -v
```

### Integration Tests

Integration tests require a real FlashForge printer on the network:

```bash
pytest tests/integration/ -v --printer-ip=192.168.1.50
```

### Physical Printer Acceptance Tests

See [TESTING.md](TESTING.md) for detailed physical printer acceptance procedures.

## Troubleshooting

### Printer Not Discovered

1. **Verify Network Connectivity**
   ```powershell
   # Check Agent sees network interfaces
   Get-NetAdapter | Where-Object { $_.Status -eq "Up" }
   
   # Ping printer (if IP known)
   ping 192.168.1.50
   ```

2. **Check Logs**
   ```powershell
   type C:\ProgramData\ForgeFleet\logs\forgefleet_agent.log
   ```

3. **Verify Printer Settings**
   - Printer must be on same LAN as Windows PC
   - Printer must have network connectivity (Ethernet or Wi-Fi)
   - Check printer's local IP via printer display menu

4. **Restart Discovery**
   - Use local UI "Scan Printers" button
   - Or restart the service: `net stop ForgeFleetAgent && net start ForgeFleetAgent`

### Cloud Connection Failed

1. **Verify Credentials**
   - Check `.env` file has correct `FORGEFLEET_API_URL` and `FORGEFLEET_AGENT_TOKEN`

2. **Check Network Connectivity**
   ```powershell
   Test-NetConnection -ComputerName api.forgefleet.example.com -Port 443
   ```

3. **View Logs**
   ```powershell
   type C:\ProgramData\ForgeFleet\logs\forgefleet_agent.log | tail -50
   ```

4. **Restart Service**
   ```powershell
   net stop ForgeFleetAgent
   net start ForgeFleetAgent
   ```

### High CPU Usage

1. Check telemetry interval in `.env` (default: 5 seconds)
2. Check discovery is not running continuously
3. Review logs for error loops
4. Ensure printer is responding normally

## Security Considerations

- **No Inbound Ports**: Agent requires no inbound router ports
- **Outbound Only**: All cloud communication is outbound-initiated
- **TLS/HTTPS**: All cloud connections use HTTPS
- **Credential Protection**: Tokens and secrets never logged or exposed
- **Workspace Isolation**: Printers isolated to paired workspace
- **Local API**: Optional local UI uses localhost only, no network exposure

## Development

### Code Standards

- Python 3.11+ with type hints
- Async/await using asyncio
- Structured logging (structlog)
- Unit tests for all major components
- Clear error handling and validation

### Adding New Printer Models

1. Create adapter in `src/forgefleet_agent/printers/flashforge/`
2. Extend `FlashForgeAdapter` base class
3. Implement required protocol methods
4. Add model-specific tests
5. Register in adapter registry

Example:

```python
# src/forgefleet_agent/printers/flashforge/adventurer.py
from .base import FlashForgeAdapter

class FlashForgeAdventerAdapter(FlashForgeAdapter):
    MODEL = "Adventurer"
    SUPPORTED_FIRMWARE = ["5.1.8+"]
    
    async def get_printer_status(self) -> dict:
        # Implement Adventurer-specific protocol
        pass
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run tests: `pytest tests/ -v`
5. Submit a pull request

## License

MIT License - See [LICENSE](LICENSE) file

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation and logs
- Review [TESTING.md](TESTING.md) for printer troubleshooting
- Contact ForgeFleet support

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

**ForgeFleet Agent** - Connecting your 3D printers to the cloud, securely and reliably.