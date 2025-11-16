"""Test sync command - test calendar connectivity."""

from datetime import datetime, timedelta

from kalendar.cli.app_factory import create_application


def test_sync_command(args) -> int:
    """Execute test-sync command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print("Kalendar - Calendar Sync Test")
    print("=" * 50)

    try:
        # Create application
        cache_dir = getattr(args, 'cache_dir', None)
        app = create_application(config_path=args.config, cache_dir=cache_dir)

        config = app.deps.config
        enabled_sources = config.get_enabled_sources()

        print(f"\nTesting {len(enabled_sources)} calendar source(s)...")
        print()

        # Test sync
        sync_result = app.sync_calendars.execute()

        # Display results for each source
        all_success = True
        for source in enabled_sources:
            result = sync_result.source_results.get(source.id)

            if result and result.status.value == "success":
                print(f"✓ {source.name}")
                print(f"  Status: SUCCESS")
                print(f"  Type: {source.source_type.value}")
                print(f"  Events fetched: {result.events_fetched}")
                print(f"  Duration: {result.duration_seconds:.2f}s")
            else:
                all_success = False
                print(f"✗ {source.name}")
                print(f"  Status: FAILED")
                print(f"  Type: {source.source_type.value}")
                if result and result.error_message:
                    print(f"  Error: {result.error_message}")
            print()

        # Summary
        print("=" * 50)
        if all_success:
            print("All calendar sources synced successfully!")
            print(f"Total events: {len(sync_result.events)}")
            return 0
        else:
            print("Some calendar sources failed to sync")
            print("Check configuration and credentials")
            return 1

    except FileNotFoundError as e:
        print(f"\nError: Configuration file not found")
        print(f"  {e}")
        return 1

    except ValueError as e:
        print(f"\nError: Invalid configuration")
        print(f"  {e}")
        return 1

    except Exception as e:
        print(f"\nError: Sync test failed")
        print(f"  {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        return 1
