"""Application factory for creating use cases with dependencies.

This module creates application use cases with their required dependencies
wired in, following Clean Architecture principles.
"""

from kalendar.application.usecases.render_monthly_view import RenderMonthlyViewUseCase
from kalendar.application.usecases.sync_calendars import SyncCalendarsUseCase
from kalendar.application.usecases.update_display import UpdateDisplayUseCase
from kalendar.cli.dependencies import Dependencies
from kalendar.domain.services.event_aggregator import EventAggregator
from kalendar.domain.services.monthly_view_builder import MonthlyViewBuilder


class Application:
    """Application facade providing access to all use cases.

    This class creates and configures use cases with their dependencies,
    making them easy to use from CLI commands.
    """

    def __init__(self, dependencies: Dependencies):
        """Initialize application with dependencies.

        Args:
            dependencies: Dependency injection container
        """
        self.deps = dependencies

        # Domain services
        self._event_aggregator: EventAggregator | None = None
        self._monthly_view_builder: MonthlyViewBuilder | None = None

        # Use cases
        self._sync_calendars_use_case: SyncCalendarsUseCase | None = None
        self._render_monthly_view_use_case: RenderMonthlyViewUseCase | None = None
        self._update_display_use_case: UpdateDisplayUseCase | None = None

    @property
    def event_aggregator(self) -> EventAggregator:
        """Get event aggregator service."""
        if self._event_aggregator is None:
            self._event_aggregator = EventAggregator()
        return self._event_aggregator

    @property
    def monthly_view_builder(self) -> MonthlyViewBuilder:
        """Get monthly view builder service."""
        if self._monthly_view_builder is None:
            self._monthly_view_builder = MonthlyViewBuilder()
        return self._monthly_view_builder

    @property
    def sync_calendars(self) -> SyncCalendarsUseCase:
        """Get sync calendars use case.

        Returns:
            Use case for syncing calendar events from all sources
        """
        if self._sync_calendars_use_case is None:
            self._sync_calendars_use_case = SyncCalendarsUseCase(
                config=self.deps.config,
                cache=self.deps.cache,
                event_aggregator=self.event_aggregator,
                dependencies=self.deps,
            )
        return self._sync_calendars_use_case

    @property
    def render_monthly_view(self) -> RenderMonthlyViewUseCase:
        """Get render monthly view use case.

        Returns:
            Use case for rendering monthly calendar view to image
        """
        if self._render_monthly_view_use_case is None:
            self._render_monthly_view_use_case = RenderMonthlyViewUseCase(
                renderer=self.deps.renderer,
                monthly_view_builder=self.monthly_view_builder,
            )
        return self._render_monthly_view_use_case

    @property
    def update_display(self) -> UpdateDisplayUseCase:
        """Get update display use case.

        Returns:
            Use case for updating e-paper display with image
        """
        if self._update_display_use_case is None:
            self._update_display_use_case = UpdateDisplayUseCase(
                display_driver=self.deps.display_driver
            )
        return self._update_display_use_case


def create_application(
    config_path: str | None = None,
    use_simulator: bool = False,
    cache_dir: str | None = None,
) -> Application:
    """Create application with dependencies.

    This is the main factory function for creating a configured application.

    Args:
        config_path: Path to configuration file
        use_simulator: Use simulator display instead of hardware
        cache_dir: Cache directory path

    Returns:
        Configured application instance
    """
    dependencies = Dependencies(
        config_path=config_path,
        use_simulator=use_simulator,
        cache_dir=cache_dir,
    )

    return Application(dependencies=dependencies)
