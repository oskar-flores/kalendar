"""Discover CalDAV command - find calendar URLs."""

import getpass


def discover_caldav_command(args) -> int:
    """Execute discover-caldav command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print("Kalendar - CalDAV Calendar Discovery")
    print("=" * 50)

    try:
        # Import CalDAV library
        import caldav

        # Get password if not provided
        password = args.password
        if not password:
            password = getpass.getpass(f"Password for {args.username}: ")

        # Determine server URL
        server_url = args.server
        if not server_url:
            # Auto-detect iCloud
            if "icloud.com" in args.username.lower():
                server_url = "https://caldav.icloud.com/"
                print(f"\nAuto-detected iCloud CalDAV server")
            else:
                print("\nError: --server must be specified for non-iCloud accounts")
                print("Example: --server https://cloud.example.com/remote.php/dav/")
                return 1

        print(f"\nConnecting to: {server_url}")
        print(f"Username: {args.username}")
        print()

        # Connect to CalDAV server
        client = caldav.DAVClient(
            url=server_url,
            username=args.username,
            password=password,
        )

        principal = client.principal()
        calendars = principal.calendars()

        if not calendars:
            print("No calendars found")
            return 1

        print(f"Found {len(calendars)} calendar(s):\n")

        for i, calendar in enumerate(calendars, 1):
            name = calendar.name or "Unnamed Calendar"
            url = str(calendar.url)

            print(f"{i}. {name}")
            print(f"   URL: {url}")
            print()

        # Show configuration example
        print("=" * 50)
        print("Add to your config/config.yaml:")
        print("=" * 50)
        print()
        print("calendar_sources:")

        for calendar in calendars:
            name = calendar.name or "Unnamed Calendar"
            url = str(calendar.url)
            # Create safe ID from name
            safe_id = name.lower().replace(" ", "-").replace("'", "")

            print(f'  - id: "caldav-{safe_id}"')
            print(f'    name: "{name}"')
            print(f'    source_type: "caldav"')
            print(f'    calendar_id: "{url}"')
            print(f'    enabled: true')
            print()

        print("And add to your config/credentials.json:")
        print()
        print("{")
        print('  "caldav": {')
        print(f'    "username": "{args.username}",')
        print(f'    "app_password": "xxxx-xxxx-xxxx-xxxx"')
        print("  }")
        print("}")

        return 0

    except ImportError:
        print("\nError: CalDAV library not installed")
        print("Install with: uv add caldav")
        return 1

    except Exception as e:
        print(f"\nError: CalDAV discovery failed")
        print(f"  {e}")

        if "401" in str(e) or "Unauthorized" in str(e):
            print("\nAuthentication failed. Please check:")
            print("  - Username is correct")
            print("  - Using app-specific password (not regular password)")
            print("  - For iCloud: Generate at https://appleid.apple.com/")

        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()

        return 1
