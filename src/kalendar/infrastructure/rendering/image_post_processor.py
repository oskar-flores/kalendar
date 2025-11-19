"""
Image Post-Processor for E-Paper Display.

Splits RGB images into separate black and red layers
for Waveshare 7.5" 3-color e-paper display.
"""

from typing import Tuple
import logging
import time
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np

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
        start_time = time.time()

        if rgb_image.mode != "RGB":
            logger.warning(f"Converting image from {rgb_image.mode} to RGB")
            rgb_image = rgb_image.convert("RGB")

        # Apply sharpening before color threshold conversion
        # This helps preserve text edges for e-ink display
        logger.info("Applying sharpening filter for e-ink optimization")
        sharpen_start = time.time()
        sharpener = ImageEnhance.Sharpness(rgb_image)
        rgb_image = sharpener.enhance(1.5)  # 1.5x sharpening
        rgb_image = rgb_image.filter(ImageFilter.SHARPEN)
        logger.debug(f"Sharpening took {time.time() - sharpen_start:.3f}s")

        width, height = rgb_image.size
        logger.info(f"Splitting {width}x{height} RGB image into black/red layers")

        # Convert PIL image to NumPy array for vectorized operations (much faster)
        # Shape: (height, width, 3) with RGB values 0-255
        conversion_start = time.time()
        rgb_array = np.array(rgb_image)

        # Extract individual color channels
        r = rgb_array[:, :, 0]
        g = rgb_array[:, :, 1]
        b = rgb_array[:, :, 2]

        # Vectorized color detection (operates on entire arrays at once)
        # Red pixels: R > 200 AND G < 100 AND B < 100
        is_red = (r > self.RED_THRESHOLD_R) & (g < self.RED_THRESHOLD_GB) & (b < self.RED_THRESHOLD_GB)

        # Black pixels: R+G+B < 100
        is_black = ((r.astype(np.uint16) + g.astype(np.uint16) + b.astype(np.uint16)) < self.BLACK_THRESHOLD_TOTAL)

        # Create output arrays (initialized to white = 255)
        black_array = np.full((height, width), 255, dtype=np.uint8)
        red_array = np.full((height, width), 255, dtype=np.uint8)

        # Set pixel values based on color detection
        # Red pixels: 0 in red layer, 255 (white) in black layer
        red_array[is_red] = 0
        black_array[is_red] = 255

        # Black pixels: 0 in black layer, 255 (white) in red layer
        black_array[is_black] = 0
        red_array[is_black] = 255

        # Convert NumPy arrays back to PIL 1-bit images
        black_layer = Image.fromarray(black_array, mode='L').convert('1')
        red_layer = Image.fromarray(red_array, mode='L').convert('1')
        logger.debug(f"Vectorized layer conversion took {time.time() - conversion_start:.3f}s")

        # Count pixels for logging
        red_count = np.sum(is_red)
        black_count = np.sum(is_black)

        total_time = time.time() - start_time
        logger.info(
            f"Layer separation complete: {black_count} black pixels, "
            f"{red_count} red pixels (total: {total_time:.3f}s)"
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
