"""
Mock Calendar Source for testing.

Purpose: Provides deterministic calendar data for tests without network dependencies.
Returns fixture events that cover various test scenarios.
"""

from datetime import datetime, date, timezone, timedelta
from typing import List, Optional
from kalendar.domain.interfaces.ICalendarSource import (
    ICalendarSource,
    CalendarEventDTO,
    CalendarSourceConfig,
    AuthenticationError,
)


class MockCalendarSource(ICalendarSource):
    """
    Mock implementation of ICalendarSource for testing.

    Returns pre-defined fixture events that cover:
    - Single-day events
    - Multi-day events
    - All-day events
    - Events with location and description
    - Recurring events
    """

    def __init__(self, config: CalendarSourceConfig):
        """
        Initialize MockCalendarSource.

        Args:
            config: CalendarSourceConfig with source metadata
        """
        self._config = config
        self._is_authenticated = True
        self._last_sync_time: Optional[datetime] = None

        # Pre-defined fixture events
        self._fixture_events = self._create_fixture_events()

    def _create_fixture_events(self) -> List[CalendarEventDTO]:
        """Create fixture events for testing."""
        today = date.today()

        return [
            # Single-day event today
            CalendarEventDTO(
                id="mock-event-1",
                calendar_source_id=self._config.source_id,
                title="Team Meeting",
                start_datetime=datetime.combine(
                    today, datetime.min.time(), timezone.utc
                ).replace(hour=10, minute=0),
                end_datetime=datetime.combine(
                    today, datetime.min.time(), timezone.utc
                ).replace(hour=11, minute=0),
                is_all_day=False,
                location="Conference Room A",
                description="Weekly team standup",
                is_recurring=True,
                recurrence_id="mock-recurrence-1",
            ),
            # All-day event today
            CalendarEventDTO(
                id="mock-event-2",
                calendar_source_id=self._config.source_id,
                title="Birthday",
                start_datetime=datetime.combine(today, datetime.min.time(), timezone.utc),
                end_datetime=datetime.combine(
                    today + timedelta(days=1), datetime.min.time(), timezone.utc
                ),
                is_all_day=True,
                location=None,
                description="Happy birthday!",
                is_recurring=False,
                recurrence_id=None,
            ),
            # Multi-day event starting today
            CalendarEventDTO(
                id="mock-event-3",
                calendar_source_id=self._config.source_id,
                title="Conference",
                start_datetime=datetime.combine(today, datetime.min.time(), timezone.utc),
                end_datetime=datetime.combine(
                    today + timedelta(days=2), datetime.min.time(), timezone.utc
                ),
                is_all_day=True,
                location="Convention Center",
                description="Annual tech conference",
                is_recurring=False,
                recurrence_id=None,
            ),
            # Event tomorrow
            CalendarEventDTO(
                id="mock-event-4",
                calendar_source_id=self._config.source_id,
                title="Doctor Appointment",
                start_datetime=datetime.combine(
                    today + timedelta(days=1), datetime.min.time(), timezone.utc
                ).replace(hour=14, minute=30),
                end_datetime=datetime.combine(
                    today + timedelta(days=1), datetime.min.time(), timezone.utc
                ).replace(hour=15, minute=30),
                is_all_day=False,
                location="Medical Center",
                description=None,
                is_recurring=False,
                recurrence_id=None,
            ),
            # Event next week
            CalendarEventDTO(
                id="mock-event-5",
                calendar_source_id=self._config.source_id,
                title="Project Deadline",
                start_datetime=datetime.combine(
                    today + timedelta(days=7), datetime.min.time(), timezone.utc
                ).replace(hour=17, minute=0),
                end_datetime=datetime.combine(
                    today + timedelta(days=7), datetime.min.time(), timezone.utc
                ).replace(hour=17, minute=30),
                is_all_day=False,
                location=None,
                description="Final deliverables due",
                is_recurring=False,
                recurrence_id=None,
            ),
        ]

    def fetch_events(self, start_date: date, end_date: date) -> List[CalendarEventDTO]:
        """
        Fetch fixture events within date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of CalendarEventDTO objects within range
        """
        if not self._is_authenticated:
            raise AuthenticationError("Mock calendar source not authenticated")

        # Filter events by date range
        filtered_events = []
        for event in self._fixture_events:
            event_start_date = event.start_datetime.date()
            event_end_date = event.end_datetime.date()

            # Event overlaps with requested range
            if event_start_date <= end_date and event_end_date >= start_date:
                filtered_events.append(event)

        self._last_sync_time = datetime.now(timezone.utc)
        return filtered_events

    def test_connection(self) -> bool:
        """
        Test connection (always succeeds for mock).

        Returns:
            True (mock always connected)
        """
        return self._is_authenticated

    def refresh_auth(self) -> None:
        """
        Refresh authentication (no-op for mock).

        Mock implementation always stays authenticated.
        Can be configured to fail for testing error scenarios.
        """
        if not self._is_authenticated:
            raise AuthenticationError("Mock authentication refresh failed")

    def get_source_info(self) -> dict:
        """
        Get mock calendar source metadata.

        Returns:
            dict with source information
        """
        return {
            "source_id": self._config.source_id,
            "source_type": self._config.source_type,
            "calendar_name": f"Mock Calendar ({self._config.source_id})",
            "last_sync_time": self._last_sync_time,
            "is_authenticated": self._is_authenticated,
        }

    # Test helper methods

    def set_authenticated(self, authenticated: bool) -> None:
        """
        Set authentication status (for testing error scenarios).

        Args:
            authenticated: Whether mock should be authenticated
        """
        self._is_authenticated = authenticated

    def add_fixture_event(self, event: CalendarEventDTO) -> None:
        """
        Add a custom fixture event (for test scenarios).

        Args:
            event: CalendarEventDTO to add to fixtures
        """
        self._fixture_events.append(event)

    def clear_fixture_events(self) -> None:
        """Clear all fixture events (for test scenarios)."""
        self._fixture_events = []
