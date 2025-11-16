# Feature Specification: Multi-Calendar E-Paper Display

**Feature Branch**: `001-calendar-display`
**Created**: 2025-11-15
**Status**: Draft
**Input**: User description: "I want you to help me to build a simple calendar app that will run in a raspberry pi zero w, will return info for several calendars and display it in a waveshare 7.5 e paper display with 3 colors, black red and white. It will refresh once a day at a configurable hour, usually at 00:00 the data display should be able to share a global month view, with the current day events easily displayable. Will be displayed in horizontal to make a good use of the space"

## Clarifications

### Session 2025-11-15

- Q: Which color scheme should be used for the three-color display? → A: Red for current day/current events, black for other text, white background
- Q: How should users configure calendar sources and refresh time? → A: YAML/JSON config file
- Q: How many events should the "today's events" section display before truncating? → A: Maximum 5 events
- Q: Which calendar events should be displayed (based on RSVP status)? → A: Show all events regardless of RSVP status
- Q: How should multi-day events appear in the month grid? → A: Show event title only on first day, visual bar spans across days

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Monthly Calendar Overview (Priority: P1)

Family members want to see the entire month at a glance to understand upcoming commitments and availability across all family calendars.

**Why this priority**: This is the core value proposition - a persistent, always-visible monthly overview that doesn't require interaction with phones or computers. Without this, the device has no purpose.

**Independent Test**: Can be fully tested by displaying a static month view with events from multiple calendars. Success is measured by family members being able to identify free/busy days and upcoming events without additional interaction.

**Acceptance Scenarios**:

1. **Given** the display is mounted on the wall, **When** a family member walks by, **Then** they can see the current month with all days clearly labeled
2. **Given** events exist across multiple calendars (Google, Apple), **When** the display refreshes, **Then** all events from all calendars are visible in the month grid
3. **Given** it is mid-month, **When** viewing the display, **Then** the current day is visually distinguished from other days
4. **Given** some days have events and others don't, **When** viewing the month, **Then** days with events are visually distinct from empty days
5. **Given** events span multiple days, **When** viewing the month, **Then** multi-day events are clearly represented across the affected dates

---

### User Story 2 - View Current Day's Event Details (Priority: P2)

Family members want to see detailed information about today's events to know what's happening now or coming up soon.

**Why this priority**: After seeing the month overview, users need quick access to today's schedule details (times, titles, locations) without scrolling through the entire month's events.

**Independent Test**: Can be tested by displaying today's events in a dedicated section with time, title, and location. Success is measured by family members understanding what events are happening today without needing to check their phones.

**Acceptance Scenarios**:

1. **Given** today has scheduled events, **When** viewing the display, **Then** today's events are shown with start time, title, and location
2. **Given** today has multiple events, **When** viewing the display, **Then** events are sorted chronologically from earliest to latest
3. **Given** an event is currently in progress, **When** viewing the display, **Then** the current event is visually emphasized
4. **Given** today has no events, **When** viewing the display, **Then** the daily section indicates "No events today" or similar
5. **Given** event titles are very long, **When** viewing the display, **Then** titles are truncated appropriately to fit the available space

---

### User Story 3 - Automatic Daily Refresh (Priority: P3)

The system automatically updates calendar data once per day to reflect changes made in source calendars (Google, Apple).

**Why this priority**: While important for data accuracy, the display doesn't need real-time updates. Daily refresh is sufficient for family planning use cases and preserves e-paper display lifespan.

**Independent Test**: Can be tested by scheduling a refresh at a specific time, verifying that calendar data is fetched and the display is updated. Success is measured by the display showing updated events after the scheduled refresh without manual intervention.

**Acceptance Scenarios**:

1. **Given** the refresh time is configured to 00:00, **When** midnight arrives, **Then** the system fetches calendar data from all sources
2. **Given** calendar data has been fetched, **When** the refresh completes, **Then** the e-paper display is updated with the new data
3. **Given** a refresh fails due to network issues, **When** the next scheduled refresh occurs, **Then** the system retries and logs the previous failure
4. **Given** the refresh time is configurable, **When** a user changes the refresh time setting, **Then** subsequent refreshes occur at the new time
5. **Given** multiple calendars need to be fetched, **When** one calendar source fails, **Then** the display still shows data from successful sources and indicates which source failed

---

### User Story 4 - Configure Calendar Sources and Settings (Priority: P4)

Users can configure which calendars to display (Google, Apple) and set display preferences like refresh time.

**Why this priority**: This enables customization for different families but isn't needed for the basic display to work. Can be implemented after core functionality is proven.

**Independent Test**: Can be tested by providing a configuration interface (file-based or CLI) where users can add/remove calendar sources and set refresh time. Success is measured by changes taking effect after the next refresh.

**Acceptance Scenarios**:

