"""Unit tests for RenderDailyViewUseCase.

Tests the daily view rendering use case that builds DailyView from events
and prepares it for template rendering.
"""

from datetime import datetime, date
from zoneinfo import ZoneInfo

import pytest

from kalendar.domain.models.event import CalendarEvent
from kalendar.domain.models.view import DailyView
from kalendar.domain.services.daily_view_builder import DailyViewBuilder
from kalendar.application.usecases.render_daily_view import RenderDailyViewUseCase


@pytest.fixture
def sample_events() -> list[CalendarEvent]:
    """Create sample events for today."""
    tz = ZoneInfo("America/New_York")
    today = date.today()

    return [
        CalendarEvent(
            id="event-1",
            calendar_source_id="source-1",
            title="Morning Standup",
            start_datetime=datetime(today.year, today.month, today.day, 9, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 9, 30, tzinfo=tz),
            is_all_day=False,
            location="Zoom",
        ),
        CalendarEvent(
            id="event-2",
            calendar_source_id="source-1",
            title="Team Lunch",
            start_datetime=datetime(today.year, today.month, today.day, 12, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 13, 0, tzinfo=tz),
            is_all_day=False,
            location="Office Cafeteria",
        ),
    ]


@pytest.mark.unit
def test_render_daily_view_builds_daily_view(sample_events: list[CalendarEvent]) -> None:
    """Test that RenderDailyViewUseCase builds a DailyView from events."""
    # Arrange
    builder = DailyViewBuilder()
    use_case = RenderDailyViewUseCase(daily_view_builder=builder)
    today = date.today()
    max_visible = 5

    # Act
    result = use_case.execute(
        target_date=today,
        events=sample_events,
        max_visible_events=max_visible
    )

    # Assert
    assert isinstance(result, DailyView)
    assert result.date == today
    assert result.max_visible_events == max_visible
    assert len(result.get_visible_events()) == 2


@pytest.mark.unit
def test_render_daily_view_includes_current_event_detection(
    sample_events: list[CalendarEvent]
) -> None:
    """Test that RenderDailyViewUseCase identifies the currently in-progress event."""
    # Arrange
    builder = DailyViewBuilder()
    use_case = RenderDailyViewUseCase(daily_view_builder=builder)
    today = date.today()

    # Create a reference time during the first event
    tz = ZoneInfo("America/New_York")
    reference_time = datetime(today.year, today.month, today.day, 9, 15, tzinfo=tz)

    # Act
    daily_view = use_case.execute(
        target_date=today,
        events=sample_events,
        max_visible_events=5,
        reference_time=reference_time
    )

    # Get current event
    current_event = daily_view.get_current_event(reference_time)

    # Assert
    assert current_event is not None
    assert current_event.title == "Morning Standup"


@pytest.mark.unit
def test_render_daily_view_handles_empty_events() -> None:
    """Test that RenderDailyViewUseCase handles days with no events."""
    # Arrange
    builder = DailyViewBuilder()
    use_case = RenderDailyViewUseCase(daily_view_builder=builder)
    today = date.today()

    # Act
    result = use_case.execute(
        target_date=today,
        events=[],
        max_visible_events=5
    )

    # Assert
    assert isinstance(result, DailyView)
    assert result.total_event_count == 0
    assert len(result.get_visible_events()) == 0
    assert not result.has_overflow()


@pytest.mark.unit
def test_render_daily_view_enforces_max_visible_limit(
    sample_events: list[CalendarEvent]
) -> None:
    """Test that RenderDailyViewUseCase enforces the max visible events limit."""
    # Arrange
    tz = ZoneInfo("America/New_York")
    today = date.today()

    # Create 7 events
    many_events = sample_events + [
        CalendarEvent(
            id=f"extra-{i}",
            calendar_source_id="source-1",
            title=f"Event {i}",
            start_datetime=datetime(today.year, today.month, today.day, 14 + i, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 15 + i, 0, tzinfo=tz),
            is_all_day=False,
        )
        for i in range(5)
    ]

    builder = DailyViewBuilder()
    use_case = RenderDailyViewUseCase(daily_view_builder=builder)
    max_visible = 5  # FR-019

    # Act
    result = use_case.execute(
        target_date=today,
        events=many_events,
        max_visible_events=max_visible
    )

    # Assert
    assert len(result.get_visible_events()) == 5
    assert result.total_event_count == 7
    assert result.has_overflow()
    assert result.get_overflow_count() == 2


@pytest.mark.unit
def test_render_daily_view_filters_only_today_events() -> None:
    """Test that RenderDailyViewUseCase only includes events for the target date."""
    # Arrange
    tz = ZoneInfo("America/New_York")
    today = date.today()
    tomorrow = date(today.year, today.month, today.day + 1 if today.day < 28 else 1)

    events = [
        CalendarEvent(
            id="today-event",
            calendar_source_id="source-1",
            title="Today's Event",
            start_datetime=datetime(today.year, today.month, today.day, 10, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 11, 0, tzinfo=tz),
            is_all_day=False,
        ),
        CalendarEvent(
            id="tomorrow-event",
            calendar_source_id="source-1",
            title="Tomorrow's Event",
            start_datetime=datetime(tomorrow.year, tomorrow.month, tomorrow.day, 10, 0, tzinfo=tz),
            end_datetime=datetime(tomorrow.year, tomorrow.month, tomorrow.day, 11, 0, tzinfo=tz),
            is_all_day=False,
        ),
    ]

    builder = DailyViewBuilder()
    use_case = RenderDailyViewUseCase(daily_view_builder=builder)

    # Act
    result = use_case.execute(
        target_date=today,
        events=events,
        max_visible_events=5
    )

    # Assert
    assert result.total_event_count == 1
    assert result.get_visible_events()[0].title == "Today's Event"


@pytest.mark.unit
def test_render_daily_view_returns_context_for_template() -> None:
    """Test that RenderDailyViewUseCase can provide template context."""
    # Arrange
    builder = DailyViewBuilder()
    use_case = RenderDailyViewUseCase(daily_view_builder=builder)
    today = date.today()
    tz = ZoneInfo("America/New_York")

    events = [
        CalendarEvent(
            id="event-1",
            calendar_source_id="source-1",
            title="Event",
            start_datetime=datetime(today.year, today.month, today.day, 10, 0, tzinfo=tz),
            end_datetime=datetime(today.year, today.month, today.day, 11, 0, tzinfo=tz),
            is_all_day=False,
        ),
    ]

    reference_time = datetime(today.year, today.month, today.day, 10, 30, tzinfo=tz)

    # Act
    daily_view = use_case.execute(
        target_date=today,
        events=events,
        max_visible_events=5,
        reference_time=reference_time
    )

    context = use_case.get_template_context(daily_view, reference_time)

    # Assert
    assert "daily_view" in context
    assert "current_event" in context
    assert context["daily_view"] == daily_view
    assert context["current_event"] is not None
    assert context["current_event"].title == "Event"
