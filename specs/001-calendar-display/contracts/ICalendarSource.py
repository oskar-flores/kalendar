"""
Interface: Calendar Source Repository

Abstraction for calendar providers (Google Calendar, CalDAV/iCloud).
Enables dependency inversion per Clean Architecture Principle I.
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class CalendarEventDTO:
    """Data Transfer Object for calendar events across layer boundaries."""

    id: str
    calendar_source_id: str
    title: str
    start_datetime: datetime
    end_datetime: datetime
    is_all_day: bool
    location: Optional[str] = None
    description: Optional[str] = None
    is_recurring: bool = False
    recurrence_id: Optional[str] = None


@dataclass
class CalendarSourceConfig:
    """Configuration for a calendar source."""

    source_id: str
    source_type: str  # "google" or "caldav"
    calendar_id: str  # Google calendar ID or CalDAV URL
    credentials: dict  # Auth credentials (structure varies by type)


class ICalendarSource(ABC):
    """
    Interface for calendar source implementations.

    Implementations:
    - GoogleCalendarSource (uses google-api-python-client)
    - CalDAVSource (uses caldav library for iCloud)

    Testing:
    - MockCalendarSource (returns fixture data)
    - RecordingCalendarSource (records API responses for replay)
    """

    @abstractmethod
    def fetch_events(
        self,
        start_date: date,
        end_date: date,
    ) -> List[CalendarEventDTO]:
        """
        Fetch all events from this calendar source within date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of CalendarEventDTO objects

        Raises:
            AuthenticationError: If credentials are invalid/expired
            NetworkError: If unable to reach calendar provider
            CalendarSourceError: For other provider-specific errors
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test connection to calendar source without fetching events.

        Returns:
            True if connection successful, False otherwise

        Note:
            Should not raise exceptions - returns False on any error.
            Detailed error info should be logged internally.
        """
        pass

    @abstractmethod
    def refresh_auth(self) -> None:
        """
        Refresh authentication credentials if supported.

        For Google: Refresh OAuth token using refresh_token
        For CalDAV: Re-validate app-specific password

        Raises:
            AuthenticationError: If refresh fails (e.g., refresh token revoked)
        """
        pass

    @abstractmethod
    def get_source_info(self) -> dict:
        """
        Get metadata about this calendar source.

        Returns:
            dict with keys:
                - source_id: str
                - source_type: str ("google" or "caldav")
                - calendar_name: str
                - last_sync_time: Optional[datetime]
                - is_authenticated: bool
        """
        pass


class CalendarSourceError(Exception):
    """Base exception for calendar source errors."""

    pass


class AuthenticationError(CalendarSourceError):
    """Raised when authentication fails or credentials are invalid."""

    pass


class NetworkError(CalendarSourceError):
    """Raised when network communication with provider fails."""

    pass


class RateLimitError(CalendarSourceError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str, retry_after_seconds: int):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
