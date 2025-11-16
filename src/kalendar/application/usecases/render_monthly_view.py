"""
Render Monthly View Use Case.

Builds monthly calendar view and renders it to an image.
"""

from datetime import date, datetime
from typing import List, Optional
from pathlib import Path
import logging
from PIL import Image

from src.kalendar.domain.interfaces.IImageRenderer import IImageRenderer
from src.kalendar.domain.models.event import CalendarEvent
from src.kalendar.domain.services.monthly_view_builder import MonthlyViewBuilder
from src.kalendar.domain.services.daily_view_builder import DailyViewBuilder

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

    # Weekday names for header
    WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

    def __init__(
        self,
        renderer: IImageRenderer,
        monthly_view_builder: MonthlyViewBuilder,
        daily_view_builder: DailyViewBuilder,
        template_directory: Path | None = None,
    ) -> None:
        """
        Initialize RenderMonthlyViewUseCase.

        Args:
            renderer: Image renderer implementation
            monthly_view_builder: Builder for monthly calendar grid
            daily_view_builder: Builder for daily events view
            template_directory: Optional path to templates (defaults to package templates)
        """
        self._renderer = renderer
        self._monthly_view_builder = monthly_view_builder
        self._daily_view_builder = daily_view_builder

        # Set template directory
        if template_directory is None:
            # Default to package templates
            from src.kalendar.presentation import templates

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
            year=year, month=month, events=events, today=today
        )

        # Build daily view for today
        daily_view = self._daily_view_builder.build(
            target_date=today, events=events, max_visible=5  # FR-019: Max 5 events
        )

        # Identify current event if current_time provided
        current_event = None
        if current_time:
            current_event = daily_view.get_current_event(current_time)

        # Prepare template context
        context = {
            "month_name": monthly_view.get_month_name(),
            "year": year,
            "today": today,
            "weeks": monthly_view.weeks,
            "weekday_names": self.WEEKDAY_NAMES,
            "daily_view": daily_view,
            "current_event": current_event,
            "sync_timestamp": None,  # TODO: Add from sync metadata
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
