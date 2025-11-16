<!--
Sync Impact Report
==================
Version: [template] → 1.0.0
Rationale: Initial constitution creation for Kalendar family calendar e-ink display

Added Principles:
- I. Clean Architecture & Dependency Inversion
- II. Test-Driven Development (NON-NEGOTIABLE)
- III. Resource Constraints & Pi Zero Optimization
- IV. Developer Experience & Modern Python Tooling
- V. Reliability & Graceful Degradation

Added Sections:
- Hardware & Platform Constraints
- Development Workflow
- Governance

Template Consistency Status:
- ✅ .specify/templates/plan-template.md - Constitution Check section present
- ✅ .specify/templates/spec-template.md - User scenarios & requirements align
- ✅ .specify/templates/tasks-template.md - TDD workflow & task organization align
- ✅ .claude/commands/*.md - Command files reviewed for consistency

Follow-up TODOs:
- None - all placeholders resolved

Last Updated: 2025-11-15
-->

# Kalendar Constitution

## Core Principles

### I. Clean Architecture & Dependency Inversion

Code MUST be organized in layers with dependencies pointing inward toward domain logic.

**Layer Structure**:
- **Domain**: Core calendar logic (event models, recurrence rules, conflict detection) - no external dependencies
- **Application**: Use cases (sync calendars, render display, schedule refreshes) - depends only on domain
- **Infrastructure**: External integrations (Google/Apple calendar APIs, Waveshare drivers, filesystem) - depends on application interfaces
- **Presentation**: Display rendering and formatting logic

**Rules**:
- Domain layer MUST NOT import from application, infrastructure, or presentation layers
- All external dependencies (APIs, hardware) MUST be abstracted behind interfaces defined in inner layers
- Business logic MUST be testable without hardware, network, or filesystem access
- Dependency injection MUST be used to wire concrete implementations

**Rationale**: Clean architecture enables testing calendar logic without a physical display or live API connections. This is critical for TDD on resource-constrained hardware where iteration cycles would otherwise be slow. It also allows swapping calendar providers or display hardware without touching core logic.

### II. Test-Driven Development (NON-NEGOTIABLE)

Tests MUST be written before implementation code. No exceptions.

**Workflow**:
1. Write failing test specifying desired behavior
2. Verify test fails for the right reason
3. Implement minimal code to pass the test
4. Verify test passes
5. Refactor while maintaining green tests

**Coverage Requirements**:
- **Unit tests**: All domain logic (recurrence expansion, timezone handling, event merging)
- **Integration tests**: Calendar API interactions, display rendering pipeline
- **Contract tests**: All layer boundaries and external API contracts
- **Hardware abstraction tests**: Display drivers via mocked hardware interfaces

**Test Execution**:
- Tests MUST run without physical hardware (use mocks/fakes for Waveshare display)
- Tests MUST run without network access (use recorded API responses/fixtures)
- Full test suite MUST complete in <30 seconds on development machine
- CI MUST run tests on every commit

**Rationale**: Raspberry Pi Zero is slow and calendar APIs have rate limits. TDD with proper abstraction enables rapid iteration on a development machine. Tests document expected behavior for complex calendar logic (RRULE expansion, timezone conversions, DST handling) and prevent regressions when optimizing for Pi Zero constraints.

### III. Resource Constraints & Pi Zero Optimization

All code MUST respect Raspberry Pi Zero's limited resources.

**Resource Limits**:
- Memory usage MUST stay under 256MB peak (Pi Zero has 512MB total, shared with OS)
- CPU-intensive operations (image rendering, recurrence expansion) MUST complete within 10 seconds
- Display refresh cycle (fetch → render → update) MUST complete within 60 seconds
- Battery life considerations: minimize unnecessary refreshes on e-ink display

**Optimization Strategies**:
- **Lazy loading**: Fetch only events in display time window (typically 7-14 days)
- **Caching**: Cache calendar data locally; refresh only on schedule or manual trigger
- **Incremental rendering**: Only redraw display regions that changed
- **Background processing**: Use systemd timers or cron for scheduled refreshes, not polling
- **Dependency minimization**: Prefer stdlib over heavy dependencies; justify all third-party libs

**Monitoring**:
- Log memory usage at key checkpoints (post-fetch, post-render, post-display)
- Track refresh cycle duration to detect performance degradation
- Alert if memory exceeds 200MB or refresh exceeds 45 seconds

**Rationale**: Pi Zero's single-core 1GHz ARM processor and 512MB RAM require discipline. E-ink displays are slow to refresh but retain state without power, enabling infrequent updates. Respecting these constraints ensures reliable operation and acceptable battery life in a family-accessible appliance.

### IV. Developer Experience & Modern Python Tooling

Development workflow MUST prioritize fast iteration and minimal friction.

**Tooling**:
- **uvx**: All scripts and CLI tools run via `uvx` for dependency isolation
- **uv**: Fast Python package management (pip/virtualenv replacement)
- **pytest**: Testing framework with fixtures for calendar data and display mocks
- **ruff**: Linting and formatting (replaces flake8, black, isort)
- **mypy**: Static type checking (all public APIs MUST have type hints)

**Developer Workflow**:
- **One-command setup**: `uv sync` to install all dependencies
- **One-command test**: `uv run pytest` (no manual venv activation)
- **One-command format**: `uv run ruff format .`
- **One-command typecheck**: `uv run mypy src/`
- **Pre-commit hooks**: Auto-format and typecheck on commit

**Documentation**:
- README MUST include quickstart (5 minutes to first test run)
- All public functions MUST have docstrings with examples
- Architecture Decision Records (ADRs) for significant choices

**Rationale**: Modern Python tooling (uv/uvx) dramatically improves iteration speed vs traditional pip/virtualenv. Since Pi Zero deployments are slow, developer experience on a fast machine is critical. Friction in testing or linting discourages TDD and leads to bugs discovered only on hardware.

### V. Reliability & Graceful Degradation

System MUST continue operating when external dependencies fail.

**Failure Modes**:
- **Network outage**: Display cached calendar data with staleness indicator
- **API rate limit**: Delay refresh, display last successful sync time
- **Authentication failure**: Log error, display "sync error" message, retain cached data
- **Display driver error**: Log error, retry once, skip display update if persistent
- **Malformed calendar data**: Log warning, skip invalid events, display valid events

**Recovery**:
- Automatic retry with exponential backoff for transient failures
- Manual refresh trigger (button or CLI command) bypasses schedule
- Health check endpoint/command to diagnose issues without display access

**Observability**:
- Structured logging (JSON format) to file and optionally syslog
- Log rotation to prevent disk fill (max 100MB logs)
- Critical errors MUST include stack trace and system state
- Log entry MUST include: timestamp, level, component, correlation ID, message

**Rationale**: A family calendar appliance must be reliable without technical intervention. Network and API failures are inevitable. Graceful degradation (showing stale data with indicators) maintains utility. Comprehensive logging enables remote debugging since the Pi Zero may be wall-mounted or otherwise physically inaccessible.

## Hardware & Platform Constraints

### Target Platform

- **Hardware**: Raspberry Pi Zero W (ARMv6, 1GHz single-core, 512MB RAM)
- **Display**: Waveshare 7.5" e-Paper HAT (800x480, 4-color or grayscale)
- **OS**: Raspberry Pi OS Lite (headless, no desktop environment)
- **Python**: 3.11+ (via deadsnakes PPA if needed, or system Python if 3.11+)

### Display Characteristics

- **Refresh rate**: 15-30 seconds per full update (hardware limitation)
- **Partial refresh**: Faster but limited lifespan (use sparingly)
- **Retention**: Image persists indefinitely without power
- **Update strategy**: Full refresh maximum once per hour to preserve display lifespan

### Network Requirements

- **Wi-Fi**: Required for calendar sync (Pi Zero W has 2.4GHz only)
- **APIs**: Google Calendar API, Apple iCloud Calendar (CalDAV)
- **Authentication**: OAuth 2.0 for Google, app-specific password for Apple
- **Bandwidth**: Minimal (<1MB per sync for typical family calendar)

### Storage

- **SD Card**: Minimum 8GB (use high-endurance card for frequent writes)
- **Cache location**: `/var/cache/kalendar/` for calendar data (JSON)
- **Logs**: `/var/log/kalendar/` with rotation
- **Config**: `/etc/kalendar/config.yaml` for credentials and settings

## Development Workflow

### Pre-Implementation Phase

1. **Specification** (spec.md): User stories with acceptance criteria, prioritized
2. **Planning** (plan.md): Architecture, data models, API contracts, Pi Zero resource budget
3. **Constitution Check**: Verify clean architecture layers, TDD plan, resource limits
4. **Task Decomposition** (tasks.md): Implementation tasks organized by user story

### Implementation Phase (TDD Cycle)

1. **Red**: Write failing test for next requirement
2. **Green**: Implement minimal code to pass test
3. **Refactor**: Improve design, check resource usage, maintain green tests
4. **Commit**: Small commits per passing test or logical unit

### Hardware Testing

- **Development**: Test with display simulator/mock on dev machine
- **Integration**: Deploy to Pi Zero for end-to-end validation before release
- **Regression**: Automated tests run on every commit (no hardware needed)
- **Performance**: Benchmark on Pi Zero weekly to catch performance regressions

### Code Review

All changes MUST be reviewed for:
- **TDD compliance**: Tests written first, tests fail before implementation
- **Clean architecture**: Dependencies point inward, interfaces at boundaries
- **Resource usage**: Memory/CPU within budget, no unnecessary allocations
- **Type coverage**: Public APIs have type hints, mypy passes
- **Error handling**: Graceful degradation, comprehensive logging

## Governance

### Amendment Process

1. Propose change with rationale and impact on existing code
2. Stakeholder review and approval
3. Version bump (MAJOR.MINOR.PATCH per semantic versioning)
4. Update dependent templates and documentation
5. Communicate changes to team

### Versioning Policy

- **MAJOR** (x.0.0): Remove/redefine core principle, incompatible governance change
- **MINOR** (0.x.0): Add new principle, materially expand existing principle
- **PATCH** (0.0.x): Clarify wording, fix typos, non-semantic edits

### Compliance Verification

- **Design phase**: plan.md MUST include constitution check section
- **Code review**: Reviewers verify TDD workflow, clean architecture, resource limits
- **CI pipeline**: Type checking, linting, test coverage enforced
- **Deployment**: Resource monitoring on Pi Zero to catch violations in production

### Complexity Justification

Any deviation from principles MUST be justified in writing:
- Why is deviation necessary?
- What simpler approach was rejected and why?
- What is the mitigation plan?
- When will deviation be revisited?

Examples requiring justification:
- Skipping tests for "trivial" code
- Violating dependency direction (e.g., domain importing infrastructure)
- Exceeding resource budgets
- Adding heavy dependencies

**Version**: 1.0.0 | **Ratified**: 2025-11-15 | **Last Amended**: 2025-11-15
