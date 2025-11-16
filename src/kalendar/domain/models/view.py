"""View domain models for calendar display."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from kalendar.domain.models.event import CalendarEvent


@dataclass
class Day:
    """Represents a single day cell in the calendar grid.

    Attributes:
        date: The date of this day
        is_current_month: False for padding days from adjacent months
        is_today: True if this is the current day
        has_events: True if there are events on this day
        event_count: Number of events on this day
        events: List of events on this day
    """

    date: date
    is_current_month: bool
    is_today: bool
    has_events: bool
    event_count: int
    events: list[CalendarEvent]


@dataclass
class Week:
    """Represents a week row in the calendar grid.

    Attributes:
        days: Always 7 days (Sun-Sat or Mon-Sun based on config)
    """

    days: list[Day]

    def __post_init__(self) -> None:
        """Validate week has exactly 7 days."""
        if len(self.days) != 7:
            raise ValueError("Week must contain exactly 7 days")


@dataclass
class MonthlyView:
    """Represents the monthly calendar grid for display rendering.

    Attributes:
        year: Year to display
        month: Month to display (1-12)
        today: Current date for highlighting
        weeks: List of weeks in the month (typically 5-6)
        events_by_date: Map of date to events on that day
    """

    year: int
    month: int
    today: date
    weeks: list[Week]
    events_by_date: dict[date, list[CalendarEvent]]

    def __post_init__(self) -> None:
        """Validate monthly view data."""
        if not 1 <= self.month <= 12:
            raise ValueError("Month must be between 1 and 12")

        if not self.weeks:
            raise ValueError("MonthlyView must have at least one week")

    def get_month_name(self) -> str:
        """Returns month name (e.g., 'November').

        Returns:
            Full month name
        """
        import calendar

        return calendar.month_name[self.month]

    def get_days_with_events(self) -> list[date]:
        """Returns sorted list of dates that have events.

        Returns:
            List of dates with at least one event
        """
        return sorted(self.events_by_date.keys())

    def get_all_events(self) -> list[CalendarEvent]:
        """Returns all events in the month.

        Returns:
            Flattened list of all events
        """
        all_events: list[CalendarEvent] = []
        for event_list in self.events_by_date.values():
            all_events.extend(event_list)
        return all_events


@dataclass
class DailyView:
    """Represents today's event details section.

    Attributes:
        date: The date being displayed (usually today)
        events: Events for this date, sorted by start time
        max_visible_events: Maximum events to display (5 per FR-019)
        total_event_count: Total events for this date
    """

    date: date
    events: list[CalendarEvent]
    max_visible_events: int
    total_event_count: int

    def __post_init__(self) -> None:
        """Validate daily view data."""
        if self.max_visible_events <= 0:
            raise ValueError("max_visible_events must be greater than 0")

        if self.total_event_count < len(self.events):
            raise ValueError("total_event_count cannot be less than events list length")

    def get_visible_events(self) -> list[CalendarEvent]:
        """Returns up to max_visible_events events.

        Returns:
            Slice of events list limited by max_visible_events
        """
        return self.events[: self.max_visible_events]

    def get_overflow_count(self) -> int:
        """Returns number of events not shown due to limit.

        Returns:
            Count of hidden events
        """
        return max(0, self.total_event_count - self.max_visible_events)

    def has_overflow(self) -> bool:
        """Returns True if there are more events than can be displayed.

        Returns:
            True if overflow exists
        """
        return self.get_overflow_count() > 0

    def get_current_event(self, reference_time: datetime) -> Optional[CalendarEvent]:
        """Returns the event currently in progress, if any.

        Args:
            reference_time: Time to check for current event

        Returns:
            Currently active event or None
        """
        for event in self.events:
            if event.start_datetime <= reference_time <= event.end_datetime:
                return event
        return None
