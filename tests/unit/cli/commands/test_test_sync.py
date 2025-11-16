"""Unit tests for test-sync command."""

from datetime import datetime, timezone
from unittest.mock import Mock, MagicMock, patch
from argparse import Namespace

import pytest

from kalendar.cli.commands.test_sync import test_sync_command


class TestTestSyncCommand:
    """Unit tests for test_sync_command function."""

    @pytest.fixture
    def mock_args(self):
        """Create mock command-line arguments."""
        args = Namespace()
        args.config = "config/test.yaml"
        args.verbose = False
        return args

    @pytest.fixture
    def mock_successful_sync_result(self):
        """Create a mock successful sync result."""
        result = Mock()
        result.events = [Mock(), Mock(), Mock()]  # 3 events
        result.source_results = {
            "source-1": Mock(
                status=Mock(value="success"),
                events_fetched=3,
                duration_seconds=1.23,
                error_message=None,
            )
        }
        return result

    @pytest.fixture
    def mock_failed_sync_result(self):
        """Create a mock failed sync result."""
        result = Mock()
        result.events = []
        result.source_results = {
            "source-1": Mock(
                status=Mock(value="failed"),
                events_fetched=0,
                duration_seconds=0.5,
                error_message="Authentication failed",
            )
        }
        return result

    @pytest.fixture
    def mock_mixed_sync_result(self):
        """Create a mock sync result with mixed success/failure."""
        result = Mock()
        result.events = [Mock(), Mock()]  # 2 events from successful source
        result.source_results = {
            "source-1": Mock(
                status=Mock(value="success"),
                events_fetched=2,
                duration_seconds=1.0,
                error_message=None,
            ),
            "source-2": Mock(
                status=Mock(value="failed"),
                events_fetched=0,
                duration_seconds=0.3,
                error_message="Network timeout",
            ),
        }
        return result

    @patch("kalendar.cli.commands.test_sync.create_application")
    def test_test_sync_with_successful_sources(
        self, mock_create_app, mock_args, mock_successful_sync_result, capsys
    ):
        """Test test_sync_command with all successful sources."""
        # Setup mock application
        mock_app = Mock()
        mock_source = Mock(
            id="source-1",
            name="Test Calendar",
            source_type=Mock(value="google"),
        )
        mock_app.deps.config.get_enabled_sources.return_value = [mock_source]
        mock_app.sync_calendars.execute.return_value = mock_successful_sync_result
        mock_create_app.return_value = mock_app

        # Execute
        exit_code = test_sync_command(mock_args)

        # Verify
        assert exit_code == 0
        mock_create_app.assert_called_once_with(config_path="config/test.yaml", cache_dir=None)
        mock_app.sync_calendars.execute.assert_called_once()

        # Check output
        captured = capsys.readouterr()
        assert "Test Calendar" in captured.out
        assert "SUCCESS" in captured.out
        assert "Events fetched: 3" in captured.out
        assert "All calendar sources synced successfully!" in captured.out

    @patch("kalendar.cli.commands.test_sync.create_application")
    def test_test_sync_with_failed_sources(
        self, mock_create_app, mock_args, mock_failed_sync_result, capsys
    ):
        """Test test_sync_command with failed sources."""
        # Setup mock application
        mock_app = Mock()
        mock_source = Mock(
            id="source-1",
            name="Broken Calendar",
            source_type=Mock(value="caldav"),
        )
        mock_app.deps.config.get_enabled_sources.return_value = [mock_source]
        mock_app.sync_calendars.execute.return_value = mock_failed_sync_result
        mock_create_app.return_value = mock_app

        # Execute
        exit_code = test_sync_command(mock_args)

        # Verify
        assert exit_code == 1
        mock_app.sync_calendars.execute.assert_called_once()

        # Check output
        captured = capsys.readouterr()
        assert "Broken Calendar" in captured.out
        assert "FAILED" in captured.out
        assert "Authentication failed" in captured.out
        assert "Some calendar sources failed to sync" in captured.out

    @patch("kalendar.cli.commands.test_sync.create_application")
    def test_test_sync_with_mixed_results(
        self, mock_create_app, mock_args, mock_mixed_sync_result, capsys
    ):
        """Test test_sync_command with partial success."""
        # Setup mock application
        mock_app = Mock()
        mock_sources = [
            Mock(
                id="source-1",
                name="Good Calendar",
                source_type=Mock(value="google"),
            ),
            Mock(
                id="source-2",
                name="Bad Calendar",
                source_type=Mock(value="caldav"),
            ),
        ]
        mock_app.deps.config.get_enabled_sources.return_value = mock_sources
        mock_app.sync_calendars.execute.return_value = mock_mixed_sync_result
        mock_create_app.return_value = mock_app

        # Execute
        exit_code = test_sync_command(mock_args)

        # Verify - should fail if ANY source fails
        assert exit_code == 1

        # Check output
        captured = capsys.readouterr()
        assert "Good Calendar" in captured.out
        assert "SUCCESS" in captured.out
        assert "Bad Calendar" in captured.out
        assert "FAILED" in captured.out
        assert "Network timeout" in captured.out

    @patch("kalendar.cli.commands.test_sync.create_application")
    def test_test_sync_output_format(
        self, mock_create_app, mock_args, mock_successful_sync_result, capsys
    ):
        """Test test_sync_command output formatting."""
        # Setup
        mock_app = Mock()
        # Create a proper mock with attributes set directly
        mock_source = Mock()
        mock_source.id = "source-1"
        mock_source.name = "My Calendar"
        mock_source.source_type = Mock()
        mock_source.source_type.value = "google"

        mock_app.deps.config.get_enabled_sources.return_value = [mock_source]
        mock_app.sync_calendars.execute.return_value = mock_successful_sync_result
        mock_create_app.return_value = mock_app

        # Execute
        test_sync_command(mock_args)

        # Check output format
        captured = capsys.readouterr()
        assert "Kalendar - Calendar Sync Test" in captured.out
        assert "=" * 50 in captured.out
        assert "Testing 1 calendar source(s)..." in captured.out
        assert "✓ My Calendar" in captured.out
        assert "Type: google" in captured.out
        assert "Duration:" in captured.out

    @patch("kalendar.cli.commands.test_sync.create_application")
    def test_test_sync_missing_config_file(self, mock_create_app, mock_args, capsys):
        """Test test_sync_command with missing config file."""
        # Setup - simulate FileNotFoundError
        mock_create_app.side_effect = FileNotFoundError("config/test.yaml not found")

        # Execute
        exit_code = test_sync_command(mock_args)

        # Verify
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Configuration file not found" in captured.out

    @patch("kalendar.cli.commands.test_sync.create_application")
    def test_test_sync_invalid_config(self, mock_create_app, mock_args, capsys):
        """Test test_sync_command with invalid config."""
        # Setup - simulate ValueError
        mock_create_app.side_effect = ValueError("Invalid YAML syntax")

        # Execute
        exit_code = test_sync_command(mock_args)

        # Verify
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid configuration" in captured.out

    @patch("kalendar.cli.commands.test_sync.create_application")
    def test_test_sync_unexpected_error(self, mock_create_app, mock_args, capsys):
        """Test test_sync_command with unexpected error."""
        # Setup - simulate generic exception
        mock_create_app.side_effect = RuntimeError("Unexpected error")

        # Execute
        exit_code = test_sync_command(mock_args)

        # Verify
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Sync test failed" in captured.out
        assert "Unexpected error" in captured.out

    @patch("kalendar.cli.commands.test_sync.create_application")
    def test_test_sync_verbose_mode(self, mock_create_app, mock_args, capsys):
        """Test test_sync_command with verbose flag shows traceback."""
        # Setup
        mock_args.verbose = True
        mock_create_app.side_effect = RuntimeError("Test error")

        # Execute
        exit_code = test_sync_command(mock_args)

        # Verify
        assert exit_code == 1
        captured = capsys.readouterr()
        # With verbose, should show traceback in stderr
        assert "Traceback" in captured.err or "RuntimeError" in captured.err

    @patch("kalendar.cli.commands.test_sync.create_application")
    def test_test_sync_custom_cache_dir(self, mock_create_app, mock_args, mock_successful_sync_result, capsys):
        """Test test_sync_command respects custom cache directory."""
        # Setup
        mock_args.cache_dir = "/tmp/custom-cache"
        mock_app = Mock()
        mock_source = Mock()
        mock_source.id = "source-1"
        mock_source.name = "Test Calendar"
        mock_source.source_type = Mock()
        mock_source.source_type.value = "google"

        mock_app.deps.config.get_enabled_sources.return_value = [mock_source]
        mock_app.sync_calendars.execute.return_value = mock_successful_sync_result
        mock_create_app.return_value = mock_app

        # Execute
        exit_code = test_sync_command(mock_args)

        # Verify
        assert exit_code == 0
        # Should have called create_application with cache_dir
        mock_create_app.assert_called_once_with(
            config_path="config/test.yaml",
            cache_dir="/tmp/custom-cache"
        )
