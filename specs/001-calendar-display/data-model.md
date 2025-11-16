# Data Model: Multi-Calendar E-Paper Display

**Feature**: 001-calendar-display
**Date**: 2025-11-15
**Status**: Design

---

## Domain Entities

### 1. CalendarEvent

Represents a single calendar event from any source (Google, iCloud).

**Attributes**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `id` | `str` | Yes | Unique per source | Event identifier from source calendar |
| `calendar_source_id` | `str` | Yes | - | Reference to CalendarSource that owns this event |
| `title` | `str` | Yes | Max 200 chars | Event title/summary |
| `start_datetime` | `datetime` | Yes | - | Event start time (timezone-aware) |
| `end_datetime` | `datetime` | Yes | - | Event end time (timezone-aware) |
| `is_all_day` | `bool` | Yes | Default: False | True if event spans entire day(s) |
| `location` | `str` | No | Max 150 chars | Event location |
| `description` | `str` | No | Max 1000 chars | Event description/notes |
| `is_recurring` | `bool` | Yes | Default: False | True if part of recurring series |
| `recurrence_id` | `str` | No | - | Identifier for recurring series |

**Validation Rules**:
- `end_datetime` must be >= `start_datetime`
- If `is_all_day` is True, times should be midnight in local timezone
- `title` is required and cannot be empty string

**Methods**:
```python
def is_multi_day(self) -> bool:
    """Returns True if event spans multiple calendar days."""
    return self.end_datetime.date() > self.start_datetime.date()

def is_happening_today(self, reference_date: date) -> bool:
    """Returns True if event occurs on the given date."""
    start_date = self.start_datetime.date()
    end_date = self.end_datetime.date()
    return start_date <= reference_date <= end_date

def truncated_title(self, max_length: int) -> str:
    """Returns title truncated to max_length with ellipsis if needed."""
    if len(self.title) <= max_length:
        return self.title
    return self.title[:max_length-3] + "..."

def to_display_format(self) -> dict:
    """Returns event data formatted for display templates."""
    return {
        'title': self.title,
        'start_time': self.start_datetime.strftime('%H:%M'),
        'end_time': self.end_datetime.strftime('%H:%M'),
        'location': self.location or '',
        'is_all_day': self.is_all_day,
        'is_multi_day': self.is_multi_day()
    }
```

---

### 2. CalendarSource

Represents a connected calendar (Google or Apple iCloud).

**Attributes**:

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `id` | `str` | Yes | Unique | Internal identifier for this calendar source |
| `name` | `str` | Yes | Max 100 chars | Display name (e.g., "Family Calendar") |
| `source_type` | `SourceType` | Yes | Enum | GOOGLE or CALDAV |
| `calendar_id` | `str` | Yes | - | External calendar ID (Google calendar ID or CalDAV URL) |
| `enabled` | `bool` | Yes | Default: True | Whether to include events from this source |
| `color` | `str` | No | Hex color | Visual indicator color (not used in 3-color display) |
| `last_sync_time` | `datetime` | No | - | Timestamp of last successful sync |
| `last_sync_status` | `SyncStatus` | No | Enum | SUCCESS, FAILED, PENDING |
| `credentials` | `dict` | No | - | Encrypted auth credentials (stored separately in practice) |

**Enums**:

```python
class SourceType(Enum):
    GOOGLE = "google"
    CALDAV = "caldav"

class SyncStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    NEVER_SYNCED = "never_synced"
```

**Validation Rules**:
- `calendar_id` format must match `source_type` requirements
- Google: calendar email or "primary"
- CalDAV: Full calendar URL

**Methods**:
```python
def is_stale(self, max_age_hours: int = 24) -> bool:
    """Returns True if last sync is older than max_age_hours."""
    if not self.last_sync_time:
        return True
    age = datetime.now(timezone.utc) - self.last_sync_time
    return age.total_seconds() > (max_age_hours * 3600)

def mark_sync_success(self, timestamp: datetime) -> None:
    """Update sync status after successful sync."""
    self.last_sync_time = timestamp
    self.last_sync_status = SyncStatus.SUCCESS

def mark_sync_failed(self) -> None:
    """Update sync status after failed sync."""
    self.last_sync_status = SyncStatus.FAILED
```

