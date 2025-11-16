"""Simulator display driver for development without hardware.

Saves display output to PNG files in an output directory.
"""

from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

from kalendar.domain.interfaces.IDisplayDriver import (
    DisplayHardwareError,
    DisplayNotInitializedError,
    IDisplayDriver,
)


class SimulatorDisplayDriver(IDisplayDriver):
    """Display driver that simulates e-paper display by saving to files.

    This driver is used for development and testing without physical hardware.
    It creates RGB preview images showing how the display would appear.

    Output files:
        - {timestamp}_black.png: Black layer (1-bit)
        - {timestamp}_red.png: Red layer (1-bit)
        - {timestamp}_preview.png: RGB composite showing final appearance
        - latest.png: Symlink/copy of most recent preview
    """

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize simulator display driver.

        Args:
            output_dir: Directory to save output images
                       Default: output/ in project root
        """
        self.output_dir = Path(output_dir or "output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._initialized = False
        self._display_count = 0

        print(f"[Simulator] Output directory: {self.output_dir.absolute()}")

    def get_resolution(self) -> Tuple[int, int]:
        """Get display resolution.

        Returns:
            (800, 480) matching Waveshare 7.5" HAT (B)
        """
        return (800, 480)

    def initialize(self) -> None:
        """Initialize display."""
        self._initialized = True
        print("[Simulator] Display initialized")

    def display(self, black_image: Image.Image, red_image: Image.Image) -> None:
        """Save display images to files.

        Args:
            black_image: Black layer (mode '1')
            red_image: Red layer (mode '1')

        Raises:
            DisplayNotInitializedError: If not initialized
            ValueError: If image dimensions or mode incorrect
        """
        if not self._initialized:
            raise DisplayNotInitializedError("Display must be initialized before use")

        # Validate resolution
        expected_resolution = self.get_resolution()
        if black_image.size != expected_resolution:
            raise ValueError(
                f"Black image size {black_image.size} doesn't match "
                f"display resolution {expected_resolution}"
            )
        if red_image.size != expected_resolution:
            raise ValueError(
                f"Red image size {red_image.size} doesn't match "
                f"display resolution {expected_resolution}"
            )

        # Validate mode
        if black_image.mode != "1":
            raise ValueError(
                f"Black image must be mode '1' (1-bit), got '{black_image.mode}'"
            )
        if red_image.mode != "1":
            raise ValueError(
                f"Red image must be mode '1' (1-bit), got '{red_image.mode}'"
            )

        # Save images with timestamp
        self._display_count += 1
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        black_path = self.output_dir / f"{timestamp}_black.png"
        red_path = self.output_dir / f"{timestamp}_red.png"
        preview_path = self.output_dir / f"{timestamp}_preview.png"

        # Save individual layers
        black_image.save(black_path)
        red_image.save(red_path)

        # Create and save composite preview
        preview = self._create_composite_preview(black_image, red_image)
        preview.save(preview_path)

        # Create "latest" copy for easy access
        latest_path = self.output_dir / "latest.png"
        preview.save(latest_path)

        print(f"[Simulator] Display updated: {preview_path}")
        print(f"[Simulator] View at: {latest_path}")

    def _create_composite_preview(
        self, black_image: Image.Image, red_image: Image.Image
    ) -> Image.Image:
        """Create RGB preview showing how e-paper display would look.

        Args:
            black_image: Black layer (1-bit)
            red_image: Red layer (1-bit)

        Returns:
            RGB image showing composite result
        """
        width, height = self.get_resolution()
        preview = Image.new("RGB", (width, height), (255, 255, 255))  # White bg

        pixels = preview.load()
        black_pixels = black_image.load()
        red_pixels = red_image.load()

        for y in range(height):
            for x in range(width):
                # Black pixels (0) in black layer -> black
                if black_pixels[x, y] == 0:
                    pixels[x, y] = (0, 0, 0)
                # Black pixels (0) in red layer -> red
                elif red_pixels[x, y] == 0:
                    pixels[x, y] = (255, 0, 0)
                # Otherwise white (255, 255, 255)

        return preview

    def clear(self) -> None:
        """Clear display to all white."""
        if not self._initialized:
            raise DisplayNotInitializedError("Display must be initialized before use")

        width, height = self.get_resolution()
        white_image = Image.new("1", (width, height), 255)

        self.display(white_image, white_image)
        print("[Simulator] Display cleared")

    def sleep(self) -> None:
        """Put display to sleep (no-op for simulator)."""
        if not self._initialized:
            raise DisplayNotInitializedError("Display must be initialized before use")

        print("[Simulator] Display sleeping (no-op)")

    def get_capabilities(self) -> dict:
        """Get display capabilities.

        Returns:
            Dictionary with display specifications
        """
        return {
            "resolution": self.get_resolution(),
            "colors": ["black", "red", "white"],
            "refresh_time_seconds": 0.5,  # Simulated refresh time
            "min_refresh_interval_seconds": 0,  # No hardware limit
            "partial_refresh_supported": False,
        }
