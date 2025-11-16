"""
Interface: Cache Repository

Abstraction for persistent storage of calendar data.
Enables testing without filesystem access.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


class ICache(ABC):
    """
    Interface for calendar event cache.

    Implementations:
    - FileSystemCache (JSON files in /var/cache/kalendar/)
    - InMemoryCache (for testing)
    - SQLiteCache (future: if query performance becomes issue)

    Responsibilities:
    - Store fetched calendar events
    - Retrieve cached events
    - Track cache freshness
    - Manage cache expiration
    """

    @abstractmethod
    def save_events(
        self,
        source_id: str,
        events: List[Dict[str, Any]],
        timestamp: datetime,
    ) -> None:
        """
        Save events for a specific calendar source.

        Args:
            source_id: Unique identifier for calendar source
            events: List of event dictionaries (serialized CalendarEventDTO)
            timestamp: Timestamp of this cache update

        Raises:
            CacheWriteError: If save operation fails
        """
        pass

    @abstractmethod
    def load_events(
        self,
        source_id: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Load cached events for a specific calendar source.

        Args:
            source_id: Unique identifier for calendar source

        Returns:
            List of event dictionaries, or None if no cache exists

        Raises:
            CacheReadError: If load operation fails
        """
        pass

    @abstractmethod
    def get_cache_timestamp(self, source_id: str) -> Optional[datetime]:
        """
        Get timestamp of last cache update for a source.

        Args:
            source_id: Unique identifier for calendar source

        Returns:
            Datetime of last update, or None if no cache exists
        """
        pass

    @abstractmethod
    def is_cache_valid(
        self,
        source_id: str,
        max_age_hours: int = 24,
    ) -> bool:
        """
        Check if cached data is still fresh.

        Args:
            source_id: Unique identifier for calendar source
            max_age_hours: Maximum cache age in hours

        Returns:
            True if cache exists and is within max_age_hours
        """
        pass

    @abstractmethod
    def clear_cache(self, source_id: str) -> None:
        """
        Clear cached data for a specific source.

        Args:
            source_id: Unique identifier for calendar source

        Raises:
            CacheWriteError: If clear operation fails
        """
        pass

    @abstractmethod
    def clear_all_caches(self) -> None:
        """
        Clear all cached data for all sources.

        Raises:
            CacheWriteError: If clear operation fails
        """
        pass

    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics and metadata.

        Returns:
            dict with keys:
                - total_sources: int (number of cached sources)
                - total_events: int (total cached events across all sources)
                - oldest_cache_age_hours: float
                - cache_size_bytes: int (total disk/memory usage)
                - cache_location: str (path or description)
        """
        pass


class CacheError(Exception):
    """Base exception for cache errors."""

    pass


class CacheReadError(CacheError):
    """Raised when reading from cache fails."""

    pass


class CacheWriteError(CacheError):
    """Raised when writing to cache fails."""

    pass
