"""Mock display driver for testing.

Saves display output to files instead of physical hardware.
"""

from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

from kalendar.domain.interfaces.IDisplayDriver import (
    DisplayHardwareError,
    DisplayNotInitializedError,
    IDisplayDriver,
)


class MockDisplayDriver(IDisplayDriver):
    """Mock display driver that saves images to files for testing.

    This driver simulates display behavior without hardware:
    - Saves black and red buffers as separate PNG files
    - Tracks initialization state
    - Validates image dimensions and modes
    - Records display call history for test assertions
    """

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize mock display driver.

        Args:
            output_dir: Directory to save output images (default: /tmp/kalendar_mock)
        """
        self.output_dir = Path(output_dir or "/tmp/kalendar_mock")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self._initialized = False
        self._display_count = 0
        self._last_black_image: Optional[Image.Image] = None
        self._last_red_image: Optional[Image.Image] = None

    def get_resolution(self) -> Tuple[int, int]:
        """Get display resolution.

        Returns:
            (800, 480) matching Waveshare 7.5" HAT (B)
        """
        return (800, 480)

    def initialize(self) -> None:
        """Initialize display (no-op for mock)."""
        self._initialized = True

    def display(self, black_image: Image.Image, red_image: Image.Image) -> None:
        """Save images to files.

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

        # Save images
        self._display_count += 1
        black_path = self.output_dir / f"display_{self._display_count:03d}_black.png"
        red_path = self.output_dir / f"display_{self._display_count:03d}_red.png"

        black_image.save(black_path)
        red_image.save(red_path)

        # Store for test assertions
        self._last_black_image = black_image.copy()
        self._last_red_image = red_image.copy()

        # Create composite preview (for visual debugging)
        self._save_composite_preview(black_image, red_image)

    def _save_composite_preview(
        self, black_image: Image.Image, red_image: Image.Image
    ) -> None:
        """Create RGB preview showing how display would look.

        Args:
            black_image: Black layer
            red_image: Red layer
        """
        # Create RGB image
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
                # Otherwise white

        preview_path = self.output_dir / f"display_{self._display_count:03d}_preview.png"
        preview.save(preview_path)

    def clear(self) -> None:
        """Clear display (saves white images)."""
        if not self._initialized:
            raise DisplayNotInitializedError("Display must be initialized before use")

        width, height = self.get_resolution()
        white_image = Image.new("1", (width, height), 255)

        self.display(white_image, white_image)

    def sleep(self) -> None:
        """Put display to sleep (no-op for mock)."""
        if not self._initialized:
            raise DisplayNotInitializedError("Display must be initialized before use")
        # No-op for mock

    def get_capabilities(self) -> dict:
        """Get display capabilities.

        Returns:
            Dictionary with display specs
        """
        return {
            "resolution": self.get_resolution(),
            "colors": ["black", "red", "white"],
            "refresh_time_seconds": 0.1,  # Fast for testing
            "min_refresh_interval_seconds": 0,  # No limit for mock
            "partial_refresh_supported": False,
        }

    # Test helper methods

    def get_display_count(self) -> int:
        """Get number of times display() was called.

        Returns:
            Number of display() calls
        """
        return self._display_count

    def get_last_images(self) -> Tuple[Optional[Image.Image], Optional[Image.Image]]:
        """Get last displayed images.

        Returns:
            Tuple of (black_image, red_image) or (None, None) if never displayed
        """
        return (self._last_black_image, self._last_red_image)

    def is_initialized(self) -> bool:
        """Check if display is initialized.

        Returns:
            True if initialized
        """
        return self._initialized

    def reset(self) -> None:
        """Reset mock state (for test isolation)."""
        self._initialized = False
        self._display_count = 0
        self._last_black_image = None
        self._last_red_image = None