---

### 3. MonthlyView

Represents the monthly calendar grid for display rendering.

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `year` | `int` | Yes | Year to display |
| `month` | `int` | Yes | Month to display (1-12) |
| `today` | `date` | Yes | Current date for highlighting |
| `weeks` | `List[Week]` | Yes | List of weeks in the month (typically 5-6) |
| `events_by_date` | `Dict[date, List[CalendarEvent]]` | Yes | Map of date to events on that day |

**Nested Types**:

```python
@dataclass
class Day:
    """Represents a single day cell in the calendar grid."""
    date: date
    is_current_month: bool  # False for padding days from adjacent months
    is_today: bool
    has_events: bool
    event_count: int
    events: List[CalendarEvent]

@dataclass
class Week:
    """Represents a week row in the calendar grid."""
    days: List[Day]  # Always 7 days (Sun-Sat or Mon-Sun based on config)
```

**Methods**:
```python
def get_month_name(self) -> str:
    """Returns month name (e.g., 'November')."""
    return calendar.month_name[self.month]

def get_days_with_events(self) -> List[date]:
    """Returns sorted list of dates that have events."""
    return sorted(self.events_by_date.keys())

def get_multi_day_event_spans(self) -> List[Tuple[CalendarEvent, List[date]]]:
    """Returns list of (event, dates) for multi-day events to render bars."""
    spans = []
    for event in self.get_all_events():
        if event.is_multi_day():
            dates = self._get_date_range(event.start_datetime.date(),
                                         event.end_datetime.date())
            spans.append((event, dates))
    return spans
```

---

### 4. DailyView

Represents today's event details section.

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `date` | `date` | Yes | The date being displayed (usually today) |
| `events` | `List[CalendarEvent]` | Yes | Events for this date, sorted by start time |
| `max_visible_events` | `int` | Yes | Maximum events to display (5 per FR-019) |
| `total_event_count` | `int` | Yes | Total events for this date |

**Validation Rules**:
- `events` must be sorted by `start_datetime` ascending
- `max_visible_events` enforced at view creation (FR-019)

**Methods**:
```python
def get_visible_events(self) -> List[CalendarEvent]:
    """Returns up to max_visible_events events."""
    return self.events[:self.max_visible_events]

def get_overflow_count(self) -> int:
    """Returns number of events not shown due to limit."""
    return max(0, self.total_event_count - self.max_visible_events)

def has_overflow(self) -> bool:
    """Returns True if there are more events than can be displayed."""
    return self.get_overflow_count() > 0

def get_current_event(self, reference_time: datetime) -> Optional[CalendarEvent]:
    """Returns the event currently in progress, if any."""
    for event in self.events:
        if event.start_datetime <= reference_time <= event.end_datetime:
            return event
    return None
```

---

### 5. DisplayConfiguration

Represents user settings and preferences.

**Attributes**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `refresh_hour` | `int` | Yes | 0 | Hour of day to refresh (0-23) |
| `timezone` | `str` | Yes | "UTC" | IANA timezone (e.g., "America/New_York") |
| `week_start_day` | `int` | Yes | 0 | Week start day (0=Monday, 6=Sunday) |
| `calendar_sources` | `List[CalendarSource]` | Yes | [] | List of enabled calendar sources |
| `display_layout` | `LayoutType` | Yes | HORIZONTAL | Orientation setting |
| `max_daily_events` | `int` | Yes | 5 | Max events in today's section (FR-019) |

**Enums**:
```python
class LayoutType(Enum):
    HORIZONTAL = "horizontal"  # Landscape (required per FR-008)
    VERTICAL = "vertical"      # Portrait (not used in initial version)
```

**Validation Rules**:
- `refresh_hour` must be 0-23
- `timezone` must be valid IANA timezone string
- `week_start_day` must be 0-6
- `max_daily_events` must be > 0
- At least one `calendar_sources` must be enabled

