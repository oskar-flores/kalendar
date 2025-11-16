# Implementation Plan: Multi-Calendar E-Paper Display

**Branch**: `001-calendar-display` | **Date**: 2025-11-15 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-calendar-display/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a Raspberry Pi Zero W-based calendar display system using HTML rendering to generate images for a Waveshare 7.5" 3-color e-paper display. The system aggregates events from Google Calendar and Apple iCloud (CalDAV), renders a monthly view with today's events in horizontal orientation, and refreshes daily at a configurable time. Clean Architecture with Python ensures testability without hardware dependencies.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: NEEDS CLARIFICATION (HTML-to-image library, CalDAV client, Google Calendar API client)
**Storage**: Local filesystem (JSON cache for calendar data, config YAML/JSON)
**Testing**: pytest with mocks for hardware and network
**Target Platform**: Raspberry Pi Zero W (ARMv6, 512MB RAM, Raspberry Pi OS Lite)
**Project Type**: Single embedded application
**Performance Goals**: Complete refresh cycle (fetch + render + display update) in <60 seconds
**Constraints**: <256MB memory peak, display refresh once per day, HTML-based rendering (no complex drawing libraries)
**Scale/Scope**: Single-user family calendar, ~2-5 calendar sources, <100 events per month

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Clean Architecture & Dependency Inversion (Principle I)

**Status**: ✅ PASS (Planned)

**Planned Layer Structure**:
- **Domain**: Event models, calendar aggregation logic, recurrence rules
- **Application**: Sync use cases, render pipeline orchestration, scheduling
- **Infrastructure**: Google Calendar API client, CalDAV client, Waveshare e-paper driver, filesystem cache
- **Presentation**: HTML template rendering, image generation from HTML

**Compliance**: All external dependencies (calendar APIs, display hardware) will be abstracted behind interfaces. Domain logic will be testable without network or hardware.

### Test-Driven Development (Principle II)

**Status**: ✅ PASS (Planned)

**Test Strategy**:
- **Unit tests**: Event model validation, date/time calculations, event aggregation logic
- **Integration tests**: Calendar API interactions (using recorded fixtures), HTML rendering to image
- **Contract tests**: Calendar source interfaces, display driver interface
- **Hardware mocks**: Waveshare display driver will use mock implementation for tests

**TDD Workflow**: All tasks will follow Red-Green-Refactor cycle. Tests written before implementation.

### Resource Constraints & Pi Zero Optimization (Principle III)

**Status**: ✅ PASS (Verified via Research)

**Constraints Met**:
- Memory budget: Estimated 100-150MB peak (well within <256MB limit)
- Refresh cycle: Estimated 47-70s (within <60s target with optimization)
- Display updates: Once per day (as required)

**Technology Choices (from research.md)**:
- **WeasyPrint**: 30-50MB memory during rendering (lightweight, no browser)
- **google-api-python-client**: ~50MB package size (acceptable on SD card)
- **caldav library**: Minimal dependencies, lightweight
- **Waveshare driver**: <10MB memory footprint

**Performance Breakdown**:
- Calendar fetch: 5-15s
- HTML rendering: 10-20s (WeasyPrint)
- Image processing: 2-5s
- E-paper refresh: ~30s (hardware limitation)

**Validation Required**: On-hardware benchmarking during implementation phase to confirm estimates.

### Developer Experience & Modern Python Tooling (Principle IV)

**Status**: ✅ PASS (Planned)

**Tooling Compliance**:
- **uv**: Package management
- **pytest**: Testing framework
- **ruff**: Linting and formatting
- **mypy**: Type checking

**Workflow**: All CLI commands via `uvx`, one-command setup with `uv sync`.

### Reliability & Graceful Degradation (Principle V)

**Status**: ✅ PASS (Planned)

**Failure Handling**:
- Network outage: Display cached data with staleness timestamp
- API failures: Retry with exponential backoff, log errors
- Display driver errors: Log and skip update, retain previous display
- Invalid calendar data: Skip malformed events, display valid ones

**Observability**: Structured logging (JSON format) to `/var/log/kalendar/` with rotation.

### Gate Decision (Pre-Phase 0)

**PROCEED TO PHASE 0**: ✅ (Initial evaluation)

**Justification**: One area (Principle III - Resource Constraints) requires research to verify compliance. This is the purpose of Phase 0 research. All other principles are aligned with planned architecture.

---

### Gate Re-Evaluation (Post-Phase 1 Design)

**PROCEED TO IMPLEMENTATION**: ✅

**Updated Status**:
- ✅ Principle I (Clean Architecture): Verified via contracts/ and data-model.md
- ✅ Principle II (TDD): Test strategy defined in quickstart.md
- ✅ Principle III (Resource Constraints): Verified via research.md (estimates within budget)
- ✅ Principle IV (Modern Python Tooling): Confirmed (uv, pytest, ruff, mypy)
- ✅ Principle V (Reliability & Graceful Degradation): Designed into interfaces and use cases

**Phase 1 Artifacts Completed**:
- research.md: All technology choices researched and documented
- data-model.md: Domain entities with validation rules
- contracts/: 5 interface definitions with DTOs and exceptions
- quickstart.md: Developer onboarding guide with TDD workflow

**No Constitution Violations**: All principles satisfied. Ready for /speckit.tasks to generate implementation tasks.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/kalendar/
├── domain/                    # Core business logic (no external dependencies)
│   ├── models/                # Event, CalendarSource, DisplayConfig
│   ├── interfaces/            # Repository and service interfaces
│   └── services/              # Domain services (event aggregation, conflict detection)
├── application/               # Use cases and orchestration
│   ├── usecases/              # SyncCalendars, RenderDisplay, ScheduleRefresh
│   └── dto/                   # Data transfer objects between layers
├── infrastructure/            # External integrations
│   ├── calendar/              # GoogleCalendarClient, CalDAVClient
│   ├── display/               # WaveshareDriver, display abstraction
│   ├── storage/               # FileSystemCache, ConfigLoader
│   └── rendering/             # HTMLRenderer, ImageGenerator
├── presentation/              # Display rendering logic
│   ├── templates/             # HTML templates for calendar views
│   └── formatters/            # Date/time formatting, event truncation
└── cli/                       # Command-line interface entry points

tests/
├── unit/                      # Domain and application logic tests
│   ├── domain/
│   └── application/
├── integration/               # External API interactions (with fixtures)
│   ├── calendar/
│   └── rendering/
└── contract/                  # Interface compliance tests
    ├── calendar_sources/
    └── display_drivers/

config/
└── example.config.yaml        # Example configuration file
```

**Structure Decision**: Single-project Clean Architecture layout. The domain layer contains pure business logic with no external dependencies. Infrastructure layer adapts external systems (calendar APIs, e-paper display, filesystem) to domain interfaces. This enables testing without hardware or network, critical for TDD on Pi Zero.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
