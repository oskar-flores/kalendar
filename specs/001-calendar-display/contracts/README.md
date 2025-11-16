# API Contracts

This directory contains interface definitions (contracts) for all external dependencies and layer boundaries in the Kalendar application.

## Purpose

These interfaces enable **Clean Architecture** (Constitution Principle I) and **Test-Driven Development** (Constitution Principle II) by:

1. **Dependency Inversion**: Domain and application layers depend on these interfaces, not concrete implementations
2. **Testability**: Mock implementations allow testing without hardware, network, or filesystem
3. **Flexibility**: Swap implementations (e.g., different display hardware) without changing business logic

## Contracts

### ICalendarSource.py

**Purpose**: Abstract calendar providers (Google Calendar, CalDAV/iCloud)

**Implementations**:
- `GoogleCalendarSource` - Uses google-api-python-client
- `CalDAVSource` - Uses caldav library for iCloud
- `MockCalendarSource` - Returns fixture data for testing

**Key Methods**:
- `fetch_events(start_date, end_date)` - Fetch events from source
- `test_connection()` - Verify connectivity
- `refresh_auth()` - Refresh OAuth/auth credentials

### IDisplayDriver.py

**Purpose**: Abstract e-paper display hardware

**Implementations**:
- `WaveshareEPD75BDriver` - Real hardware driver
- `MockDisplayDriver` - Saves to file for testing
- `SimulatorDisplayDriver` - Shows in window for development

**Key Methods**:
- `initialize()` - Initialize hardware
- `display(black_image, red_image)` - Update display (two-buffer system)
- `sleep()` - Enter low-power mode

**Note**: Waveshare 7.5" HAT (B) uses separate buffers for black and red layers.

### IImageRenderer.py

**Purpose**: Abstract HTML/CSS rendering to images

**Implementations**:
- `WeasyPrintRenderer` - Uses weasyprint library
- `MockRenderer` - Returns test fixture images

**Key Methods**:
- `render_html_string(html, css, width, height)` - Render HTML string
- `render_template(template_name, context)` - Render from template file

### ICache.py

**Purpose**: Abstract persistent storage for calendar data

**Implementations**:
- `FileSystemCache` - JSON files in /var/cache/kalendar/
- `InMemoryCache` - For testing
- `SQLiteCache` - Future: if query performance becomes issue

**Key Methods**:
- `save_events(source_id, events, timestamp)` - Cache events
- `load_events(source_id)` - Retrieve cached events
- `is_cache_valid(source_id, max_age_hours)` - Check freshness

### IConfigLoader.py

**Purpose**: Abstract configuration loading

**Implementations**:
- `YAMLConfigLoader` - Reads /etc/kalendar/config.yaml
- `InMemoryConfigLoader` - For testing
- `EnvironmentConfigLoader` - Reads from environment variables

**Key Methods**:
- `load_config(path)` - Load configuration
- `load_credentials(path)` - Load auth credentials (separate for security)
- `validate_config(config)` - Validate configuration values

## Usage in Layers

### Domain Layer

**Dependencies**: None (pure business logic)

Domain layer does NOT import any interfaces - it contains pure models and domain services with no external dependencies.

### Application Layer

**Dependencies**: Interfaces from this directory

Application layer use cases (e.g., `SyncCalendarsUseCase`) accept interfaces as constructor parameters:

```python
class SyncCalendarsUseCase:
    def __init__(
        self,
        calendar_sources: List[ICalendarSource],
        cache: ICache,
        config_loader: IConfigLoader,
    ):
        self.calendar_sources = calendar_sources
        self.cache = cache
        self.config_loader = config_loader
```

### Infrastructure Layer

**Dependencies**: Concrete implementations implement these interfaces

Infrastructure layer provides concrete implementations:

```python
from contracts.ICalendarSource import ICalendarSource, CalendarEventDTO

class GoogleCalendarSource(ICalendarSource):
    def fetch_events(self, start_date, end_date) -> List[CalendarEventDTO]:
        # Implementation using google-api-python-client
        ...
```

