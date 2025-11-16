"""Test display command - display test pattern on e-paper."""

from PIL import Image, ImageDraw

from kalendar.cli.app_factory import create_application


def test_display_command(args) -> int:
    """Execute test-display command.

    Args:
        args: Parsed command-line arguments

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    print("Kalendar - Display Hardware Test")
    print("=" * 50)

    try:
        # Create application
        app = create_application(
            config_path=args.config,
            use_simulator=args.simulator,
        )

        driver = app.deps.display_driver
        caps = driver.get_capabilities()

        print(f"\nDisplay specifications:")
        print(f"  Resolution: {caps['resolution'][0]}x{caps['resolution'][1]}")
        print(f"  Colors: {', '.join(caps['colors'])}")
        print(f"  Refresh time: ~{caps['refresh_time_seconds']}s")

        if args.simulator:
            print(f"\nMode: SIMULATOR (output will be saved to output/)")
        else:
            print(f"\nMode: HARDWARE")
            print(f"\nWARNING: This will refresh the e-paper display (~30 seconds)")
            response = input("Continue? [y/N]: ")
            if response.lower() != 'y':
                print("Cancelled")
                return 0

        # Create test pattern
        print("\nGenerating test pattern...")

        width, height = driver.get_resolution()
        test_image = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(test_image)

        # Title
        draw.text((20, 20), "Kalendar Display Test", fill=(0, 0, 0))

        # Black stripes
        for x in range(0, width, 200):
            draw.rectangle([x, 100, x + 80, height - 100], fill=(0, 0, 0))

        # Red stripes
        for x in range(100, width, 200):
            draw.rectangle([x, 100, x + 80, height - 100], fill=(255, 0, 0))

        # Grid lines
        for i in range(0, width, 100):
            draw.line([(i, 0), (i, height)], fill=(128, 128, 128), width=1)
        for i in range(0, height, 60):
            draw.line([(0, i), (width, i)], fill=(128, 128, 128), width=1)

        # Display test pattern
        print("Updating display...")
        app.update_display.execute(test_image)

        print("\nTest pattern displayed successfully!")

        if args.simulator:
            print("Output saved to: output/latest.png")

        return 0

    except Exception as e:
        print(f"\nError: Display test failed")
        print(f"  {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        return 1
