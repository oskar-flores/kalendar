# Tasks: Multi-Calendar E-Paper Display

**Input**: Design documents from `/specs/001-calendar-display/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Following TDD workflow (Constitution Principle II - NON-NEGOTIABLE). All tests must be written FIRST and FAIL before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (src/kalendar/{domain,application,infrastructure,presentation,cli}/, tests/{unit,integration,contract}/, config/)
- [X] T002 Initialize Python project with pyproject.toml using uv (Python 3.11+, pytest, ruff, mypy)
- [X] T003 [P] Configure ruff for linting and formatting in pyproject.toml
- [X] T004 [P] Configure mypy for strict type checking in pyproject.toml
- [X] T005 [P] Create .gitignore for Python project (venv, __pycache__, .pytest_cache, etc.)
- [X] T006 Create example configuration file in config/example.config.yaml
- [X] T007 Create README.md with project overview and quickstart link

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Domain Models (Core Entities)

- [X] T008 [P] Write tests for CalendarEvent model in tests/unit/domain/models/test_event.py
- [X] T009 [P] Write tests for CalendarSource model in tests/unit/domain/models/test_source.py
- [X] T010 [P] Write tests for DisplayConfiguration model in tests/unit/domain/models/test_config.py
- [X] T011 [P] Write tests for SyncMetadata model in tests/unit/domain/models/test_sync_metadata.py
- [X] T012 [P] Implement CalendarEvent model in src/kalendar/domain/models/event.py (with validation, is_multi_day, truncated_title methods)
- [X] T013 [P] Implement CalendarSource model in src/kalendar/domain/models/source.py (with is_stale, mark_sync_success methods)
- [X] T014 [P] Implement DisplayConfiguration model in src/kalendar/domain/models/config.py (with get_enabled_sources, get_next_refresh_time methods)
- [X] T015 [P] Implement SyncMetadata model in src/kalendar/domain/models/sync_metadata.py (with is_cache_valid, get_staleness_hours methods)
- [X] T016 [P] Create domain enums in src/kalendar/domain/models/enums.py (SourceType, SyncStatus, LayoutType)

### Domain Services (Business Logic)

- [X] T017 [P] Write tests for EventAggregator service in tests/unit/domain/services/test_event_aggregator.py
- [X] T018 [P] Write tests for MonthlyViewBuilder service in tests/unit/domain/services/test_monthly_view_builder.py
- [X] T019 [P] Write tests for DailyViewBuilder service in tests/unit/domain/services/test_daily_view_builder.py
- [X] T020 [P] Implement EventAggregator service in src/kalendar/domain/services/event_aggregator.py (aggregate_events, deduplicate_events, get_events_for_date)
- [X] T021 [P] Implement MonthlyViewBuilder service in src/kalendar/domain/services/monthly_view_builder.py (build MonthlyView with weeks, days, event mapping)
- [X] T022 [P] Implement DailyViewBuilder service in src/kalendar/domain/services/daily_view_builder.py (build DailyView with sorted events, max 5 visible per FR-019)

### Infrastructure Interfaces (Contracts)

- [X] T023 Copy interface definitions from specs/001-calendar-display/contracts/ to src/kalendar/domain/interfaces/ (ICalendarSource, IDisplayDriver, IImageRenderer, ICache, IConfigLoader)

### Infrastructure - Configuration

- [X] T024 Write tests for YAMLConfigLoader in tests/integration/infrastructure/test_yaml_config_loader.py
- [X] T025 Implement YAMLConfigLoader in src/kalendar/infrastructure/storage/yaml_config_loader.py (load_config, save_config, validate_config, load_credentials)
- [X] T026 [P] Implement InMemoryConfigLoader for testing in tests/fixtures/mock_config_loader.py

### Infrastructure - Cache

- [X] T027 Write tests for FileSystemCache in tests/integration/infrastructure/test_filesystem_cache.py
- [X] T028 Implement FileSystemCache in src/kalendar/infrastructure/storage/filesystem_cache.py (save_events, load_events, is_cache_valid using JSON)
- [X] T029 [P] Implement InMemoryCache for testing in tests/fixtures/mock_cache.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View Monthly Calendar Overview (Priority: P1) 🎯 MVP

**Goal**: Display entire month with events from multiple calendars, current day highlighted, days with events visually distinct

**Independent Test**: Can be fully tested by displaying a static month view with events from multiple calendars. Success is measured by family members being able to identify free/busy days and upcoming events without additional interaction.

### Tests for User Story 1 (TDD - RED phase)

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T030 [P] [US1] Contract test for ICalendarSource interface in tests/contract/test_calendar_source_contract.py
- [X] T031 [P] [US1] Integration test for Google Calendar sync in tests/integration/calendar/test_google_calendar_integration.py (with recorded fixtures)
- [X] T032 [P] [US1] Integration test for CalDAV sync in tests/integration/calendar/test_caldav_integration.py (with recorded fixtures)
- [X] T033 [P] [US1] Contract test for IImageRenderer interface in tests/contract/test_image_renderer_contract.py
- [X] T034 [P] [US1] Integration test for WeasyPrint HTML rendering in tests/integration/rendering/test_weasyprint_integration.py

### Implementation for User Story 1 (GREEN phase)

#### Calendar Data Fetching

- [X] T035 [P] [US1] Implement GoogleCalendarSource in src/kalendar/infrastructure/calendar/google_calendar_source.py (fetch_events, test_connection, refresh_auth using google-api-python-client)
- [X] T036 [P] [US1] Implement CalDAVSource in src/kalendar/infrastructure/calendar/caldav_source.py (fetch_events, test_connection, refresh_auth using caldav library)
- [X] T037 [P] [US1] Create MockCalendarSource for testing in tests/fixtures/mock_calendar_source.py (returns fixture events)

#### Display Rendering

- [X] T038 [US1] Create MonthlyView and DailyView domain models in src/kalendar/domain/models/view.py (MonthlyView with weeks/days, DailyView with events)
- [X] T039 [US1] Write tests for MonthlyView and DailyView models in tests/unit/domain/models/test_view.py
- [X] T040 [P] [US1] Implement WeasyPrintRenderer in src/kalendar/infrastructure/rendering/weasyprint_renderer.py (render_html_string, render_template)
- [X] T041 [P] [US1] Create HTML template for monthly calendar view in src/kalendar/presentation/templates/calendar_view.html (800x480 landscape, month grid, responsive layout)
- [X] T042 [P] [US1] Create CSS stylesheet for calendar in src/kalendar/presentation/templates/calendar_view.css (black/red/white color scheme per FR-010, current day red highlight)

#### Use Case - Sync Calendars

- [X] T043 [US1] Write tests for SyncCalendarsUseCase in tests/unit/application/usecases/test_sync_calendars.py
- [X] T044 [US1] Implement SyncCalendarsUseCase in src/kalendar/application/usecases/sync_calendars.py (fetch from all sources, aggregate, deduplicate, cache, handle errors per FR-014)

#### Use Case - Render Monthly Display

- [X] T045 [US1] Write tests for RenderMonthlyViewUseCase in tests/unit/application/usecases/test_render_monthly_view.py
- [X] T046 [US1] Implement RenderMonthlyViewUseCase in src/kalendar/application/usecases/render_monthly_view.py (build MonthlyView, render HTML template, return image)

#### Image Post-Processing

- [X] T047 [US1] Write tests for ImagePostProcessor in tests/unit/infrastructure/rendering/test_image_post_processor.py
- [X] T048 [US1] Implement ImagePostProcessor in src/kalendar/infrastructure/rendering/image_post_processor.py (split RGB image into black/red layers for e-paper display)

**Checkpoint**: At this point, User Story 1 should be fully functional - can sync calendars and render monthly view to image file

---

## Phase 4: User Story 2 - View Current Day's Event Details (Priority: P2)

**Goal**: Display today's events with time, title, location in dedicated section, sorted chronologically, max 5 events

**Independent Test**: Can be tested by displaying today's events in a dedicated section with time, title, and location. Success is measured by family members understanding what events are happening today without needing to check their phones.

### Tests for User Story 2 (TDD - RED phase)

- [X] T049 [P] [US2] Integration test for daily view rendering in tests/integration/rendering/test_daily_view_integration.py
- [X] T050 [P] [US2] Unit test for event overflow handling in tests/unit/domain/models/test_daily_view.py

### Implementation for User Story 2 (GREEN phase)

- [X] T051 [US2] Extend calendar_view.html template to include today's events section in src/kalendar/presentation/templates/calendar_view.html (below month grid, max 5 events per FR-019)
- [X] T052 [US2] Add today's events styling to CSS in src/kalendar/presentation/templates/calendar_styles.css (red for current event per FR-010, chronological layout)
- [X] T053 [US2] Write tests for RenderDailyViewUseCase in tests/unit/application/usecases/test_render_daily_view.py
- [X] T054 [US2] Implement RenderDailyViewUseCase in src/kalendar/application/usecases/render_daily_view.py (build DailyView with current event highlighting, overflow indicator)
- [X] T055 [US2] Update RenderMonthlyViewUseCase to include DailyView data in template context in src/kalendar/application/usecases/render_monthly_view.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - monthly view with today's events section

---

## Phase 5: User Story 3 - Automatic Daily Refresh (Priority: P3)

**Goal**: System automatically updates calendar data once per day at configurable time, retries on failure, displays stale data if sync fails

**Independent Test**: Can be tested by scheduling a refresh at a specific time, verifying that calendar data is fetched and the display is updated. Success is measured by the display showing updated events after the scheduled refresh without manual intervention.

### Tests for User Story 3 (TDD - RED phase)

- [ ] T056 [P] [US3] Integration test for scheduled refresh in tests/integration/test_scheduler.py
- [ ] T057 [P] [US3] Unit test for refresh retry logic in tests/unit/application/usecases/test_refresh_use_case.py

### Implementation for User Story 3 (GREEN phase)

#### Scheduling

- [ ] T058 [US3] Write tests for ScheduleRefreshUseCase in tests/unit/application/usecases/test_schedule_refresh.py
- [ ] T059 [US3] Implement ScheduleRefreshUseCase in src/kalendar/application/usecases/schedule_refresh.py (calculate next refresh time from config, schedule task)

#### Refresh Orchestration

- [ ] T060 [US3] Write tests for RefreshDisplayUseCase in tests/unit/application/usecases/test_refresh_display.py
- [ ] T061 [US3] Implement RefreshDisplayUseCase in src/kalendar/application/usecases/refresh_display.py (orchestrates sync + render + display update, handles failures per FR-014)

#### Error Handling & Graceful Degradation

- [ ] T062 [US3] Implement retry logic with exponential backoff in src/kalendar/infrastructure/utils/retry.py
- [ ] T063 [US3] Add staleness timestamp display to template in src/kalendar/presentation/templates/calendar_view.html (show last successful sync per FR-015)
- [ ] T064 [US3] Implement logging infrastructure in src/kalendar/infrastructure/logging/structured_logger.py (JSON format to /var/log/kalendar/ per FR-012)

**Checkpoint**: All core user stories should now be independently functional - system auto-refreshes daily

---

## Phase 6: User Story 4 - Configure Calendar Sources and Settings (Priority: P4)

**Goal**: Users can configure which calendars to display and set display preferences like refresh time via config file

**Independent Test**: Can be tested by providing a configuration file where users can add/remove calendar sources and set refresh time. Success is measured by changes taking effect after the next refresh.

### Tests for User Story 4 (TDD - RED phase)

- [X] T065 [P] [US4] Integration test for config file changes in tests/integration/test_config_updates.py
- [X] T066 [P] [US4] Unit test for config validation in tests/unit/infrastructure/storage/test_config_validation.py

### Implementation for User Story 4 (GREEN phase)

- [X] T067 [US4] Add config validation rules to YAMLConfigLoader in src/kalendar/infrastructure/storage/yaml_config_loader.py (validate refresh_hour 0-23, timezone IANA, at least 1 enabled source per FR validation matrix)
- [X] T068 [US4] Create comprehensive example.config.yaml in config/ with comments explaining all options
- [X] T069 [US4] Create comprehensive configuration documentation in docs/configuration.md with setup instructions for all calendar types

**Checkpoint**: Configuration system complete - users can customize calendar sources and settings

---

## Phase 7: Hardware Integration & Display Driver

**Purpose**: Integrate e-paper display hardware (can be done in parallel with user stories for simulator mode)

### Tests for Display Driver (TDD - RED phase)

- [X] T070 [P] Contract test for IDisplayDriver interface in tests/contract/test_display_driver_contract.py
- [X] T071 [P] Integration test for Waveshare driver (hardware-dependent) in tests/integration/display/test_waveshare_integration.py

### Implementation for Display Driver (GREEN phase)

- [X] T072 [P] Implement WaveshareEPD75BDriver in src/kalendar/infrastructure/display/waveshare_driver.py (initialize, display with black/red buffers, sleep, get_capabilities)
- [X] T073 [P] Implement MockDisplayDriver for testing in tests/fixtures/mock_display_driver.py (saves to file instead of hardware)
- [X] T074 [P] Implement SimulatorDisplayDriver for development in src/kalendar/infrastructure/display/simulator_driver.py (shows in window or saves to output/ directory)

### Display Update Use Case

- [X] T075 Write tests for UpdateDisplayUseCase in tests/unit/application/usecases/test_update_display.py
- [X] T076 Implement UpdateDisplayUseCase in src/kalendar/application/usecases/update_display.py (initialize display, convert image to black/red buffers, update display, handle hardware errors per FR-014)

**Checkpoint**: Display integration complete - can render to actual e-paper hardware

---

## Phase 8: CLI & Application Entry Points

**Purpose**: Command-line interface for manual operations and daemon mode

### Tests for CLI (TDD - RED phase)

- [X] T077 [P] Integration test for CLI commands in tests/integration/cli/test_cli_commands.py

### Implementation for CLI (GREEN phase)

- [X] T078 [P] Create CLI main entry point in src/kalendar/cli/main.py (using argparse or click)
- [X] T079 [P] Implement `refresh` command in src/kalendar/cli/commands/refresh.py (manual refresh, --simulator flag)
- [X] T080 [P] Implement `test-display` command in src/kalendar/cli/commands/test_display.py (hardware test with pattern)
- [X] T081 [P] Implement `test-sync` command in src/kalendar/cli/commands/test_sync.py (test calendar connectivity)
- [X] T082 [P] Implement `auth` command in src/kalendar/cli/commands/auth.py (Google OAuth flow helper)
- [X] T083 [P] Implement `discover-caldav` command in src/kalendar/cli/commands/discover_caldav.py (find iCloud calendar URLs)

### Dependency Injection & Application Wiring

- [X] T084 Create dependency injection container in src/kalendar/cli/dependencies.py (wire together all infrastructure implementations based on config)
- [X] T085 Create application factory in src/kalendar/cli/app_factory.py (create_application with all use cases)

**Checkpoint**: CLI complete - can manually trigger all operations

---

## Phase 9: Systemd Integration & Deployment

**Purpose**: Automatic startup and scheduled refresh on Raspberry Pi

- [ ] T086 Create systemd service file template in deployment/kalendar.service
- [ ] T087 Create systemd timer file template in deployment/kalendar.timer
- [ ] T088 Create deployment script in deployment/install.sh (copy files, set permissions, enable service)
- [ ] T089 Update quickstart.md with Pi Zero deployment instructions
- [ ] T090 Create uninstall script in deployment/uninstall.sh

**Checkpoint**: Deployment automation complete

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T091 [P] Add comprehensive docstrings to all public APIs (domain models, use cases, interfaces)
- [ ] T092 [P] Add type hints validation with mypy to all modules
- [ ] T093 [P] Performance optimization: benchmark refresh cycle on Pi Zero, ensure <60s per FR-003
- [ ] T094 [P] Memory profiling: verify peak memory <256MB on Pi Zero per Principle III
- [ ] T095 [P] Create logging documentation in docs/logging.md (log locations, formats, rotation)
- [ ] T096 [P] Security review: ensure credentials.json has chmod 600, no secrets in logs
- [ ] T097 Add edge case handling for timezone transitions (daylight saving) per edge case list
- [ ] T098 Add edge case handling for events with emoji/special characters per edge case list
- [ ] T099 Run full quickstart.md validation on clean Pi Zero W
- [ ] T100 Create troubleshooting guide in docs/troubleshooting.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (P1): Can start after Foundational - No dependencies on other stories
  - User Story 2 (P2): Can start after Foundational - Extends US1 template but independently testable
  - User Story 3 (P3): Can start after Foundational - Orchestrates US1+US2 but independently testable
  - User Story 4 (P4): Can start after Foundational - Configuration layer, no dependencies on other stories
- **Hardware Integration (Phase 7)**: Can proceed in parallel with user stories (using simulator mode)
- **CLI (Phase 8)**: Depends on all use cases being implemented (US1, US2, US3)
- **Deployment (Phase 9)**: Depends on CLI completion
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1) - Monthly Overview**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2) - Daily Details**: Can start after Foundational - Extends US1 template but can be tested independently
- **User Story 3 (P3) - Auto Refresh**: Can start after Foundational - Orchestrates US1+US2 but independently testable with mocks
- **User Story 4 (P4) - Configuration**: Can start after Foundational - Independent configuration layer

### Within Each User Story

- Tests MUST be written FIRST and FAIL before implementation (TDD - RED phase)
- Domain models before domain services
- Domain services before use cases
- Infrastructure interfaces before infrastructure implementations
- Use cases before CLI commands
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003 (ruff config), T004 (mypy config), T005 (gitignore) can run in parallel

**Phase 2 (Foundational)**:
- T008-T011 (all domain model tests) can run in parallel
- T012-T016 (all domain model implementations) can run in parallel after tests
- T017-T019 (all domain service tests) can run in parallel
- T020-T022 (all domain service implementations) can run in parallel after tests
- T024-T029 (config and cache infrastructure) can run in parallel

**User Story 1**:
- T030-T034 (all contract/integration tests) can run in parallel
- T035-T037 (calendar source implementations) can run in parallel
- T040-T042 (rendering infrastructure) can run in parallel

**User Story 2**:
- T049-T050 (tests) can run in parallel

**User Story 3**:
- T056-T057 (tests) can run in parallel

**User Story 4**:
- T065-T066 (tests) can run in parallel

**Phase 7 (Display)**:
- T070-T074 (all display driver work) can run in parallel

**Phase 8 (CLI)**:
- T078-T083 (all CLI commands) can run in parallel after T084-T085

**Phase 10 (Polish)**:
- T091-T096 (all polish tasks) can run in parallel

---

## Parallel Example: User Story 1 - Monthly Overview

```bash
# Launch all tests for User Story 1 together (RED phase):
Task: "Contract test for ICalendarSource interface in tests/contract/test_calendar_source_contract.py"
Task: "Integration test for Google Calendar sync in tests/integration/calendar/test_google_calendar_integration.py"
Task: "Integration test for CalDAV sync in tests/integration/calendar/test_caldav_integration.py"
Task: "Contract test for IImageRenderer interface in tests/contract/test_image_renderer_contract.py"
Task: "Integration test for WeasyPrint HTML rendering in tests/integration/rendering/test_weasyprint_integration.py"

