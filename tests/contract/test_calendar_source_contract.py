"""
Contract test for ICalendarSource interface.

Purpose: Verify that all implementations of ICalendarSource comply with the interface contract.
This test should be run against GoogleCalendarSource, CalDAVSource, and MockCalendarSource.

TDD: This test is written FIRST and should FAIL until implementations exist.
"""

import pytest
from datetime import datetime, date, timezone, timedelta
from typing import Type
from src.kalendar.domain.interfaces.ICalendarSource import (
    ICalendarSource,
    CalendarEventDTO,
    CalendarSourceConfig,
    CalendarSourceError,
    AuthenticationError,
    NetworkError,
)


class ICalendarSourceContractTest:
    """
    Base contract test for ICalendarSource implementations.

    Subclass this test for each implementation and provide the implementation class.
    """

    @pytest.fixture
    def source_config(self) -> CalendarSourceConfig:
        """Override in subclass to provide test configuration."""
        raise NotImplementedError("Subclass must provide source_config fixture")

    @pytest.fixture
    def calendar_source(self, source_config: CalendarSourceConfig) -> ICalendarSource:
        """Override in subclass to provide calendar source implementation."""
        raise NotImplementedError("Subclass must provide calendar_source fixture")

    def test_fetch_events_returns_list(self, calendar_source: ICalendarSource) -> None:
        """fetch_events should return a list of CalendarEventDTO objects."""
        # Arrange
        start = date.today()
        end = start + timedelta(days=7)

        # Act
        events = calendar_source.fetch_events(start, end)

        # Assert
        assert isinstance(events, list)
        for event in events:
            assert isinstance(event, CalendarEventDTO)

    def test_fetch_events_respects_date_range(self, calendar_source: ICalendarSource) -> None:
        """fetch_events should only return events within the specified date range."""
        # Arrange
        start = date.today()
        end = start + timedelta(days=7)

        # Act
        events = calendar_source.fetch_events(start, end)

        # Assert
        for event in events:
            event_start_date = event.start_datetime.date()
            event_end_date = event.end_datetime.date()
            # Event must overlap with requested date range
            assert (
                event_start_date <= end and event_end_date >= start
            ), f"Event {event.id} outside date range: {event_start_date} to {event_end_date}"

    def test_fetch_events_with_empty_range_returns_empty_list(
        self, calendar_source: ICalendarSource
    ) -> None:
        """fetch_events with far future date should return empty list."""
        # Arrange
        start = date(2099, 1, 1)
        end = date(2099, 1, 7)

        # Act
        events = calendar_source.fetch_events(start, end)

        # Assert
        assert isinstance(events, list)
        assert len(events) == 0

    def test_fetch_events_dto_has_required_fields(
        self, calendar_source: ICalendarSource
    ) -> None:
        """CalendarEventDTO should have all required fields."""
        # Arrange
        start = date.today()
        end = start + timedelta(days=30)

        # Act
        events = calendar_source.fetch_events(start, end)

        # Assert
        if events:  # Only check if there are events
            event = events[0]
            assert isinstance(event.id, str)
            assert len(event.id) > 0
            assert isinstance(event.calendar_source_id, str)
            assert isinstance(event.title, str)
            assert len(event.title) > 0
            assert isinstance(event.start_datetime, datetime)
            assert isinstance(event.end_datetime, datetime)
            assert isinstance(event.is_all_day, bool)
            assert event.location is None or isinstance(event.location, str)
            assert event.description is None or isinstance(event.description, str)
            assert isinstance(event.is_recurring, bool)
            assert event.recurrence_id is None or isinstance(event.recurrence_id, str)

    def test_fetch_events_dto_validates_datetime_order(
        self, calendar_source: ICalendarSource
    ) -> None:
        """CalendarEventDTO end_datetime should be >= start_datetime."""
        # Arrange
        start = date.today()
        end = start + timedelta(days=30)

        # Act
        events = calendar_source.fetch_events(start, end)

        # Assert
        for event in events:
            assert event.end_datetime >= event.start_datetime, (
                f"Event {event.id} has end before start: "
                f"{event.start_datetime} > {event.end_datetime}"
            )

    def test_test_connection_returns_bool(self, calendar_source: ICalendarSource) -> None:
        """test_connection should return a boolean value."""
        # Act
        result = calendar_source.test_connection()

        # Assert
        assert isinstance(result, bool)

    def test_test_connection_no_exceptions(self, calendar_source: ICalendarSource) -> None:
        """test_connection should not raise exceptions (returns False instead)."""
        # Act & Assert - should not raise
        try:
            result = calendar_source.test_connection()
            assert isinstance(result, bool)
        except Exception as e:
            pytest.fail(f"test_connection() raised {type(e).__name__}: {e}")

    def test_get_source_info_returns_dict(self, calendar_source: ICalendarSource) -> None:
        """get_source_info should return a dictionary with required keys."""
        # Act
        info = calendar_source.get_source_info()

        # Assert
        assert isinstance(info, dict)
        assert "source_id" in info
        assert "source_type" in info
        assert "calendar_name" in info
        assert "last_sync_time" in info
        assert "is_authenticated" in info

        # Validate types
        assert isinstance(info["source_id"], str)
        assert info["source_type"] in ["google", "caldav", "mock"]  # Allow mock for testing
        assert isinstance(info["calendar_name"], str)
        assert info["last_sync_time"] is None or isinstance(
            info["last_sync_time"], datetime
        )
        assert isinstance(info["is_authenticated"], bool)

    def test_refresh_auth_callable(self, calendar_source: ICalendarSource) -> None:
        """refresh_auth should be callable (may succeed or raise AuthenticationError)."""
        # Act & Assert - should be callable
        # May raise AuthenticationError (which is acceptable)
        try:
            calendar_source.refresh_auth()
        except AuthenticationError:
            # This is an acceptable outcome for refresh_auth
            pass
        except Exception as e:
            pytest.fail(
                f"refresh_auth() raised unexpected {type(e).__name__}: {e}. "
                f"Should only raise AuthenticationError."
            )


