"""UpdateDisplayUseCase: Update e-paper display with rendered calendar image.

This use case handles:
- Converting RGB calendar images to black/red layers for e-paper
- Initializing display hardware
- Updating the display
- Putting display to sleep for power saving
- Error handling per FR-014 (graceful degradation)
"""

from PIL import Image

from kalendar.domain.interfaces.IDisplayDriver import (
    DisplayHardwareError,
    IDisplayDriver,
)


class UpdateDisplayUseCase:
    """Use case for updating the e-paper display.

    This orchestrates the process of taking a rendered calendar image
    and displaying it on the e-paper hardware.
    """

    def __init__(self, display_driver: IDisplayDriver):
        """Initialize use case with display driver.

        Args:
            display_driver: Display driver implementation (hardware, simulator, or mock)
        """
        self.display_driver = display_driver

    def execute(self, rgb_image: Image.Image) -> None:
        """Update display with calendar image.

        Args:
            rgb_image: RGB image (800x480) with calendar rendered
                      - Black pixels (0, 0, 0) -> black on display
                      - Red pixels (255, 0, 0) -> red on display
                      - White pixels (255, 255, 255) -> white on display
                      - Other colors -> converted to nearest (black/red/white)

        Raises:
            ValueError: If image size doesn't match display resolution
            DisplayHardwareError: If display update fails
        """
        # Validate image size
        expected_resolution = self.display_driver.get_resolution()
        if rgb_image.size != expected_resolution:
            raise ValueError(
                f"Image size {rgb_image.size} doesn't match "
                f"display resolution {expected_resolution}. "
                f"Image must be exactly {expected_resolution[0]}x{expected_resolution[1]} pixels."
            )

        # Convert RGB to black/red layers
        black_layer, red_layer = self._rgb_to_bwr_layers(rgb_image)

        # Initialize display
        self.display_driver.initialize()

        # Update display
        try:
            self.display_driver.display(black_layer, red_layer)
        except DisplayHardwareError:
            # Re-raise hardware errors to caller
            raise
        finally:
            # Always try to sleep display for power saving
            try:
                self.display_driver.sleep()
            except Exception:
                # Ignore sleep errors - display may already be in error state
                pass

    def _rgb_to_bwr_layers(
        self, rgb_image: Image.Image
    ) -> tuple[Image.Image, Image.Image]:
        """Convert RGB image to black/white/red layers for e-paper.

        Args:
            rgb_image: RGB image to convert

        Returns:
            Tuple of (black_layer, red_layer) as 1-bit images
            - black_layer: 0 (black) for black pixels, 255 (white) elsewhere
            - red_layer: 0 (black) for red pixels, 255 (white) elsewhere
        """
        width, height = rgb_image.size

        # Create 1-bit images for black and red layers
        black_layer = Image.new("1", (width, height), 255)  # White background
        red_layer = Image.new("1", (width, height), 255)  # White background

        # Load pixel data
        rgb_pixels = rgb_image.load()
        black_pixels = black_layer.load()
        red_pixels = red_layer.load()

        # Convert each pixel
        for y in range(height):
            for x in range(width):
                r, g, b = rgb_pixels[x, y]

                # Determine color based on RGB values
                if self._is_black(r, g, b):
                    # Black pixel -> mark as black (0) in black layer
                    black_pixels[x, y] = 0
                elif self._is_red(r, g, b):
                    # Red pixel -> mark as black (0) in red layer
                    red_pixels[x, y] = 0
                # White pixels remain white (255) in both layers

        return black_layer, red_layer

    def _is_black(self, r: int, g: int, b: int) -> bool:
        """Determine if RGB values represent black.

        Args:
            r, g, b: RGB color values (0-255)

        Returns:
            True if color should be rendered as black
        """
        # Color is black if all components are dark (below threshold)
        threshold = 85  # Values below this are considered black
        return r < threshold and g < threshold and b < threshold

    def _is_red(self, r: int, g: int, b: int) -> bool:
        """Determine if RGB values represent red.

        Args:
            r, g, b: RGB color values (0-255)

        Returns:
            True if color should be rendered as red
        """
        # Color is red if:
        # - Red component is high
        # - Green and blue components are low
        red_threshold = 170  # Red must be at least this bright
        other_threshold = 85  # Green/blue must be below this

        return r >= red_threshold and g < other_threshold and b < other_threshold
