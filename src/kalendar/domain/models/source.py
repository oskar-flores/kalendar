"""CalendarSource domain model."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from kalendar.domain.models.enums import SourceType, SyncStatus


@dataclass
class CalendarSource:
    """Represents a connected calendar (Google or Apple iCloud).

    Attributes:
        id: Internal identifier for this calendar source
        name: Display name (e.g., "Family Calendar")
        source_type: GOOGLE or CALDAV
        calendar_id: External calendar ID (Google calendar ID or CalDAV URL)
        enabled: Whether to include events from this source
        color: Visual indicator color (not used in 3-color display)
        last_sync_time: Timestamp of last successful sync
        last_sync_status: SUCCESS, FAILED, PENDING, or NEVER_SYNCED
        credentials: Encrypted auth credentials (stored separately in practice)
    """

    id: str
    name: str
    source_type: SourceType
    calendar_id: str
    enabled: bool
    color: Optional[str] = None
    last_sync_time: Optional[datetime] = None
    last_sync_status: SyncStatus = field(default=SyncStatus.NEVER_SYNCED)
    credentials: Optional[dict[str, str]] = None

    def __post_init__(self) -> None:
        """Validate calendar source data after initialization."""
        if not self.name:
            raise ValueError("Calendar source name cannot be empty")

        if not self.calendar_id:
            raise ValueError("Calendar ID cannot be empty")

        if len(self.name) > 100:
            raise ValueError("Calendar source name cannot exceed 100 characters")

    def is_stale(self, max_age_hours: int = 24) -> bool:
        """Returns True if last sync is older than max_age_hours.

        Args:
            max_age_hours: Maximum age in hours before considering stale

        Returns:
            True if stale or never synced, False if fresh
        """
        if not self.last_sync_time:
            return True

        age = datetime.now(timezone.utc) - self.last_sync_time
        return age.total_seconds() > (max_age_hours * 3600)

    def mark_sync_success(self, timestamp: datetime) -> None:
        """Update sync status after successful sync.

        Args:
            timestamp: Time of successful sync
        """
        self.last_sync_time = timestamp
        self.last_sync_status = SyncStatus.SUCCESS

    def mark_sync_failed(self) -> None:
        """Update sync status after failed sync."""
        self.last_sync_status = SyncStatus.FAILED
