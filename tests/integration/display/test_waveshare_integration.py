"""Integration tests for Waveshare display driver.

NOTE: These tests require actual hardware and only run on Raspberry Pi.
They will be skipped in development/CI environments.
"""

import pytest
from PIL import Image

from kalendar.domain.interfaces.IDisplayDriver import DisplayHardwareError


# Skip all tests if Waveshare library not available (no hardware)
try:
    from waveshare_epd import epd7in5b_V2
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False


pytestmark = pytest.mark.skipif(
    not HARDWARE_AVAILABLE,
    reason="Waveshare hardware not available (only runs on Raspberry Pi)"
)


@pytest.mark.hardware
class TestWaveshareIntegration:
    """Integration tests for Waveshare 7.5" HAT (B) driver.

    These tests interact with actual hardware and should be run:
    - On Raspberry Pi with display connected
    - Manually during hardware validation
    - NOT in automated CI/CD pipelines
    """

    @pytest.fixture
    def driver(self):
        """Provide Waveshare driver instance."""
        from kalendar.infrastructure.display.waveshare_driver import WaveshareEPD75BDriver
        return WaveshareEPD75BDriver()

    def test_hardware_initialization(self, driver):
        """Hardware can be initialized successfully."""
        driver.initialize()
        assert driver._initialized is True

    def test_display_test_pattern(self, driver):
        """Display can show test pattern (black/red stripes)."""
        driver.initialize()

        width, height = driver.get_resolution()

        # Create test pattern: vertical black and red stripes
        black_image = Image.new("1", (width, height), 255)  # White background
        red_image = Image.new("1", (width, height), 255)

        from PIL import ImageDraw
        draw_black = ImageDraw.Draw(black_image)
        draw_red = ImageDraw.Draw(red_image)

        # Black stripes every 100 pixels
        for x in range(0, width, 200):
            draw_black.rectangle([x, 0, x + 50, height], fill=0)

        # Red stripes offset by 100 pixels
        for x in range(100, width, 200):
            draw_red.rectangle([x, 0, x + 50, height], fill=0)

        # Display (will take ~30 seconds)
        print("Displaying test pattern (this will take ~30 seconds)...")
        driver.display(black_image, red_image)

        # Sleep after display
        driver.sleep()

    def test_clear_display(self, driver):
        """Display can be cleared to all white."""
        driver.initialize()

        print("Clearing display (this will take ~30 seconds)...")
        driver.clear()

        driver.sleep()

    def test_get_capabilities_returns_correct_specs(self, driver):
        """get_capabilities() returns Waveshare specs."""
        caps = driver.get_capabilities()

        assert caps["resolution"] == (800, 480)
        assert set(caps["colors"]) == {"black", "red", "white"}
        assert caps["refresh_time_seconds"] == 30.0
        assert caps["min_refresh_interval_seconds"] == 180
        assert caps["partial_refresh_supported"] is False

    def test_full_refresh_cycle(self, driver):
        """Complete refresh cycle works (initialize -> display -> sleep)."""
        driver.initialize()

        width, height = driver.get_resolution()

        # Create simple calendar-like test image
        black_image = Image.new("1", (width, height), 255)
        red_image = Image.new("1", (width, height), 255)

        from PIL import ImageDraw, ImageFont
        draw_black = ImageDraw.Draw(black_image)
        draw_red = ImageDraw.Draw(red_image)

        # Title in red
        draw_red.text((10, 10), "Kalendar Hardware Test", fill=0)

        # Grid lines in black
        for i in range(0, width, 100):
            draw_black.line([(i, 0), (i, height)], fill=0, width=2)
        for i in range(0, height, 60):
            draw_black.line([(0, i), (width, i)], fill=0, width=2)

        print("Full refresh cycle test (this will take ~30 seconds)...")
        driver.display(black_image, red_image)
        driver.sleep()


@pytest.mark.skipif(HARDWARE_AVAILABLE, reason="Only run when hardware is NOT available")
def test_waveshare_driver_fails_without_hardware():
    """WaveshareDriver raises helpful error when hardware not available."""
    from kalendar.infrastructure.display.waveshare_driver import WaveshareEPD75BDriver

    driver = WaveshareEPD75BDriver()

    with pytest.raises(DisplayHardwareError, match="Waveshare library not found"):
        driver.initialize()
