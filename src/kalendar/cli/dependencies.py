"""Dependency injection container for wiring infrastructure implementations.

This module creates and wires together all infrastructure implementations
based on configuration, following Clean Architecture dependency inversion.
"""

from pathlib import Path
from typing import Optional

from typing import List

from kalendar.domain.interfaces.ICache import ICache
from kalendar.domain.interfaces.ICalendarSource import ICalendarSource, CalendarSourceConfig
from kalendar.domain.interfaces.IConfigLoader import IConfigLoader
from kalendar.domain.interfaces.IDisplayDriver import IDisplayDriver
from kalendar.domain.interfaces.IImageRenderer import IImageRenderer
from kalendar.domain.models.config import DisplayConfiguration
from kalendar.domain.models.source import CalendarSource
from kalendar.domain.models.enums import SourceType
from kalendar.infrastructure.calendar.google_calendar_source import GoogleCalendarSource
from kalendar.infrastructure.calendar.caldav_source import CalDAVSource
from kalendar.infrastructure.display.simulator_driver import SimulatorDisplayDriver
from kalendar.infrastructure.display.waveshare_driver import WaveshareEPD75BDriver
from kalendar.infrastructure.rendering.weasyprint_renderer import WeasyPrintRenderer
from kalendar.infrastructure.storage.filesystem_cache import FileSystemCache
from kalendar.infrastructure.storage.yaml_config_loader import YAMLConfigLoader


class Dependencies:
    """Dependency injection container.

    Creates and manages infrastructure implementations based on configuration.
    Follows Clean Architecture: domain depends on interfaces, infrastructure
    implements those interfaces.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        use_simulator: bool = False,
        cache_dir: Optional[str] = None,
    ):
        """Initialize dependencies.

        Args:
            config_path: Path to configuration file (default: config/config.yaml)
            use_simulator: Use simulator display instead of hardware
            cache_dir: Cache directory (default: /var/cache/kalendar)
        """
        self.config_path = config_path or "config/config.yaml"
        self.use_simulator = use_simulator
        self.cache_dir = Path(cache_dir or "/var/cache/kalendar")

        # Lazy-loaded components
        self._config_loader: Optional[IConfigLoader] = None
        self._config: Optional[DisplayConfiguration] = None
        self._cache: Optional[ICache] = None
        self._renderer: Optional[IImageRenderer] = None
        self._display_driver: Optional[IDisplayDriver] = None

    @property
    def config_loader(self) -> IConfigLoader:
        """Get configuration loader.

        Returns:
            YAML configuration loader implementation
        """
        if self._config_loader is None:
            self._config_loader = YAMLConfigLoader()
        return self._config_loader

    @property
    def config(self) -> DisplayConfiguration:
        """Get configuration.

        Returns:
            Loaded and validated display configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if self._config is None:
            self._config = self.config_loader.load_config(self.config_path)
        return self._config

    @property
    def cache(self) -> ICache:
        """Get event cache.

        Returns:
            Filesystem cache implementation
        """
        if self._cache is None:
            self._cache = FileSystemCache(cache_dir=str(self.cache_dir))
        return self._cache

    @property
    def renderer(self) -> IImageRenderer:
        """Get image renderer.

        Returns:
            WeasyPrint HTML renderer implementation
        """
        if self._renderer is None:
            template_dir = Path("src/kalendar/presentation/templates")
            self._renderer = WeasyPrintRenderer(template_dir=str(template_dir))
        return self._renderer

    @property
    def display_driver(self) -> IDisplayDriver:
        """Get display driver.

        Returns:
            Display driver implementation (simulator or hardware based on config)
        """
        if self._display_driver is None:
            if self.use_simulator:
                self._display_driver = SimulatorDisplayDriver(output_dir="output")
            else:
                # Try hardware driver, fall back to simulator
                try:
                    self._display_driver = WaveshareEPD75BDriver()
                except Exception:
                    print(
                        "Warning: Hardware display not available, using simulator mode"
                    )
                    self._display_driver = SimulatorDisplayDriver(output_dir="output")

        return self._display_driver

    def create_calendar_source(self, source_config: CalendarSource) -> ICalendarSource:
        """Create ICalendarSource implementation from CalendarSource configuration.

        Args:
            source_config: CalendarSource domain model with configuration

        Returns:
            ICalendarSource implementation (GoogleCalendarSource, CalDAVSource, or MockCalendarSource)

        Raises:
            ValueError: If source_type is unknown
        """
        # Convert CalendarSource to CalendarSourceConfig
        config = CalendarSourceConfig(
            source_id=source_config.id,
            source_type=source_config.source_type.value,
            calendar_id=source_config.calendar_id,
            credentials=source_config.credentials or {},
        )

        # Factory pattern: create appropriate implementation
        if source_config.source_type == SourceType.GOOGLE:
            return GoogleCalendarSource(config)
        elif source_config.source_type == SourceType.CALDAV:
            return CalDAVSource(config)
        elif source_config.source_type == SourceType.MOCK:
            # Import MockCalendarSource from test fixtures
            from tests.fixtures.mock_calendar_source import MockCalendarSource
            return MockCalendarSource(config)
        else:
            raise ValueError(f"Unknown source type: {source_config.source_type}")

    def get_calendar_sources(self) -> List[ICalendarSource]:
        """Get all enabled calendar source implementations.

        Returns:
            List of ICalendarSource implementations for all enabled sources
        """
        source_configs = self.config.get_enabled_sources()
        return [self.create_calendar_source(config) for config in source_configs]

    def reset(self) -> None:
        """Reset all cached dependencies (useful for testing)."""
        self._config_loader = None
        self._config = None
        self._cache = None
        self._renderer = None
        self._display_driver = None
