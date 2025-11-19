"""
Image Post-Processor for E-Paper Display.

Splits RGB images into separate black and red layers
for Waveshare 7.5" 3-color e-paper display.
"""

from typing import Tuple
import logging
import time
from PIL import Image, ImageFilter, ImageEnhance

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

        # Get raw RGB bytes using Pillow's tobytes() - fast C operation
        # Format: R1 G1 B1 R2 G2 B2 R3 G3 B3 ... (3 bytes per pixel)
        conversion_start = time.time()
        rgb_bytes = rgb_image.tobytes()

        # Create output byte arrays for black and red layers
        # Initialize all pixels to 255 (white)
        pixel_count = width * height
        black_bytes = bytearray(pixel_count)
        red_bytes = bytearray(pixel_count)

        # Initialize all to white (255)
        for i in range(pixel_count):
            black_bytes[i] = 255
            red_bytes[i] = 255

        # Process each pixel using byte offsets
        # Each pixel is 3 consecutive bytes: R, G, B
        red_count = 0
        black_count = 0

        for i in range(pixel_count):
            # Calculate byte offset for this pixel (3 bytes per pixel)
            byte_offset = i * 3
            r = rgb_bytes[byte_offset]
            g = rgb_bytes[byte_offset + 1]
            b = rgb_bytes[byte_offset + 2]

            # Check if pixel is red: R > 200 AND G < 100 AND B < 100
            if r > self.RED_THRESHOLD_R and g < self.RED_THRESHOLD_GB and b < self.RED_THRESHOLD_GB:
                red_bytes[i] = 0  # Red pixel in red layer
                black_bytes[i] = 255  # White in black layer
                red_count += 1

            # Check if pixel is black: R+G+B < 100
            elif (r + g + b) < self.BLACK_THRESHOLD_TOTAL:
                black_bytes[i] = 0  # Black pixel in black layer
                red_bytes[i] = 255  # White in red layer
                black_count += 1

            # Otherwise: white (already initialized to 255)

        # Convert byte arrays back to PIL images
        # frombytes() is a fast C operation
        black_layer = Image.frombytes('L', (width, height), bytes(black_bytes))
        red_layer = Image.frombytes('L', (width, height), bytes(red_bytes))

        # Convert to 1-bit images for e-paper display
        black_layer = black_layer.convert('1')
        red_layer = red_layer.convert('1')

        logger.debug(f"Layer conversion took {time.time() - conversion_start:.3f}s")

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