**Methods**:
```python
def get_enabled_sources(self) -> List[CalendarSource]:
    """Returns list of enabled calendar sources."""
    return [source for source in self.calendar_sources if source.enabled]

def get_refresh_time_today(self) -> datetime:
    """Returns today's scheduled refresh time in configured timezone."""
    tz = ZoneInfo(self.timezone)
    now = datetime.now(tz)
    return now.replace(hour=self.refresh_hour, minute=0, second=0, microsecond=0)

def get_next_refresh_time(self) -> datetime:
    """Returns next scheduled refresh time."""
    refresh_today = self.get_refresh_time_today()
    if datetime.now(ZoneInfo(self.timezone)) > refresh_today:
        return refresh_today + timedelta(days=1)
    return refresh_today
```

---

### 6. SyncMetadata

Represents synchronization state and cache information.

**Attributes**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `last_successful_sync` | `datetime` | No | Timestamp of last successful sync across all sources |
| `sync_results` | `Dict[str, SyncResult]` | Yes | Map of source_id to sync result |
| `cached_events_count` | `int` | Yes | Total number of events in cache |
| `cache_valid_until` | `datetime` | No | When cached data expires |

**Nested Types**:
```python
@dataclass
class SyncResult:
    """Result of syncing a single calendar source."""
    source_id: str
    status: SyncStatus
    timestamp: datetime
    events_fetched: int
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
```

**Methods**:
```python
def is_cache_valid(self) -> bool:
    """Returns True if cached data is still valid."""
    if not self.cache_valid_until:
        return False
    return datetime.now(timezone.utc) < self.cache_valid_until

def get_failed_sources(self) -> List[str]:
    """Returns list of source IDs that failed to sync."""
    return [
        source_id for source_id, result in self.sync_results.items()
        if result.status == SyncStatus.FAILED
    ]

def get_staleness_hours(self) -> float:
    """Returns hours since last successful sync."""
    if not self.last_successful_sync:
        return float('inf')
    delta = datetime.now(timezone.utc) - self.last_successful_sync
    return delta.total_seconds() / 3600
```

---

## Domain Services

### EventAggregator

Combines events from multiple calendar sources, handles conflicts and deduplication.

**Responsibilities**:
- Merge events from multiple `CalendarSource` instances
- Deduplicate events that appear in multiple calendars
- Sort events by start time
- Filter events by date range

**Interface**:
```python
class EventAggregator:
    def aggregate_events(
        self,
        sources: List[CalendarSource],
        start_date: date,
        end_date: date
    ) -> List[CalendarEvent]:
        """Fetch and merge events from all sources for date range."""
        pass

    def deduplicate_events(
        self,
        events: List[CalendarEvent]
    ) -> List[CalendarEvent]:
        """Remove duplicate events based on title, time, and location."""
        pass

    def get_events_for_date(
        self,
        events: List[CalendarEvent],
        target_date: date
    ) -> List[CalendarEvent]:
        """Filter events occurring on a specific date."""
        pass
```

---

### MonthlyViewBuilder

Constructs `MonthlyView` domain object from events and configuration.

**Responsibilities**:
- Generate calendar grid for a given month
- Map events to days in the grid
- Identify multi-day event spans
- Handle month boundary padding

**Interface**:
```python
class MonthlyViewBuilder:
    def build(
        self,
        year: int,
        month: int,
        events: List[CalendarEvent],
        config: DisplayConfiguration
    ) -> MonthlyView:
        """Build monthly calendar view."""
        pass

    def _generate_weeks(
        self,
        year: int,
        month: int,
        week_start_day: int
    ) -> List[Week]:
        """Generate week rows with proper padding."""
        pass
```

---

### DailyViewBuilder

Constructs `DailyView` domain object from events.

**Responsibilities**:
- Filter events for a specific date
- Sort events by start time
- Enforce max visible events limit (FR-019)
- Identify currently-in-progress event

**Interface**:
```python
class DailyViewBuilder:
    def build(
        self,
        target_date: date,
        events: List[CalendarEvent],
        max_visible: int
    ) -> DailyView:
        """Build daily event view."""
        pass

    def _sort_by_start_time(
        self,
        events: List[CalendarEvent]
    ) -> List[CalendarEvent]:
        """Sort events chronologically."""
        pass
```

---

## Relationships