# Test against MockCalendarSource (implementation in next task)
class TestMockCalendarSourceContract(ICalendarSourceContractTest):
    """Contract test for MockCalendarSource."""

    @pytest.fixture
    def source_config(self) -> CalendarSourceConfig:
        """Configuration for MockCalendarSource."""
        return CalendarSourceConfig(
            source_id="mock-calendar",
            source_type="mock",
            calendar_id="mock",
            credentials={},
        )

    @pytest.fixture
    def calendar_source(self, source_config: CalendarSourceConfig) -> ICalendarSource:
        """Create MockCalendarSource instance."""
        # This will fail until MockCalendarSource is implemented
        from tests.fixtures.mock_calendar_source import MockCalendarSource

        return MockCalendarSource(source_config)


# Placeholder for GoogleCalendarSource contract test
# Uncomment when GoogleCalendarSource is implemented
# class TestGoogleCalendarSourceContract(ICalendarSourceContractTest):
#     @pytest.fixture
#     def source_config(self) -> CalendarSourceConfig:
#         # Load from test credentials
#         pass
#
#     @pytest.fixture
#     def calendar_source(self, source_config: CalendarSourceConfig) -> ICalendarSource:
#         from src.kalendar.infrastructure.calendar.google_calendar_source import (
#             GoogleCalendarSource,
#         )
#         return GoogleCalendarSource(source_config)


# Placeholder for CalDAVSource contract test
# Uncomment when CalDAVSource is implemented
# class TestCalDAVSourceContract(ICalendarSourceContractTest):
#     @pytest.fixture
#     def source_config(self) -> CalendarSourceConfig:
#         # Load from test credentials
#         pass
#
#     @pytest.fixture
#     def calendar_source(self, source_config: CalendarSourceConfig) -> ICalendarSource:
#         from src.kalendar.infrastructure.calendar.caldav_source import CalDAVSource
#         return CalDAVSource(source_config)
