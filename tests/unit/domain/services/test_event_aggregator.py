"""Unit tests for EventAggregator domain service."""

from datetime import date, datetime, timezone

import pytest

from kalendar.domain.models.event import CalendarEvent
from kalendar.domain.services.event_aggregator import EventAggregator


class TestEventAggregator:
    """Test suite for EventAggregator service."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.aggregator = EventAggregator()

    def test_deduplicate_events_no_duplicates(self) -> None:
        """Should return all events when there are no duplicates."""
        events = [
            CalendarEvent(
                id="evt-1",
                calendar_source_id="src-1",
                title="Meeting A",
                start_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 11, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
            CalendarEvent(
                id="evt-2",
                calendar_source_id="src-1",
                title="Meeting B",
                start_datetime=datetime(2025, 11, 16, 14, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 15, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
        ]

        result = self.aggregator.deduplicate_events(events)
        assert len(result) == 2

    def test_deduplicate_events_exact_duplicates(self) -> None:
        """Should remove exact duplicate events."""
        event_duplicate = [
            CalendarEvent(
                id="evt-1",
                calendar_source_id="src-1",
                title="Team Standup",
                start_datetime=datetime(2025, 11, 16, 9, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 9, 30, tzinfo=timezone.utc),
                is_all_day=False,
                location="Office",
            ),
            CalendarEvent(
                id="evt-2",  # Different ID
                calendar_source_id="src-2",  # Different source
                title="Team Standup",  # Same title
                start_datetime=datetime(2025, 11, 16, 9, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 9, 30, tzinfo=timezone.utc),
                is_all_day=False,
                location="Office",  # Same location
            ),
        ]

        result = self.aggregator.deduplicate_events(event_duplicate)
        assert len(result) == 1
        assert result[0].title == "Team Standup"

    def test_deduplicate_events_different_times(self) -> None:
        """Should keep events with same title but different times."""
        events = [
            CalendarEvent(
                id="evt-1",
                calendar_source_id="src-1",
                title="Lunch",
                start_datetime=datetime(2025, 11, 16, 12, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 13, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
            CalendarEvent(
                id="evt-2",
                calendar_source_id="src-1",
                title="Lunch",
                start_datetime=datetime(2025, 11, 17, 12, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 17, 13, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
        ]

        result = self.aggregator.deduplicate_events(events)
        assert len(result) == 2

    def test_get_events_for_date_single_day_events(self) -> None:
        """Should filter events occurring on specific date."""
        target = date(2025, 11, 16)
        events = [
            CalendarEvent(
                id="evt-1",
                calendar_source_id="src-1",
                title="Morning Event",
                start_datetime=datetime(2025, 11, 16, 9, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
            CalendarEvent(
                id="evt-2",
                calendar_source_id="src-1",
                title="Different Day",
                start_datetime=datetime(2025, 11, 17, 9, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 17, 10, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
            CalendarEvent(
                id="evt-3",
                calendar_source_id="src-1",
                title="Evening Event",
                start_datetime=datetime(2025, 11, 16, 18, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 19, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
        ]

        result = self.aggregator.get_events_for_date(events, target)
        assert len(result) == 2
        assert all(e.start_datetime.date() == target for e in result)

    def test_get_events_for_date_multi_day_events(self) -> None:
        """Should include multi-day events that span target date."""
        target = date(2025, 11, 16)
        events = [
            CalendarEvent(
                id="evt-1",
                calendar_source_id="src-1",
                title="Weekend Trip",
                start_datetime=datetime(2025, 11, 15, 10, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 17, 18, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
            CalendarEvent(
                id="evt-2",
                calendar_source_id="src-1",
                title="Not This Week",
                start_datetime=datetime(2025, 11, 20, 9, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 20, 10, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
        ]

        result = self.aggregator.get_events_for_date(events, target)
        assert len(result) == 1
        assert result[0].title == "Weekend Trip"

    def test_get_events_for_date_all_day_events(self) -> None:
        """Should include all-day events for target date."""
        target = date(2025, 11, 16)
        events = [
            CalendarEvent(
                id="evt-1",
                calendar_source_id="src-1",
                title="Birthday",
                start_datetime=datetime(2025, 11, 16, 0, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 17, 0, 0, tzinfo=timezone.utc),
                is_all_day=True,
            ),
        ]

        result = self.aggregator.get_events_for_date(events, target)
        assert len(result) == 1
        assert result[0].is_all_day is True

    def test_get_events_for_date_empty_list(self) -> None:
        """Should return empty list when no events match."""
        target = date(2025, 11, 16)
        events: list[CalendarEvent] = []

        result = self.aggregator.get_events_for_date(events, target)
        assert len(result) == 0

    def test_get_events_for_date_sorted_by_time(self) -> None:
        """Should return events sorted by start time."""
        target = date(2025, 11, 16)
        events = [
            CalendarEvent(
                id="evt-1",
                calendar_source_id="src-1",
                title="Afternoon",
                start_datetime=datetime(2025, 11, 16, 14, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 15, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
            CalendarEvent(
                id="evt-2",
                calendar_source_id="src-1",
                title="Morning",
                start_datetime=datetime(2025, 11, 16, 9, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 10, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
            CalendarEvent(
                id="evt-3",
                calendar_source_id="src-1",
                title="Lunch",
                start_datetime=datetime(2025, 11, 16, 12, 0, tzinfo=timezone.utc),
                end_datetime=datetime(2025, 11, 16, 13, 0, tzinfo=timezone.utc),
                is_all_day=False,
            ),
        ]

        result = self.aggregator.get_events_for_date(events, target)
        assert len(result) == 3
        assert result[0].title == "Morning"
        assert result[1].title == "Lunch"
        assert result[2].title == "Afternoon"
