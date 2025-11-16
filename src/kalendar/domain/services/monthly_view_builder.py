"""MonthlyViewBuilder domain service."""

import calendar
from datetime import date, timedelta

from kalendar.domain.models.config import DisplayConfiguration
from kalendar.domain.models.event import CalendarEvent
from kalendar.domain.models.view import Day, MonthlyView, Week


class MonthlyViewBuilder:
    """Constructs MonthlyView domain object from events and configuration.

    Responsibilities:
    - Generate calendar grid for a given month
    - Map events to days in the grid
    - Handle month boundary padding
    """

    def build(
        self,
        year: int,
        month: int,
        events: list[CalendarEvent],
        config: DisplayConfiguration,
    ) -> MonthlyView:
        """Build monthly calendar view.

        Args:
            year: Year to display
            month: Month to display (1-12)
            events: All calendar events
            config: Display configuration

        Returns:
            MonthlyView object ready for rendering
        """
        today = date.today()

        # Group events by date
        events_by_date: dict[date, list[CalendarEvent]] = {}
        for event in events:
            # Get all dates this event spans
            start_date = event.start_datetime.date()
            end_date = event.end_datetime.date()

            current_date = start_date
            while current_date <= end_date:
                # Only include dates in the target month
                if current_date.year == year and current_date.month == month:
                    if current_date not in events_by_date:
                        events_by_date[current_date] = []
                    events_by_date[current_date].append(event)
                current_date += timedelta(days=1)

        # Generate weeks
        weeks = self._generate_weeks(year, month, today, events_by_date, config)

        return MonthlyView(
            year=year,
            month=month,
            today=today,
            weeks=weeks,
            events_by_date=events_by_date,
        )

    def _generate_weeks(
        self,
        year: int,
        month: int,
        today: date,
        events_by_date: dict[date, list[CalendarEvent]],
        config: DisplayConfiguration,
    ) -> list[Week]:
        """Generate week rows with proper padding.

        Args:
            year: Year of the month
            month: Month number (1-12)
            today: Current date for highlighting
            events_by_date: Events grouped by date
            config: Display configuration

        Returns:
            List of Week objects with proper day padding
        """
        # Get first and last day of month
        first_day = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])

        # Calculate padding based on week_start_day
        # 0 = Monday, 6 = Sunday
        first_weekday = first_day.weekday()  # 0 = Monday
        week_start = config.week_start_day

        # Calculate how many days to pad at start
        days_before = (first_weekday - week_start) % 7

        # Start from the first day shown (may be previous month)
        current_date = first_day - timedelta(days=days_before)

        weeks: list[Week] = []
        week_days: list[Day] = []

        # Generate days until we've covered the whole month
        while current_date <= last_day or len(week_days) > 0:
            # Create day object
            is_current_month = current_date.month == month
            is_today_flag = current_date == today
            has_events = current_date in events_by_date
            event_count = len(events_by_date.get(current_date, []))
            day_events = events_by_date.get(current_date, [])

            day = Day(
                date=current_date,
                is_current_month=is_current_month,
                is_today=is_today_flag,
                has_events=has_events,
                event_count=event_count,
                events=day_events,
            )

            week_days.append(day)

            # Complete week when we have 7 days
            if len(week_days) == 7:
                weeks.append(Week(days=week_days))
                week_days = []

            current_date += timedelta(days=1)

            # Stop if we've passed the last day and completed the week
            if current_date > last_day and len(week_days) == 0:
                break

        return weeks
