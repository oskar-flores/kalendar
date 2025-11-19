"""Waveshare 7.5" e-Paper HAT (B) display driver.

This driver interfaces with the Waveshare 7.5" 3-color e-paper display.
Hardware: https://www.waveshare.com/7.5inch-e-paper-hat-b.htm

NOTE: This driver requires actual hardware and only works on Raspberry Pi.
Use SimulatorDisplayDriver or MockDisplayDriver for development/testing.
"""

import logging
import signal
from typing import Optional, Tuple

from PIL import Image

from kalendar.domain.interfaces.IDisplayDriver import (
    DisplayHardwareError,
    DisplayNotInitializedError,
    IDisplayDriver,
)

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Raised when a hardware operation times out."""
    pass


def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Hardware operation timed out")


class WaveshareEPD75BDriver(IDisplayDriver):
    """Display driver for Waveshare 7.5" e-Paper HAT (B).

    Specifications:
        - Resolution: 800x480 pixels
        - Colors: Black, Red, White
        - Partial Refresh: Not supported
        - Full Refresh Time: ~30 seconds
        - Interface: SPI

    Hardware Setup:
        1. Enable SPI: sudo raspi-config -> Interface Options -> SPI -> Yes
        2. Connect display HAT to GPIO pins
        3. Ensure SPI is enabled in /boot/config.txt
    """

    def __init__(self):
        """Initialize Waveshare driver.

        Note: Hardware communication is not established until initialize() is called.
        """
        self._initialized = False
        self._epd: Optional[object] = None  # Will be EPD instance from library

    def get_resolution(self) -> Tuple[int, int]:
        """Get display resolution.

        Returns:
            (800, 480) - Waveshare 7.5" HAT (B) resolution
        """
        return (800, 480)

    def initialize(self) -> None:
        """Initialize display hardware.

        Raises:
            DisplayHardwareError: If hardware initialization fails
        """
        logger.info("Initializing Waveshare 7.5\" e-Paper display...")

        try:
            # Configure GPIO pin factory to use lgpio (modern backend for Raspberry Pi)
            # This must be set before importing waveshare_epd
            import os
            os.environ.setdefault('GPIOZERO_PIN_FACTORY', 'lgpio')
            logger.debug("GPIO factory set to lgpio")

            # Import Waveshare library (only available on Raspberry Pi)
            # This import will fail in development/test environments
            logger.debug("Importing Waveshare library...")
            from waveshare_epd import epd7in5b_V2

            logger.debug("Creating EPD instance...")
            self._epd = epd7in5b_V2.EPD()

            # Initialize hardware with timeout protection (60 seconds)
            logger.info("Calling EPD.init() - this may take up to 60 seconds...")

            # Set up timeout using signal.alarm()
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(60)  # 60 second timeout

            try:
                self._epd.init()
                signal.alarm(0)  # Cancel alarm on success
                logger.info("Display initialized successfully")
            except TimeoutError:
                signal.alarm(0)  # Cancel alarm
                raise DisplayHardwareError(
                    "Display initialization timed out after 60 seconds. "
                    "This usually indicates: (1) BUSY pin stuck HIGH, "
                    "(2) SPI communication failure, or (3) Hardware not connected. "
                    "Check: SPI enabled, cables connected, adequate power supply."
                )

            self._initialized = True

        except ImportError as e:
            raise DisplayHardwareError(
                "Waveshare library not found. This driver only works on Raspberry Pi "
                "with waveshare-epd library installed. "
                "For development, use SimulatorDisplayDriver instead."
            ) from e
        except TimeoutError:
            # Re-raise TimeoutError wrapped as DisplayHardwareError
            raise
        except Exception as e:
            signal.alarm(0)  # Ensure alarm is cancelled
            raise DisplayHardwareError(f"Failed to initialize display hardware: {e}") from e

    def display(self, black_image: Image.Image, red_image: Image.Image) -> None:
        """Update display with new content.

        Args:
            black_image: PIL Image in mode '1' (1-bit black/white)
            red_image: PIL Image in mode '1' (1-bit black/white)

        Raises:
            DisplayNotInitializedError: If not initialized
            ValueError: If image sizes or modes incorrect
            DisplayHardwareError: If display update fails
        """
        if not self._initialized or self._epd is None:
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

        logger.info("Converting images to display buffers...")

        try:
            # Use Waveshare library's getbuffer() method to convert images
            # This ensures proper buffer format and mutability
            logger.debug("Calling getbuffer() for black image...")
            black_buffer = self._epd.getbuffer(black_image)

            logger.debug("Calling getbuffer() for red image...")
            red_buffer = self._epd.getbuffer(red_image)

            # Send to display with timeout protection (90 seconds for full refresh)
            logger.info("Sending display data (this may take up to 90 seconds)...")

            # Set up timeout using signal.alarm()
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(90)  # 90 second timeout (display refresh ~30s + buffer)

            try:
                logger.debug("Calling EPD.display() - waiting for hardware...")
                self._epd.display(black_buffer, red_buffer)
                signal.alarm(0)  # Cancel alarm on success
                logger.info("Display update completed successfully")
            except TimeoutError:
                signal.alarm(0)  # Cancel alarm
                raise DisplayHardwareError(
                    "Display update timed out after 90 seconds. "
                    "This usually indicates: (1) BUSY pin stuck HIGH during refresh, "
                    "(2) Hardware malfunction, or (3) Power supply issue during refresh. "
                    "The display refresh normally takes ~30 seconds. "
                    "Check: Power supply adequate for display refresh, SPI communication stable."
                )

        except TimeoutError:
            # Re-raise TimeoutError as is (already wrapped)
            raise
        except Exception as e:
            signal.alarm(0)  # Ensure alarm is cancelled
            raise DisplayHardwareError(f"Failed to update display: {e}") from e

    def clear(self) -> None:
        """Clear display to all white.

        Raises:
            DisplayNotInitializedError: If not initialized
            DisplayHardwareError: If clear operation fails
        """
        if not self._initialized or self._epd is None:
            raise DisplayNotInitializedError("Display must be initialized before use")

        try:
            self._epd.Clear()
        except Exception as e:
            raise DisplayHardwareError(f"Failed to clear display: {e}") from e

    def sleep(self) -> None:
        """Put display into low-power sleep mode.

        Raises:
            DisplayNotInitializedError: If not initialized
            DisplayHardwareError: If sleep operation fails
        """
        if not self._initialized or self._epd is None:
            raise DisplayNotInitializedError("Display must be initialized before use")

        try:
            self._epd.sleep()
        except Exception as e:
            raise DisplayHardwareError(f"Failed to put display to sleep: {e}") from e

    def get_capabilities(self) -> dict:
        """Get display capabilities.

        Returns:
            Dictionary with display specifications
        """
        return {
            "resolution": self.get_resolution(),
            "colors": ["black", "red", "white"],
            "refresh_time_seconds": 30.0,  # Full refresh time
            "min_refresh_interval_seconds": 180,  # Min 3 minutes between refreshes
            "partial_refresh_supported": False,
        }
