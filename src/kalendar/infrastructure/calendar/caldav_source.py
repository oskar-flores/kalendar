"""
CalDAV Calendar Source Implementation.

Uses caldav library to fetch events from CalDAV servers (iCloud, etc.).
Implements ICalendarSource interface with basic authentication.
"""

from datetime import date, datetime, timezone, timedelta
from typing import List, Optional
import logging

import caldav
from caldav import DAVClient, Calendar
from icalendar import Calendar as ICalendar, Event
from recurring_ical_events import of

from src.kalendar.domain.interfaces.ICalendarSource import (
    ICalendarSource,
    CalendarEventDTO,
    CalendarSourceConfig,
    CalendarSourceError,
    AuthenticationError,
    NetworkError,
)

logger = logging.getLogger(__name__)


class CalDAVSource(ICalendarSource):
    """
    CalDAV implementation of ICalendarSource.

    Supports:
        - iCloud Calendar (https://caldav.icloud.com/)
        - Other CalDAV-compliant servers

    Authentication:
        Uses basic authentication with username and app-specific password.
        For iCloud: Generate app-specific password at appleid.apple.com

    Configuration:
        calendar_id: Full CalDAV URL to calendar
        credentials["username"]: CalDAV username (e.g., email)
        credentials["app_password"]: App-specific password
    """

    def __init__(self, config: CalendarSourceConfig) -> None:
        """
        Initialize CalDAV source.

        Args:
            config: CalendarSourceConfig with CalDAV settings

        Raises:
            ValueError: If config is missing required credentials
        """
        self._config = config
        self._client: Optional[DAVClient] = None
        self._calendar: Optional[Calendar] = None
        self._last_sync_time: Optional[datetime] = None

        # Validate configuration
        if "username" not in config.credentials:
            raise ValueError("CalDAV config missing 'username' in credentials")
        if "app_password" not in config.credentials:
            raise ValueError("CalDAV config missing 'app_password' in credentials")

        self._username = config.credentials["username"]
        self._password = config.credentials["app_password"]

        # Initialize connection
        self._connect()

    def _connect(self) -> None:
        """
        Connect to CalDAV server and get calendar.

        Raises:
            AuthenticationError: If connection fails
        """
        try:
            # Extract base URL from calendar URL for iCloud
            # iCloud calendar URLs: https://caldav.icloud.com/[user-id]/calendars/[calendar-id]/
            if "icloud.com" in self._config.calendar_id:
                base_url = "https://caldav.icloud.com/"
            else:
                # For other servers, try to extract base URL
                from urllib.parse import urlparse

                parsed = urlparse(self._config.calendar_id)
                base_url = f"{parsed.scheme}://{parsed.netloc}/"

            # Create DAV client
            self._client = DAVClient(url=base_url, username=self._username, password=self._password)

            # Get calendar by URL
            self._calendar = caldav.Calendar(client=self._client, url=self._config.calendar_id)

            logger.info(f"Connected to CalDAV calendar: {self._config.calendar_id}")

        except Exception as e:
            logger.error(f"Failed to connect to CalDAV: {e}")
            raise AuthenticationError(f"Failed to connect to CalDAV: {e}")

    def fetch_events(self, start_date: date, end_date: date) -> List[CalendarEventDTO]:
        """
        Fetch events from CalDAV calendar within date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of CalendarEventDTO objects

        Raises:
            AuthenticationError: If credentials are invalid
            NetworkError: If unable to reach CalDAV server
        """
        if not self._calendar:
            raise AuthenticationError("CalDAV calendar not initialized")

        try:
            # Convert dates to datetime for CalDAV query
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            # Fetch events from CalDAV server
            events_result = self._calendar.date_search(
                start=start_datetime, end=end_datetime, expand=True
            )

            events = []
            for caldav_event in events_result:
                try:
                    # Parse iCalendar data
                    ical_data = caldav_event.data
                    cal = ICalendar.from_ical(ical_data)

                    # Extract VEVENT components and expand recurring events
                    for component in cal.walk():
                        if component.name == "VEVENT":
                            # Use recurring_ical_events to expand recurring events
                            event_instances = of(cal).between(start_datetime, end_datetime)

                            for event_instance in event_instances:
                                try:
                                    event_dto = self._parse_event(
                                        event_instance, component, caldav_event.id
                                    )
                                    events.append(event_dto)
                                except Exception as e:
                                    logger.warning(f"Failed to parse event instance: {e}")
                                    continue

                except Exception as e:
                    logger.warning(f"Failed to parse CalDAV event {caldav_event.id}: {e}")
                    continue

            self._last_sync_time = datetime.now(timezone.utc)
            logger.info(f"Fetched {len(events)} events from CalDAV calendar")

            return events

        except caldav.lib.error.AuthorizationError as e:
            raise AuthenticationError(f"CalDAV authentication failed: {e}")
        except caldav.lib.error.NotFoundError as e:
            raise CalendarSourceError(f"Calendar not found: {e}")
        except Exception as e:
            raise NetworkError(f"Failed to fetch CalDAV events: {e}")

    def _parse_event(
        self, event_instance: Event, component: Event, caldav_id: str
    ) -> CalendarEventDTO:
        """
        Parse iCalendar event to CalendarEventDTO.

        Args:
            event_instance: Event instance (possibly from recurring series)
            component: Original VEVENT component
            caldav_id: CalDAV event ID

        Returns:
            CalendarEventDTO
        """
        # Get start and end times
        dtstart = event_instance.get("DTSTART").dt
        dtend = event_instance.get("DTEND")

        # Handle missing DTEND (use DURATION or default to start time)
        if dtend:
            dtend = dtend.dt
        else:
            duration = event_instance.get("DURATION")
            if duration:
                dtend = dtstart + duration.dt
            else:
                dtend = dtstart + timedelta(hours=1)  # Default 1 hour

        # Check if all-day event (date vs datetime)
        is_all_day = isinstance(dtstart, date) and not isinstance(dtstart, datetime)

        # Convert to datetime with timezone if needed
        if is_all_day:
            start_datetime = datetime.combine(dtstart, datetime.min.time(), timezone.utc)
            end_datetime = datetime.combine(dtend, datetime.min.time(), timezone.utc)
        else:
            # Ensure timezone-aware
            if dtstart.tzinfo is None:
                start_datetime = dtstart.replace(tzinfo=timezone.utc)
            else:
                start_datetime = dtstart

            if dtend.tzinfo is None:
                end_datetime = dtend.replace(tzinfo=timezone.utc)
            else:
                end_datetime = dtend

        # Extract event details
        summary = str(event_instance.get("SUMMARY", "(No title)"))
        location = event_instance.get("LOCATION")
        description = event_instance.get("DESCRIPTION")

        # Check if recurring
        is_recurring = component.get("RRULE") is not None
        recurrence_id = str(component.get("UID")) if is_recurring else None

        # Generate unique ID for this instance
        instance_id = caldav_id
        if is_recurring:
            # Append start time to UID for recurring event instances
            instance_id = f"{caldav_id}_{start_datetime.isoformat()}"

        return CalendarEventDTO(
            id=instance_id,
            calendar_source_id=self._config.source_id,
            title=summary,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            is_all_day=is_all_day,
            location=str(location) if location else None,
            description=str(description) if description else None,
            is_recurring=is_recurring,
            recurrence_id=recurrence_id,
        )

    def test_connection(self) -> bool:
        """
        Test connection to CalDAV server without fetching events.

        Returns:
            True if connection successful, False otherwise
        """
        if not self._calendar:
            return False

        try:
            # Try to get calendar properties (lightweight check)
            props = self._calendar.get_properties([caldav.dav.DisplayName()])
            logger.info(f"Connection test successful: {props}")
            return True
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return False

    def refresh_auth(self) -> None:
        """
        Refresh authentication (reconnect for CalDAV).

        Raises:
            AuthenticationError: If reconnection fails
        """
        try:
            self._connect()
            logger.info(f"CalDAV connection refreshed for {self._config.source_id}")
        except Exception as e:
            raise AuthenticationError(f"Failed to refresh CalDAV connection: {e}")

    def get_source_info(self) -> dict:
        """
        Get metadata about this CalDAV source.

        Returns:
            dict with source information
        """
        calendar_name = self._config.calendar_id

        # Try to fetch calendar display name
        if self._calendar:
            try:
                props = self._calendar.get_properties([caldav.dav.DisplayName()])
                display_name = props.get("{DAV:}displayname")
                if display_name:
                    calendar_name = str(display_name)
            except Exception:
                pass

        return {
            "source_id": self._config.source_id,
            "source_type": "caldav",
            "calendar_name": calendar_name,
            "last_sync_time": self._last_sync_time,
            "is_authenticated": self._calendar is not None,
        }
