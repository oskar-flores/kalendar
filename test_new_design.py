"""Quick test script to render the new calendar design."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from PIL import Image

# Import the necessary classes
from src.kalendar.domain.models.event import CalendarEvent
from src.kalendar.domain.models.config import DisplayConfiguration
from src.kalendar.domain.services.monthly_view_builder import MonthlyViewBuilder
from src.kalendar.domain.services.daily_view_builder import DailyViewBuilder
from src.kalendar.infrastructure.rendering.weasyprint_renderer import WeasyPrintRenderer
from src.kalendar.application.usecases.render_monthly_view import RenderMonthlyViewUseCase


def create_sample_events():
    """Create some sample events for testing."""
    now = datetime.now(timezone.utc)
    today = now.date()

    events = [
        # Today's events
        CalendarEvent(
            id="1",
            calendar_source_id="test",
            title="Team Standup",
            start_datetime=now.replace(hour=9, minute=0),
            end_datetime=now.replace(hour=9, minute=30),
            is_all_day=False,
        ),
        CalendarEvent(
            id="2",
            calendar_source_id="test",
            title="Design Review Meeting",
            start_datetime=now.replace(hour=14, minute=0),
            end_datetime=now.replace(hour=15, minute=0),
            is_all_day=False,
        ),
        CalendarEvent(
            id="3",
            calendar_source_id="test",
            title="Lunch with Client",
            start_datetime=now.replace(hour=12, minute=30),
            end_datetime=now.replace(hour=13, minute=30),
            is_all_day=False,
            location="Cafe Downtown",
        ),
        # Tomorrow's events
        CalendarEvent(
            id="4",
            calendar_source_id="test",
            title="Project Kickoff",
            start_datetime=(now + timedelta(days=1)).replace(hour=10, minute=0),
            end_datetime=(now + timedelta(days=1)).replace(hour=11, minute=0),
            is_all_day=False,
        ),
        CalendarEvent(
            id="5",
            calendar_source_id="test",
            title="Sprint Planning",
            start_datetime=(now + timedelta(days=1)).replace(hour=15, minute=0),
            end_datetime=(now + timedelta(days=1)).replace(hour=16, minute=30),
            is_all_day=False,
        ),
        # Day after tomorrow
        CalendarEvent(
            id="6",
            calendar_source_id="test",
            title="Code Review",
            start_datetime=(now + timedelta(days=2)).replace(hour=11, minute=0),
            end_datetime=(now + timedelta(days=2)).replace(hour=12, minute=0),
            is_all_day=False,
        ),
        # Next week
        CalendarEvent(
            id="7",
            calendar_source_id="test",
            title="Weekly Sync",
            start_datetime=(now + timedelta(days=3)).replace(hour=14, minute=0),
            end_datetime=(now + timedelta(days=3)).replace(hour=15, minute=0),
            is_all_day=False,
        ),
        CalendarEvent(
            id="8",
            calendar_source_id="test",
            title="All-day Workshop",
            start_datetime=(now + timedelta(days=5)).replace(hour=0, minute=0),
            end_datetime=(now + timedelta(days=5)).replace(hour=23, minute=59),
            is_all_day=True,
        ),
    ]

    return events


def main():
    """Render calendar with new design and save to file."""
    print("Testing new calendar design...")
    print("=" * 60)

    # Create sample data
    events = create_sample_events()
    now = datetime.now(timezone.utc)
    today = now.date()

    print(f"Created {len(events)} sample events")
    print(f"Rendering for: {today.strftime('%B %d, %Y')}")

    # Create configuration
    from src.kalendar.domain.models.enums import LayoutType, SourceType
    from src.kalendar.domain.models.source import CalendarSource

    dummy_source = CalendarSource(
        id="test-1",
        name="Test Calendar",
        source_type=SourceType.GOOGLE,
        calendar_id="test@example.com",
        enabled=True,
        credentials=None,
    )

    config = DisplayConfiguration(
        timezone="UTC",
        week_start_day=0,  # Monday
        refresh_hour=6,
        max_daily_events=5,
        display_layout=LayoutType.HORIZONTAL,
        calendar_sources=[dummy_source],
    )

    # Create builders
    monthly_builder = MonthlyViewBuilder()
    daily_builder = DailyViewBuilder()

    # Create renderer
    renderer = WeasyPrintRenderer()

    # Create use case
    use_case = RenderMonthlyViewUseCase(
        renderer=renderer,
        monthly_view_builder=monthly_builder,
        daily_view_builder=daily_builder,
        config=config,
    )

    # Render
    print("\nRendering calendar...")
    image = use_case.execute(
        events=events,
        year=today.year,
        month=today.month,
        today=today,
        current_time=now,
    )

    # Save output
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "new_calendar_design.png"

    image.save(output_path)

    print(f"\n✓ Rendered successfully!")
    print(f"  Size: {image.size[0]}x{image.size[1]} pixels")
    print(f"  Mode: {image.mode}")
    print(f"  Saved to: {output_path}")
    print("\nView the result with:")
    print(f"  xdg-open {output_path}")


if __name__ == "__main__":
    main()
