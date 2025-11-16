"""Unit tests for YAML config loader credentials loading.

Tests that credentials are loaded from separate credentials file
and merged into calendar sources based on source_type.
"""

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from kalendar.domain.models.enums import SourceType
from kalendar.infrastructure.storage.yaml_config_loader import YAMLConfigLoader


class TestCredentialsLoading:
    """Test loading credentials from separate file and merging into sources."""

    @pytest.fixture
    def loader(self):
        """Create YAML config loader."""
        return YAMLConfigLoader()

    @pytest.fixture
    def sample_credentials(self):
        """Sample credentials with both CalDAV and Google credentials."""
        return {
            "caldav": {
                "username": "user@icloud.com",
                "app_password": "xxxx-xxxx-xxxx-xxxx"
            },
            "google": {
                "token_file": "config/google_token.json",
                "credentials_file": "config/google_credentials.json"
            }
        }

    @pytest.fixture
    def config_with_caldav_source(self):
        """Config with CalDAV calendar source."""
        return {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "caldav-test",
                    "name": "Test CalDAV",
                    "source_type": "caldav",
                    "calendar_id": "https://caldav.icloud.com/123/calendars/456/",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

    @pytest.fixture
    def config_with_google_source(self):
        """Config with Google calendar source."""
        return {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "google-test",
                    "name": "Test Google",
                    "source_type": "google",
                    "calendar_id": "primary",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

    @pytest.fixture
    def config_with_mixed_sources(self):
        """Config with both CalDAV and Google sources."""
        return {
            "refresh_hour": 0,
            "timezone": "UTC",
            "week_start_day": 0,
            "calendar_sources": [
                {
                    "id": "caldav-family",
                    "name": "Family Calendar",
                    "source_type": "caldav",
                    "calendar_id": "https://caldav.icloud.com/123/calendars/456/",
                    "enabled": True,
                },
                {
                    "id": "google-work",
                    "name": "Work Calendar",
                    "source_type": "google",
                    "calendar_id": "work@gmail.com",
                    "enabled": True,
                },
                {
                    "id": "caldav-personal",
                    "name": "Personal Calendar",
                    "source_type": "caldav",
                    "calendar_id": "https://caldav.icloud.com/123/calendars/789/",
                    "enabled": True,
                }
            ],
            "display": {"max_daily_events": 5, "layout": "horizontal"},
        }

    def test_load_config_with_credentials_file_path(self, loader, config_with_caldav_source, sample_credentials):
        """Config with credentials_file path should load and merge credentials."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create credentials file
            credentials_path = Path(tmpdir) / "credentials.json"
            with open(credentials_path, "w") as f:
                json.dump(sample_credentials, f)

            # Create config file with credentials_file reference
            config_with_caldav_source["credentials_file"] = str(credentials_path)
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.safe_dump(config_with_caldav_source, f)

            # Load config
            config = loader.load_config(str(config_path))

            # Verify credentials were merged into CalDAV source
            assert len(config.calendar_sources) == 1
            caldav_source = config.calendar_sources[0]
            assert caldav_source.credentials is not None
            assert caldav_source.credentials["username"] == "user@icloud.com"
            assert caldav_source.credentials["app_password"] == "xxxx-xxxx-xxxx-xxxx"

    def test_caldav_source_gets_caldav_credentials(self, loader, config_with_caldav_source, sample_credentials):
        """CalDAV source should receive credentials from caldav section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            credentials_path = Path(tmpdir) / "credentials.json"
            with open(credentials_path, "w") as f:
                json.dump(sample_credentials, f)

            config_with_caldav_source["credentials_file"] = str(credentials_path)
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.safe_dump(config_with_caldav_source, f)

            config = loader.load_config(str(config_path))

            caldav_source = config.calendar_sources[0]
            assert caldav_source.source_type == SourceType.CALDAV
            assert caldav_source.credentials == sample_credentials["caldav"]

    def test_google_source_gets_google_credentials(self, loader, config_with_google_source, sample_credentials):
        """Google source should receive credentials from google section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            credentials_path = Path(tmpdir) / "credentials.json"
            with open(credentials_path, "w") as f:
                json.dump(sample_credentials, f)

            config_with_google_source["credentials_file"] = str(credentials_path)
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.safe_dump(config_with_google_source, f)

            config = loader.load_config(str(config_path))

            google_source = config.calendar_sources[0]
            assert google_source.source_type == SourceType.GOOGLE
            assert google_source.credentials == sample_credentials["google"]

    def test_mixed_sources_get_correct_credentials(self, loader, config_with_mixed_sources, sample_credentials):
        """Multiple sources should each get their correct credentials."""
        with tempfile.TemporaryDirectory() as tmpdir:
            credentials_path = Path(tmpdir) / "credentials.json"
            with open(credentials_path, "w") as f:
                json.dump(sample_credentials, f)

            config_with_mixed_sources["credentials_file"] = str(credentials_path)
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.safe_dump(config_with_mixed_sources, f)

            config = loader.load_config(str(config_path))

            assert len(config.calendar_sources) == 3

            # First source: CalDAV
            caldav_family = config.calendar_sources[0]
            assert caldav_family.id == "caldav-family"
            assert caldav_family.source_type == SourceType.CALDAV
            assert caldav_family.credentials == sample_credentials["caldav"]

            # Second source: Google
            google_work = config.calendar_sources[1]
            assert google_work.id == "google-work"
            assert google_work.source_type == SourceType.GOOGLE
            assert google_work.credentials == sample_credentials["google"]

            # Third source: CalDAV (should get same caldav credentials)
            caldav_personal = config.calendar_sources[2]
            assert caldav_personal.id == "caldav-personal"
            assert caldav_personal.source_type == SourceType.CALDAV
            assert caldav_personal.credentials == sample_credentials["caldav"]

    def test_config_without_credentials_file_has_none_credentials(self, loader, config_with_caldav_source):
        """Config without credentials_file should set credentials to None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't add credentials_file to config
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.safe_dump(config_with_caldav_source, f)

            config = loader.load_config(str(config_path))

            caldav_source = config.calendar_sources[0]
            assert caldav_source.credentials is None

    def test_missing_credentials_file_raises_error(self, loader, config_with_caldav_source):
        """Config with non-existent credentials_file should raise FileNotFoundError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Reference non-existent credentials file
            config_with_caldav_source["credentials_file"] = "/nonexistent/credentials.json"
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.safe_dump(config_with_caldav_source, f)

            with pytest.raises(FileNotFoundError, match="Credentials file not found"):
                loader.load_config(str(config_path))

    def test_credentials_missing_source_type_sets_none(self, loader, config_with_caldav_source):
        """If credentials don't have section for source_type, set credentials to None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Credentials file with only google, no caldav
            credentials = {
                "google": {
                    "token_file": "config/google_token.json",
                    "credentials_file": "config/google_credentials.json"
                }
            }
            credentials_path = Path(tmpdir) / "credentials.json"
            with open(credentials_path, "w") as f:
                json.dump(credentials, f)

            config_with_caldav_source["credentials_file"] = str(credentials_path)
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.safe_dump(config_with_caldav_source, f)

            config = loader.load_config(str(config_path))

            # CalDAV source should have None credentials since caldav section is missing
            caldav_source = config.calendar_sources[0]
            assert caldav_source.credentials is None

    def test_empty_credentials_file(self, loader, config_with_caldav_source):
        """Empty credentials file should set all source credentials to None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Empty credentials file
            credentials_path = Path(tmpdir) / "credentials.json"
            with open(credentials_path, "w") as f:
                json.dump({}, f)

            config_with_caldav_source["credentials_file"] = str(credentials_path)
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.safe_dump(config_with_caldav_source, f)

            config = loader.load_config(str(config_path))

            caldav_source = config.calendar_sources[0]
            assert caldav_source.credentials is None

    def test_disabled_source_still_gets_credentials(self, loader, sample_credentials):
        """Disabled sources should still receive credentials (they just won't be used)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                "refresh_hour": 0,
                "timezone": "UTC",
                "week_start_day": 0,
                "calendar_sources": [
                    {
                        "id": "caldav-enabled",
                        "name": "Enabled CalDAV",
                        "source_type": "caldav",
                        "calendar_id": "https://caldav.icloud.com/123/calendars/abc/",
                        "enabled": True,
                    },
                    {
                        "id": "caldav-disabled",
                        "name": "Disabled CalDAV",
                        "source_type": "caldav",
                        "calendar_id": "https://caldav.icloud.com/123/calendars/456/",
                        "enabled": False,  # Disabled
                    }
                ],
                "display": {"max_daily_events": 5, "layout": "horizontal"},
            }

            credentials_path = Path(tmpdir) / "credentials.json"
            with open(credentials_path, "w") as f:
                json.dump(sample_credentials, f)

            config["credentials_file"] = str(credentials_path)
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, "w") as f:
                yaml.safe_dump(config, f)

            loaded_config = loader.load_config(str(config_path))

            # Find the disabled source
            disabled_source = [s for s in loaded_config.calendar_sources if s.id == "caldav-disabled"][0]
            assert disabled_source.enabled is False
            assert disabled_source.credentials == sample_credentials["caldav"]
