"""CalendarEvent domain model."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CalendarEvent:
    """Represents a single calendar event from any source.

    Attributes:
        id: Event identifier from source calendar (unique per source)
        calendar_source_id: Reference to CalendarSource that owns this event
        title: Event title/summary (max 200 chars)
        start_datetime: Event start time (timezone-aware)
        end_datetime: Event end time (timezone-aware)
        is_all_day: True if event spans entire day(s)
        location: Event location (max 150 chars)
        description: Event description/notes (max 1000 chars)
        is_recurring: True if part of recurring series
        recurrence_id: Identifier for recurring series
    """

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

    def __post_init__(self) -> None:
        """Validate event data after initialization."""
        if not self.title:
            raise ValueError("Event title cannot be empty")

        if self.end_datetime < self.start_datetime:
            raise ValueError("Event end_datetime must be >= start_datetime")

        if len(self.title) > 200:
            raise ValueError("Event title cannot exceed 200 characters")

        if self.location and len(self.location) > 150:
            raise ValueError("Event location cannot exceed 150 characters")

        if self.description and len(self.description) > 1000:
            raise ValueError("Event description cannot exceed 1000 characters")

    def is_multi_day(self) -> bool:
        """Returns True if event spans multiple calendar days.

        Returns:
            True if end date is after start date, False otherwise
        """
        return self.end_datetime.date() > self.start_datetime.date()

    def truncated_title(self, max_length: int) -> str:
        """Returns title truncated to max_length with ellipsis if needed.

        Args:
            max_length: Maximum length of returned string

        Returns:
            Title string, truncated with "..." if longer than max_length
        """
        if len(self.title) <= max_length:
            return self.title
        return self.title[: max_length - 3] + "..."
