"""Integration tests for CLI commands.

Tests CLI command execution and argument parsing.
"""

import subprocess
import sys
from pathlib import Path

import pytest


class TestCLICommands:
    """Integration tests for CLI commands."""

    @pytest.fixture
    def cli_path(self):
        """Get path to CLI entry point."""
        return Path("src/kalendar/cli/main.py")

    def test_cli_help(self, cli_path):
        """CLI shows help when run with no arguments."""
        result = subprocess.run(
            [sys.executable, str(cli_path)],
            capture_output=True,
            text=True,
        )

        assert "kalendar" in result.stdout.lower()
        assert "refresh" in result.stdout
        assert "test-display" in result.stdout
        assert "test-sync" in result.stdout

    def test_cli_version_info(self, cli_path):
        """CLI shows version/usage information."""
        result = subprocess.run(
            [sys.executable, str(cli_path), "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "kalendar" in result.stdout.lower()

    def test_refresh_command_help(self, cli_path):
        """Refresh command shows help."""
        result = subprocess.run(
            [sys.executable, str(cli_path), "refresh", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "refresh" in result.stdout.lower()
        assert "--simulator" in result.stdout

    def test_test_display_command_help(self, cli_path):
        """Test-display command shows help."""
        result = subprocess.run(
            [sys.executable, str(cli_path), "test-display", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "test-display" in result.stdout.lower() or "test pattern" in result.stdout.lower()

    def test_test_sync_command_help(self, cli_path):
        """Test-sync command shows help."""
        result = subprocess.run(
            [sys.executable, str(cli_path), "test-sync", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "sync" in result.stdout.lower()

    def test_auth_command_help(self, cli_path):
        """Auth command shows help."""
        result = subprocess.run(
            [sys.executable, str(cli_path), "auth", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "auth" in result.stdout.lower()

    def test_discover_caldav_command_help(self, cli_path):
        """Discover-caldav command shows help."""
        result = subprocess.run(
            [sys.executable, str(cli_path), "discover-caldav", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "caldav" in result.stdout.lower()

    def test_refresh_missing_config_fails_gracefully(self, cli_path, tmp_path):
        """Refresh fails gracefully when config file missing."""
        nonexistent_config = tmp_path / "nonexistent.yaml"

        result = subprocess.run(
            [
                sys.executable,
                str(cli_path),
                "--config",
                str(nonexistent_config),
                "refresh",
                "--simulator",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        # Error can be in stdout or stderr
        output = (result.stdout + result.stderr).lower()
        assert "not found" in output or "error" in output

    def test_invalid_command_fails(self, cli_path):
        """Invalid command shows error."""
        result = subprocess.run(
            [sys.executable, str(cli_path), "invalid-command"],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0

    @pytest.mark.slow
    def test_refresh_with_example_config_simulator(self, cli_path, tmp_path):
        """Refresh with example config in simulator mode (if config valid)."""
        # This test only runs if example config exists and is valid
        example_config = Path("config/example.config.yaml")
        if not example_config.exists():
            pytest.skip("Example config not found")

        result = subprocess.run(
            [
                sys.executable,
                str(cli_path),
                "refresh",
                "--config",
                str(example_config),
                "--simulator",
                "--cache-dir",
                str(tmp_path / "cache"),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # May fail due to missing credentials, but should not crash
        assert "error" in result.stdout.lower() or "success" in result.stdout.lower() or "refresh" in result.stdout.lower()

    def test_test_sync_command_with_no_sources(self, cli_path, tmp_path):
        """Test-sync command with no calendar sources configured."""
        # Create a test config file with no sources
        config_content = """
refresh_hour: 6
timezone: America/New_York
calendar_sources: []

cache:
  type: file
  file_cache_dir: {cache_dir}

display:
  driver: simulator
"""
        config_path = tmp_path / "test_config.yaml"
        config_path.write_text(config_content.format(cache_dir=str(tmp_path / "cache")))

        result = subprocess.run(
            [
                sys.executable,
                str(cli_path),
                "--config",
                str(config_path),
                "test-sync",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should succeed with exit code 0 (no sources to sync is not a failure)
        assert result.returncode == 0, f"Command failed with: {result.stderr}\n{result.stdout}"

        # Output should contain success message
        assert "Testing 0 calendar source" in result.stdout, f"Expected 0 sources in output: {result.stdout}"
        assert "All calendar sources synced successfully!" in result.stdout, f"Expected success message in output: {result.stdout}"
