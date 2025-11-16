"""Main CLI entry point for Kalendar.

Provides command-line interface for:
- Manual calendar refresh
- Display testing
- Calendar sync testing
- OAuth authentication
- CalDAV discovery
"""

import argparse
import sys


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="kalendar",
        description="Multi-calendar e-paper display for Raspberry Pi",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kalendar refresh                           # Refresh display with calendars
  kalendar refresh --simulator               # Refresh in simulator mode
  kalendar test-display                      # Test display with pattern
  kalendar test-sync                         # Test calendar connectivity
  kalendar auth google --credentials creds.json  # Authorize Google Calendar
  kalendar discover-caldav --username you@icloud.com  # Find iCloud CalDAV URLs
  kalendar discover-caldav --username you@gmail.com --service icloud  # Gmail-based Apple ID
  kalendar discover-caldav --username you@gmail.com --service gmail   # Google Calendar CalDAV

For more information, see: docs/configuration.md
        """,
    )

    # Global arguments
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # refresh command
    refresh_parser = subparsers.add_parser(
        "refresh",
        help="Refresh calendar display",
        description="Sync calendars and update e-paper display",
    )
    refresh_parser.add_argument(
        "--simulator",
        action="store_true",
        help="Use simulator mode (save to output/ instead of hardware)",
    )
    refresh_parser.add_argument(
        "--cache-dir",
        type=str,
        help="Cache directory (default: /var/cache/kalendar)",
    )

    # test-display command
    test_display_parser = subparsers.add_parser(
        "test-display",
        help="Test e-paper display",
        description="Display test pattern on e-paper hardware",
    )
    test_display_parser.add_argument(
        "--simulator",
        action="store_true",
        help="Use simulator mode",
    )

    # test-sync command
    test_sync_parser = subparsers.add_parser(
        "test-sync",
        help="Test calendar synchronization",
        description="Test connectivity to all configured calendar sources",
    )
    test_sync_parser.add_argument(
        "--cache-dir",
        type=str,
        help="Cache directory (default: /var/cache/kalendar)",
    )

    # auth command
    auth_parser = subparsers.add_parser(
        "auth",
        help="Authorize calendar access",
        description="Run OAuth authorization flow for calendar services",
    )
    auth_parser.add_argument(
        "service",
        choices=["google"],
        help="Service to authorize (currently only 'google' supported)",
    )
    auth_parser.add_argument(
        "--credentials",
        type=str,
        required=True,
        help="Path to credentials JSON file from Google Cloud Console",
    )

    # discover-caldav command
    discover_parser = subparsers.add_parser(
        "discover-caldav",
        help="Discover CalDAV calendar URLs",
        description="Find calendar URLs for iCloud, Nextcloud, etc.",
    )
    discover_parser.add_argument(
        "--username",
        type=str,
        required=True,
        help="CalDAV username (usually email address)",
    )
    discover_parser.add_argument(
        "--password",
        type=str,
        help="App-specific password (will prompt if not provided)",
    )
    discover_parser.add_argument(
        "--service",
        type=str,
        choices=["icloud", "gmail", "nextcloud"],
        help="CalDAV service provider (icloud, gmail, or nextcloud)",
    )
    discover_parser.add_argument(
        "--server",
        type=str,
        help=(
            "CalDAV server URL (overrides --service, "
            "auto-detected for iCloud emails if not provided)"
        ),
    )

    # Parse arguments
    args = parser.parse_args()

    # Show help if no command
    if not args.command:
        parser.print_help()
        return 0

    # Set verbosity
    if args.verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)

    # Execute command
    try:
        if args.command == "refresh":
            from kalendar.cli.commands.refresh import refresh_command
            return refresh_command(args)

        elif args.command == "test-display":
            from kalendar.cli.commands.test_display import test_display_command
            return test_display_command(args)

        elif args.command == "test-sync":
            from kalendar.cli.commands.test_sync import test_sync_command
            return test_sync_command(args)

        elif args.command == "auth":
            from kalendar.cli.commands.auth import auth_command
            return auth_command(args)

        elif args.command == "discover-caldav":
            from kalendar.cli.commands.discover_caldav import discover_caldav_command
            return discover_caldav_command(args)

        else:
            print(f"Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
