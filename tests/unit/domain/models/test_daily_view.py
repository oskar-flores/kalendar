"""Unit tests for DailyView domain model.

Tests the DailyView model's overflow handling, event visibility limits,
and current event identification per FR-019.
"""

from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

import pytest

from kalendar.domain.models.event import CalendarEvent
from kalendar.domain.models.view import DailyView


@pytest.fixture
def sample_date() -> date:
    """Return a fixed date for testing."""
    return date(2025, 11, 16)


@pytest.fixture
def sample_events(sample_date: date) -> list[CalendarEvent]:
    """Create sample events for testing."""
    tz = ZoneInfo("America/New_York")

    return [
        CalendarEvent(
            id=f"event-{i}",
            calendar_source_id="source-1",
            title=f"Event {i}",
            start_datetime=datetime(
                sample_date.year,
                sample_date.month,
                sample_date.day,
                9 + i,
                0,
                tzinfo=tz
            ),
            end_datetime=datetime(
                sample_date.year,
                sample_date.month,
                sample_date.day,
                10 + i,
                0,
                tzinfo=tz
            ),
            is_all_day=False,
        )
        for i in range(8)  # Create 8 events
    ]


@pytest.mark.unit
def test_daily_view_get_visible_events_returns_up_to_max(
    sample_date: date,
    sample_events: list[CalendarEvent]
) -> None:
    """Test that get_visible_events returns at most max_visible_events."""
    # Arrange
    max_visible = 5
    daily_view = DailyView(
        date=sample_date,
        events=sample_events,  # 8 events
        max_visible_events=max_visible,
        total_event_count=len(sample_events)
    )

    # Act
    visible = daily_view.get_visible_events()

    # Assert
    assert len(visible) == max_visible
    assert all(event.title == f"Event {i}" for i, event in enumerate(visible))


@pytest.mark.unit
def test_daily_view_get_overflow_count_calculates_correctly(
    sample_date: date,
    sample_events: list[CalendarEvent]
) -> None:
    """Test that get_overflow_count returns correct number of hidden events."""
    # Arrange
    max_visible = 5
    daily_view = DailyView(
        date=sample_date,
        events=sample_events,  # 8 events
        max_visible_events=max_visible,
        total_event_count=len(sample_events)
    )

    # Act
    overflow_count = daily_view.get_overflow_count()

    # Assert
    assert overflow_count == 3  # 8 - 5 = 3


@pytest.mark.unit
def test_daily_view_has_overflow_true_when_events_exceed_limit(
    sample_date: date,
    sample_events: list[CalendarEvent]
) -> None:
    """Test that has_overflow returns True when total exceeds max_visible."""
    # Arrange
    max_visible = 5
    daily_view = DailyView(
        date=sample_date,
        events=sample_events,  # 8 events
        max_visible_events=max_visible,
        total_event_count=len(sample_events)
    )

    # Act & Assert
    assert daily_view.has_overflow() is True


@pytest.mark.unit
def test_daily_view_has_overflow_false_when_events_within_limit(
    sample_date: date,
    sample_events: list[CalendarEvent]
) -> None:
    """Test that has_overflow returns False when total is within max_visible."""
    # Arrange
    max_visible = 10  # More than available events
    daily_view = DailyView(
        date=sample_date,
        events=sample_events[:5],  # Only 5 events
        max_visible_events=max_visible,
        total_event_count=5
    )

    # Act & Assert
    assert daily_view.has_overflow() is False


@pytest.mark.unit
def test_daily_view_get_overflow_count_zero_when_no_overflow(
    sample_date: date,
    sample_events: list[CalendarEvent]
) -> None:
    """Test that get_overflow_count returns 0 when no overflow."""
    # Arrange
    max_visible = 10
    daily_view = DailyView(
        date=sample_date,
        events=sample_events[:5],
        max_visible_events=max_visible,
        total_event_count=5
    )

    # Act
    overflow_count = daily_view.get_overflow_count()

    # Assert
    assert overflow_count == 0


