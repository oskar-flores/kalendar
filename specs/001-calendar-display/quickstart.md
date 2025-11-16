# Quickstart Guide: Multi-Calendar E-Paper Display

**Feature**: 001-calendar-display
**Target**: Developers setting up the project for the first time
**Time to first test run**: 5 minutes (on development machine)

---

## Prerequisites

- **Python**: 3.11 or higher
- **uv**: Modern Python package manager ([install guide](https://github.com/astral-sh/uv))
- **Git**: For cloning repository
- **Optional**: Raspberry Pi Zero W for hardware testing

---

## Development Machine Setup (5 minutes)

### 1. Clone Repository

```bash
git clone <repository-url>
cd kalendar
git checkout 001-calendar-display
```

### 2. Install Dependencies

```bash
# Install all dependencies and create virtual environment
uv sync

# Verify installation
uv run python --version  # Should show 3.11+
```

### 3. Run Tests

```bash
# Run full test suite (no hardware needed)
uv run pytest

# Run with coverage
uv run pytest --cov=src/kalendar

# Run only unit tests (fast)
uv run pytest tests/unit/

# Run integration tests (uses mocks, no network)
uv run pytest tests/integration/
```

### 4. Type Checking and Linting

```bash
# Type check
uv run mypy src/

# Lint and format
uv run ruff check .
uv run ruff format .
```

---

## Project Structure Overview

```
kalendar/
├── src/kalendar/              # Source code (Clean Architecture layers)
│   ├── domain/                # Domain models and business logic
│   ├── application/           # Use cases and orchestration
│   ├── infrastructure/        # External integrations (APIs, hardware, filesystem)
│   ├── presentation/          # Display rendering and templates
│   └── cli/                   # Command-line interface
│
├── tests/                     # Test suite
│   ├── unit/                  # Fast tests, no I/O
│   ├── integration/           # Tests with mocked external dependencies
│   └── contract/              # Interface compliance tests
│
├── specs/001-calendar-display/  # Design documentation
│   ├── spec.md                # Feature specification
│   ├── plan.md                # Implementation plan (this document's sibling)
│   ├── research.md            # Technology research findings
│   ├── data-model.md          # Domain entities
│   ├── contracts/             # Interface definitions
│   └── quickstart.md          # This file
│
├── config/                    # Configuration examples
│   └── example.config.yaml    # Example configuration file
│
├── pyproject.toml             # Python project metadata and dependencies
└── README.md                  # Project overview
```

---

## Running the Application (Development)

### Simulator Mode (No Hardware)

Run the calendar display using a mock display driver that saves to a file:

```bash
# Create a test configuration
cp config/example.config.yaml config/dev.config.yaml

# Edit config/dev.config.yaml with your settings
# (Or use environment variables - see Configuration section below)

# Run once (simulate daily refresh)
uv run kalendar refresh --config config/dev.config.yaml --simulator

# Output will be saved to ./output/calendar_display.png
```

### Watch Mode (Auto-refresh on code changes)

```bash
# Install watchdog for file watching
uv add --dev watchdog

# Run in watch mode (refreshes on code changes)
uv run kalendar watch --config config/dev.config.yaml --simulator
```

---

## Configuration

### Minimal Configuration (config/dev.config.yaml)

```yaml
refresh_hour: 0  # Midnight
timezone: "America/New_York"
week_start_day: 0  # Monday

calendar_sources:
  # Add your calendar sources after setting up credentials (see below)
  []

display:
  max_daily_events: 5
  layout: "horizontal"
```

### Setting Up Calendar Sources

#### Google Calendar

1. **Create Google Cloud Project**:
   - Go to https://console.cloud.google.com/
   - Create new project
   - Enable Google Calendar API
   - Create OAuth 2.0 credentials (Desktop application type)
   - Download `credentials.json`

2. **Initial Authorization** (on development machine):
   ```bash
   # Place credentials.json in config/
   uv run kalendar auth google --credentials config/credentials.json

   # This will:
   # 1. Open browser for Google OAuth flow
   # 2. Save token.json with refresh token
   ```

3. **Add to configuration**:
   ```yaml
   calendar_sources:
     - id: "google-primary"
       name: "My Google Calendar"
       source_type: "google"
       calendar_id: "primary"  # or specific calendar ID
       enabled: true
   ```

4. **Credentials file** (config/credentials.json):
   ```json
   {
     "google": {
       "token_file": "config/google_token.json",
       "credentials_file": "config/google_credentials.json"
     }
   }
   ```

#### Apple iCloud Calendar (CalDAV)

1. **Generate App-Specific Password**:
   - Go to https://appleid.apple.com/
   - Sign in
   - Security section → App-Specific Passwords
   - Generate password (save it securely)

2. **Find Calendar URL**:
   ```bash
   # Use caldav library to discover calendars
   uv run kalendar discover-caldav \
     --username your_apple_id@icloud.com \
     --password xxxx-xxxx-xxxx-xxxx  # app-specific password

   # Output will show calendar names and URLs
   ```

3. **Add to configuration**:
   ```yaml
   calendar_sources:
     - id: "icloud-family"
       name: "Family Calendar"
       source_type: "caldav"
       calendar_id: "https://caldav.icloud.com/.../calendar/"
       enabled: true
   ```

4. **Credentials file** (config/credentials.json):
   ```json
   {
     "caldav": {
       "username": "your_apple_id@icloud.com",
       "app_password": "xxxx-xxxx-xxxx-xxxx"
     }
   }
   ```

---

## Test-Driven Development Workflow

Following Constitution Principle II (TDD is **NON-NEGOTIABLE**):

### 1. Red - Write Failing Test

```python
# tests/unit/domain/test_calendar_event.py

def test_calendar_event_is_multi_day():
    """Event spanning multiple days should return True for is_multi_day()."""
    # Arrange
    event = CalendarEvent(
        id="test-1",
        calendar_source_id="source-1",
        title="Weekend Trip",
        start_datetime=datetime(2025, 11, 15, 9, 0),
        end_datetime=datetime(2025, 11, 17, 18, 0),  # 2 days later
        is_all_day=False
    )

    # Act
    result = event.is_multi_day()

    # Assert
    assert result is True
```

```bash
# Run test - should fail (method not implemented yet)
uv run pytest tests/unit/domain/test_calendar_event.py::test_calendar_event_is_multi_day -v
```

### 2. Green - Implement Minimal Code

```python
# src/kalendar/domain/models/event.py

@dataclass
class CalendarEvent:
    # ... fields ...

    def is_multi_day(self) -> bool:
        """Returns True if event spans multiple calendar days."""
        return self.end_datetime.date() > self.start_datetime.date()
```

```bash
# Run test - should pass
uv run pytest tests/unit/domain/test_calendar_event.py::test_calendar_event_is_multi_day -v
```

### 3. Refactor - Improve Design

```python
# No refactoring needed for this simple case
# But if method was complex, refactor while keeping tests green
```

### 4. Commit

```bash
git add tests/unit/domain/test_calendar_event.py src/kalendar/domain/models/event.py
git commit -m "Add CalendarEvent.is_multi_day() method

Test: test_calendar_event_is_multi_day
Verifies that events spanning multiple days are correctly identified."
```

---

## Raspberry Pi Zero W Setup

### 1. Prepare Pi Zero

```bash
# On your development machine, prepare SD card with Raspberry Pi OS Lite
# (Use Raspberry Pi Imager: https://www.raspberrypi.com/software/)

# SSH into Pi Zero
ssh pi@raspberrypi.local

# Update system
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Install System Dependencies

```bash
# Python 3.11 (if not already installed)
sudo apt-get install python3.11 python3.11-venv python3-pip -y

# WeasyPrint system dependencies
sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0 -y

# Waveshare e-paper dependencies
sudo apt-get install python3-pil python3-numpy -y

# Enable SPI for e-paper display
sudo raspi-config
# Navigate to: Interfacing Options -> SPI -> Yes
# Reboot when prompted
```

### 3. Install uv on Pi Zero

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

### 4. Deploy Application

```bash
# On development machine, create deployment package
git archive --format=tar.gz --output=kalendar.tar.gz 001-calendar-display

# Transfer to Pi Zero
scp kalendar.tar.gz pi@raspberrypi.local:~/

# On Pi Zero, extract and install
ssh pi@raspberrypi.local
cd ~
tar -xzf kalendar.tar.gz -C kalendar
cd kalendar
uv sync
```

### 5. Transfer Credentials

```bash
# On development machine, copy authorized tokens to Pi Zero
scp config/google_token.json pi@raspberrypi.local:~/kalendar/config/
scp config/credentials.json pi@raspberrypi.local:~/kalendar/config/

# Secure credentials on Pi Zero
ssh pi@raspberrypi.local
chmod 600 ~/kalendar/config/credentials.json
chmod 600 ~/kalendar/config/google_token.json
```

### 6. Test Hardware

```bash
# On Pi Zero, test e-paper display
uv run kalendar test-display

# Test calendar sync
uv run kalendar test-sync --config config/dev.config.yaml

# Full refresh test (fetch + render + display)
uv run kalendar refresh --config config/dev.config.yaml
```

### 7. Configure Systemd Service (Auto-refresh)

```bash
# Create systemd service file
sudo nano /etc/systemd/system/kalendar.service
```

```ini
[Unit]
Description=Kalendar E-Paper Display
After=network.target

[Service]
Type=oneshot
User=pi
WorkingDirectory=/home/pi/kalendar
ExecStart=/home/pi/.cargo/bin/uv run kalendar refresh --config /home/pi/kalendar/config/dev.config.yaml

[Install]
WantedBy=multi-user.target
```

```bash
# Create systemd timer for daily refresh at configured hour
sudo nano /etc/systemd/system/kalendar.timer
```

```ini
[Unit]
Description=Kalendar Daily Refresh Timer
Requires=kalendar.service

[Timer]
OnCalendar=daily
Persistent=true
Unit=kalendar.service

[Install]
WantedBy=timers.target
```

```bash
# Enable and start timer
sudo systemctl daemon-reload
sudo systemctl enable kalendar.timer
sudo systemctl start kalendar.timer

# Check status
sudo systemctl status kalendar.timer
sudo journalctl -u kalendar.service -f  # View logs
```

---

## Common Development Tasks

### Add a New Domain Model

1. Write test in `tests/unit/domain/test_new_model.py`
2. Implement model in `src/kalendar/domain/models/new_model.py`
3. Add type hints and docstrings
4. Run: `uv run pytest tests/unit/domain/test_new_model.py`
5. Run: `uv run mypy src/kalendar/domain/models/new_model.py`

### Add a New Use Case

1. Write test in `tests/unit/application/test_new_usecase.py`
2. Define use case in `src/kalendar/application/usecases/new_usecase.py`
3. Inject dependencies via constructor (use interfaces from contracts/)
4. Run: `uv run pytest tests/unit/application/test_new_usecase.py`

### Add a New Infrastructure Adapter

1. Define interface in `specs/001-calendar-display/contracts/INewAdapter.py`
2. Write contract test in `tests/contract/test_new_adapter_contract.py`
3. Write integration test in `tests/integration/test_new_adapter.py` (with mocks)
4. Implement adapter in `src/kalendar/infrastructure/new_adapter.py`
5. Run contract tests against implementation

### Debug Memory Usage (Pi Zero)

```bash
# On Pi Zero, monitor memory during refresh
uv run kalendar refresh --config config/dev.config.yaml --profile-memory

# Output will show peak memory usage at each stage:
# - After calendar fetch: XXX MB
# - After HTML render: XXX MB
# - After image processing: XXX MB
# - After display update: XXX MB
```

---

## Troubleshooting

### Tests failing with import errors

```bash
# Ensure you're using uv run, not direct python
uv run pytest  # Correct
python -m pytest  # May fail if venv not activated
```

### Google Calendar authentication fails on Pi Zero

```bash
# Ensure token.json was copied correctly
ls -la ~/kalendar/config/google_token.json

# Test token refresh
uv run kalendar test-auth google
```

### E-paper display not updating

```bash
# Check SPI is enabled
ls /dev/spidev*  # Should show /dev/spidev0.0 and /dev/spidev0.1

# Test display hardware
uv run kalendar test-display --pattern test

# Check GPIO permissions
sudo usermod -a -G spi,gpio pi
```

### WeasyPrint rendering too slow on Pi Zero

```bash
# Benchmark rendering
uv run kalendar benchmark-render --iterations 5

# If >20 seconds, simplify HTML template
# See presentation/templates/calendar_view.html
```

---

## Next Steps

1. **Read the spec**: Review [spec.md](./spec.md) for feature requirements
2. **Review architecture**: See [plan.md](./plan.md) for design decisions
3. **Explore contracts**: Check [contracts/](./contracts/) for interface definitions
4. **Start implementing**: Follow TDD workflow (Red-Green-Refactor)
5. **Run benchmarks**: Test on actual Pi Zero hardware early

---

## Getting Help

- **Constitution**: See [.specify/memory/constitution.md](../../.specify/memory/constitution.md) for project principles
- **Issues**: Report bugs or questions in GitHub Issues
- **Logs**: Check `/var/log/kalendar/` on Pi Zero for runtime errors

---

**Happy coding! Remember: Tests first, always. 🧪**
