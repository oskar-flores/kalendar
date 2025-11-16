"""
Unit tests for SyncCalendarsUseCase.

Purpose: Test calendar synchronization logic with mocks.
Following TDD - tests written FIRST.
"""

import pytest
from datetime import date, datetime, timezone, timedelta
from typing import List
from unittest.mock import Mock, MagicMock

from kalendar.domain.interfaces.ICalendarSource import (
    CalendarEventDTO,
    CalendarSourceError,
    NetworkError,
)
from kalendar.domain.models.source import CalendarSource, SyncStatus


class TestSyncCalendarsUseCase:
    """Test suite for SyncCalendarsUseCase."""

    @pytest.fixture
    def mock_cache(self) -> Mock:
        """Create mock cache."""
        cache = Mock()
        cache.save_events = Mock()
        cache.load_events = Mock(return_value=None)
        cache.is_cache_valid = Mock(return_value=False)
        return cache

    @pytest.fixture
    def mock_config(self) -> Mock:
        """Create mock config."""
        config = Mock()
        config.get_enabled_sources = Mock(return_value=[])
        return config

    @pytest.fixture
    def mock_event_aggregator(self) -> Mock:
        """Create mock event aggregator."""
        return Mock()

    @pytest.fixture
    def mock_calendar_source(self) -> Mock:
        """Create mock calendar source that returns test events."""
        source = Mock()
        source.get_source_info = Mock(
            return_value={
                "source_id": "test-source",
                "source_type": "mock",
                "calendar_name": "Test Calendar",
                "is_authenticated": True,
            }
        )

        # Return sample events
        sample_events = [
            CalendarEventDTO(
                id="event-1",
                calendar_source_id="test-source",
                title="Test Event 1",
                start_datetime=datetime.now(timezone.utc),
                end_datetime=datetime.now(timezone.utc) + timedelta(hours=1),
                is_all_day=False,
            ),
            CalendarEventDTO(
                id="event-2",
                calendar_source_id="test-source",
                title="Test Event 2",
                start_datetime=datetime.now(timezone.utc) + timedelta(hours=2),
                end_datetime=datetime.now(timezone.utc) + timedelta(hours=3),
                is_all_day=False,
            ),
        ]
        source.fetch_events = Mock(return_value=sample_events)
        return source

    @pytest.fixture
    def calendar_sources(self, mock_calendar_source: Mock) -> List[Mock]:
        """Create list of calendar sources."""
        return [mock_calendar_source]

    def test_sync_calendars_fetches_from_all_sources(
        self, mock_config: Mock, mock_cache: Mock, mock_event_aggregator: Mock, calendar_sources: List[Mock]
    ) -> None:
        """SyncCalendarsUseCase should fetch events from all calendar sources."""
        # This test will pass once SyncCalendarsUseCase is implemented
        from kalendar.application.usecases.sync_calendars import SyncCalendarsUseCase

        # Arrange
        use_case = SyncCalendarsUseCase(config=mock_config, cache=mock_cache, event_aggregator=mock_event_aggregator, dependencies=Mock())
        start = date.today()
        end = start + timedelta(days=30)

        # Act
        result = use_case.execute(calendar_sources, start, end)

        # Assert
        assert calendar_sources[0].fetch_events.called
        assert calendar_sources[0].fetch_events.call_args[0] == (start, end)

    def test_sync_calendars_caches_fetched_events(
        self, mock_config: Mock, mock_cache: Mock, mock_event_aggregator: Mock, calendar_sources: List[Mock]
    ) -> None:
        """SyncCalendarsUseCase should save fetched events to cache."""
        from kalendar.application.usecases.sync_calendars import SyncCalendarsUseCase

        # Arrange
        use_case = SyncCalendarsUseCase(config=mock_config, cache=mock_cache, event_aggregator=mock_event_aggregator, dependencies=Mock())
        start = date.today()
        end = start + timedelta(days=30)

        # Act
        result = use_case.execute(calendar_sources, start, end)

        # Assert
        assert mock_cache.save_events.called

    def test_sync_calendars_aggregates_events_from_multiple_sources(
        self, mock_config: Mock, mock_cache: Mock, mock_event_aggregator: Mock
    ) -> None:
        """SyncCalendarsUseCase should aggregate events from multiple sources."""
        from kalendar.application.usecases.sync_calendars import SyncCalendarsUseCase

        # Arrange
        source1 = Mock()
        source1.get_source_info = Mock(return_value={"source_id": "source-1"})
        source1.fetch_events = Mock(
            return_value=[
                CalendarEventDTO(
                    id="evt-1",
                    calendar_source_id="source-1",
                    title="Event 1",
                    start_datetime=datetime.now(timezone.utc),
                    end_datetime=datetime.now(timezone.utc) + timedelta(hours=1),
                    is_all_day=False,
                )
            ]
        )

        source2 = Mock()
        source2.get_source_info = Mock(return_value={"source_id": "source-2"})
        source2.fetch_events = Mock(
            return_value=[
                CalendarEventDTO(
                    id="evt-2",
                    calendar_source_id="source-2",
                    title="Event 2",
                    start_datetime=datetime.now(timezone.utc),
                    end_datetime=datetime.now(timezone.utc) + timedelta(hours=1),
                    is_all_day=False,
                )
            ]
        )

        use_case = SyncCalendarsUseCase(config=mock_config, cache=mock_cache, event_aggregator=mock_event_aggregator, dependencies=Mock())
        start = date.today()
        end = start + timedelta(days=30)

        # Act
        result = use_case.execute([source1, source2], start, end)

        # Assert
        assert len(result.events) == 2

    def test_sync_calendars_handles_source_failure_gracefully(
        self, mock_cache: Mock
    ) -> None:
        """SyncCalendarsUseCase should continue if one source fails."""
        from kalendar.application.usecases.sync_calendars import SyncCalendarsUseCase

        # Arrange
        failing_source = Mock()
        failing_source.get_source_info = Mock(return_value={"source_id": "failing"})
        failing_source.fetch_events = Mock(side_effect=NetworkError("Connection failed"))

        working_source = Mock()
        working_source.get_source_info = Mock(return_value={"source_id": "working"})
        working_source.fetch_events = Mock(
            return_value=[
                CalendarEventDTO(
                    id="evt-1",
                    calendar_source_id="working",
                    title="Event 1",
                    start_datetime=datetime.now(timezone.utc),
                    end_datetime=datetime.now(timezone.utc) + timedelta(hours=1),
                    is_all_day=False,
                )
            ]
        )

        use_case = SyncCalendarsUseCase(config=Mock(), cache=mock_cache, event_aggregator=Mock(), dependencies=Mock())
        start = date.today()
        end = start + timedelta(days=30)

        # Act
        result = use_case.execute([failing_source, working_source], start, end)

        # Assert
        assert len(result.events) == 1  # Should have event from working source
        assert len(result.errors) == 1  # Should record error from failing source

    def test_sync_calendars_deduplicates_events(self, mock_cache: Mock) -> None:
        """SyncCalendarsUseCase should deduplicate events with same title and time."""
        from kalendar.application.usecases.sync_calendars import SyncCalendarsUseCase

        # Arrange
        same_time = datetime.now(timezone.utc)
        source1 = Mock()
        source1.get_source_info = Mock(return_value={"source_id": "source-1"})
        source1.fetch_events = Mock(
            return_value=[
                CalendarEventDTO(
                    id="evt-1",
                    calendar_source_id="source-1",
                    title="Meeting",
                    start_datetime=same_time,
                    end_datetime=same_time + timedelta(hours=1),
                    is_all_day=False,
                    location="Room A",
                )
            ]
        )

        source2 = Mock()
        source2.get_source_info = Mock(return_value={"source_id": "source-2"})
        source2.fetch_events = Mock(
            return_value=[
                CalendarEventDTO(
                    id="evt-2",
                    calendar_source_id="source-2",
                    title="Meeting",  # Same title
                    start_datetime=same_time,  # Same time
                    end_datetime=same_time + timedelta(hours=1),
                    is_all_day=False,
                    location="Room A",  # Same location
                )
            ]
        )

        use_case = SyncCalendarsUseCase(config=Mock(), cache=mock_cache, event_aggregator=Mock(), dependencies=Mock())
        start = date.today()
        end = start + timedelta(days=30)

        # Act
        result = use_case.execute([source1, source2], start, end)

        # Assert
        assert len(result.events) == 1  # Should deduplicate

    def test_sync_calendars_returns_sync_metadata(
        self, mock_cache: Mock, calendar_sources: List[Mock]
    ) -> None:
        """SyncCalendarsUseCase should return metadata about sync operation."""
        from kalendar.application.usecases.sync_calendars import SyncCalendarsUseCase

        # Arrange
        use_case = SyncCalendarsUseCase(config=Mock(), cache=mock_cache, event_aggregator=Mock(), dependencies=Mock())
        start = date.today()
        end = start + timedelta(days=30)

        # Act
        result = use_case.execute(calendar_sources, start, end)

        # Assert
        assert hasattr(result, "events")
        assert hasattr(result, "timestamp")
        assert hasattr(result, "sources_synced")
        assert hasattr(result, "errors")