# After tests fail, launch all calendar source implementations together (GREEN phase):
Task: "Implement GoogleCalendarSource in src/kalendar/infrastructure/calendar/google_calendar_source.py"
Task: "Implement CalDAVSource in src/kalendar/infrastructure/calendar/caldav_source.py"
Task: "Create MockCalendarSource for testing in tests/fixtures/mock_calendar_source.py"

# Launch rendering implementations together:
Task: "Implement WeasyPrintRenderer in src/kalendar/infrastructure/rendering/weasyprint_renderer.py"
Task: "Create HTML template in src/kalendar/presentation/templates/calendar_view.html"
Task: "Create CSS stylesheet in src/kalendar/presentation/templates/calendar_styles.css"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only) - Recommended

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T029) - CRITICAL, blocks all stories
3. Complete Phase 3: User Story 1 (T030-T048)
4. Complete Phase 7: Display Driver with Simulator (T070-T076)
5. Complete Phase 8: CLI for manual refresh (T078-T085)
6. **STOP and VALIDATE**: Test User Story 1 independently in simulator mode
7. Deploy to Pi Zero with hardware, validate
8. **MVP COMPLETE**: Monthly calendar view with multiple calendar sources

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + Display Simulator + CLI → Test independently → **MVP - Monthly View**
3. Add User Story 2 → Test independently → **v1.1 - Daily Details**
4. Add User Story 3 → Test independently → **v1.2 - Auto Refresh**
5. Add User Story 4 → Test independently → **v1.3 - Configuration**
6. Add Phase 9: Systemd → **v1.4 - Full Automation**
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T029)
2. Once Foundational is done:
   - Developer A: User Story 1 (T030-T048)
   - Developer B: User Story 2 (T049-T055)
   - Developer C: Display Driver (T070-T076)
3. Stories complete and integrate independently
4. CLI developer (Developer D) integrates all use cases (T078-T085)

---

## Notes

- **[P]** tasks = different files, no dependencies, can run in parallel
- **[Story]** label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD is NON-NEGOTIABLE**: Verify tests fail (RED) before implementing (GREEN)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Target: <60s refresh cycle, <256MB memory peak on Pi Zero W
- All external dependencies abstracted behind interfaces for testability