@pytest.mark.unit
def test_daily_view_get_current_event_returns_event_in_progress(
    sample_date: date
) -> None:
    """Test that get_current_event returns the event currently in progress."""
    # Arrange
    tz = ZoneInfo("America/New_York")
    reference_time = datetime(
        sample_date.year,
        sample_date.month,
        sample_date.day,
        10,
        30,
        tzinfo=tz
    )

    events = [
        CalendarEvent(
            id="past",
            calendar_source_id="source-1",
            title="Past Event",
            start_datetime=datetime(sample_date.year, sample_date.month, sample_date.day, 8, 0, tzinfo=tz),
            end_datetime=datetime(sample_date.year, sample_date.month, sample_date.day, 9, 0, tzinfo=tz),
            is_all_day=False,
        ),
        CalendarEvent(
            id="current",
            calendar_source_id="source-1",
            title="Current Event",
            start_datetime=datetime(sample_date.year, sample_date.month, sample_date.day, 10, 0, tzinfo=tz),
            end_datetime=datetime(sample_date.year, sample_date.month, sample_date.day, 11, 0, tzinfo=tz),
            is_all_day=False,
        ),
        CalendarEvent(
            id="future",
            calendar_source_id="source-1",
            title="Future Event",
            start_datetime=datetime(sample_date.year, sample_date.month, sample_date.day, 12, 0, tzinfo=tz),
            end_datetime=datetime(sample_date.year, sample_date.month, sample_date.day, 13, 0, tzinfo=tz),
            is_all_day=False,
        ),
    ]

    daily_view = DailyView(
        date=sample_date,
        events=events,
        max_visible_events=5,
        total_event_count=3
    )

    # Act
    current_event = daily_view.get_current_event(reference_time)

    # Assert
    assert current_event is not None
    assert current_event.title == "Current Event"


@pytest.mark.unit
def test_daily_view_get_current_event_returns_none_when_no_current(
    sample_date: date
) -> None:
    """Test that get_current_event returns None when no event is in progress."""
    # Arrange
    tz = ZoneInfo("America/New_York")
    reference_time = datetime(
        sample_date.year,
        sample_date.month,
        sample_date.day,
        11,
        30,  # Between events
        tzinfo=tz
    )

    events = [
        CalendarEvent(
            id="past",
            calendar_source_id="source-1",
            title="Past Event",
            start_datetime=datetime(sample_date.year, sample_date.month, sample_date.day, 9, 0, tzinfo=tz),
            end_datetime=datetime(sample_date.year, sample_date.month, sample_date.day, 10, 0, tzinfo=tz),
            is_all_day=False,
        ),
        CalendarEvent(
            id="future",
            calendar_source_id="source-1",
            title="Future Event",
            start_datetime=datetime(sample_date.year, sample_date.month, sample_date.day, 12, 0, tzinfo=tz),
            end_datetime=datetime(sample_date.year, sample_date.month, sample_date.day, 13, 0, tzinfo=tz),
            is_all_day=False,
        ),
    ]

    daily_view = DailyView(
        date=sample_date,
        events=events,
        max_visible_events=5,
        total_event_count=2
    )

    # Act
    current_event = daily_view.get_current_event(reference_time)

    # Assert
    assert current_event is None


@pytest.mark.unit
def test_daily_view_enforces_max_visible_events_limit(
    sample_date: date,
    sample_events: list[CalendarEvent]
) -> None:
    """Test that DailyView enforces FR-019 requirement of max 5 visible events."""
    # Arrange
    max_visible = 5  # FR-019 requirement
    daily_view = DailyView(
        date=sample_date,
        events=sample_events,  # 8 events
        max_visible_events=max_visible,
        total_event_count=len(sample_events)
    )

    # Act
    visible = daily_view.get_visible_events()

    # Assert
    assert len(visible) <= max_visible, "FR-019: Max 5 events must be enforced"
    assert daily_view.max_visible_events == 5


@pytest.mark.unit
def test_daily_view_empty_events_list(sample_date: date) -> None:
    """Test that DailyView handles empty events list correctly."""
    # Arrange
    daily_view = DailyView(
        date=sample_date,
        events=[],
        max_visible_events=5,
        total_event_count=0
    )

    # Act & Assert
    assert daily_view.get_visible_events() == []
    assert daily_view.get_overflow_count() == 0
    assert daily_view.has_overflow() is False
    assert daily_view.total_event_count == 0
