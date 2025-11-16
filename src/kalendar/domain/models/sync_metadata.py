"""SyncMetadata domain model."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from kalendar.domain.models.enums import SyncStatus


@dataclass
class SyncResult:
    """Result of syncing a single calendar source.

    Attributes:
        source_id: ID of the calendar source
        status: Sync status (SUCCESS, FAILED, etc.)
        timestamp: When the sync was attempted
        events_fetched: Number of events retrieved
        error_message: Error details if sync failed
        duration_seconds: How long the sync took
    """

    source_id: str
    status: SyncStatus
    timestamp: datetime
    events_fetched: int
    error_message: Optional[str] = None
    duration_seconds: float = 0.0


@dataclass
class SyncMetadata:
    """Represents synchronization state and cache information.

    Attributes:
        last_successful_sync: Timestamp of last successful sync across all sources
        sync_results: Map of source_id to sync result
        cached_events_count: Total number of events in cache
        cache_valid_until: When cached data expires
    """

    sync_results: dict[str, SyncResult]
    cached_events_count: int
    last_successful_sync: Optional[datetime] = None
    cache_valid_until: Optional[datetime] = None

    def is_cache_valid(self) -> bool:
        """Returns True if cached data is still valid.

        Returns:
            True if cache hasn't expired, False otherwise
        """
        if not self.cache_valid_until:
            return False
        return datetime.now(timezone.utc) < self.cache_valid_until

    def get_failed_sources(self) -> list[str]:
        """Returns list of source IDs that failed to sync.

        Returns:
            List of source_id strings for failed syncs
        """
        return [
            source_id
            for source_id, result in self.sync_results.items()
            if result.status == SyncStatus.FAILED
        ]

    def get_staleness_hours(self) -> float:
        """Returns hours since last successful sync.

        Returns:
            Hours as float, or infinity if never synced
        """
        if not self.last_successful_sync:
            return float("inf")

        delta = datetime.now(timezone.utc) - self.last_successful_sync
        return delta.total_seconds() / 3600
