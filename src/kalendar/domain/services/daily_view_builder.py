"""DailyViewBuilder domain service."""

from datetime import date

from kalendar.domain.models.event import CalendarEvent
from kalendar.domain.models.view import DailyView


class DailyViewBuilder:
    """Constructs DailyView domain object from events.

    Responsibilities:
    - Filter events for a specific date
    - Sort events by start time
    - Enforce max visible events limit
    """

    def build(
        self, target_date: date, events: list[CalendarEvent], max_visible: int
    ) -> DailyView:
        """Build daily event view.

        Args:
            target_date: Date to show events for
            events: All calendar events
            max_visible: Maximum events to display

        Returns:
            DailyView object ready for rendering
        """
        # Filter events for target date
        daily_events = self._filter_events_for_date(events, target_date)

        # Sort by start time
        sorted_events = self._sort_by_start_time(daily_events)

        return DailyView(
            date=target_date,
            events=sorted_events,
            max_visible_events=max_visible,
            total_event_count=len(sorted_events),
        )

    def _filter_events_for_date(
        self, events: list[CalendarEvent], target_date: date
    ) -> list[CalendarEvent]:
        """Filter events occurring on target date.

        Args:
            events: All events to filter
            target_date: Date to filter for

        Returns:
            Events occurring on target_date
        """
        matching: list[CalendarEvent] = []

        for event in events:
            start_date = event.start_datetime.date()
            end_date = event.end_datetime.date()

            # Include event if it spans target date
            if start_date <= target_date <= end_date:
                matching.append(event)

        return matching

    def _sort_by_start_time(
        self, events: list[CalendarEvent]
    ) -> list[CalendarEvent]:
        """Sort events chronologically by start time.

        All-day events are placed first, followed by timed events sorted by start time.

        Args:
            events: Events to sort

        Returns:
            Events sorted by all-day status first, then by start_datetime
        """
        # Sort: all-day events first (is_all_day=True), then by start time
        return sorted(events, key=lambda e: (not e.is_all_day, e.start_datetime))
