"""
Interface: E-Paper Display Driver

Abstraction for Waveshare e-paper display hardware.
Enables testing without physical hardware (Principle II - TDD).
"""

from abc import ABC, abstractmethod
from typing import Tuple
from PIL import Image


class IDisplayDriver(ABC):
    """
    Interface for e-paper display drivers.

    Implementations:
    - WaveshareEPD75BDriver (real hardware driver)
    - MockDisplayDriver (saves to file for testing)
    - SimulatorDisplayDriver (shows in window for development)

    Note:
        The Waveshare 7.5" HAT (B) uses a two-buffer system:
        - Black buffer: Pixels that should be black (all other pixels white)
        - Red buffer: Pixels that should be red (all other pixels white)

        Where both buffers have "black" (value 0), the display shows black.
        Where only red buffer has "black", display shows red.
    """

    @abstractmethod
    def get_resolution(self) -> Tuple[int, int]:
        """
        Get display resolution.

        Returns:
            Tuple of (width, height) in pixels
            For Waveshare 7.5" HAT (B): (800, 480)
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize display hardware.

        Must be called before display() or clear().

        Raises:
            DisplayHardwareError: If hardware initialization fails
        """
        pass

    @abstractmethod
    def display(self, black_image: Image.Image, red_image: Image.Image) -> None:
        """
        Update display with new content.

        Args:
            black_image: PIL Image in mode '1' (1-bit black/white)
                        - 0 (black) pixels will appear black on display
                        - 255 (white) pixels will be white (or red from red_image)

            red_image: PIL Image in mode '1' (1-bit black/white)
                      - 0 (black) pixels will appear red on display
                      - 255 (white) pixels will not affect display

        Notes:
            - Both images must match display resolution
            - Full refresh takes ~30 seconds on Waveshare 7.5" HAT (B)
            - Should not be called more frequently than min_refresh_interval

        Raises:
            DisplayHardwareError: If display update fails
            ValueError: If image sizes don't match resolution
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clear display to all white.

        Raises:
            DisplayHardwareError: If clear operation fails
        """
        pass

    @abstractmethod
    def sleep(self) -> None:
        """
        Put display into low-power sleep mode.

        Should be called after display() to conserve power.
        Display content is retained while sleeping.

        Raises:
            DisplayHardwareError: If sleep operation fails
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> dict:
        """
        Get display capabilities and constraints.

        Returns:
            dict with keys:
                - resolution: Tuple[int, int]
                - colors: List[str] (e.g., ["black", "red", "white"])
                - refresh_time_seconds: float (typical full refresh time)
                - min_refresh_interval_seconds: int (min time between refreshes)
                - partial_refresh_supported: bool
        """
        pass


class DisplayHardwareError(Exception):
    """Raised when display hardware operation fails."""

    pass


class DisplayNotInitializedError(DisplayHardwareError):
    """Raised when display operation attempted before initialization."""

    pass
