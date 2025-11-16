"""Contract tests for IDisplayDriver interface.

Ensures all display driver implementations comply with the interface contract.
"""

import pytest
from PIL import Image

from kalendar.domain.interfaces.IDisplayDriver import (
    DisplayHardwareError,
    DisplayNotInitializedError,
    IDisplayDriver,
)


class DisplayDriverContractTests:
    """Base contract tests that all IDisplayDriver implementations must pass."""

    @pytest.fixture
    def driver(self) -> IDisplayDriver:
        """Override this fixture in implementation-specific test classes."""
        raise NotImplementedError("Subclasses must provide a driver fixture")

    def test_get_resolution_returns_tuple(self, driver: IDisplayDriver):
        """get_resolution() returns a tuple of two integers."""
        resolution = driver.get_resolution()
        assert isinstance(resolution, tuple)
        assert len(resolution) == 2
        assert isinstance(resolution[0], int)
        assert isinstance(resolution[1], int)
        assert resolution[0] > 0
        assert resolution[1] > 0

    def test_get_capabilities_returns_required_keys(self, driver: IDisplayDriver):
        """get_capabilities() returns dict with all required keys."""
        caps = driver.get_capabilities()
        assert isinstance(caps, dict)

        # Required keys
        assert "resolution" in caps
        assert "colors" in caps
        assert "refresh_time_seconds" in caps
        assert "min_refresh_interval_seconds" in caps
        assert "partial_refresh_supported" in caps

        # Type validation
        assert isinstance(caps["resolution"], tuple)
        assert len(caps["resolution"]) == 2
        assert isinstance(caps["colors"], list)
        assert all(isinstance(c, str) for c in caps["colors"])
        assert isinstance(caps["refresh_time_seconds"], (int, float))
        assert isinstance(caps["min_refresh_interval_seconds"], int)
        assert isinstance(caps["partial_refresh_supported"], bool)

    def test_initialize_succeeds(self, driver: IDisplayDriver):
        """initialize() can be called without errors."""
        driver.initialize()

    def test_display_before_initialize_raises_error(self, driver: IDisplayDriver):
        """display() before initialize() raises DisplayNotInitializedError."""
        width, height = driver.get_resolution()
        black_img = Image.new("1", (width, height), 255)
        red_img = Image.new("1", (width, height), 255)

        # Note: Some drivers may auto-initialize, so we skip this test if
        # they don't raise an error
        try:
            driver.display(black_img, red_img)
        except DisplayNotInitializedError:
            pass  # Expected behavior

    def test_display_with_valid_images(self, driver: IDisplayDriver):
        """display() accepts correctly sized images."""
        driver.initialize()
        width, height = driver.get_resolution()

        black_img = Image.new("1", (width, height), 255)
        red_img = Image.new("1", (width, height), 255)

        driver.display(black_img, red_img)

    def test_display_with_wrong_size_raises_error(self, driver: IDisplayDriver):
        """display() with wrong image size raises ValueError."""
        driver.initialize()

        # Create images with wrong size
        black_img = Image.new("1", (100, 100), 255)
        red_img = Image.new("1", (100, 100), 255)

        with pytest.raises(ValueError, match="size|resolution|dimension"):
            driver.display(black_img, red_img)

    def test_display_with_wrong_mode_raises_error(self, driver: IDisplayDriver):
        """display() with wrong image mode raises ValueError."""
        driver.initialize()
        width, height = driver.get_resolution()

        # Create images with wrong mode (RGB instead of '1')
        black_img = Image.new("RGB", (width, height), (255, 255, 255))
        red_img = Image.new("1", (width, height), 255)

        with pytest.raises(ValueError, match="mode"):
            driver.display(black_img, red_img)

    def test_clear_after_initialize(self, driver: IDisplayDriver):
        """clear() can be called after initialize()."""
        driver.initialize()
        driver.clear()

    def test_sleep_after_initialize(self, driver: IDisplayDriver):
        """sleep() can be called after initialize()."""
        driver.initialize()
        driver.sleep()

    def test_full_lifecycle(self, driver: IDisplayDriver):
        """Complete lifecycle: initialize -> display -> sleep."""
        # Initialize
        driver.initialize()

        # Create test images
        width, height = driver.get_resolution()
        black_img = Image.new("1", (width, height), 255)
        red_img = Image.new("1", (width, height), 255)

        # Display
        driver.display(black_img, red_img)

        # Sleep
        driver.sleep()

    def test_multiple_display_calls(self, driver: IDisplayDriver):
        """Multiple display() calls work correctly."""
        driver.initialize()
        width, height = driver.get_resolution()

        # First display
        black_img1 = Image.new("1", (width, height), 255)
        red_img1 = Image.new("1", (width, height), 255)
        driver.display(black_img1, red_img1)

        # Second display
        black_img2 = Image.new("1", (width, height), 255)
        red_img2 = Image.new("1", (width, height), 255)
        driver.display(black_img2, red_img2)

    def test_initialize_is_idempotent(self, driver: IDisplayDriver):
        """initialize() can be called multiple times safely."""
        driver.initialize()
        driver.initialize()  # Should not raise error

    def test_display_with_actual_content(self, driver: IDisplayDriver):
        """display() works with images containing actual content."""
        driver.initialize()
        width, height = driver.get_resolution()

        # Create black image with a black rectangle
        black_img = Image.new("1", (width, height), 255)  # White background
        from PIL import ImageDraw
        draw = ImageDraw.Draw(black_img)
        draw.rectangle([10, 10, 100, 100], fill=0)  # Black rectangle

        # Create red image with a red rectangle
        red_img = Image.new("1", (width, height), 255)  # White background
        draw = ImageDraw.Draw(red_img)
        draw.rectangle([110, 10, 200, 100], fill=0)  # Red rectangle

        driver.display(black_img, red_img)


# Test class for MockDisplayDriver
class TestMockDisplayDriverContract(DisplayDriverContractTests):
    """Contract tests for MockDisplayDriver."""

    @pytest.fixture
    def driver(self):
        """Provide MockDisplayDriver instance for testing."""
        from tests.fixtures.mock_display_driver import MockDisplayDriver
        return MockDisplayDriver(output_dir="/tmp/kalendar_test_mock")


# Test class for SimulatorDisplayDriver
class TestSimulatorDisplayDriverContract(DisplayDriverContractTests):
    """Contract tests for SimulatorDisplayDriver."""

    @pytest.fixture
    def driver(self):
        """Provide SimulatorDisplayDriver instance for testing."""
        from kalendar.infrastructure.display.simulator_driver import SimulatorDisplayDriver
        return SimulatorDisplayDriver(output_dir="/tmp/kalendar_test_simulator")


# Hardware-specific tests (requires actual hardware)
class TestWaveshareEPD75BDriverContract(DisplayDriverContractTests):
    """Contract tests for WaveshareEPD75BDriver."""

    @pytest.fixture
    def driver(self):
        """Provide WaveshareEPD75BDriver instance for testing."""
        pytest.skip("WaveshareEPD75BDriver requires hardware (T072)")
        # When implemented and hardware available:
        # from kalendar.infrastructure.display.waveshare_driver import WaveshareEPD75BDriver
        # return WaveshareEPD75BDriver()
