"""
Interface: HTML to Image Renderer

Abstraction for HTML/CSS rendering engine (WeasyPrint).
Enables testing with mock renderer.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
from PIL import Image


class IImageRenderer(ABC):
    """
    Interface for HTML to image rendering.

    Implementations:
    - WeasyPrintRenderer (uses weasyprint library)
    - MockRenderer (returns test fixture images)
    - FileBasedRenderer (loads pre-rendered images for testing)

    Note:
        Renderer produces RGB images which must be post-processed
        to separate black and red channels for e-paper display.
    """

    @abstractmethod
    def render_html_string(
        self,
        html_content: str,
        css_content: Optional[str] = None,
        width: int = 800,
        height: int = 480,
    ) -> Image.Image:
        """
        Render HTML string to PNG image.

        Args:
            html_content: HTML markup as string
            css_content: Optional CSS stylesheet as string
            width: Target image width in pixels
            height: Target image height in pixels

        Returns:
            PIL Image object in RGB mode

        Raises:
            RenderError: If HTML rendering fails
            ValueError: If width/height are invalid
        """
        pass

    @abstractmethod
    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        width: int = 800,
        height: int = 480,
    ) -> Image.Image:
        """
        Render HTML template with context data to PNG image.

        Args:
            template_name: Name of template file (e.g., "calendar_view.html")
            context: Dictionary of template variables
            width: Target image width in pixels
            height: Target image height in pixels

        Returns:
            PIL Image object in RGB mode

        Raises:
            TemplateNotFoundError: If template file doesn't exist
            RenderError: If rendering fails
            ValueError: If context data is invalid
        """
        pass

    @abstractmethod
    def set_template_directory(self, directory: Path) -> None:
        """
        Set directory for loading HTML templates.

        Args:
            directory: Path to template directory

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        pass

    @abstractmethod
    def get_capabilities(self) -> dict:
        """
        Get renderer capabilities and limits.

        Returns:
            dict with keys:
                - max_width: int (maximum supported image width)
                - max_height: int (maximum supported image height)
                - supported_formats: List[str] (e.g., ["PNG", "JPEG"])
                - css_version: str (e.g., "CSS 2.1", "CSS 3")
                - memory_estimate_mb: float (estimated peak memory usage)
        """
        pass


class RenderError(Exception):
    """Raised when HTML rendering fails."""

    pass


class TemplateNotFoundError(RenderError):
    """Raised when template file cannot be found."""

    pass
