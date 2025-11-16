"""
Interface: Configuration Loader

Abstraction for loading application configuration.
Enables testing with different config sources.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path


class IConfigLoader(ABC):
    """
    Interface for configuration loading.

    Implementations:
    - YAMLConfigLoader (reads from /etc/kalendar/config.yaml)
    - JSONConfigLoader (alternative format)
    - InMemoryConfigLoader (for testing)
    - EnvironmentConfigLoader (reads from environment variables)

    Configuration structure defined in data-model.md:
    - refresh_hour
    - timezone
    - week_start_day
    - calendar_sources[]
    - display settings
    """

    @abstractmethod
    def load_config(self, config_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Load configuration from source.

        Args:
            config_path: Optional path to config file
                        If None, use default location (/etc/kalendar/config.yaml)

        Returns:
            Dictionary containing all configuration values

        Raises:
            ConfigNotFoundError: If config file doesn't exist
            ConfigParseError: If config file is malformed
            ConfigValidationError: If config values are invalid
        """
        pass

    @abstractmethod
    def save_config(
        self,
        config: Dict[str, Any],
        config_path: Optional[Path] = None,
    ) -> None:
        """
        Save configuration to persistent storage.

        Args:
            config: Configuration dictionary
            config_path: Optional path to config file

        Raises:
            ConfigWriteError: If save operation fails
            ConfigValidationError: If config values are invalid
        """
        pass

    @abstractmethod
    def get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            Dictionary with safe defaults:
                - refresh_hour: 0
                - timezone: "UTC"
                - week_start_day: 0 (Monday)
                - calendar_sources: []
                - max_daily_events: 5
                - layout: "horizontal"
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration values.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if valid

        Raises:
            ConfigValidationError: If validation fails (with details)
        """
        pass

    @abstractmethod
    def load_credentials(
        self,
        credentials_path: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Load authentication credentials separately from config.

        Args:
            credentials_path: Optional path to credentials file
                            If None, use default (/etc/kalendar/credentials.json)

        Returns:
            Dictionary with credential data for each calendar source

        Raises:
            ConfigNotFoundError: If credentials file doesn't exist
            ConfigParseError: If credentials file is malformed

        Note:
            Credentials stored separately for security (chmod 600)
        """
        pass


class ConfigError(Exception):
    """Base exception for configuration errors."""

    pass


class ConfigNotFoundError(ConfigError):
    """Raised when configuration file is not found."""

    pass


class ConfigParseError(ConfigError):
    """Raised when configuration file cannot be parsed."""

    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration values fail validation."""

    def __init__(self, message: str, errors: Dict[str, str]):
        super().__init__(message)
        self.errors = errors  # Map of field -> error message
