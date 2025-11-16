"""
Image Post-Processor for E-Paper Display.

Splits RGB images into separate black and red layers
for Waveshare 7.5" 3-color e-paper display.
"""

from typing import Tuple
import logging
from PIL import Image

logger = logging.getLogger(__name__)


class ImagePostProcessor:
    """
    Post-process rendered images for e-paper display.

    Purpose:
        Split RGB image into two 1-bit (binary) images:
        - Black layer: Contains pixels that should be black
        - Red layer: Contains pixels that should be red

    E-Paper Display Format:
        Waveshare 7.5B uses two buffers:
        - Black buffer: 0 = black pixel, 255 = white pixel
        - Red buffer: 0 = red pixel, 255 = white pixel

    Color Detection:
        - Red: RGB values where R > 200 and G < 100 and B < 100
        - Black: RGB values where R+G+B < 100
        - White: Everything else
    """

    # Color thresholds for detection
    RED_THRESHOLD_R = 200
    RED_THRESHOLD_GB = 100
    BLACK_THRESHOLD_TOTAL = 100

    def split_layers(self, rgb_image: Image.Image) -> Tuple[Image.Image, Image.Image]:
        """
        Split RGB image into black and red layers.

        Args:
            rgb_image: Source RGB image (800x480)

        Returns:
            Tuple of (black_layer, red_layer) as 1-bit images
            - black_layer: 0=black pixel, 255=white pixel
            - red_layer: 0=red pixel, 255=white pixel
        """
        if rgb_image.mode != "RGB":
            logger.warning(f"Converting image from {rgb_image.mode} to RGB")
            rgb_image = rgb_image.convert("RGB")

        width, height = rgb_image.size
        logger.info(f"Splitting {width}x{height} RGB image into black/red layers")

        # Create 1-bit output images (initialized to white = 255)
        black_layer = Image.new("1", (width, height), 255)
        red_layer = Image.new("1", (width, height), 255)

        # Get pixel access objects
        rgb_pixels = rgb_image.load()
        black_pixels = black_layer.load()
        red_pixels = red_layer.load()

        # Process each pixel
        red_count = 0
        black_count = 0

        for y in range(height):
            for x in range(width):
                r, g, b = rgb_pixels[x, y]

                # Check if pixel is red
                if self._is_red(r, g, b):
                    red_pixels[x, y] = 0  # 0 = red pixel in red layer
                    black_pixels[x, y] = 255  # white in black layer
                    red_count += 1

                # Check if pixel is black
                elif self._is_black(r, g, b):
                    black_pixels[x, y] = 0  # 0 = black pixel in black layer
                    red_pixels[x, y] = 255  # white in red layer
                    black_count += 1

                # Otherwise it's white (already initialized to 255)

        logger.info(
            f"Layer separation complete: {black_count} black pixels, "
            f"{red_count} red pixels"
        )

        return black_layer, red_layer

    def _is_red(self, r: int, g: int, b: int) -> bool:
        """
        Check if RGB values represent red color.

        Args:
            r, g, b: RGB color values (0-255)

        Returns:
            True if pixel should be rendered as red
        """
        return r > self.RED_THRESHOLD_R and g < self.RED_THRESHOLD_GB and b < self.RED_THRESHOLD_GB

    def _is_black(self, r: int, g: int, b: int) -> bool:
        """
        Check if RGB values represent black color.

        Args:
            r, g, b: RGB color values (0-255)

        Returns:
            True if pixel should be rendered as black
        """
        return (r + g + b) < self.BLACK_THRESHOLD_TOTAL
