"""
Google Calendar Source Implementation.

Uses google-api-python-client to fetch events from Google Calendar.
Implements ICalendarSource interface with OAuth 2.0 authentication.
"""

from datetime import date, datetime, timezone
from typing import List, Optional, Dict, Any
from pathlib import Path
import json
import logging

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.kalendar.domain.interfaces.ICalendarSource import (
    ICalendarSource,
    CalendarEventDTO,
    CalendarSourceConfig,
    CalendarSourceError,
    AuthenticationError,
    NetworkError,
    RateLimitError,
)

logger = logging.getLogger(__name__)


class GoogleCalendarSource(ICalendarSource):
    """
    Google Calendar implementation of ICalendarSource.

    Authentication:
        Uses OAuth 2.0 with token-based authentication.
        Requires initial authorization on desktop to generate token.json.
        Automatically refreshes expired tokens using refresh_token.

    Configuration:
        credentials["token_file"]: Path to token.json (contains access/refresh tokens)
        credentials["credentials_file"]: Path to credentials.json (OAuth client ID/secret)
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    def __init__(self, config: CalendarSourceConfig) -> None:
        """
        Initialize Google Calendar source.

        Args:
            config: CalendarSourceConfig with Google Calendar settings

        Raises:
            ValueError: If config is missing required credentials
        """
        self._config = config
        self._credentials: Optional[Credentials] = None
        self._service: Optional[Any] = None
        self._last_sync_time: Optional[datetime] = None

        # Validate configuration
        if "token_file" not in config.credentials:
            raise ValueError("Google Calendar config missing 'token_file' in credentials")

        self._token_file = Path(config.credentials["token_file"])
        self._credentials_file = None
        if "credentials_file" in config.credentials:
            self._credentials_file = Path(config.credentials["credentials_file"])

        # Load credentials on initialization
        self._load_credentials()

    def _load_credentials(self) -> None:
        """
        Load credentials from token file.

        If token is expired and refresh_token exists, automatically refresh.
        """
        if not self._token_file.exists():
            logger.warning(f"Token file not found: {self._token_file}")
            return

        try:
            self._credentials = Credentials.from_authorized_user_file(
                str(self._token_file), self.SCOPES
            )

            # Refresh if expired
            if self._credentials and self._credentials.expired and self._credentials.refresh_token:
                self._credentials.refresh(Request())
                self._save_credentials()

            # Build service
            if self._credentials and self._credentials.valid:
                self._service = build("calendar", "v3", credentials=self._credentials)
                logger.info(f"Google Calendar service initialized for {self._config.source_id}")

        except Exception as e:
            logger.error(f"Failed to load Google credentials: {e}")
            raise AuthenticationError(f"Failed to load credentials: {e}")

    def _save_credentials(self) -> None:
        """Save credentials to token file after refresh."""
        if self._credentials:
            with open(self._token_file, "w") as token:
                token.write(self._credentials.to_json())

    def fetch_events(self, start_date: date, end_date: date) -> List[CalendarEventDTO]:
        """
        Fetch events from Google Calendar within date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of CalendarEventDTO objects

        Raises:
            AuthenticationError: If credentials are invalid/expired
            NetworkError: If unable to reach Google Calendar API
            RateLimitError: If API rate limit is exceeded
        """
        if not self._service:
            raise AuthenticationError("Google Calendar service not initialized")

        # Convert dates to RFC3339 timestamps
        time_min = datetime.combine(start_date, datetime.min.time(), timezone.utc).isoformat()
        time_max = datetime.combine(end_date, datetime.max.time(), timezone.utc).isoformat()

        try:
            events_result = (
                self._service.events()
                .list(
                    calendarId=self._config.calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=2500,  # Google Calendar API max per page
                    singleEvents=True,  # Expand recurring events
                    orderBy="startTime",
                )
                .execute()
            )

            items = events_result.get("items", [])
            events = []

            for item in items:
                try:
                    event_dto = self._parse_event(item)
                    events.append(event_dto)
                except Exception as e:
                    logger.warning(f"Failed to parse event {item.get('id')}: {e}")
                    continue

            self._last_sync_time = datetime.now(timezone.utc)
            logger.info(
                f"Fetched {len(events)} events from Google Calendar {self._config.calendar_id}"
            )

            return events

        except HttpError as e:
            if e.resp.status == 401:
                raise AuthenticationError(f"Authentication failed: {e}")
            elif e.resp.status == 403:
                raise AuthenticationError(f"Access forbidden: {e}")
            elif e.resp.status == 429:
                # Extract retry-after header if available
                retry_after = int(e.resp.get("retry-after", 60))
                raise RateLimitError(f"Rate limit exceeded: {e}", retry_after)
            elif e.resp.status >= 500:
                raise NetworkError(f"Google Calendar API error: {e}")
            else:
                raise CalendarSourceError(f"Google Calendar API error: {e}")
        except Exception as e:
            raise NetworkError(f"Failed to fetch events: {e}")

    def _parse_event(self, item: Dict[str, Any]) -> CalendarEventDTO:
        """
        Parse Google Calendar API event to CalendarEventDTO.

        Args:
            item: Event data from Google Calendar API

        Returns:
            CalendarEventDTO
        """
        # Parse start/end datetime
        start = item.get("start", {})
        end = item.get("end", {})

        # All-day events use 'date' field, timed events use 'dateTime'
        is_all_day = "date" in start

        if is_all_day:
            start_datetime = datetime.fromisoformat(start["date"]).replace(tzinfo=timezone.utc)
            end_datetime = datetime.fromisoformat(end["date"]).replace(tzinfo=timezone.utc)
        else:
            start_datetime = datetime.fromisoformat(start["dateTime"])
            end_datetime = datetime.fromisoformat(end["dateTime"])

        # Extract recurrence info
        is_recurring = "recurringEventId" in item
        recurrence_id = item.get("recurringEventId")

        return CalendarEventDTO(
            id=item["id"],
            calendar_source_id=self._config.source_id,
            title=item.get("summary", "(No title)"),
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            is_all_day=is_all_day,
            location=item.get("location"),
            description=item.get("description"),
            is_recurring=is_recurring,
            recurrence_id=recurrence_id,
        )

    def test_connection(self) -> bool:
        """
        Test connection to Google Calendar without fetching events.

        Returns:
            True if connection successful, False otherwise
        """
        if not self._service:
            return False

        try:
            # Try to fetch calendar metadata (lightweight check)
            calendar = self._service.calendars().get(calendarId=self._config.calendar_id).execute()
            logger.info(f"Connection test successful: {calendar.get('summary')}")
            return True
        except Exception as e:
            logger.warning(f"Connection test failed: {e}")
            return False

    def refresh_auth(self) -> None:
        """
        Refresh OAuth token using refresh_token.

        Raises:
            AuthenticationError: If refresh fails
        """
        if not self._credentials:
            raise AuthenticationError("No credentials loaded")

        if not self._credentials.refresh_token:
            raise AuthenticationError("No refresh token available")

        try:
            self._credentials.refresh(Request())
            self._save_credentials()

            # Rebuild service with new credentials
            self._service = build("calendar", "v3", credentials=self._credentials)
            logger.info(f"Token refreshed for {self._config.source_id}")

        except Exception as e:
            raise AuthenticationError(f"Failed to refresh token: {e}")

    def get_source_info(self) -> dict:
        """
        Get metadata about this Google Calendar source.

        Returns:
            dict with source information
        """
        calendar_name = self._config.calendar_id

        # Try to fetch calendar display name
        if self._service:
            try:
                calendar = (
                    self._service.calendars().get(calendarId=self._config.calendar_id).execute()
                )
                calendar_name = calendar.get("summary", self._config.calendar_id)
            except Exception:
                pass

        return {
            "source_id": self._config.source_id,
            "source_type": "google",
            "calendar_name": calendar_name,
            "last_sync_time": self._last_sync_time,
            "is_authenticated": self._credentials is not None and self._credentials.valid,
        }