### Testing

**Dependencies**: Mock implementations

Tests use mock implementations:

```python
def test_sync_calendars():
    # Arrange
    mock_calendar = MockCalendarSource(fixture_events=[...])
    mock_cache = InMemoryCache()
    use_case = SyncCalendarsUseCase([mock_calendar], mock_cache, ...)

    # Act
    result = use_case.execute()

    # Assert
    assert result.success
    assert mock_cache.get_cache_stats()['total_events'] == 5
```

## Contract Testing

Each interface should have a **contract test suite** that verifies any implementation adheres to the contract:

```python
# tests/contract/test_calendar_source_contract.py

def test_calendar_source_contract(calendar_source: ICalendarSource):
    """Contract test that any ICalendarSource implementation must pass."""

    # Test 1: fetch_events returns list of CalendarEventDTO
    events = calendar_source.fetch_events(
        start_date=date(2025, 11, 1),
        end_date=date(2025, 11, 30)
    )
    assert isinstance(events, list)
    for event in events:
        assert isinstance(event, CalendarEventDTO)

    # Test 2: test_connection returns bool
    result = calendar_source.test_connection()
    assert isinstance(result, bool)

    # Test 3: get_source_info returns required keys
    info = calendar_source.get_source_info()
    assert 'source_id' in info
    assert 'source_type' in info
```

Run contract tests against:
- Real implementations (integration tests)
- Mock implementations (unit tests)

## Dependency Injection

Concrete implementations are wired together at application startup using dependency injection:

```python
# main.py or dependency injection container

def create_application():
    # Load configuration
    config_loader = YAMLConfigLoader()
    config = config_loader.load_config()

    # Create calendar sources based on config
    calendar_sources = []
    for source_config in config['calendar_sources']:
        if source_config['source_type'] == 'google':
            calendar_sources.append(GoogleCalendarSource(source_config))
        elif source_config['source_type'] == 'caldav':
            calendar_sources.append(CalDAVSource(source_config))

    # Create other infrastructure
    cache = FileSystemCache(Path('/var/cache/kalendar'))
    renderer = WeasyPrintRenderer()
    display = WaveshareEPD75BDriver()

    # Create use cases with injected dependencies
    sync_use_case = SyncCalendarsUseCase(calendar_sources, cache, config_loader)
    render_use_case = RenderDisplayUseCase(cache, renderer, display, config)

    return Application(sync_use_case, render_use_case)
```

## Adding New Contracts

When adding a new interface:

1. Define interface in this directory (e.g., `INewService.py`)
2. Include abstract base class, DTOs, and custom exceptions
3. Document purpose, implementations, and key methods
4. Create contract test suite in `tests/contract/`
5. Implement concrete version in `src/kalendar/infrastructure/`
6. Implement mock version for testing
7. Update this README

## Relationship to Data Model

Interfaces use **Data Transfer Objects (DTOs)** defined alongside the interface (not domain models).

- Domain models live in `src/kalendar/domain/models/`
- DTOs for interfaces live in `specs/001-calendar-display/contracts/`

DTOs are simple dataclasses for transferring data across layer boundaries. Domain models contain business logic and validation.

Example:

```python
# Contract DTO (in ICalendarSource.py)
@dataclass
class CalendarEventDTO:
    id: str
    title: str
    start_datetime: datetime
    # ... (no methods, simple data)

# Domain Model (in src/kalendar/domain/models/event.py)
@dataclass
class CalendarEvent:
    id: str
    title: str
    start_datetime: datetime
    # ... (includes validation and business logic)

    def is_multi_day(self) -> bool:
        return self.end_datetime.date() > self.start_datetime.date()

    def truncated_title(self, max_length: int) -> str:
        # Business logic for display formatting
        ...
```

Application layer converts between DTOs and domain models.

---

**See Also**:
- [Data Model](../data-model.md) - Domain entities and relationships
- [Clean Architecture Principle](../../.specify/memory/constitution.md#i-clean-architecture--dependency-inversion)
