"""Unit tests for AppFactory dependency injection."""

import tempfile
from pathlib import Path

import pytest
import yaml

from kalendar.cli.app_factory import Application
from kalendar.cli.dependencies import Dependencies


class TestApplicationRenderMonthlyView:
    """Test Application creates RenderMonthlyViewUseCase correctly."""

    @pytest.fixture
    def test_config(self):
        """Create minimal valid configuration."""
        return {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test-cal",
                    "name": "Test Calendar",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

    @pytest.fixture
    def temp_config_file(self, test_config):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(test_config, f)
            return f.name

    @pytest.fixture
    def app_factory(self, temp_config_file):
        """Create Application with test configuration."""
        deps = Dependencies(config_path=temp_config_file, use_simulator=True)
        return Application(deps)

    def test_create_render_monthly_view_use_case_returns_use_case(self, app_factory):
        """render_monthly_view property should return initialized use case."""
        use_case = app_factory.render_monthly_view

        assert use_case is not None
        from kalendar.application.usecases.render_monthly_view import RenderMonthlyViewUseCase
        assert isinstance(use_case, RenderMonthlyViewUseCase)

    def test_render_monthly_view_use_case_has_renderer(self, app_factory):
        """RenderMonthlyViewUseCase should have renderer dependency."""
        use_case = app_factory.render_monthly_view

        assert hasattr(use_case, '_renderer')
        assert use_case._renderer is not None

    def test_render_monthly_view_use_case_has_monthly_view_builder(self, app_factory):
        """RenderMonthlyViewUseCase should have monthly_view_builder dependency."""
        use_case = app_factory.render_monthly_view

        assert hasattr(use_case, '_monthly_view_builder')
        assert use_case._monthly_view_builder is not None

    def test_render_monthly_view_use_case_has_daily_view_builder(self, app_factory):
        """RenderMonthlyViewUseCase should have daily_view_builder dependency."""
        use_case = app_factory.render_monthly_view

        assert hasattr(use_case, '_daily_view_builder')
        assert use_case._daily_view_builder is not None

    def test_app_factory_has_daily_view_builder_property(self, app_factory):
        """Application should have daily_view_builder property."""
        assert hasattr(app_factory, 'daily_view_builder')

        daily_view_builder = app_factory.daily_view_builder

        assert daily_view_builder is not None
        from kalendar.domain.services.daily_view_builder import DailyViewBuilder
        assert isinstance(daily_view_builder, DailyViewBuilder)

    def test_daily_view_builder_is_created(self, app_factory):
        """DailyViewBuilder should be created successfully."""
        daily_view_builder = app_factory.daily_view_builder

        # Builder should be created (no timezone in DailyViewBuilder)
        assert daily_view_builder is not None

    def test_multiple_calls_return_same_instance(self, app_factory):
        """Multiple calls should return the same use case instance (singleton)."""
        use_case1 = app_factory.render_monthly_view
        use_case2 = app_factory.render_monthly_view

        assert use_case1 is use_case2
