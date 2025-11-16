"""Domain enumerations for kalendar."""

from enum import Enum


class SourceType(Enum):
    """Type of calendar source."""

    GOOGLE = "google"
    CALDAV = "caldav"


class SyncStatus(Enum):
    """Status of calendar synchronization."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    NEVER_SYNCED = "never_synced"


class LayoutType(Enum):
    """Display layout orientation."""

    HORIZONTAL = "horizontal"  # Landscape (800x480)
    VERTICAL = "vertical"  # Portrait (not used in initial version)