```
DisplayConfiguration
    ├─── 1..* CalendarSource
    │         └─── 1..* CalendarEvent
    │
    ├─── builds MonthlyView
    │         ├─── contains Week (1..6)
    │         │       └─── contains Day (7)
    │         │               └─── references CalendarEvent (0..*)
    │         └─── events_by_date: Dict[date, List[CalendarEvent]]
    │
    └─── builds DailyView
              └─── contains CalendarEvent (0..5 visible, 0..* total)

SyncMetadata
    └─── tracks SyncResult for each CalendarSource
```

---

## State Transitions

### CalendarSource Sync Status

```
NEVER_SYNCED
    │
    ├─ (sync attempt starts) → PENDING
    │
PENDING
    │
    ├─ (sync succeeds) → SUCCESS
    │
    └─ (sync fails) → FAILED

SUCCESS / FAILED
    │
    └─ (next sync attempt) → PENDING
```

### Cache Lifecycle

```
1. Empty Cache
   └─> First Sync → Cache Populated (cache_valid_until = now + 24h)

2. Valid Cache
   └─> Scheduled Refresh → New Sync → Cache Updated (cache_valid_until refreshed)

3. Stale Cache (past cache_valid_until)
   └─> Display stale data with warning → Next sync → Cache Updated

4. Network Failure
   └─> Keep displaying stale data → Log failure → Retry at next scheduled time
```

---

## Validation Matrix

| Entity | Validation Rule | Rationale | Related FR |
|--------|----------------|-----------|------------|
| `CalendarEvent` | end >= start | Prevent invalid time ranges | FR-005 |
| `CalendarEvent` | title not empty | Display requirement | FR-005 |
| `DisplayConfiguration` | refresh_hour 0-23 | Valid hour | FR-007 |
| `DisplayConfiguration` | >= 1 enabled source | Must have data to display | FR-001 |
| `DailyView` | max 5 visible events | User story requirement | FR-019 |
| `MonthlyView` | events sorted by date | Display consistency | FR-006 |
| `CalendarSource` | valid timezone string | Correct time display | FR-002 |

---

## Persistence Strategy

### Calendar Events Cache

**Format**: JSON file per source
**Location**: `/var/cache/kalendar/sources/{source_id}.json`
**Structure**:
```json
{
  "source_id": "google-primary",
  "source_name": "Family Calendar",
  "last_sync": "2025-11-15T00:00:00Z",
  "events": [
    {
      "id": "event123",
      "title": "Doctor Appointment",
      "start_datetime": "2025-11-16T14:00:00-05:00",
      "end_datetime": "2025-11-16T15:00:00-05:00",
      "is_all_day": false,
      "location": "Medical Center",
      "description": "",
      "is_recurring": false
    }
  ]
}
```

### Configuration

**Format**: YAML
**Location**: `/etc/kalendar/config.yaml`
**Structure**:
```yaml
refresh_hour: 0
timezone: "America/New_York"
week_start_day: 0  # Monday

calendar_sources:
  - id: "google-primary"
    name: "Family Calendar"
    source_type: "google"
    calendar_id: "primary"
    enabled: true

  - id: "icloud-family"
    name: "iCloud Family"
    source_type: "caldav"
    calendar_id: "https://caldav.icloud.com/.../calendar/"
    enabled: true

display:
  max_daily_events: 5
  layout: "horizontal"
```

### Credentials

**Format**: JSON (separate from config for security)
**Location**: `/etc/kalendar/credentials.json` (chmod 600)
**Structure**:
```json
{
  "google": {
    "token_file": "/etc/kalendar/google_token.json",
    "credentials_file": "/etc/kalendar/google_credentials.json"
  },
  "caldav": {
    "username": "user@icloud.com",
    "app_password": "xxxx-xxxx-xxxx-xxxx"
  }
}
```

---

## Type Hints

All domain models will use Python type hints for mypy compliance:

```python
from dataclasses import dataclass
from datetime import datetime, date
from typing import List, Dict, Optional
from enum import Enum

@dataclass
class CalendarEvent:
    id: str
    calendar_source_id: str
    title: str
    start_datetime: datetime
    end_datetime: datetime
    is_all_day: bool
    location: Optional[str] = None
    description: Optional[str] = None
    is_recurring: bool = False
    recurrence_id: Optional[str] = None
```

---

**Data Model Complete**: Ready for contract generation (Phase 1 continues).
