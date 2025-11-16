"""Refresh command - sync calendars and update display."""

import sys
from datetime import datetime

from kalendar.cli.app_factory import create_application


def refresh_command(args) -> int:
    """Execute refresh command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print("Kalendar - Refreshing calendar display")
    print("=" * 50)

    try:
        # Create application with dependencies
        app = create_application(
            config_path=args.config,
            use_simulator=args.simulator,
            cache_dir=args.cache_dir,
        )

        # Display configuration summary
        config = app.deps.config
        print(f"\nConfiguration:")
        print(f"  Timezone: {config.timezone}")
        print(f"  Week starts: {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][config.week_start_day]}")
        print(f"  Refresh hour: {config.refresh_hour}:00")
        print(f"  Max daily events: {config.max_daily_events}")

        enabled_sources = config.get_enabled_sources()
        print(f"\nEnabled calendar sources ({len(enabled_sources)}):")
        for source in enabled_sources:
            print(f"  - {source.name} ({source.source_type.value})")

        if args.simulator:
            print(f"\nMode: SIMULATOR (output will be saved to output/)")
        else:
            print(f"\nMode: HARDWARE")

        # Step 1: Sync calendars
        print("\n" + "=" * 50)
        print("Step 1: Syncing calendars...")
        print("=" * 50)

        sync_result = app.sync_calendars.execute()

        print(f"\nSync completed:")
        print(f"  Events fetched: {len(sync_result.events)}")
        print(f"  Sources synced: {len([r for r in sync_result.source_results.values() if r.status.value == 'success'])}/{len(sync_result.source_results)}")

        if sync_result.errors:
            print(f"\n  Warnings/Errors:")
            for error in sync_result.errors:
                print(f"    - {error}")

        # Step 2: Render calendar view
        print("\n" + "=" * 50)
        print("Step 2: Rendering calendar view...")
        print("=" * 50)

        now = datetime.now()
        calendar_image = app.render_monthly_view.execute(
            events=sync_result.events,
            year=now.year,
            month=now.month,
            today=now.date(),
        )

        print(f"\nRendered calendar image:")
        print(f"  Size: {calendar_image.size[0]}x{calendar_image.size[1]} pixels")
        print(f"  Mode: {calendar_image.mode}")

        # Step 3: Update display
        print("\n" + "=" * 50)
        print("Step 3: Updating display...")
        print("=" * 50)

        app.update_display.execute(calendar_image)

        print("\nDisplay updated successfully!")

        if args.simulator:
            print("\nOutput saved to: output/latest.png")
            print("View the rendered calendar with: open output/latest.png")

        # Summary
        print("\n" + "=" * 50)
        print("Refresh complete!")
        print("=" * 50)
        print(f"  Total events: {len(sync_result.events)}")
        print(f"  Display updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return 0

    except FileNotFoundError as e:
        print(f"\nError: Configuration file not found")
        print(f"  {e}")
        print(f"\nPlease create a configuration file:")
        print(f"  cp config/example.config.yaml {args.config}")
        print(f"  # Edit {args.config} with your calendar sources")
        return 1

    except ValueError as e:
        print(f"\nError: Invalid configuration")
        print(f"  {e}")
        print(f"\nPlease check your configuration file: {args.config}")
        print(f"See docs/configuration.md for help")
        return 1

    except Exception as e:
        print(f"\nError: Refresh failed")
        print(f"  {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
