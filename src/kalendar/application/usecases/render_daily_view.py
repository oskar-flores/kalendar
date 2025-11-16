"""RenderDailyViewUseCase - Builds DailyView for template rendering.

This use case orchestrates building a DailyView from calendar events,
identifying the currently in-progress event, and preparing context for
the HTML template.
"""

from datetime import date, datetime
from typing import Optional, Any

from kalendar.domain.models.event import CalendarEvent
from kalendar.domain.models.view import DailyView
from kalendar.domain.services.daily_view_builder import DailyViewBuilder


class RenderDailyViewUseCase:
    """Use case for rendering today's events section.

    Responsibilities:
    - Build DailyView from events for a specific date
    - Identify currently in-progress event
    - Prepare template context with daily view data
    - Enforce max visible events limit (FR-019)
    """

    def __init__(self, daily_view_builder: DailyViewBuilder) -> None:
        """Initialize use case with dependencies.

        Args:
            daily_view_builder: Service to build DailyView from events
        """
        self._daily_view_builder = daily_view_builder

    def execute(
        self,
        target_date: date,
        events: list[CalendarEvent],
        max_visible_events: int,
        reference_time: Optional[datetime] = None,
    ) -> DailyView:
        """Build DailyView for the target date.

        Args:
            target_date: Date to show events for (usually today)
            events: All calendar events (will be filtered for target_date)
            max_visible_events: Maximum events to display (5 per FR-019)
            reference_time: Optional time to identify current event

        Returns:
            DailyView ready for template rendering
        """
        # Build daily view using domain service
        daily_view = self._daily_view_builder.build(
            target_date=target_date,
            events=events,
            max_visible=max_visible_events,
        )

        return daily_view

    def get_template_context(
        self,
        daily_view: DailyView,
        reference_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Prepare template context for rendering.

        Args:
            daily_view: DailyView to render
            reference_time: Optional time to identify current event

        Returns:
            Dictionary with template context variables
        """
        current_event = None
        if reference_time:
            current_event = daily_view.get_current_event(reference_time)

        return {
            "daily_view": daily_view,
            "current_event": current_event,
        }
