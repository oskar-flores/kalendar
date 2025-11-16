# Kalendar - Multi-Calendar E-Paper Display

A Raspberry Pi Zero W-based calendar display system that aggregates events from Google Calendar and Apple iCloud, rendering them on a Waveshare 7.5" 3-color e-paper display.

## Features

- **Multi-source calendar aggregation**: Combine events from Google Calendar and iCloud (CalDAV)
- **Monthly calendar view**: Full month grid with current day highlighted
- **Today's events section**: Detailed view of today's events with time and location
- **Automatic daily refresh**: Scheduled updates at configurable time
- **E-paper display**: Low-power 3-color (black/red/white) e-ink display
- **Offline support**: Displays cached data if sync fails

## Quick Start

See [specs/001-calendar-display/quickstart.md](specs/001-calendar-display/quickstart.md) for detailed setup instructions.

### Development Machine (5 minutes)

```bash
# Clone repository
git clone <repository-url>
cd kalendar
git checkout 001-calendar-display

# Install dependencies using uv
uv sync

# Run tests
uv run pytest

# Run in simulator mode (no hardware needed)
cp config/example.config.yaml config/dev.config.yaml
uv run kalendar refresh --config config/dev.config.yaml --simulator
```

### Raspberry Pi Zero W Deployment

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install python3.11 python3-cffi python3-brotli \
  libpango-1.0-0 libpangoft2-1.0-0 python3-pil python3-numpy -y

# Enable SPI for e-paper display
sudo raspi-config  # Interfacing Options -> SPI -> Yes

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Deploy application
cd ~/kalendar
uv sync

# Configure calendar sources (see quickstart.md)
cp config/example.config.yaml config/config.yaml
# Edit config/config.yaml with your calendar sources

# Test display
uv run kalendar test-display

# Manual refresh
uv run kalendar refresh --config config/config.yaml

# Enable systemd service for automatic daily refresh (see quickstart.md)
```

## Hardware Requirements

- **Raspberry Pi Zero W** (or any Raspberry Pi model)
- **Waveshare 7.5inch e-Paper HAT (B)** - 800×480 3-color display
- **MicroSD card** (8GB+, Raspberry Pi OS Lite recommended)
- **Power supply** (5V micro-USB for Pi Zero W)

## Calendar Setup

### Google Calendar

1. Create OAuth credentials at https://console.cloud.google.com/
2. Enable Google Calendar API
3. Download credentials.json
4. Run authorization: `uv run kalendar auth google --credentials config/credentials.json`

### Apple iCloud Calendar (CalDAV)

1. Generate app-specific password at https://appleid.apple.com/
2. Discover calendar URLs: `uv run kalendar discover-caldav --username your@icloud.com --password xxxx-xxxx-xxxx-xxxx`
3. Add calendar URLs to config.yaml

See [quickstart.md](specs/001-calendar-display/quickstart.md) for detailed instructions.

## Architecture

Built with Clean Architecture principles:

- **Domain layer**: Calendar events, display configuration, business logic
- **Application layer**: Use cases for syncing, rendering, and displaying
- **Infrastructure layer**: Google Calendar API, CalDAV client, e-paper driver, filesystem cache
- **Presentation layer**: HTML/CSS templates for calendar rendering

All external dependencies are abstracted behind interfaces, enabling testing without hardware or network access.

## Development

### Test-Driven Development

This project follows strict TDD workflow (Red-Green-Refactor):

```bash
# Run all tests
uv run pytest

# Run specific test categories
uv run pytest -m unit          # Fast unit tests
uv run pytest -m integration   # Integration tests (mocked dependencies)
uv run pytest -m contract      # Interface compliance tests

# Run with coverage
uv run pytest --cov=src/kalendar --cov-report=html
```

### Code Quality

```bash
# Type checking
uv run mypy src/

# Linting
uv run ruff check .

# Formatting
uv run ruff format .
```

## Project Structure

```
kalendar/
├── src/kalendar/          # Source code
│   ├── domain/            # Domain models and business logic
│   ├── application/       # Use cases
│   ├── infrastructure/    # External integrations
│   ├── presentation/      # Display templates
│   └── cli/               # Command-line interface
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── contract/          # Contract tests
├── config/                # Configuration files
├── specs/001-calendar-display/  # Design documentation
│   ├── spec.md            # Feature specification
│   ├── plan.md            # Implementation plan
│   ├── quickstart.md      # Developer guide
│   └── contracts/         # Interface definitions
└── pyproject.toml         # Python project configuration
```

## Documentation

- **Quickstart Guide**: [specs/001-calendar-display/quickstart.md](specs/001-calendar-display/quickstart.md)
- **Feature Specification**: [specs/001-calendar-display/spec.md](specs/001-calendar-display/spec.md)
- **Implementation Plan**: [specs/001-calendar-display/plan.md](specs/001-calendar-display/plan.md)
- **Technical Research**: [specs/001-calendar-display/research.md](specs/001-calendar-display/research.md)
- **Data Model**: [specs/001-calendar-display/data-model.md](specs/001-calendar-display/data-model.md)

## License

MIT

## Contributing

This project follows the principles defined in [.specify/memory/constitution.md](.specify/memory/constitution.md).

Key principles:
- Clean Architecture with dependency inversion
- Test-Driven Development (TDD) - tests first, always
- Resource constraints optimization for Raspberry Pi Zero
- Modern Python tooling (uv, pytest, ruff, mypy)
- Reliability and graceful degradation
