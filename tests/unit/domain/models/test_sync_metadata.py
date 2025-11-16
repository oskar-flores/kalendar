"""Unit tests for SyncMetadata domain model."""

from datetime import datetime, timedelta, timezone

import pytest

from kalendar.domain.models.enums import SyncStatus
from kalendar.domain.models.sync_metadata import SyncMetadata, SyncResult


class TestSyncResult:
    """Test suite for SyncResult model."""

    def test_create_successful_sync_result(self) -> None:
        """Should create a successful sync result."""
        result = SyncResult(
            source_id="src-1",
            status=SyncStatus.SUCCESS,
            timestamp=datetime.now(timezone.utc),
            events_fetched=42,
            duration_seconds=5.3,
        )

        assert result.source_id == "src-1"
        assert result.status == SyncStatus.SUCCESS
        assert result.events_fetched == 42
        assert result.duration_seconds == 5.3
        assert result.error_message is None

    def test_create_failed_sync_result(self) -> None:
        """Should create a failed sync result with error message."""
        result = SyncResult(
            source_id="src-2",
            status=SyncStatus.FAILED,
            timestamp=datetime.now(timezone.utc),
            events_fetched=0,
            error_message="Connection timeout",
            duration_seconds=30.0,
        )

        assert result.status == SyncStatus.FAILED
        assert result.error_message == "Connection timeout"
        assert result.events_fetched == 0


class TestSyncMetadata:
    """Test suite for SyncMetadata model."""

    def test_create_empty_sync_metadata(self) -> None:
        """Should create empty sync metadata."""
        metadata = SyncMetadata(
            sync_results={},
            cached_events_count=0,
        )

        assert len(metadata.sync_results) == 0
        assert metadata.cached_events_count == 0
        assert metadata.last_successful_sync is None

    def test_is_cache_valid_no_expiry(self) -> None:
        """Cache without expiry should be invalid."""
        metadata = SyncMetadata(
            sync_results={},
            cached_events_count=10,
        )

        assert metadata.is_cache_valid() is False

    def test_is_cache_valid_future_expiry(self) -> None:
        """Cache with future expiry should be valid."""
        metadata = SyncMetadata(
            sync_results={},
            cached_events_count=10,
            cache_valid_until=datetime.now(timezone.utc) + timedelta(hours=12),
        )

        assert metadata.is_cache_valid() is True

    def test_is_cache_valid_past_expiry(self) -> None:
        """Cache with past expiry should be invalid."""
        metadata = SyncMetadata(
            sync_results={},
            cached_events_count=10,
            cache_valid_until=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        assert metadata.is_cache_valid() is False

    def test_get_failed_sources_none_failed(self) -> None:
        """Should return empty list when all sources succeeded."""
        now = datetime.now(timezone.utc)
        metadata = SyncMetadata(
            sync_results={
                "src-1": SyncResult(
                    source_id="src-1",
                    status=SyncStatus.SUCCESS,
                    timestamp=now,
                    events_fetched=10,
                ),
                "src-2": SyncResult(
                    source_id="src-2",
                    status=SyncStatus.SUCCESS,
                    timestamp=now,
                    events_fetched=15,
                ),
            },
            cached_events_count=25,
        )

        failed = metadata.get_failed_sources()
        assert len(failed) == 0

    def test_get_failed_sources_some_failed(self) -> None:
        """Should return list of failed source IDs."""
        now = datetime.now(timezone.utc)
        metadata = SyncMetadata(
            sync_results={
                "src-1": SyncResult(
                    source_id="src-1",
                    status=SyncStatus.SUCCESS,
                    timestamp=now,
                    events_fetched=10,
                ),
                "src-2": SyncResult(
                    source_id="src-2",
                    status=SyncStatus.FAILED,
                    timestamp=now,
                    events_fetched=0,
                    error_message="Network error",
                ),
                "src-3": SyncResult(
                    source_id="src-3",
                    status=SyncStatus.FAILED,
                    timestamp=now,
                    events_fetched=0,
                    error_message="Auth failed",
                ),
            },
            cached_events_count=10,
        )

        failed = metadata.get_failed_sources()
        assert len(failed) == 2
        assert "src-2" in failed
        assert "src-3" in failed

    def test_get_staleness_hours_never_synced(self) -> None:
        """Should return infinity for never-synced metadata."""
        metadata = SyncMetadata(
            sync_results={},
            cached_events_count=0,
        )

        staleness = metadata.get_staleness_hours()
        assert staleness == float("inf")

    def test_get_staleness_hours_recent_sync(self) -> None:
        """Should calculate staleness hours since last sync."""
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        metadata = SyncMetadata(
            last_successful_sync=one_hour_ago,
            sync_results={},
            cached_events_count=10,
        )

        staleness = metadata.get_staleness_hours()
        assert 0.9 <= staleness <= 1.1  # Allow small time variance

    def test_get_staleness_hours_old_sync(self) -> None:
        """Should calculate staleness for old sync."""
        two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)
        metadata = SyncMetadata(
            last_successful_sync=two_days_ago,
            sync_results={},
            cached_events_count=10,
        )

        staleness = metadata.get_staleness_hours()
        assert 47 <= staleness <= 49  # ~48 hours with variance

    def test_sync_metadata_with_all_fields(self) -> None:
        """Should create complete sync metadata with all fields."""
        now = datetime.now(timezone.utc)
        metadata = SyncMetadata(
            last_successful_sync=now,
            sync_results={
                "src-1": SyncResult(
                    source_id="src-1",
                    status=SyncStatus.SUCCESS,
                    timestamp=now,
                    events_fetched=25,
                    duration_seconds=3.5,
                )
            },
            cached_events_count=25,
            cache_valid_until=now + timedelta(hours=24),
        )

        assert metadata.last_successful_sync == now
        assert metadata.cached_events_count == 25
        assert metadata.is_cache_valid() is True
        assert len(metadata.get_failed_sources()) == 0
        assert metadata.get_staleness_hours() < 0.1  # Very recent
