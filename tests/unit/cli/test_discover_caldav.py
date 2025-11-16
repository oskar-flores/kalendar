"""Unit tests for discover-caldav command.

Tests the --service parameter and server URL detection logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace
import sys


class TestDiscoverCalDAVService:
    """Test --service parameter for CalDAV provider detection."""

    def _create_mock_caldav(self):
        """Create a mock caldav module with client."""
        mock_caldav = MagicMock()
        mock_client = MagicMock()
        mock_principal = MagicMock()
        mock_calendar = MagicMock()
        mock_calendar.name = "Test Calendar"
        mock_calendar.url = "https://caldav.icloud.com/12345/calendars/test/"
        mock_principal.calendars.return_value = [mock_calendar]
        mock_client.principal.return_value = mock_principal
        mock_caldav.DAVClient.return_value = mock_client
        return mock_caldav

    @patch('kalendar.cli.commands.discover_caldav.getpass.getpass')
    def test_service_icloud_with_gmail_username(self, mock_getpass):
        """Gmail Apple ID with --service icloud should use iCloud server."""
        # Arrange
        mock_getpass.return_value = "test-password"
        mock_caldav = self._create_mock_caldav()

        # Mock the import statement
        with patch.dict('sys.modules', {'caldav': mock_caldav}):
            from kalendar.cli.commands.discover_caldav import discover_caldav_command

            args = Namespace(
                username="someone@gmail.com",
                password=None,
                server=None,
                service="icloud",
                verbose=False
            )

            # Act
            result = discover_caldav_command(args)

            # Assert
            assert result == 0
            mock_caldav.DAVClient.assert_called_once_with(
                url="https://caldav.icloud.com/",
                username="someone@gmail.com",
                password="test-password"
            )

    @patch('kalendar.cli.commands.discover_caldav.getpass.getpass')
    def test_service_gmail_uses_google_server(self, mock_getpass):
        """--service gmail should use Google CalDAV server."""
        # Arrange
        mock_getpass.return_value = "test-password"
        mock_caldav = self._create_mock_caldav()
        mock_calendar = MagicMock()
        mock_calendar.name = "Test Calendar"
        mock_calendar.url = "https://caldav.google.com/user/calendars/test/"
        mock_principal = MagicMock()
        mock_principal.calendars.return_value = [mock_calendar]
        mock_client = MagicMock()
        mock_client.principal.return_value = mock_principal
        mock_caldav.DAVClient.return_value = mock_client

        # Mock the import statement
        with patch.dict('sys.modules', {'caldav': mock_caldav}):
            from kalendar.cli.commands.discover_caldav import discover_caldav_command

            args = Namespace(
                username="user@gmail.com",
                password=None,
                server=None,
                service="gmail",
                verbose=False
            )

            # Act
            result = discover_caldav_command(args)

            # Assert
            assert result == 0
            mock_caldav.DAVClient.assert_called_once_with(
                url="https://caldav.google.com/",
                username="user@gmail.com",
                password="test-password"
            )

    @patch('kalendar.cli.commands.discover_caldav.getpass.getpass')
    def test_auto_detect_icloud_still_works(self, mock_getpass):
        """iCloud emails should still auto-detect without --service."""
        # Arrange
        mock_getpass.return_value = "test-password"
        mock_caldav = self._create_mock_caldav()

        # Mock the import statement
        with patch.dict('sys.modules', {'caldav': mock_caldav}):
            from kalendar.cli.commands.discover_caldav import discover_caldav_command

            args = Namespace(
                username="user@icloud.com",
                password=None,
                server=None,
                service=None,
                verbose=False
            )

            # Act
            result = discover_caldav_command(args)

            # Assert
            assert result == 0
            mock_caldav.DAVClient.assert_called_once_with(
                url="https://caldav.icloud.com/",
                username="user@icloud.com",
                password="test-password"
            )

    def test_gmail_without_service_or_server_fails(self, capsys):
        """Gmail email without --service or --server should require one."""
        # Arrange
        from kalendar.cli.commands.discover_caldav import discover_caldav_command

        args = Namespace(
            username="user@gmail.com",
            password="test-password",
            server=None,
            service=None,
            verbose=False
        )

        # Act
        result = discover_caldav_command(args)

        # Assert
        assert result == 1
        captured = capsys.readouterr()
        assert "must be specified" in captured.out or "Error" in captured.out

    @patch('kalendar.cli.commands.discover_caldav.getpass.getpass')
    def test_server_parameter_overrides_service(self, mock_getpass):
        """Explicit --server should override --service."""
        # Arrange
        mock_getpass.return_value = "test-password"
        mock_caldav = MagicMock()
        mock_client = MagicMock()
        mock_principal = MagicMock()
        mock_calendar = MagicMock()
        mock_calendar.name = "Test Calendar"
        mock_calendar.url = "https://custom.server.com/calendars/test/"
        mock_principal.calendars.return_value = [mock_calendar]
        mock_client.principal.return_value = mock_principal
        mock_caldav.DAVClient.return_value = mock_client

        # Mock the import statement
        with patch.dict('sys.modules', {'caldav': mock_caldav}):
            from kalendar.cli.commands.discover_caldav import discover_caldav_command

            args = Namespace(
                username="user@gmail.com",
                password=None,
                server="https://custom.server.com/",
                service="icloud",  # Should be overridden by --server
                verbose=False
            )

            # Act
            result = discover_caldav_command(args)

            # Assert
            assert result == 0
            mock_caldav.DAVClient.assert_called_once_with(
                url="https://custom.server.com/",
                username="user@gmail.com",
                password="test-password"
            )

    def test_service_nextcloud_uses_generic_message(self, capsys):
        """--service nextcloud should inform user to provide --server."""
        # Arrange
        from kalendar.cli.commands.discover_caldav import discover_caldav_command

        args = Namespace(
            username="user@example.com",
            password="test-password",
            server=None,
            service="nextcloud",
            verbose=False
        )

        # Act
        result = discover_caldav_command(args)

        # Assert
        # Nextcloud requires explicit server URL since each instance is different
        assert result == 1
        captured = capsys.readouterr()
        assert "server" in captured.out.lower() or "nextcloud" in captured.out.lower()
