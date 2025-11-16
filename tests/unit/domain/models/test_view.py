"""Unit tests for view domain models."""

from datetime import date, datetime, timezone

import pytest

from kalendar.domain.models.event import CalendarEvent
from kalendar.domain.models.view import Day, DailyView, MonthlyView, Week


class TestDay:
    """Test suite for Day model."""

    def test_create_day_with_events(self) -> None:
        """Should create day with events."""
        event = CalendarEvent(
            id="evt-1",
            calendar_source_id="src-1",
            title="Meeting",
            start_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )

        day = Day(
            date=date(2025, 11, 16),
            is_current_month=True,
            is_today=True,
            has_events=True,
            event_count=1,
            events=[event],
        )

        assert day.has_events is True
        assert day.event_count == 1
        assert len(day.events) == 1


class TestWeek:
    """Test suite for Week model."""

    def test_create_week_with_seven_days(self) -> None:
        """Should create week with 7 days."""
        days = [
            Day(
                date=date(2025, 11, i),
                is_current_month=True,
                is_today=False,
                has_events=False,
                event_count=0,
                events=[],
            )
            for i in range(10, 17)
        ]

        week = Week(days=days)
        assert len(week.days) == 7

    def test_week_validates_seven_days(self) -> None:
        """Should reject week with wrong number of days."""
        with pytest.raises(ValueError, match="Week must contain exactly 7 days"):
            Week(days=[])


class TestMonthlyView:
    """Test suite for MonthlyView model."""

    def test_create_monthly_view(self) -> None:
        """Should create valid monthly view."""
        week = Week(
            days=[
                Day(
                    date=date(2025, 11, i),
                    is_current_month=True,
                    is_today=False,
                    has_events=False,
                    event_count=0,
                    events=[],
                )
                for i in range(10, 17)
            ]
        )

        monthly = MonthlyView(
            year=2025,
            month=11,
            today=date(2025, 11, 16),
            weeks=[week],
            events_by_date={},
        )

        assert monthly.year == 2025
        assert monthly.month == 11

    def test_get_month_name(self) -> None:
        """Should return correct month name."""
        week = Week(
            days=[
                Day(
                    date=date(2025, 11, i),
                    is_current_month=True,
                    is_today=False,
                    has_events=False,
                    event_count=0,
                    events=[],
                )
                for i in range(10, 17)
            ]
        )

        monthly = MonthlyView(
            year=2025,
            month=11,
            today=date(2025, 11, 16),
            weeks=[week],
            events_by_date={},
        )

        assert monthly.get_month_name() == "November"

    def test_validate_month_range(self) -> None:
        """Should validate month is 1-12."""
        week = Week(
            days=[
                Day(
                    date=date(2025, 11, i),
                    is_current_month=True,
                    is_today=False,
                    has_events=False,
                    event_count=0,
                    events=[],
                )
                for i in range(10, 17)
            ]
        )

        with pytest.raises(ValueError, match="Month must be between 1 and 12"):
            MonthlyView(
                year=2025,
                month=13,
                today=date(2025, 11, 16),
                weeks=[week],
                events_by_date={},
            )


class TestDailyView:
    """Test suite for DailyView model."""

    def test_create_daily_view(self) -> None:
        """Should create valid daily view."""
        events = [
            CalendarEvent(
                id="evt-1",
                calendar_source_id="src-1",
                title="Meeting",
                start_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
                is_all_day=False,
            )
        ]

        daily = DailyView(
            date=date(2025, 11, 16),
            events=events,
            max_visible_events=5,
            total_event_count=1,
        )

        assert daily.date == date(2025, 11, 16)
        assert len(daily.events) == 1

    def test_get_visible_events_within_limit(self) -> None:
        """Should return all events when under limit."""
        events = [
            CalendarEvent(
                id=f"evt-{i}",
                calendar_source_id="src-1",
                title=f"Event {i}",
                start_datetime=datetime(2025, 11, 16, 10 + i, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 11 + i, 0, tzinfo=timezone.utc),
                is_all_day=False,
            )
            for i in range(3)
        ]

        daily = DailyView(
            date=date(2025, 11, 16),
            events=events,
            max_visible_events=5,
            total_event_count=3,
        )

        visible = daily.get_visible_events()
        assert len(visible) == 3

    def test_get_visible_events_at_limit(self) -> None:
        """Should cap events at max_visible_events."""
        events = [
            CalendarEvent(
                id=f"evt-{i}",
                calendar_source_id="src-1",
                title=f"Event {i}",
                start_datetime=datetime(2025, 11, 16, 10 + i, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 11 + i, 0, tzinfo=timezone.utc),
                is_all_day=False,
            )
            for i in range(10)
        ]

        daily = DailyView(
            date=date(2025, 11, 16),
            events=events,
            max_visible_events=5,
            total_event_count=10,
        )

        visible = daily.get_visible_events()
        assert len(visible) == 5

    def test_get_overflow_count_no_overflow(self) -> None:
        """Should return 0 when no overflow."""
        daily = DailyView(
            date=date(2025, 11, 16),
            events=[],
            max_visible_events=5,
            total_event_count=3,
        )

        assert daily.get_overflow_count() == 0
        assert daily.has_overflow() is False

    def test_get_overflow_count_with_overflow(self) -> None:
        """Should calculate overflow correctly."""
        daily = DailyView(
            date=date(2025, 11, 16),
            events=[],
            max_visible_events=5,
            total_event_count=8,
        )

        assert daily.get_overflow_count() == 3
        assert daily.has_overflow() is True
