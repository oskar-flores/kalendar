"""
Sync Calendars Use Case.

Fetches events from multiple calendar sources, aggregates them,
deduplicates, and caches the results.
"""

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional
import logging

from kalendar.domain.interfaces.ICalendarSource import (
    ICalendarSource,
    CalendarEventDTO,
    CalendarSourceError,
)
from kalendar.domain.interfaces.ICache import ICache
from kalendar.domain.models.event import CalendarEvent

logger = logging.getLogger(__name__)


@dataclass
class SourceSyncResult:
    """Result of syncing a single calendar source."""

    status: Any  # SyncStatus enum
    events_fetched: int
    duration_seconds: float
    error_message: Optional[str] = None


@dataclass
class SyncResult:
    """Result of calendar synchronization operation."""

    events: List[CalendarEvent]
    timestamp: datetime
    sources_synced: int
    total_sources: int
    errors: List[Dict[str, str]]  # List of {"source_id": str, "error": str}
    source_results: Dict[str, SourceSyncResult]  # Per-source sync results


class SyncCalendarsUseCase:
    """
    Use case: Synchronize calendar events from multiple sources.

    Responsibilities:
        - Fetch events from all enabled calendar sources
        - Aggregate events from multiple sources
        - Deduplicate events that appear in multiple calendars
        - Cache fetched events for offline access
        - Handle errors gracefully (continue if one source fails)

    Error Handling (per FR-014):
        - If a source fails, continue with other sources
        - Record errors but don't fail the entire sync
        - Use cached data as fallback if available
    """

    def __init__(self, config: Any, cache: ICache, event_aggregator: Any, dependencies: Any = None) -> None:
        """
        Initialize SyncCalendarsUseCase.

        Args:
            config: Configuration with calendar sources
            cache: Cache implementation for storing events
            event_aggregator: Event aggregator service (unused for now)
            dependencies: Dependencies container with calendar source factory
        """
        self._config = config
        self._cache = cache
        self._event_aggregator = event_aggregator
        self._dependencies = dependencies

    def execute(
        self,
        calendar_sources: Optional[List[ICalendarSource]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> SyncResult:
        """
        Synchronize calendar events from multiple sources.

        Args:
            calendar_sources: List of calendar sources to sync (defaults to enabled sources from config)
            start_date: Start of date range to fetch (defaults to today)
            end_date: End of date range to fetch (defaults to 30 days from today)

        Returns:
            SyncResult with aggregated events and metadata
        """
        from datetime import timedelta

        # Use defaults if not provided
        if calendar_sources is None:
            # Use factory from dependencies to create ICalendarSource implementations
            if self._dependencies is None:
                raise ValueError(
                    "Dependencies not provided. Cannot create calendar sources automatically."
                )
            calendar_sources = self._dependencies.get_calendar_sources()
        if start_date is None:
            start_date = date.today()
        if end_date is None:
            end_date = start_date + timedelta(days=30)

        all_events: List[CalendarEventDTO] = []
        errors: List[Dict[str, str]] = []
        source_results: Dict[str, SourceSyncResult] = {}
        sources_synced = 0

        logger.info(
            f"Starting sync for {len(calendar_sources)} sources "
            f"from {start_date} to {end_date}"
        )

        # Fetch from each source
        for source in calendar_sources:
            source_info = source.get_source_info()
            source_id = source_info["source_id"]

            import time
            start_time = time.time()

            try:
                # Fetch events from this source
                events = source.fetch_events(start_date, end_date)
                all_events.extend(events)
                sources_synced += 1

                duration = time.time() - start_time

                # Cache events for this source
                self._cache_source_events(source_id, events)

                logger.info(f"Synced {len(events)} events from {source_id}")

                # Create mock SyncStatus for success
                from kalendar.domain.models.source import SyncStatus
                source_results[source_id] = SourceSyncResult(
                    status=SyncStatus.SUCCESS,
                    events_fetched=len(events),
                    duration_seconds=duration,
                    error_message=None,
                )

            except CalendarSourceError as e:
                duration = time.time() - start_time
                logger.error(f"Failed to sync {source_id}: {e}")
                errors.append({"source_id": source_id, "error": str(e)})

                from kalendar.domain.models.source import SyncStatus
                source_results[source_id] = SourceSyncResult(
                    status=SyncStatus.FAILED,
                    events_fetched=0,
                    duration_seconds=duration,
                    error_message=str(e),
                )

                # Try to use cached data as fallback
                cached_events = self._load_cached_events(source_id)
                if cached_events:
                    all_events.extend(cached_events)
                    logger.warning(f"Using {len(cached_events)} cached events for {source_id}")

            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"Unexpected error syncing {source_id}: {e}")
                errors.append({"source_id": source_id, "error": f"Unexpected error: {e}"})

                from kalendar.domain.models.source import SyncStatus
                source_results[source_id] = SourceSyncResult(
                    status=SyncStatus.FAILED,
                    events_fetched=0,
                    duration_seconds=duration,
                    error_message=f"Unexpected error: {e}",
                )

        # Deduplicate events
        deduplicated_events = self._deduplicate_events(all_events)

        # Convert DTOs to domain models
        domain_events = [self._dto_to_domain(event) for event in deduplicated_events]

        logger.info(
            f"Sync complete: {len(domain_events)} events from "
            f"{sources_synced}/{len(calendar_sources)} sources"
        )

        return SyncResult(
            events=domain_events,
            timestamp=datetime.now(timezone.utc),
            sources_synced=sources_synced,
            total_sources=len(calendar_sources),
            errors=errors,
            source_results=source_results,
        )

    def _cache_source_events(
        self, source_id: str, events: List[CalendarEventDTO]
    ) -> None:
        """
        Cache events for a specific source.

        Args:
            source_id: Calendar source ID
            events: Events to cache
        """
        try:
            # Convert DTOs to serializable dicts
            event_dicts = [self._dto_to_dict(event) for event in events]

            # Save to cache
            self._cache.save_events(
                source_id=source_id,
                events=event_dicts,
                timestamp=datetime.now(timezone.utc),
            )
        except Exception as e:
            logger.warning(f"Failed to cache events for {source_id}: {e}")

    def _load_cached_events(self, source_id: str) -> List[CalendarEventDTO]:
        """
        Load cached events for a source.

        Args:
            source_id: Calendar source ID

        Returns:
            List of CalendarEventDTO from cache, empty if not available
        """
        try:
            cached_dicts = self._cache.load_events(source_id)
            if cached_dicts:
                return [self._dict_to_dto(d) for d in cached_dicts]
        except Exception as e:
            logger.warning(f"Failed to load cached events for {source_id}: {e}")

        return []

    def _deduplicate_events(
        self, events: List[CalendarEventDTO]
    ) -> List[CalendarEventDTO]:
        """
        Remove duplicate events based on title, start time, and location.

        Args:
            events: List of events (possibly with duplicates)

        Returns:
            Deduplicated list of events
        """
        seen_keys = set()
        unique_events = []

        for event in events:
            # Create deduplication key
            key = (
                event.title.lower().strip(),
                event.start_datetime,
                event.end_datetime,
                (event.location or "").lower().strip(),
            )

            if key not in seen_keys:
                seen_keys.add(key)
                unique_events.append(event)
            else:
                logger.debug(f"Deduplicated event: {event.title} at {event.start_datetime}")

        logger.info(f"Deduplicated {len(events) - len(unique_events)} events")
        return unique_events

    def _dto_to_dict(self, dto: CalendarEventDTO) -> Dict[str, Any]:
        """Convert CalendarEventDTO to serializable dict."""
        return {
            "id": dto.id,
            "calendar_source_id": dto.calendar_source_id,
            "title": dto.title,
            "start_datetime": dto.start_datetime.isoformat(),
            "end_datetime": dto.end_datetime.isoformat(),
            "is_all_day": dto.is_all_day,
            "location": dto.location,
            "description": dto.description,
            "is_recurring": dto.is_recurring,
            "recurrence_id": dto.recurrence_id,
        }

    def _dict_to_dto(self, data: Dict[str, Any]) -> CalendarEventDTO:
        """Convert dict to CalendarEventDTO."""
        return CalendarEventDTO(
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

    def _dto_to_domain(self, dto: CalendarEventDTO) -> CalendarEvent:
        """Convert CalendarEventDTO to CalendarEvent domain model."""
        return CalendarEvent(
            id=dto.id,
            calendar_source_id=dto.calendar_source_id,
            title=dto.title,
            start_datetime=dto.start_datetime,
            end_datetime=dto.end_datetime,
            is_all_day=dto.is_all_day,
            location=dto.location,
            description=dto.description,
            is_recurring=dto.is_recurring,
            recurrence_id=dto.recurrence_id,
        )
