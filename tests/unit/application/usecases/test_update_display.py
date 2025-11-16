"""Unit tests for UpdateDisplayUseCase.

Tests the use case that updates the e-paper display with rendered calendar image.
"""

import pytest
from PIL import Image
from unittest.mock import Mock

from kalendar.domain.interfaces.IDisplayDriver import DisplayHardwareError
from tests.fixtures.mock_display_driver import MockDisplayDriver


class TestUpdateDisplayUseCase:
    """Test UpdateDisplayUseCase functionality."""

    @pytest.fixture
    def mock_display(self):
        """Provide mock display driver."""
        return MockDisplayDriver(output_dir="/tmp/kalendar_test_update_display")

    @pytest.fixture
    def use_case(self, mock_display):
        """Provide UpdateDisplayUseCase with mock display."""
        # Import here to avoid circular dependencies during test discovery
        from kalendar.application.usecases.update_display import UpdateDisplayUseCase
        return UpdateDisplayUseCase(display_driver=mock_display)

    def test_update_display_with_rgb_image(self, use_case, mock_display):
        """update_display() converts RGB image to black/red layers and displays."""
        # Arrange
        width, height = 800, 480
        rgb_image = Image.new("RGB", (width, height), (255, 255, 255))

        from PIL import ImageDraw
        draw = ImageDraw.Draw(rgb_image)
        # Draw black rectangle
        draw.rectangle([10, 10, 100, 100], fill=(0, 0, 0))
        # Draw red rectangle
        draw.rectangle([110, 10, 200, 100], fill=(255, 0, 0))

        # Act
        use_case.execute(rgb_image)

        # Assert
        assert mock_display.is_initialized()
        assert mock_display.get_display_count() == 1

        black_img, red_img = mock_display.get_last_images()
        assert black_img is not None
        assert red_img is not None
        assert black_img.size == (width, height)
        assert red_img.size == (width, height)

    def test_update_display_initializes_driver(self, use_case, mock_display):
        """update_display() initializes driver before use."""
        # Arrange
        rgb_image = Image.new("RGB", (800, 480), (255, 255, 255))

        # Act
        use_case.execute(rgb_image)

        # Assert
        assert mock_display.is_initialized()

    def test_update_display_puts_driver_to_sleep(self, use_case, mock_display):
        """update_display() puts driver to sleep after display."""
        # Arrange
        rgb_image = Image.new("RGB", (800, 480), (255, 255, 255))
        mock_display.sleep_called = False

        # Monkey patch to track sleep call
        original_sleep = mock_display.sleep
        def track_sleep():
            mock_display.sleep_called = True
            original_sleep()
        mock_display.sleep = track_sleep

        # Act
        use_case.execute(rgb_image)

        # Assert
        assert mock_display.sleep_called

    def test_update_display_converts_black_pixels_correctly(self, use_case, mock_display):
        """Black pixels in RGB image become black in black layer."""
        # Arrange
        rgb_image = Image.new("RGB", (800, 480), (255, 255, 255))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(rgb_image)
        draw.rectangle([0, 0, 50, 50], fill=(0, 0, 0))  # Black

        # Act
        use_case.execute(rgb_image)

        # Assert
        black_img, _ = mock_display.get_last_images()
        pixels = black_img.load()
        # Black pixel should be 0 in black layer
        assert pixels[25, 25] == 0

    def test_update_display_converts_red_pixels_correctly(self, use_case, mock_display):
        """Red pixels in RGB image become black in red layer."""
        # Arrange
        rgb_image = Image.new("RGB", (800, 480), (255, 255, 255))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(rgb_image)
        draw.rectangle([100, 100, 150, 150], fill=(255, 0, 0))  # Red

        # Act
        use_case.execute(rgb_image)

        # Assert
        _, red_img = mock_display.get_last_images()
        pixels = red_img.load()
        # Red pixel should be 0 in red layer
        assert pixels[125, 125] == 0

    def test_update_display_converts_white_pixels_correctly(self, use_case, mock_display):
        """White pixels in RGB image stay white in both layers."""
        # Arrange
        rgb_image = Image.new("RGB", (800, 480), (255, 255, 255))

        # Act
        use_case.execute(rgb_image)

        # Assert
        black_img, red_img = mock_display.get_last_images()
        black_pixels = black_img.load()
        red_pixels = red_img.load()
        # White pixel should be 255 in both layers
        assert black_pixels[400, 240] == 255
        assert red_pixels[400, 240] == 255

    def test_update_display_with_wrong_size_raises_error(self, use_case):
        """update_display() with wrong image size raises ValueError."""
        # Arrange
        wrong_size_image = Image.new("RGB", (640, 480), (255, 255, 255))

        # Act & Assert
        with pytest.raises(ValueError, match="size|resolution|dimension"):
            use_case.execute(wrong_size_image)

    def test_update_display_handles_hardware_errors_gracefully(self, mock_display):
        """update_display() handles display errors gracefully."""
        # Arrange
        from kalendar.application.usecases.update_display import UpdateDisplayUseCase

        # Create mock that raises error on display
        failing_display = Mock(spec=MockDisplayDriver)
        failing_display.get_resolution.return_value = (800, 480)
        failing_display.display.side_effect = DisplayHardwareError("Hardware failed")

        use_case = UpdateDisplayUseCase(display_driver=failing_display)

        rgb_image = Image.new("RGB", (800, 480), (255, 255, 255))

        # Act & Assert
        with pytest.raises(DisplayHardwareError, match="Hardware failed"):
            use_case.execute(rgb_image)

    def test_update_display_with_grayscale_colors(self, use_case, mock_display):
        """update_display() handles grayscale colors (converts to black/white)."""
        # Arrange
        rgb_image = Image.new("RGB", (800, 480), (255, 255, 255))
        from PIL import ImageDraw
        draw = ImageDraw.Draw(rgb_image)

        # Gray should be treated as black or white based on threshold
        draw.rectangle([0, 0, 50, 50], fill=(128, 128, 128))  # Mid-gray

        # Act
        use_case.execute(rgb_image)

        # Assert - should complete without error
        assert mock_display.get_display_count() == 1

    def test_update_display_resize_if_needed(self, use_case, mock_display):
        """update_display() can resize image to match display resolution."""
        # Arrange
        # Create image with slightly different size
        rgb_image = Image.new("RGB", (400, 240), (255, 255, 255))

        # Act - should resize internally if configured to do so
        # For now, this should raise an error
        with pytest.raises(ValueError):
            use_case.execute(rgb_image)

    def test_update_display_multiple_times(self, use_case, mock_display):
        """update_display() can be called multiple times successfully."""
        # Arrange
        rgb_image1 = Image.new("RGB", (800, 480), (255, 255, 255))
        rgb_image2 = Image.new("RGB", (800, 480), (0, 0, 0))

        # Act
        use_case.execute(rgb_image1)
        use_case.execute(rgb_image2)

        # Assert
        assert mock_display.get_display_count() == 2
