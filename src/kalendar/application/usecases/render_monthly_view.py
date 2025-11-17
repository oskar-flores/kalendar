"""
Render Monthly View Use Case.

Builds monthly calendar view and renders it to an image.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional
from pathlib import Path
import logging
from PIL import Image

from kalendar.domain.interfaces.IImageRenderer import IImageRenderer
from kalendar.domain.models.config import DisplayConfiguration
from kalendar.domain.models.event import CalendarEvent
from kalendar.domain.models.view import Day, MonthlyView
from kalendar.domain.services.monthly_view_builder import MonthlyViewBuilder
from kalendar.domain.services.daily_view_builder import DailyViewBuilder

logger = logging.getLogger(__name__)


class RenderMonthlyViewUseCase:
    """
    Use case: Render monthly calendar view to image.

    Responsibilities:
        - Build MonthlyView from events using MonthlyViewBuilder
        - Build DailyView for today's events using DailyViewBuilder
        - Prepare template context with view data
        - Render HTML template to image using IImageRenderer
        - Return 800x480 RGB image for e-paper display

    Output:
        PIL Image in RGB mode (800x480 pixels)
        Ready for post-processing to separate black/red layers
    """

    # E-paper display dimensions
    WIDTH = 800
    HEIGHT = 480

    # Weekday names for header (Spanish, Sunday-first base array)
    WEEKDAY_NAMES_BASE = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

    # Spanish month names
    MONTH_NAMES_ES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                      "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    # Spanish weekday abbreviations for week preview
    WEEKDAY_ABBREV_ES = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]

    def __init__(
        self,
        renderer: IImageRenderer,
        monthly_view_builder: MonthlyViewBuilder,
        daily_view_builder: DailyViewBuilder,
        config: DisplayConfiguration,
        template_directory: Path | None = None,
    ) -> None:
        """
        Initialize RenderMonthlyViewUseCase.

        Args:
            renderer: Image renderer implementation
            monthly_view_builder: Builder for monthly calendar grid
            daily_view_builder: Builder for daily events view
            config: Display configuration
            template_directory: Optional path to templates (defaults to package templates)
        """
        self._renderer = renderer
        self._monthly_view_builder = monthly_view_builder
        self._daily_view_builder = daily_view_builder
        self._config = config

        # Set template directory
        if template_directory is None:
            # Default to package templates
            from kalendar.presentation import templates

            template_directory = Path(templates.__file__).parent

        self._renderer.set_template_directory(template_directory)

        logger.info(f"RenderMonthlyViewUseCase initialized with templates from {template_directory}")

    def execute(
        self,
        events: List[CalendarEvent],
        year: int,
        month: int,
        today: date,
        current_time: Optional[datetime] = None
    ) -> Image.Image:
        """
        Render monthly calendar view to image.

        Args:
            events: List of calendar events to display
            year: Year to display
            month: Month to display (1-12)
            today: Current date for highlighting
            current_time: Optional current time for identifying in-progress event

        Returns:
            PIL Image in RGB mode (800x480)
        """
        logger.info(f"Rendering monthly view for {year}-{month:02d} with {len(events)} events")

        # Build monthly view
        monthly_view = self._monthly_view_builder.build(
            year=year, month=month, events=events, config=self._config
        )

        # Build daily view for today
        daily_view = self._daily_view_builder.build(
            target_date=today, events=events, max_visible=5  # FR-019: Max 5 events
        )

        # Identify current event if current_time provided
        current_event = None
        if current_time:
            current_event = daily_view.get_current_event(current_time)

        # Build upcoming days view (today + next 6 days for week preview)
        upcoming_days = self._build_upcoming_days(today, events, monthly_view)

        # Rotate weekday names based on week_start_day configuration
        # week_start_day: 0=Monday, 1=Tuesday, ..., 6=Sunday
        weekday_names = self._get_rotated_weekday_names(self._config.week_start_day)

        # Spanish translations
        spanish_labels = {
            "today_and_upcoming": "HOY Y PRÓXIMOS",
            "today": "HOY",
            "this_week": "ESTA SEMANA",
            "all_day": "Todo el día",
            "synced": "Sincronizado:",
            "more": "más",
        }

        # Get Spanish month and weekday names
        month_name_es = self.MONTH_NAMES_ES[month - 1]
        weekday_full_names_es = self.WEEKDAY_NAMES_BASE
        weekday_abbrev_es = self.WEEKDAY_ABBREV_ES

        # Prepare template context
        context = {
            "month_name": month_name_es,
            "year": year,
            "today": today,
            "weeks": monthly_view.weeks,
            "weekday_names": weekday_names,
            "weekday_full_names": weekday_full_names_es,
            "weekday_abbrev": weekday_abbrev_es,
            "daily_view": daily_view,
            "current_event": current_event,
            "upcoming_days": upcoming_days,
            "sync_timestamp": None,  # TODO: Add from sync metadata
            "labels": spanish_labels,
        }

        # Render template to image
        image = self._renderer.render_template(
            template_name="calendar_view.html",
            context=context,
            width=self.WIDTH,
            height=self.HEIGHT,
        )

        logger.info(
            f"Rendered {image.width}x{image.height} image in {image.mode} mode"
        )

        return image

    def _build_upcoming_days(
        self, start_date: date, events: List[CalendarEvent], monthly_view: MonthlyView
    ) -> List[Day]:
        """
        Build list of upcoming days with their events.

        Args:
            start_date: Starting date (typically today)
            events: All calendar events
            monthly_view: MonthlyView to extract event mappings from

        Returns:
            List of Day objects for the next 7 days (today + 6 more)
        """
        upcoming_days = []
        events_by_date = monthly_view.events_by_date

        for i in range(7):
            current_date = start_date + timedelta(days=i)
            is_today_flag = current_date == start_date
            day_events = events_by_date.get(current_date, [])

            day = Day(
                date=current_date,
                is_current_month=current_date.month == monthly_view.month,
                is_today=is_today_flag,
                has_events=len(day_events) > 0,
                event_count=len(day_events),
                events=day_events,
            )
            upcoming_days.append(day)

        return upcoming_days

    def _get_rotated_weekday_names(self, week_start_day: int) -> List[str]:
        """
        Rotate weekday names based on week_start_day configuration.

        Args:
            week_start_day: Week start day (0=Monday, 1=Tuesday, ..., 6=Sunday)

        Returns:
            List of weekday names rotated to match configuration
        """
        # The base array is Sunday-first: ["Domingo", "Lunes", ..., "Sábado"]
        # We need to rotate it based on week_start_day
        # week_start_day=0 (Monday) -> rotate by 1: ["Lunes", "Martes", ..., "Domingo"]
        # week_start_day=6 (Sunday) -> no rotation: ["Domingo", "Lunes", ..., "Sábado"]

        # Calculate rotation: convert week_start_day (0=Mon) to Sunday-based index
        # Monday(0) is index 1 in Sunday-first array, so rotation = (week_start_day + 1) % 7
        rotation = (week_start_day + 1) % 7

        # Rotate the array
        return self.WEEKDAY_NAMES_BASE[rotation:] + self.WEEKDAY_NAMES_BASE[:rotation]
