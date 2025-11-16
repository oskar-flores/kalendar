"""EventAggregator domain service."""

from datetime import date

from kalendar.domain.models.event import CalendarEvent


class EventAggregator:
    """Combines events from multiple calendar sources.

    Responsibilities:
    - Merge events from multiple CalendarSource instances
    - Deduplicate events that appear in multiple calendars
    - Sort events by start time
    - Filter events by date range
    """

    def deduplicate_events(self, events: list[CalendarEvent]) -> list[CalendarEvent]:
        """Remove duplicate events based on title, time, and location.

        Args:
            events: List of calendar events (possibly with duplicates)

        Returns:
            List of unique events
        """
        if not events:
            return []

        # Track unique events by (title, start_time, end_time, location)
        seen: set[tuple[str, str, str, str]] = set()
        unique_events: list[CalendarEvent] = []

        for event in events:
            # Create signature for deduplication
            signature = (
                event.title,
                event.start_datetime.isoformat(),
                event.end_datetime.isoformat(),
                event.location or "",
            )

            if signature not in seen:
                seen.add(signature)
                unique_events.append(event)

        return unique_events

    def get_events_for_date(
        self, events: list[CalendarEvent], target_date: date
    ) -> list[CalendarEvent]:
        """Filter events occurring on a specific date.

        Includes:
        - Events that start on target_date
        - Multi-day events that span target_date
        - All-day events on target_date

        Args:
            events: List of all calendar events
            target_date: Date to filter for

        Returns:
            List of events occurring on target_date, sorted by start time
        """
        matching_events: list[CalendarEvent] = []

        for event in events:
            start_date = event.start_datetime.date()
            end_date = event.end_datetime.date()

            # Check if event occurs on target date
            if start_date <= target_date <= end_date:
                matching_events.append(event)

        # Sort by start time
        matching_events.sort(key=lambda e: e.start_datetime)

        return matching_events
