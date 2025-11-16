"""Integration tests for daily view rendering.

Tests the complete rendering pipeline for today's events section,
including HTML template rendering with DailyView data.
"""

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

import pytest

from kalendar.domain.models.event import CalendarEvent
from kalendar.domain.models.view import DailyView
from kalendar.domain.services.daily_view_builder import DailyViewBuilder


@pytest.fixture
def sample_events() -> list[CalendarEvent]:
    """Create sample events for today."""
    tz = ZoneInfo("America/New_York")
    today = date.today()

    return [
        CalendarEvent(
            id="event-1",
            calendar_source_id="source-1",
            title="Morning Meeting",
            start_datetime=datetime(today.year, today.month, today.day, 9, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 10, 0, tzinfo=tz),
            is_all_day=False,
            location="Conference Room A",
        ),
        CalendarEvent(
            id="event-2",
            calendar_source_id="source-1",
            title="Lunch with Team",
            start_datetime=datetime(today.year, today.month, today.day, 12, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 13, 0, tzinfo=tz),
            is_all_day=False,
            location="Cafeteria",
        ),
        CalendarEvent(
            id="event-3",
            calendar_source_id="source-1",
            title="Project Review",
            start_datetime=datetime(today.year, today.month, today.day, 14, 30, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 16, 0, tzinfo=tz),
            is_all_day=False,
            location="Meeting Room B",
        ),
    ]


@pytest.mark.integration
def test_daily_view_integration_renders_todays_events(sample_events: list[CalendarEvent]) -> None:
    """Test that DailyView correctly renders today's events in chronological order."""
    # Arrange
    builder = DailyViewBuilder()
    today = date.today()
    max_visible = 5

    # Act
    daily_view = builder.build(
        target_date=today,
        events=sample_events,
        max_visible=max_visible
    )

    # Assert
    assert daily_view.date == today
    assert len(daily_view.get_visible_events()) == 3
    assert daily_view.total_event_count == 3
    assert not daily_view.has_overflow()

    # Verify chronological order
    visible_events = daily_view.get_visible_events()
    assert visible_events[0].title == "Morning Meeting"
    assert visible_events[1].title == "Lunch with Team"
    assert visible_events[2].title == "Project Review"


@pytest.mark.integration
def test_daily_view_integration_handles_overflow(sample_events: list[CalendarEvent]) -> None:
    """Test that DailyView correctly handles overflow when more than max events."""
    # Arrange
    tz = ZoneInfo("America/New_York")
    today = date.today()

    # Add more events to exceed the limit (spread across different hours)
    extra_events = [
        CalendarEvent(
            id="event-4",
            calendar_source_id="source-1",
            title="Event 4",
            start_datetime=datetime(today.year, today.month, today.day, 16, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 17, 0, tzinfo=tz),
            is_all_day=False,
        ),
        CalendarEvent(
            id="event-5",
            calendar_source_id="source-1",
            title="Event 5",
            start_datetime=datetime(today.year, today.month, today.day, 17, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 18, 0, tzinfo=tz),
            is_all_day=False,
        ),
        CalendarEvent(
            id="event-6",
            calendar_source_id="source-1",
            title="Event 6",
            start_datetime=datetime(today.year, today.month, today.day, 18, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 19, 0, tzinfo=tz),
            is_all_day=False,
        ),
        CalendarEvent(
            id="event-7",
            calendar_source_id="source-1",
            title="Event 7",
            start_datetime=datetime(today.year, today.month, today.day, 19, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 20, 0, tzinfo=tz),
            is_all_day=False,
        ),
    ]

    all_events = sample_events + extra_events
    builder = DailyViewBuilder()
    max_visible = 5  # Per FR-019

    # Act
    daily_view = builder.build(
        target_date=today,
        events=all_events,
        max_visible=max_visible
    )

    # Assert
    assert daily_view.total_event_count == 7
    assert len(daily_view.get_visible_events()) == 5  # Limited to max
    assert daily_view.has_overflow()
    assert daily_view.get_overflow_count() == 2  # 7 - 5 = 2


@pytest.mark.integration
def test_daily_view_integration_identifies_current_event() -> None:
    """Test that DailyView can identify the currently in-progress event."""
    # Arrange
    tz = ZoneInfo("America/New_York")
    now = datetime.now(tz)
    today = now.date()

    # Create events: past, current, future
    events = [
        CalendarEvent(
            id="past-event",
            calendar_source_id="source-1",
            title="Past Event",
            start_datetime=now.replace(hour=8, minute=0),
            end_datetime=now.replace(hour=9, minute=0),
            is_all_day=False,
        ),
        CalendarEvent(
            id="current-event",
            calendar_source_id="source-1",
            title="Current Event",
            start_datetime=now - timedelta(minutes=30),  # Started 30 min ago
            end_datetime=now + timedelta(minutes=30),  # Ends in 30 min
            is_all_day=False,
        ),
        CalendarEvent(
            id="future-event",
            calendar_source_id="source-1",
            title="Future Event",
            start_datetime=now.replace(hour=now.hour + 2, minute=0),
            end_datetime=now.replace(hour=now.hour + 3, minute=0),
            is_all_day=False,
        ),
    ]

    builder = DailyViewBuilder()

    # Act
    daily_view = builder.build(
        target_date=today,
        events=events,
        max_visible=5
    )

    current_event = daily_view.get_current_event(now)

    # Assert
    assert current_event is not None
    assert current_event.title == "Current Event"


@pytest.mark.integration
def test_daily_view_integration_handles_all_day_events() -> None:
    """Test that DailyView correctly handles all-day events."""
    # Arrange
    tz = ZoneInfo("America/New_York")
    today = date.today()

    events = [
        CalendarEvent(
            id="all-day-1",
            calendar_source_id="source-1",
            title="All Day Event",
            start_datetime=datetime(today.year, today.month, today.day, 0, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 23, 59, tzinfo=tz),
            is_all_day=True,
        ),
        CalendarEvent(
            id="timed-1",
            calendar_source_id="source-1",
            title="Timed Event",
            start_datetime=datetime(today.year, today.month, today.day, 10, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 11, 0, tzinfo=tz),
            is_all_day=False,
        ),
    ]

    builder = DailyViewBuilder()

    # Act
    daily_view = builder.build(
        target_date=today,
        events=events,
        max_visible=5
    )

    visible_events = daily_view.get_visible_events()

    # Assert
    assert len(visible_events) == 2
    # All-day events should appear first
    assert visible_events[0].is_all_day
    assert visible_events[0].title == "All Day Event"


@pytest.mark.integration
def test_daily_view_integration_empty_day() -> None:
    """Test that DailyView handles days with no events."""
    # Arrange
    builder = DailyViewBuilder()
    today = date.today()

    # Act
    daily_view = builder.build(
        target_date=today,
        events=[],
        max_visible=5
    )

    # Assert
    assert daily_view.total_event_count == 0
    assert len(daily_view.get_visible_events()) == 0
    assert not daily_view.has_overflow()
    assert daily_view.get_overflow_count() == 0
