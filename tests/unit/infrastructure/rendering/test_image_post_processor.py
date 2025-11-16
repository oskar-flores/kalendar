"""
Unit tests for ImagePostProcessor.

Purpose: Test RGB image splitting into black/red layers for e-paper display.
Following TDD - tests written FIRST.
"""

import pytest
from PIL import Image


class TestImagePostProcessor:
    """Test suite for ImagePostProcessor."""

    @pytest.fixture
    def test_image(self) -> Image.Image:
        """Create test RGB image with black, red, and white pixels."""
        img = Image.new("RGB", (100, 100), (255, 255, 255))  # White background
        pixels = img.load()

        # Draw some black pixels
        for x in range(10, 20):
            pixels[x, 10] = (0, 0, 0)  # Black

        # Draw some red pixels
        for x in range(30, 40):
            pixels[x, 10] = (255, 0, 0)  # Red

        return img

    def test_split_layers_returns_two_images(self, test_image: Image.Image) -> None:
        """split_layers should return black and red layer images."""
        from src.kalendar.infrastructure.rendering.image_post_processor import (
            ImagePostProcessor,
        )

        # Arrange
        processor = ImagePostProcessor()

        # Act
        black_layer, red_layer = processor.split_layers(test_image)

        # Assert
        assert isinstance(black_layer, Image.Image)
        assert isinstance(red_layer, Image.Image)

    def test_split_layers_preserves_dimensions(self, test_image: Image.Image) -> None:
        """split_layers should preserve image dimensions."""
        from src.kalendar.infrastructure.rendering.image_post_processor import (
            ImagePostProcessor,
        )

        # Arrange
        processor = ImagePostProcessor()

        # Act
        black_layer, red_layer = processor.split_layers(test_image)

        # Assert
        assert black_layer.size == test_image.size
        assert red_layer.size == test_image.size

    def test_split_layers_outputs_1bit_images(self, test_image: Image.Image) -> None:
        """split_layers should output 1-bit (binary) images."""
        from src.kalendar.infrastructure.rendering.image_post_processor import (
            ImagePostProcessor,
        )

        # Arrange
        processor = ImagePostProcessor()

        # Act
        black_layer, red_layer = processor.split_layers(test_image)

        # Assert
        assert black_layer.mode == "1"  # 1-bit image
        assert red_layer.mode == "1"

    def test_split_layers_separates_black_pixels(self, test_image: Image.Image) -> None:
        """split_layers should put black pixels in black layer."""
        from src.kalendar.infrastructure.rendering.image_post_processor import (
            ImagePostProcessor,
        )

        # Arrange
        processor = ImagePostProcessor()

        # Act
        black_layer, red_layer = processor.split_layers(test_image)

        # Assert
        # Black pixels (10-19, 10) should be in black layer (value 0 = black)
        black_pixels = black_layer.load()
        assert black_pixels[15, 10] == 0  # Black pixel

        # Red pixels (30-39, 10) should NOT be in black layer (value 255 = white)
        assert black_pixels[35, 10] == 255  # White pixel

    def test_split_layers_separates_red_pixels(self, test_image: Image.Image) -> None:
        """split_layers should put red pixels in red layer."""
        from src.kalendar.infrastructure.rendering.image_post_processor import (
            ImagePostProcessor,
        )

        # Arrange
        processor = ImagePostProcessor()

        # Act
        black_layer, red_layer = processor.split_layers(test_image)

        # Assert
        # Red pixels (30-39, 10) should be in red layer (value 0 = red)
        red_pixels = red_layer.load()
        assert red_pixels[35, 10] == 0  # Red pixel

        # Black pixels (10-19, 10) should NOT be in red layer (value 255 = white)
        assert red_pixels[15, 10] == 255  # White pixel

    def test_split_layers_handles_white_background(self, test_image: Image.Image) -> None:
        """split_layers should make white background white in both layers."""
        from src.kalendar.infrastructure.rendering.image_post_processor import (
            ImagePostProcessor,
        )

        # Arrange
        processor = ImagePostProcessor()

        # Act
        black_layer, red_layer = processor.split_layers(test_image)

        # Assert
        # White background (0, 0) should be white in both layers
        black_pixels = black_layer.load()
        red_pixels = red_layer.load()
        assert black_pixels[0, 0] == 255  # White
        assert red_pixels[0, 0] == 255  # White
