"""Integration tests for configuration file changes.

Tests that configuration updates are properly loaded and applied.
"""

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import yaml

from kalendar.domain.models.enums import LayoutType, SourceType
from kalendar.infrastructure.storage.yaml_config_loader import YAMLConfigLoader


class TestConfigUpdates:
    """Test configuration file updates and reloading."""

    def test_load_and_save_config_roundtrip(self):
        """Config can be loaded, modified, saved, and reloaded."""
        # Arrange
        loader = YAMLConfigLoader()

        # Create temporary config file
        config_data = {
            "refresh_hour": 0,
            "timezone": "America/New_York",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test-source",
                    "name": "Test Calendar",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {
                "max_daily_events": 5,
                "layout": "horizontal",
            },
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name

        try:
            # Act - Load config
            config = loader.load_config(config_path)

            # Modify config
            config.refresh_hour = 8
            config.max_daily_events = 10

            # Save modified config
            loader.save_config(config, config_path)

            # Reload config
            reloaded_config = loader.load_config(config_path)

            # Assert - Changes persisted
            assert reloaded_config.refresh_hour == 8
            assert reloaded_config.max_daily_events == 10
            assert reloaded_config.timezone == "America/New_York"
            assert len(reloaded_config.calendar_sources) == 1

        finally:
            # Cleanup
            Path(config_path).unlink(missing_ok=True)

    def test_add_calendar_source_to_config(self):
        """New calendar sources can be added to configuration."""
        # Arrange
        loader = YAMLConfigLoader()

        config_data = {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "placeholder",
                    "name": "Placeholder",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {
                "max_daily_events": 5,
                "layout": "horizontal",
            },
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name

        try:
            # Act - Load config, remove placeholder, and add source
            config = loader.load_config(config_path)

            from kalendar.domain.models.source import CalendarSource

            # Remove placeholder and add new source
            config.calendar_sources = [
                CalendarSource(
                    id="new-source",
                    name="New Calendar",
                    source_type=SourceType.CALDAV,
                    calendar_id="https://caldav.example.com/calendar/",
                    enabled=True,
                )
            ]

            loader.save_config(config, config_path)

            # Reload
            reloaded_config = loader.load_config(config_path)

            # Assert - New source present
            assert len(reloaded_config.calendar_sources) == 1
            assert reloaded_config.calendar_sources[0].id == "new-source"
            assert reloaded_config.calendar_sources[0].source_type == SourceType.CALDAV

        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_disable_calendar_source_in_config(self):
        """Calendar sources can be disabled in configuration."""
        # Arrange
        loader = YAMLConfigLoader()

        config_data = {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "source-1",
                    "name": "Calendar 1",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                },
                {
                    "id": "source-2",
                    "name": "Calendar 2",
                    "source_type": "caldav",
                    "calendar_id": "https://example.com/cal",
                    "enabled": True,
                },
            ],
            "display": {
                "max_daily_events": 5,
                "layout": "horizontal",
            },
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name

        try:
            # Act - Load and disable one source
            config = loader.load_config(config_path)
            config.calendar_sources[1].enabled = False
            loader.save_config(config, config_path)

            # Reload
            reloaded_config = loader.load_config(config_path)

            # Assert - Only one source enabled
            enabled_sources = reloaded_config.get_enabled_sources()
            assert len(enabled_sources) == 1
            assert enabled_sources[0].id == "source-1"

        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_update_refresh_time_in_config(self):
        """Refresh hour can be updated in configuration."""
        # Arrange
        loader = YAMLConfigLoader()

        config_data = {
            "refresh_hour": 0,
            "timezone": "America/Los_Angeles",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test-source",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {
                "max_daily_events": 5,
                "layout": "horizontal",
            },
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name

        try:
            # Act - Update refresh hour
            config = loader.load_config(config_path)
            config.refresh_hour = 23
            loader.save_config(config, config_path)

            # Reload
            reloaded_config = loader.load_config(config_path)

            # Assert
            assert reloaded_config.refresh_hour == 23
            assert reloaded_config.timezone == "America/Los_Angeles"

        finally:
            Path(config_path).unlink(missing_ok=True)

    def test_change_display_layout_in_config(self):
        """Display layout can be changed in configuration."""
        # Arrange
        loader = YAMLConfigLoader()

        config_data = {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test-source",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {
                "max_daily_events": 5,
                "layout": "horizontal",
            },
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name

        try:
            # Act - Change layout
            config = loader.load_config(config_path)
            config.display_layout = LayoutType.VERTICAL
            loader.save_config(config, config_path)

            # Reload
            reloaded_config = loader.load_config(config_path)

            # Assert
            assert reloaded_config.display_layout == LayoutType.VERTICAL

        finally:
            Path(config_path).unlink(missing_ok=True)
