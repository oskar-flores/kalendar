"""YAML configuration loader implementation."""

from pathlib import Path
from typing import Any

import yaml

from kalendar.domain.models.config import DisplayConfiguration
from kalendar.domain.models.enums import LayoutType, SourceType
from kalendar.domain.models.source import CalendarSource


class YAMLConfigLoader:
    """Loads configuration from YAML files.

    Implements configuration loading, saving, and validation.
    """

    def load_config(self, config_path: str) -> DisplayConfiguration:
        """Load configuration from YAML file.

        Args:
            config_path: Path to YAML config file

        Returns:
            DisplayConfiguration object

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return self._parse_config(data)

    def save_config(self, config: DisplayConfiguration, config_path: str) -> None:
        """Save configuration to YAML file.

        Args:
            config: Configuration to save
            config_path: Path to save to
        """
        data = self._serialize_config(config)

        path = Path(config_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    def validate_config(self, config_path: str) -> bool:
        """Validate configuration file without loading fully.

        Args:
            config_path: Path to config file

        Returns:
            True if valid, False otherwise
        """
        try:
            self.load_config(config_path)
            return True
        except Exception:
            return False

    def load_credentials(self, credentials_path: str) -> dict[str, Any]:
        """Load credentials from separate file.

        Args:
            credentials_path: Path to credentials file

        Returns:
            Credentials dictionary

        Raises:
            FileNotFoundError: If credentials file doesn't exist
        """
        path = Path(credentials_path)
        if not path.exists():
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")

        with open(path) as f:
            return yaml.safe_load(f) or {}

    def _parse_config(self, data: dict[str, Any]) -> DisplayConfiguration:
        """Parse YAML data into DisplayConfiguration.

        Args:
            data: Raw YAML data

        Returns:
            DisplayConfiguration object
        """
        # Parse calendar sources
        sources: list[CalendarSource] = []
        for src_data in data.get("calendar_sources", []):
            source = CalendarSource(
                id=src_data["id"],
                name=src_data["name"],
                source_type=SourceType(src_data["source_type"]),
                calendar_id=src_data["calendar_id"],
                enabled=src_data.get("enabled", True),
                color=src_data.get("color"),
            )
            sources.append(source)

        # Parse display settings
        display = data.get("display", {})

        return DisplayConfiguration(
            refresh_hour=data["refresh_hour"],
            timezone=data["timezone"],
            week_start_day=data.get("week_start_day", 0),
            calendar_sources=sources,
            display_layout=LayoutType(display.get("layout", "horizontal")),
            max_daily_events=display.get("max_daily_events", 5),
        )

    def _serialize_config(self, config: DisplayConfiguration) -> dict[str, Any]:
        """Serialize DisplayConfiguration to dict.

        Args:
            config: Configuration to serialize

        Returns:
            Dictionary ready for YAML serialization
        """
        return {
            "refresh_hour": config.refresh_hour,
            "timezone": config.timezone,
            "week_start_day": config.week_start_day,
            "calendar_sources": [
                {
                    "id": src.id,
                    "name": src.name,
                    "source_type": src.source_type.value,
                    "calendar_id": src.calendar_id,
                    "enabled": src.enabled,
                    "color": src.color,
                }
                for src in config.calendar_sources
            ],
            "display": {
                "max_daily_events": config.max_daily_events,
                "layout": config.display_layout.value,
            },
        }
