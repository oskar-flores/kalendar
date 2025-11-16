"""Unit tests for CalendarSource domain model."""

from datetime import datetime, timedelta, timezone

import pytest

from kalendar.domain.models.enums import SourceType, SyncStatus
from kalendar.domain.models.source import CalendarSource


class TestCalendarSource:
    """Test suite for CalendarSource model."""

    def test_create_google_calendar_source(self) -> None:
        """Should create a valid Google Calendar source."""
        source = CalendarSource(
            id="google-1",
            name="Family Calendar",
            source_type=SourceType.GOOGLE,
            calendar_id="primary",
            enabled=True,
        )

        assert source.id == "google-1"
        assert source.name == "Family Calendar"
        assert source.source_type == SourceType.GOOGLE
        assert source.calendar_id == "primary"
        assert source.enabled is True

    def test_create_caldav_source(self) -> None:
        """Should create a valid CalDAV source."""
        source = CalendarSource(
            id="caldav-1",
            name="iCloud Calendar",
            source_type=SourceType.CALDAV,
            calendar_id="https://caldav.icloud.com/123/calendars/456/",
            enabled=True,
        )

        assert source.source_type == SourceType.CALDAV
        assert source.calendar_id.startswith("https://")

    def test_is_stale_never_synced(self) -> None:
        """Source with no last_sync_time should be considered stale."""
        source = CalendarSource(
            id="src-1",
            name="Test Calendar",
            source_type=SourceType.GOOGLE,
            calendar_id="primary",
            enabled=True,
        )

        assert source.is_stale() is True

    def test_is_stale_recent_sync(self) -> None:
        """Recently synced source should not be stale."""
        source = CalendarSource(
            id="src-1",
            name="Test Calendar",
            source_type=SourceType.GOOGLE,
            calendar_id="primary",
            enabled=True,
            last_sync_time=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        assert source.is_stale(max_age_hours=24) is False

    def test_is_stale_old_sync(self) -> None:
        """Source with old sync should be stale."""
        source = CalendarSource(
            id="src-1",
            name="Test Calendar",
            source_type=SourceType.GOOGLE,
            calendar_id="primary",
            enabled=True,
            last_sync_time=datetime.now(timezone.utc) - timedelta(hours=25),
        )

        assert source.is_stale(max_age_hours=24) is True

    def test_is_stale_custom_max_age(self) -> None:
        """Should respect custom max_age_hours parameter."""
        source = CalendarSource(
            id="src-1",
            name="Test Calendar",
            source_type=SourceType.GOOGLE,
            calendar_id="primary",
            enabled=True,
            last_sync_time=datetime.now(timezone.utc) - timedelta(hours=2),
        )

        assert source.is_stale(max_age_hours=1) is True
        assert source.is_stale(max_age_hours=3) is False

    def test_mark_sync_success(self) -> None:
        """Should update sync status and timestamp on success."""
        source = CalendarSource(
            id="src-1",
            name="Test Calendar",
            source_type=SourceType.GOOGLE,
            calendar_id="primary",
            enabled=True,
        )

        sync_time = datetime.now(timezone.utc)
        source.mark_sync_success(sync_time)

        assert source.last_sync_time == sync_time
        assert source.last_sync_status == SyncStatus.SUCCESS

    def test_mark_sync_failed(self) -> None:
        """Should update sync status on failure."""
        source = CalendarSource(
            id="src-1",
            name="Test Calendar",
            source_type=SourceType.GOOGLE,
            calendar_id="primary",
            enabled=True,
        )

        source.mark_sync_failed()

        assert source.last_sync_status == SyncStatus.FAILED

    def test_disabled_source(self) -> None:
        """Should handle disabled sources."""
        source = CalendarSource(
            id="src-1",
            name="Disabled Calendar",
            source_type=SourceType.GOOGLE,
            calendar_id="primary",
            enabled=False,
        )

        assert source.enabled is False

    def test_source_with_color(self) -> None:
        """Should store optional color attribute."""
        source = CalendarSource(
            id="src-1",
            name="Work Calendar",
            source_type=SourceType.GOOGLE,
            calendar_id="work@company.com",
            enabled=True,
            color="#FF5733",
        )

        assert source.color == "#FF5733"

    def test_initial_sync_status(self) -> None:
        """New source should have NEVER_SYNCED status by default."""
        source = CalendarSource(
            id="src-1",
            name="New Calendar",
            source_type=SourceType.GOOGLE,
            calendar_id="primary",
            enabled=True,
        )

        assert source.last_sync_status == SyncStatus.NEVER_SYNCED
