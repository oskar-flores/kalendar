"""Unit tests for CalendarEvent domain model."""

from datetime import datetime, timezone

import pytest

from kalendar.domain.models.event import CalendarEvent


class TestCalendarEvent:
    """Test suite for CalendarEvent model."""

    def test_create_valid_event(self) -> None:
        """Should create a valid calendar event with required fields."""
        event = CalendarEvent(
            id="evt-123",
            calendar_source_id="src-1",
            title="Team Meeting",
            start_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )

        assert event.id == "evt-123"
        assert event.calendar_source_id == "src-1"
        assert event.title == "Team Meeting"
        assert event.is_all_day is False

    def test_is_multi_day_single_day_event(self) -> None:
        """Single-day event should return False for is_multi_day()."""
        event = CalendarEvent(
            id="evt-1",
            calendar_source_id="src-1",
            title="Dentist",
            start_datetime=datetime(2025, 11, 16, 9, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )

        assert event.is_multi_day() is False

    def test_is_multi_day_spans_multiple_days(self) -> None:
        """Event spanning multiple days should return True for is_multi_day()."""
        event = CalendarEvent(
            id="evt-2",
            calendar_source_id="src-1",
            title="Conference",
            start_datetime=datetime(2025, 11, 15, 9, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 17, 18, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )

        assert event.is_multi_day() is True

    def test_is_multi_day_crosses_midnight(self) -> None:
        """Event crossing midnight should return True for is_multi_day()."""
        event = CalendarEvent(
            id="evt-3",
            calendar_source_id="src-1",
            title="Late Event",
            start_datetime=datetime(2025, 11, 16, 23, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 17, 1, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )

        assert event.is_multi_day() is True

    def test_truncated_title_short_title(self) -> None:
        """Short title should not be truncated."""
        event = CalendarEvent(
            id="evt-1",
            calendar_source_id="src-1",
            title="Meet",
            start_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )

        assert event.truncated_title(20) == "Meet"

    def test_truncated_title_long_title(self) -> None:
        """Long title should be truncated with ellipsis."""
        event = CalendarEvent(
            id="evt-1",
            calendar_source_id="src-1",
            title="This is a very long title that should be truncated",
            start_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )

        result = event.truncated_title(20)
        assert len(result) == 20
        assert result.endswith("...")
        assert result == "This is a very lo..."

    def test_truncated_title_exact_length(self) -> None:
        """Title exactly at max length should not be truncated."""
        event = CalendarEvent(
            id="evt-1",
            calendar_source_id="src-1",
            title="Exactly20Characters",
            start_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
            is_all_day=False,
        )

        result = event.truncated_title(20)
        assert result == "Exactly20Characters"

    def test_event_with_optional_fields(self) -> None:
        """Should create event with optional location and description."""
        event = CalendarEvent(
            id="evt-1",
            calendar_source_id="src-1",
            title="Client Meeting",
            start_datetime=datetime(2025, 11, 16, 14, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 16, 15, 30, tzinfo=timezone.utc),
            is_all_day=False,
            location="Conference Room A",
            description="Quarterly review with client",
        )

        assert event.location == "Conference Room A"
        assert event.description == "Quarterly review with client"

    def test_all_day_event(self) -> None:
        """Should handle all-day events correctly."""
        event = CalendarEvent(
            id="evt-1",
            calendar_source_id="src-1",
            title="Birthday",
            start_datetime=datetime(2025, 11, 16, 0, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 17, 0, 0, tzinfo=timezone.utc),
            is_all_day=True,
        )

        assert event.is_all_day is True
        assert event.is_multi_day() is True

    def test_recurring_event(self) -> None:
        """Should handle recurring event properties."""
        event = CalendarEvent(
            id="evt-1",
            calendar_source_id="src-1",
            title="Weekly Standup",
            start_datetime=datetime(2025, 11, 16, 9, 0, tzinfo=timezone.utc),
            end_datetime=datetime(2025, 11, 16, 9, 30, tzinfo=timezone.utc),
            is_all_day=False,
            is_recurring=True,
            recurrence_id="weekly-standup-series",
        )

        assert event.is_recurring is True
        assert event.recurrence_id == "weekly-standup-series"
