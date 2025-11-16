"""Unit tests for CalDAV URL parsing and base URL extraction.

Tests that CalDAV source correctly extracts base URLs from various
calendar URL formats, especially iCloud URLs with specific servers.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from kalendar.domain.interfaces.ICalendarSource import CalendarSourceConfig
from kalendar.infrastructure.calendar.caldav_source import CalDAVSource


class TestCalDAVURLParsing:
    """Test CalDAV URL parsing for base URL extraction."""

    @pytest.fixture
    def mock_caldav_modules(self):
        """Mock caldav library modules to avoid actual network calls."""
        with patch('kalendar.infrastructure.calendar.caldav_source.DAVClient') as mock_client, \
             patch('kalendar.infrastructure.calendar.caldav_source.caldav') as mock_caldav:

            # Mock the Calendar class
            mock_calendar_instance = MagicMock()
            mock_caldav.Calendar.return_value = mock_calendar_instance

            # Mock the client instance
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            yield {
                'DAVClient': mock_client,
                'caldav': mock_caldav,
                'client_instance': mock_client_instance,
                'calendar_instance': mock_calendar_instance
            }

    def test_extract_base_url_from_icloud_with_specific_server(self, mock_caldav_modules):
        """iCloud URL with specific server (p42-caldav) should extract correct base URL."""
        config = CalendarSourceConfig(
            source_id="test-caldav",
            source_type="caldav",
            calendar_id="https://p42-caldav.icloud.com:443/297718975/calendars/2dd0d963-970b-45eb-b6f4-e3ff300a5132/",
            credentials={
                "username": "user@icloud.com",
                "app_password": "xxxx-xxxx-xxxx-xxxx"
            }
        )

        source = CalDAVSource(config)

        # Verify DAVClient was called with correct base URL
        mock_caldav_modules['DAVClient'].assert_called_once()
        call_args = mock_caldav_modules['DAVClient'].call_args

        assert call_args[1]['url'] == "https://p42-caldav.icloud.com:443/"
        assert call_args[1]['username'] == "user@icloud.com"
        assert call_args[1]['password'] == "xxxx-xxxx-xxxx-xxxx"

    def test_extract_base_url_from_icloud_standard(self, mock_caldav_modules):
        """Standard iCloud URL should extract caldav.icloud.com as base."""
        config = CalendarSourceConfig(
            source_id="test-caldav",
            source_type="caldav",
            calendar_id="https://caldav.icloud.com/12345/calendars/abcdef/",
            credentials={
                "username": "user@icloud.com",
                "app_password": "xxxx-xxxx-xxxx-xxxx"
            }
        )

        source = CalDAVSource(config)

        call_args = mock_caldav_modules['DAVClient'].call_args
        assert call_args[1]['url'] == "https://caldav.icloud.com/"

    def test_extract_base_url_with_port_number(self, mock_caldav_modules):
        """URL with port number should preserve port in base URL."""
        config = CalendarSourceConfig(
            source_id="test-caldav",
            source_type="caldav",
            calendar_id="https://p42-caldav.icloud.com:443/297718975/calendars/calendar-id/",
            credentials={
                "username": "user@icloud.com",
                "app_password": "xxxx-xxxx-xxxx-xxxx"
            }
        )

        source = CalDAVSource(config)

        call_args = mock_caldav_modules['DAVClient'].call_args
        assert call_args[1]['url'] == "https://p42-caldav.icloud.com:443/"

    def test_extract_base_url_from_nextcloud(self, mock_caldav_modules):
        """Nextcloud CalDAV URL should extract correct base URL."""
        config = CalendarSourceConfig(
            source_id="test-caldav",
            source_type="caldav",
            calendar_id="https://cloud.example.com:8443/remote.php/dav/calendars/user/personal/",
            credentials={
                "username": "nextcloud_user",
                "app_password": "app-password-123"
            }
        )

        source = CalDAVSource(config)

        call_args = mock_caldav_modules['DAVClient'].call_args
        assert call_args[1]['url'] == "https://cloud.example.com:8443/"

    def test_extract_base_url_without_port(self, mock_caldav_modules):
        """URL without explicit port should use default https (no :443)."""
        config = CalendarSourceConfig(
            source_id="test-caldav",
            source_type="caldav",
            calendar_id="https://caldav.example.com/calendars/user/calendar/",
            credentials={
                "username": "user@example.com",
                "app_password": "password123"
            }
        )

        source = CalDAVSource(config)

        call_args = mock_caldav_modules['DAVClient'].call_args
        assert call_args[1]['url'] == "https://caldav.example.com/"

    def test_extract_base_url_http_not_https(self, mock_caldav_modules):
        """HTTP URL (not HTTPS) should preserve http scheme."""
        config = CalendarSourceConfig(
            source_id="test-caldav",
            source_type="caldav",
            calendar_id="http://localhost:5232/user/calendar/",
            credentials={
                "username": "local_user",
                "app_password": "local_password"
            }
        )

        source = CalDAVSource(config)

        call_args = mock_caldav_modules['DAVClient'].call_args
        assert call_args[1]['url'] == "http://localhost:5232/"

    def test_calendar_initialized_with_full_url(self, mock_caldav_modules):
        """Calendar should be initialized with the full calendar URL."""
        full_calendar_url = "https://p42-caldav.icloud.com:443/297718975/calendars/2dd0d963-970b-45eb-b6f4-e3ff300a5132/"

        config = CalendarSourceConfig(
            source_id="test-caldav",
            source_type="caldav",
            calendar_id=full_calendar_url,
            credentials={
                "username": "user@icloud.com",
                "app_password": "xxxx-xxxx-xxxx-xxxx"
            }
        )

        source = CalDAVSource(config)

        # Verify Calendar was initialized with full URL
        mock_caldav_modules['caldav'].Calendar.assert_called_once()
        call_args = mock_caldav_modules['caldav'].Calendar.call_args

        assert call_args[1]['url'] == full_calendar_url
        assert call_args[1]['client'] == mock_caldav_modules['client_instance']

    def test_different_icloud_servers_get_correct_base_urls(self, mock_caldav_modules):
        """Different iCloud server numbers (p42, p69, etc.) should extract correctly."""
        test_servers = [
            ("https://p42-caldav.icloud.com:443/123/calendars/abc/", "https://p42-caldav.icloud.com:443/"),
            ("https://p69-caldav.icloud.com/456/calendars/def/", "https://p69-caldav.icloud.com/"),
            ("https://p01-caldav.icloud.com:443/789/calendars/ghi/", "https://p01-caldav.icloud.com:443/"),
        ]

        for calendar_url, expected_base_url in test_servers:
            # Reset mock
            mock_caldav_modules['DAVClient'].reset_mock()

            config = CalendarSourceConfig(
                source_id="test-caldav",
                source_type="caldav",
                calendar_id=calendar_url,
                credentials={
                    "username": "user@icloud.com",
                    "app_password": "xxxx-xxxx-xxxx-xxxx"
                }
            )

            source = CalDAVSource(config)

            call_args = mock_caldav_modules['DAVClient'].call_args
            assert call_args[1]['url'] == expected_base_url, \
                f"Calendar URL {calendar_url} should extract base URL {expected_base_url}"
