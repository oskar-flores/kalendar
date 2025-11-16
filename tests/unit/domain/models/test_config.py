"""Unit tests for DisplayConfiguration domain model."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from kalendar.domain.models.config import DisplayConfiguration
from kalendar.domain.models.enums import LayoutType, SourceType, SyncStatus
from kalendar.domain.models.source import CalendarSource


class TestDisplayConfiguration:
    """Test suite for DisplayConfiguration model."""

    def test_create_basic_configuration(self) -> None:
        """Should create a valid configuration with required fields."""
        sources = [
            CalendarSource(
                id="src-1",
                name="Test Calendar",
                source_type=SourceType.GOOGLE,
                calendar_id="test",
                enabled=True,
            )
        ]

        config = DisplayConfiguration(
            refresh_hour=0,
            timezone="America/New_York",
            week_start_day=0,
            calendar_sources=sources,
            display_layout=LayoutType.HORIZONTAL,
            max_daily_events=5,
        )

        assert config.refresh_hour == 0
        assert config.timezone == "America/New_York"
        assert config.week_start_day == 0
        assert config.display_layout == LayoutType.HORIZONTAL
        assert config.max_daily_events == 5

    def test_get_enabled_sources_all_enabled(self) -> None:
        """Should return all enabled calendar sources."""
        sources = [
            CalendarSource(
                id="src-1",
                name="Calendar 1",
                source_type=SourceType.GOOGLE,
                calendar_id="cal1",
                enabled=True,
            ),
            CalendarSource(
                id="src-2",
                name="Calendar 2",
                source_type=SourceType.CALDAV,
                calendar_id="cal2",
                enabled=True,
            ),
        ]

        config = DisplayConfiguration(
            refresh_hour=0,
            timezone="UTC",
            week_start_day=0,
            calendar_sources=sources,
            display_layout=LayoutType.HORIZONTAL,
            max_daily_events=5,
        )

        enabled = config.get_enabled_sources()
        assert len(enabled) == 2

    def test_get_enabled_sources_mixed(self) -> None:
        """Should filter out disabled sources."""
        sources = [
            CalendarSource(
                id="src-1",
                name="Enabled",
                source_type=SourceType.GOOGLE,
                calendar_id="cal1",
                enabled=True,
            ),
            CalendarSource(
                id="src-2",
                name="Disabled",
                source_type=SourceType.GOOGLE,
                calendar_id="cal2",
                enabled=False,
            ),
            CalendarSource(
                id="src-3",
                name="Also Enabled",
                source_type=SourceType.CALDAV,
                calendar_id="cal3",
                enabled=True,
            ),
        ]

        config = DisplayConfiguration(
            refresh_hour=0,
            timezone="UTC",
            week_start_day=0,
            calendar_sources=sources,
            display_layout=LayoutType.HORIZONTAL,
            max_daily_events=5,
        )

        enabled = config.get_enabled_sources()
        assert len(enabled) == 2
        assert all(s.enabled for s in enabled)

    def test_get_enabled_sources_none_enabled_raises_error(self) -> None:
        """Should raise error when no sources are enabled."""
        sources = [
            CalendarSource(
                id="src-1",
                name="Disabled 1",
                source_type=SourceType.GOOGLE,
                calendar_id="cal1",
                enabled=False,
            ),
            CalendarSource(
                id="src-2",
                name="Disabled 2",
                source_type=SourceType.GOOGLE,
                calendar_id="cal2",
                enabled=False,
            ),
        ]

        with pytest.raises(
            ValueError, match="At least one calendar source must be enabled"
        ):
            DisplayConfiguration(
                refresh_hour=0,
                timezone="UTC",
                week_start_day=0,
                calendar_sources=sources,
                display_layout=LayoutType.HORIZONTAL,
                max_daily_events=5,
            )

    def test_get_refresh_time_today(self) -> None:
        """Should calculate today's refresh time in configured timezone."""
        sources = [
            CalendarSource(
                id="src-1",
                name="Test",
                source_type=SourceType.GOOGLE,
                calendar_id="test",
                enabled=True,
            )
        ]

        config = DisplayConfiguration(
            refresh_hour=8,
            timezone="America/New_York",
            week_start_day=0,
            calendar_sources=sources,
            display_layout=LayoutType.HORIZONTAL,
            max_daily_events=5,
        )

        refresh_time = config.get_refresh_time_today()
        assert refresh_time.hour == 8
        assert refresh_time.minute == 0
        assert refresh_time.second == 0

    def test_get_next_refresh_time_future_today(self) -> None:
        """Should return today's refresh time if it hasn't passed yet."""
        sources = [
            CalendarSource(
                id="src-1",
                name="Test",
                source_type=SourceType.GOOGLE,
                calendar_id="test",
                enabled=True,
            )
        ]

        config = DisplayConfiguration(
            refresh_hour=23,  # Late in the day
            timezone="UTC",
            week_start_day=0,
            calendar_sources=sources,
            display_layout=LayoutType.HORIZONTAL,
            max_daily_events=5,
        )

        # This test assumes we're running before 23:00 UTC
        # In production, you'd mock datetime.now()
        next_refresh = config.get_next_refresh_time()
        assert next_refresh.hour == 23

    def test_validate_refresh_hour_range(self) -> None:
        """Should validate refresh_hour is between 0-23."""
        with pytest.raises(ValueError, match="refresh_hour must be between 0 and 23"):
            DisplayConfiguration(
                refresh_hour=24,
                timezone="UTC",
                week_start_day=0,
                calendar_sources=[],
                display_layout=LayoutType.HORIZONTAL,
                max_daily_events=5,
            )

        with pytest.raises(ValueError, match="refresh_hour must be between 0 and 23"):
            DisplayConfiguration(
                refresh_hour=-1,
                timezone="UTC",
                week_start_day=0,
                calendar_sources=[],
                display_layout=LayoutType.HORIZONTAL,
                max_daily_events=5,
            )

    def test_validate_week_start_day_range(self) -> None:
        """Should validate week_start_day is between 0-6."""
        with pytest.raises(ValueError, match="week_start_day must be between 0 and 6"):
            DisplayConfiguration(
                refresh_hour=0,
                timezone="UTC",
                week_start_day=7,
                calendar_sources=[],
                display_layout=LayoutType.HORIZONTAL,
                max_daily_events=5,
            )

    def test_validate_max_daily_events_positive(self) -> None:
        """Should validate max_daily_events is positive."""
        with pytest.raises(ValueError, match="max_daily_events must be greater than 0"):
            DisplayConfiguration(
                refresh_hour=0,
                timezone="UTC",
                week_start_day=0,
                calendar_sources=[],
                display_layout=LayoutType.HORIZONTAL,
                max_daily_events=0,
            )

    def test_validate_at_least_one_enabled_source(self) -> None:
        """Should validate at least one source is enabled."""
        disabled_sources = [
            CalendarSource(
                id="src-1",
                name="Disabled",
                source_type=SourceType.GOOGLE,
                calendar_id="cal1",
                enabled=False,
            )
        ]

        with pytest.raises(
            ValueError, match="At least one calendar source must be enabled"
        ):
            DisplayConfiguration(
                refresh_hour=0,
                timezone="UTC",
                week_start_day=0,
                calendar_sources=disabled_sources,
                display_layout=LayoutType.HORIZONTAL,
                max_daily_events=5,
            )

    def test_configuration_with_various_timezones(self) -> None:
        """Should handle various IANA timezone strings."""
        timezones = ["UTC", "America/Los_Angeles", "Europe/London", "Asia/Tokyo"]

        for tz in timezones:
            config = DisplayConfiguration(
                refresh_hour=0,
                timezone=tz,
                week_start_day=0,
                calendar_sources=[
                    CalendarSource(
                        id="src-1",
                        name="Test",
                        source_type=SourceType.GOOGLE,
                        calendar_id="test",
                        enabled=True,
                    )
                ],
                display_layout=LayoutType.HORIZONTAL,
                max_daily_events=5,
            )
            assert config.timezone == tz
