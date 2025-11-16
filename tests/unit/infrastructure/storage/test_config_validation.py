"""Unit tests for configuration validation.

Tests validation rules for DisplayConfiguration according to data-model.md.
"""

from tempfile import NamedTemporaryFile

import pytest
import yaml

from kalendar.infrastructure.storage.yaml_config_loader import YAMLConfigLoader


class TestConfigValidation:
    """Test configuration validation rules."""

    def test_validate_refresh_hour_in_range_0_to_23(self):
        """Refresh hour must be 0-23."""
        # Arrange
        loader = YAMLConfigLoader()

        valid_config = {
            "refresh_hour": 23,  # Valid
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        invalid_config = {
            "refresh_hour": 24,  # Invalid
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        # Act & Assert - Valid config loads successfully
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(valid_config, f)
            valid_path = f.name

        config = loader.load_config(valid_path)
        assert config.refresh_hour == 23

        # Act & Assert - Invalid config raises ValueError
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(invalid_config, f)
            invalid_path = f.name

        with pytest.raises(ValueError, match="refresh_hour must be between 0 and 23"):
            loader.load_config(invalid_path)

    def test_validate_refresh_hour_negative(self):
        """Refresh hour must not be negative."""
        # Arrange
        loader = YAMLConfigLoader()

        invalid_config = {
            "refresh_hour": -1,  # Invalid
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(invalid_config, f)
            config_path = f.name

        # Act & Assert
        with pytest.raises(ValueError, match="refresh_hour must be between 0 and 23"):
            loader.load_config(config_path)

    def test_validate_timezone_is_valid_iana_string(self):
        """Timezone must be a valid IANA timezone string."""
        # Arrange
        loader = YAMLConfigLoader()

        valid_timezones = [
            "UTC",
            "America/New_York",
            "Europe/London",
            "Asia/Tokyo",
            "Australia/Sydney",
        ]

        invalid_timezones = [
            "Invalid/Timezone",
            "NotReal/City",
            "BadTimezone",
            "",
        ]

        base_config = {
            "refresh_hour": 0,
            "timezone": "UTC",  # Will be replaced
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        # Act & Assert - Valid timezones
        for tz in valid_timezones:
            config = base_config.copy()
            config["timezone"] = tz

            with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                yaml.safe_dump(config, f)
                config_path = f.name

            loaded_config = loader.load_config(config_path)
            assert loaded_config.timezone == tz

        # Act & Assert - Invalid timezones
        for tz in invalid_timezones:
            config = base_config.copy()
            config["timezone"] = tz

            with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
                yaml.safe_dump(config, f)
                config_path = f.name

            with pytest.raises(
                ValueError, match="timezone must be a valid IANA timezone"
            ):
                loader.load_config(config_path)

    def test_validate_at_least_one_enabled_source(self):
        """At least one calendar source must be enabled."""
        # Arrange
        loader = YAMLConfigLoader()

        # Valid - At least one enabled
        valid_config = {
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
                    "enabled": False,
                },
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        # Invalid - No enabled sources
        invalid_config = {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "source-1",
                    "name": "Calendar 1",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": False,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        # Invalid - Empty sources list
        empty_sources_config = {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        # Act & Assert - Valid config
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(valid_config, f)
            valid_path = f.name

        config = loader.load_config(valid_path)
        assert len(config.get_enabled_sources()) == 1

        # Act & Assert - Invalid config (all disabled)
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(invalid_config, f)
            invalid_path = f.name

        with pytest.raises(ValueError, match="At least one calendar source must be enabled"):
            loader.load_config(invalid_path)

        # Act & Assert - Invalid config (empty list)
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(empty_sources_config, f)
            empty_path = f.name

        with pytest.raises(ValueError, match="At least one calendar source must be enabled"):
            loader.load_config(empty_path)

    def test_validate_week_start_day_0_to_6(self):
        """Week start day must be 0-6."""
        # Arrange
        loader = YAMLConfigLoader()

        valid_config = {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 6,  # Valid (Sunday)
            "calendar_sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        invalid_config = {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 7,  # Invalid
            "calendar_sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        # Act & Assert - Valid
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(valid_config, f)
            valid_path = f.name

        config = loader.load_config(valid_path)
        assert config.week_start_day == 6

        # Act & Assert - Invalid
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(invalid_config, f)
            invalid_path = f.name

        with pytest.raises(ValueError, match="week_start_day must be between 0 and 6"):
            loader.load_config(invalid_path)

    def test_validate_max_daily_events_positive(self):
        """Max daily events must be greater than 0."""
        # Arrange
        loader = YAMLConfigLoader()

        valid_config = {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 1, "layout": "horizontal"},
        }

        invalid_config = {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 0, "layout": "horizontal"},
        }

        # Act & Assert - Valid
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(valid_config, f)
            valid_path = f.name

        config = loader.load_config(valid_path)
        assert config.max_daily_events == 1

        # Act & Assert - Invalid
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(invalid_config, f)
            invalid_path = f.name

        with pytest.raises(ValueError, match="max_daily_events must be greater than 0"):
            loader.load_config(invalid_path)

    def test_validate_config_method_returns_true_for_valid(self):
        """validate_config method returns True for valid configuration."""
        # Arrange
        loader = YAMLConfigLoader()

        valid_config = {
            "refresh_hour": 12,
            "timezone": "America/Chicago",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "test",
                    "name": "Test",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(valid_config, f)
            config_path = f.name

        # Act
        is_valid = loader.validate_config(config_path)

        # Assert
        assert is_valid is True

    def test_validate_config_method_returns_false_for_invalid(self):
        """validate_config method returns False for invalid configuration."""
        # Arrange
        loader = YAMLConfigLoader()

        invalid_config = {
            "refresh_hour": 99,  # Invalid
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [],  # Invalid - no sources
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(invalid_config, f)
            config_path = f.name

        # Act
        is_valid = loader.validate_config(config_path)

        # Assert
        assert is_valid is False
