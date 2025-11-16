"""File system cache implementation."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from kalendar.domain.models.event import CalendarEvent

logger = logging.getLogger(__name__)


class FileSystemCache:
    """Caches calendar events to JSON files on disk.

    Implements persistent caching with validation.
    """

    def __init__(self, cache_dir: str = "./cache") -> None:
        """Initialize filesystem cache.

        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)

        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            # Fallback to user cache directory if system cache is not writable
            fallback_dir = Path.home() / ".cache" / "kalendar"
            logger.warning(
                f"Permission denied for cache directory '{cache_dir}'. "
                f"Falling back to '{fallback_dir}'"
            )
            self.cache_dir = fallback_dir
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def save_events(
        self, source_id: str, events: list, timestamp: datetime
    ) -> None:
        """Save events to cache for a specific source.

        Args:
            source_id: Calendar source ID
            events: Events to cache (CalendarEvent objects or dicts)
            timestamp: Sync timestamp
        """
        cache_file = self.cache_dir / f"{source_id}.json"

        # Serialize events - handle both CalendarEvent objects and dicts
        serialized_events = []
        for event in events:
            if isinstance(event, dict):
                # Already a dict, use as-is
                serialized_events.append(event)
            else:
                # CalendarEvent object, serialize it
                serialized_events.append(self._serialize_event(event))

        data = {
            "source_id": source_id,
            "last_sync": timestamp.isoformat(),
            "events": serialized_events,
        }

        with open(cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_events(self, source_id: str) -> Optional[list[CalendarEvent]]:
        """Load cached events for a source.

        Args:
            source_id: Calendar source ID

        Returns:
            List of cached events or None if cache doesn't exist
        """
        cache_file = self.cache_dir / f"{source_id}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file) as f:
                data = json.load(f)

            # Validate required keys exist
            if "events" not in data:
                return None

            return [self._deserialize_event(e) for e in data["events"]]
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache file - return None
            return None

    def is_cache_valid(self, source_id: str, max_age_hours: int = 24) -> bool:
        """Check if cache is valid for a source.

        Args:
            source_id: Calendar source ID
            max_age_hours: Maximum cache age in hours

        Returns:
            True if cache exists and is fresh
        """
        cache_file = self.cache_dir / f"{source_id}.json"

        if not cache_file.exists():
            return False

        try:
            with open(cache_file) as f:
                data = json.load(f)

            last_sync = datetime.fromisoformat(data["last_sync"])
            age = datetime.now(timezone.utc) - last_sync
            return age.total_seconds() < (max_age_hours * 3600)
        except (json.JSONDecodeError, KeyError, ValueError):
            return False

    def clear_cache(self, source_id: Optional[str] = None) -> None:
        """Clear cache for a source or all sources.

        Args:
            source_id: Source to clear, or None to clear all
        """
        if source_id:
            cache_file = self.cache_dir / f"{source_id}.json"
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()

    def _serialize_event(self, event: CalendarEvent) -> dict[str, any]:
        """Serialize event to dict.

        Args:
            event: Event to serialize

        Returns:
            Dictionary ready for JSON serialization
        """
        return {
            "id": event.id,
            "calendar_source_id": event.calendar_source_id,
            "title": event.title,
            "start_datetime": event.start_datetime.isoformat(),
            "end_datetime": event.end_datetime.isoformat(),
            "is_all_day": event.is_all_day,
            "location": event.location,
            "description": event.description,
            "is_recurring": event.is_recurring,
            "recurrence_id": event.recurrence_id,
        }

    def _deserialize_event(self, data: dict[str, any]) -> CalendarEvent:
        """Deserialize dict to CalendarEvent.

        Args:
            data: Event data from JSON

        Returns:
            CalendarEvent object
        """
        return CalendarEvent(
            id=data["id"],
            calendar_source_id=data["calendar_source_id"],
            title=data["title"],
            start_datetime=datetime.fromisoformat(data["start_datetime"]),
            end_datetime=datetime.fromisoformat(data["end_datetime"]),
            is_all_day=data["is_all_day"],
            location=data.get("location"),
            description=data.get("description"),
            is_recurring=data.get("is_recurring", False),
            recurrence_id=data.get("recurrence_id"),
        )