1. **Given** a user has Google and Apple calendar credentials, **When** they configure calendar sources, **Then** both calendars are included in the next refresh
2. **Given** a user wants to exclude a specific calendar, **When** they remove it from the configuration, **Then** events from that calendar no longer appear on the display
3. **Given** a user prefers a different refresh time, **When** they change the refresh hour setting, **Then** daily refreshes occur at the new time
4. **Given** configuration is updated, **When** invalid settings are provided (e.g., invalid hour), **Then** the system logs an error and uses default settings
5. **Given** multiple users share the device, **When** configuration changes are made, **Then** all users see the same updated display after the next refresh

---

### Edge Cases

- What happens when a calendar source (Google or Apple) is unreachable during refresh?
- How does the system handle calendars with hundreds of events in a single month?
- What happens when an event title contains special characters or emoji?
- How does the system handle timezone differences between calendar sources?
- What happens when the display hardware fails to initialize or update?
- How does the system handle events that span midnight (multi-day events)?
- What happens when calendar authentication expires or credentials become invalid?
- How does the system handle daylight saving time transitions?
- What happens when there are more events in a single day than can fit in the display area?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST aggregate events from multiple calendar sources (Google Calendar and Apple iCloud Calendar)
- **FR-002**: System MUST display a monthly calendar view showing the current month with all days clearly visible
- **FR-003**: System MUST visually distinguish the current day from other days in the month view
- **FR-004**: System MUST indicate which days have events using visual markers (color or styling)
- **FR-005**: System MUST display today's events in a dedicated section with start time, event title, and location
- **FR-006**: System MUST sort today's events chronologically by start time
- **FR-007**: System MUST refresh calendar data automatically once per day at a configurable time (default: 00:00)
- **FR-008**: System MUST render all display content in horizontal (landscape) orientation
- **FR-009**: System MUST use the Waveshare 7.5" e-paper display's three-color capability (black, red, white)
- **FR-010**: System MUST use red color for current day highlighting and today's events, black color for all other text, and white for background
- **FR-011**: System MUST persist calendar data locally to display cached information when network is unavailable
- **FR-012**: System MUST log all refresh attempts, successes, and failures with timestamps
- **FR-013**: System MUST handle authentication for both Google Calendar (OAuth 2.0) and Apple iCloud Calendar (CalDAV)
- **FR-014**: System MUST gracefully handle network failures by displaying the most recent successful calendar data
- **FR-015**: System MUST indicate on the display when data is stale (last successful sync timestamp)
- **FR-016**: System MUST support configuration of calendar sources and refresh time via YAML or JSON configuration file
- **FR-017**: System MUST respect calendar event privacy settings and display public/shared events only
- **FR-020**: System MUST display all events regardless of RSVP status (accepted, declined, tentative, or no response)
- **FR-018**: System MUST handle event titles that exceed available display space by truncating with ellipsis
- **FR-019**: System MUST display a maximum of 5 events in the "today's events" section; if more exist, show "+N more events" indicator
- **FR-021**: System MUST display multi-day events in the month grid by showing the event title on the first day and rendering a visual bar that spans across all affected days

### Key Entities

- **Calendar Source**: Represents a connected calendar (Google or Apple), including authentication credentials, calendar ID, and sync status
- **Calendar Event**: Represents a single event with attributes: title, start time, end time, location, description, source calendar, all-day flag
- **Monthly View**: Represents the current month's calendar grid with day numbers, event indicators, and current day highlighting
- **Daily View**: Represents today's event list with detailed information for each event
- **Display Configuration**: Represents user settings including enabled calendar sources, refresh time, timezone, and display preferences
- **Sync Status**: Represents the state of calendar synchronization including last sync time, success/failure status, and error messages

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Family members can identify the current day and see if it has events within 2 seconds of looking at the display
- **SC-002**: Family members can determine if a specific day in the month has events without interacting with the device
- **SC-003**: The display completes a full refresh cycle (fetch all calendars, render, update display) within 60 seconds
- **SC-004**: The system successfully syncs calendar data on 95% of scheduled refresh attempts (assuming network availability)
- **SC-005**: Today's events are displayed with sufficient detail (time, title, location) that family members don't need to check their phones for basic event information
- **SC-006**: The display remains readable from 2 meters away in typical indoor lighting conditions
- **SC-007**: Calendar data is cached such that the display shows useful information even after 7 days without successful sync
- **SC-008**: The system operates continuously for 30 days without requiring manual intervention or restart
- **SC-009**: Events from all configured calendar sources appear on the display within 24 hours of being created in the source calendar
- **SC-010**: The e-paper display lifespan is preserved by limiting full refreshes to maximum once per day

### Assumptions

- Users have valid Google and/or Apple calendar accounts with events they want to display
- The Raspberry Pi Zero W has reliable Wi-Fi connectivity at the installation location
- Calendar sources contain a reasonable number of events (fewer than 100 events per month per calendar)
- Users are comfortable editing configuration files or using command-line tools for initial setup
- The device will be mounted in a location with typical indoor lighting (no direct sunlight on the e-paper display)
- Users understand that updates are not real-time and accept the daily refresh frequency
- Event titles, locations, and descriptions are in languages supported by the display's font rendering
- The Waveshare 7.5" display uses the three-color model (specific model to be determined during planning phase)
