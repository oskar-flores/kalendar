"""
Unit tests for RenderMonthlyViewUseCase.

Purpose: Test monthly calendar view rendering logic with mocks.
Following TDD - tests written FIRST.
"""

import pytest
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import Mock
from PIL import Image

from src.kalendar.domain.models.event import CalendarEvent
from src.kalendar.domain.models.view import MonthlyView, DailyView
from src.kalendar.domain.models.config import DisplayConfiguration
from src.kalendar.domain.models.enums import LayoutType, SourceType


class TestRenderMonthlyViewUseCase:
    """Test suite for RenderMonthlyViewUseCase."""

    @pytest.fixture
    def mock_renderer(self) -> Mock:
        """Create mock image renderer."""
        renderer = Mock()
        # Return a simple test image
        test_image = Image.new("RGB", (800, 480), color="white")
        renderer.render_template = Mock(return_value=test_image)
        renderer.set_template_directory = Mock()
        return renderer

    @pytest.fixture
    def mock_monthly_view_builder(self) -> Mock:
        """Create mock monthly view builder."""
        builder = Mock()
        # Create a simple mock MonthlyView
        mock_view = Mock(spec=MonthlyView)
        mock_view.year = 2025
        mock_view.month = 11
        mock_view.weeks = []  # Add weeks attribute
        mock_view.get_month_name = Mock(return_value="November")
        builder.build = Mock(return_value=mock_view)
        return builder

    @pytest.fixture
    def mock_daily_view_builder(self) -> Mock:
        """Create mock daily view builder."""
        builder = Mock()
        # Create a simple mock DailyView
        mock_view = Mock(spec=DailyView)
        mock_view.get_visible_events = Mock(return_value=[])
        mock_view.has_overflow = Mock(return_value=False)
        builder.build = Mock(return_value=mock_view)
        return builder

    @pytest.fixture
    def sample_events(self) -> list:
        """Create sample calendar events."""
        return [
            CalendarEvent(
                id="evt-1",
                calendar_source_id="source-1",
                title="Test Event",
                start_datetime=datetime.now(timezone.utc),
                end_datetime=datetime.now(timezone.utc) + timedelta(hours=1),
                is_all_day=False,
            )
        ]

    @pytest.fixture
    def mock_config(self) -> Mock:
        """Create mock display configuration."""
        config = Mock(spec=DisplayConfiguration)
        config.timezone = "UTC"
        config.week_start_day = 0
        config.max_daily_events = 5
        return config

    def test_render_monthly_view_returns_image(
        self,
        mock_renderer: Mock,
        mock_monthly_view_builder: Mock,
        mock_daily_view_builder: Mock,
        sample_events: list,
        mock_config: Mock,
    ) -> None:
        """RenderMonthlyViewUseCase should return a PIL Image."""
        from src.kalendar.application.usecases.render_monthly_view import (
            RenderMonthlyViewUseCase,
        )

        # Arrange
        use_case = RenderMonthlyViewUseCase(
            config=mock_config,
            renderer=mock_renderer,
            monthly_view_builder=mock_monthly_view_builder,
            daily_view_builder=mock_daily_view_builder,
        )

        # Act
        result = use_case.execute(
            events=sample_events, year=2025, month=11, today=date.today()
        )

        # Assert
        assert isinstance(result, Image.Image)
        assert result.size == (800, 480)

    def test_render_monthly_view_builds_monthly_view(
        self,
        mock_renderer: Mock,
        mock_monthly_view_builder: Mock,
        mock_daily_view_builder: Mock,
        sample_events: list,
        mock_config: Mock,
    ) -> None:
        """RenderMonthlyViewUseCase should use MonthlyViewBuilder."""
        from src.kalendar.application.usecases.render_monthly_view import (
            RenderMonthlyViewUseCase,
        )

        # Arrange
        use_case = RenderMonthlyViewUseCase(
            config=mock_config,
            renderer=mock_renderer,
            monthly_view_builder=mock_monthly_view_builder,
            daily_view_builder=mock_daily_view_builder,
        )

        # Act
        result = use_case.execute(
            events=sample_events, year=2025, month=11, today=date.today()
        )

        # Assert
        assert mock_monthly_view_builder.build.called

    def test_render_monthly_view_builds_daily_view(
        self,
        mock_renderer: Mock,
        mock_monthly_view_builder: Mock,
        mock_daily_view_builder: Mock,
        sample_events: list,
        mock_config: Mock,
    ) -> None:
        """RenderMonthlyViewUseCase should use DailyViewBuilder for today's events."""
        from src.kalendar.application.usecases.render_monthly_view import (
            RenderMonthlyViewUseCase,
        )

        # Arrange
        use_case = RenderMonthlyViewUseCase(
            config=mock_config,
            renderer=mock_renderer,
            monthly_view_builder=mock_monthly_view_builder,
            daily_view_builder=mock_daily_view_builder,
        )

        # Act
        result = use_case.execute(
            events=sample_events, year=2025, month=11, today=date.today()
        )

        # Assert
        assert mock_daily_view_builder.build.called

    def test_render_monthly_view_renders_template(
        self,
        mock_renderer: Mock,
        mock_monthly_view_builder: Mock,
        mock_daily_view_builder: Mock,
        sample_events: list,
        mock_config: Mock,
    ) -> None:
        """RenderMonthlyViewUseCase should render HTML template."""
        from src.kalendar.application.usecases.render_monthly_view import (
            RenderMonthlyViewUseCase,
        )

        # Arrange
        use_case = RenderMonthlyViewUseCase(
            config=mock_config,
            renderer=mock_renderer,
            monthly_view_builder=mock_monthly_view_builder,
            daily_view_builder=mock_daily_view_builder,
        )

        # Act
        result = use_case.execute(
            events=sample_events, year=2025, month=11, today=date.today()
        )

        # Assert
        assert mock_renderer.render_template.called
        call_args = mock_renderer.render_template.call_args

        # Check template name (keyword argument)
        assert call_args.kwargs["template_name"] == "calendar_view.html"

        # Check context has required keys
        context = call_args.kwargs["context"]
        assert "month_name" in context
        assert "year" in context
        assert "weeks" in context
        assert "daily_view" in context

    def test_render_monthly_view_uses_800x480_dimensions(
        self,
        mock_renderer: Mock,
        mock_monthly_view_builder: Mock,
        mock_daily_view_builder: Mock,
        sample_events: list,
        mock_config: Mock,
    ) -> None:
        """RenderMonthlyViewUseCase should use 800x480 for e-paper display."""
        from src.kalendar.application.usecases.render_monthly_view import (
            RenderMonthlyViewUseCase,
        )

        # Arrange
        use_case = RenderMonthlyViewUseCase(
            config=mock_config,
            renderer=mock_renderer,
            monthly_view_builder=mock_monthly_view_builder,
            daily_view_builder=mock_daily_view_builder,
        )

        # Act
        result = use_case.execute(
            events=sample_events, year=2025, month=11, today=date.today()
        )

        # Assert
        call_args = mock_renderer.render_template.call_args
        assert call_args.kwargs["width"] == 800
        assert call_args.kwargs["height"] == 480
    def test_monthly_view_builder_receives_config(
        self,
        mock_renderer: Mock,
        mock_monthly_view_builder: Mock,
        mock_daily_view_builder: Mock,
        sample_events: list,
        mock_config: Mock,
    ) -> None:
        """MonthlyViewBuilder.build() should receive config parameter, not today."""
        from src.kalendar.application.usecases.render_monthly_view import (
            RenderMonthlyViewUseCase,
        )

        # Arrange
        use_case = RenderMonthlyViewUseCase(
            renderer=mock_renderer,
            monthly_view_builder=mock_monthly_view_builder,
            daily_view_builder=mock_daily_view_builder,
            config=mock_config,
        )

        # Act
        today = date(2025, 11, 16)
        result = use_case.execute(
            events=sample_events,
            year=2025,
            month=11,
            today=today,
        )

        # Assert - monthly_view_builder.build should be called with config
        mock_monthly_view_builder.build.assert_called_once()
        call_args = mock_monthly_view_builder.build.call_args

        # Should receive: year, month, events, config
        assert call_args.kwargs["year"] == 2025
        assert call_args.kwargs["month"] == 11
        assert call_args.kwargs["events"] == sample_events
        assert call_args.kwargs["config"] == mock_config
        # Should NOT receive 'today' as a parameter
        assert "today" not in call_args.kwargs
