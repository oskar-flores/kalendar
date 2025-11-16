"""DisplayConfiguration domain model."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from kalendar.domain.models.enums import LayoutType
from kalendar.domain.models.source import CalendarSource


@dataclass
class DisplayConfiguration:
    """Represents user settings and preferences.

    Attributes:
        refresh_hour: Hour of day to refresh (0-23)
        timezone: IANA timezone (e.g., "America/New_York")
        week_start_day: Week start day (0=Monday, 6=Sunday)
        calendar_sources: List of enabled calendar sources
        display_layout: Orientation setting (HORIZONTAL or VERTICAL)
        max_daily_events: Max events in today's section
    """

    refresh_hour: int
    timezone: str
    week_start_day: int
    calendar_sources: list[CalendarSource]
    display_layout: LayoutType
    max_daily_events: int

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not 0 <= self.refresh_hour <= 23:
            raise ValueError("refresh_hour must be between 0 and 23")

        if not 0 <= self.week_start_day <= 6:
            raise ValueError("week_start_day must be between 0 and 6")

        if self.max_daily_events <= 0:
            raise ValueError("max_daily_events must be greater than 0")

        # Validate timezone is a valid IANA timezone
        try:
            ZoneInfo(self.timezone)
        except Exception:
            raise ValueError(
                f"timezone must be a valid IANA timezone, got: {self.timezone}"
            )

        # Validate at least one source is enabled
        if not any(source.enabled for source in self.calendar_sources):
            raise ValueError("At least one calendar source must be enabled")

    def get_enabled_sources(self) -> list[CalendarSource]:
        """Returns list of enabled calendar sources.

        Returns:
            List of CalendarSource objects with enabled=True
        """
        return [source for source in self.calendar_sources if source.enabled]

    def get_refresh_time_today(self) -> datetime:
        """Returns today's scheduled refresh time in configured timezone.

        Returns:
            datetime object for today's refresh time
        """
        tz = ZoneInfo(self.timezone)
        now = datetime.now(tz)
        return now.replace(hour=self.refresh_hour, minute=0, second=0, microsecond=0)

    def get_next_refresh_time(self) -> datetime:
        """Returns next scheduled refresh time.

        Returns:
            datetime object for next refresh (today or tomorrow)
        """
        refresh_today = self.get_refresh_time_today()
        if datetime.now(ZoneInfo(self.timezone)) > refresh_today:
            return refresh_today + timedelta(days=1)
        return refresh_today
