"""
WeasyPrint HTML to Image Renderer Implementation.

Uses WeasyPrint library to render HTML/CSS to PNG images.
Optimized for Raspberry Pi Zero W with memory constraints.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from io import BytesIO
import logging

from PIL import Image
from weasyprint import HTML, CSS
import jinja2
from jinja2 import Environment, FileSystemLoader

from kalendar.domain.interfaces.IImageRenderer import (
    IImageRenderer,
    RenderError,
    TemplateNotFoundError,
)

logger = logging.getLogger(__name__)


class WeasyPrintRenderer(IImageRenderer):
    """
    WeasyPrint implementation of IImageRenderer.

    Uses WeasyPrint for HTML/CSS rendering to PNG.
    Suitable for Raspberry Pi Zero W (low memory footprint).

    Memory Usage:
        Estimated 30-50MB peak during rendering (per research.md)

    Capabilities:
        - CSS 2.1 and partial CSS 3 support
        - Fixed-layout rendering (ideal for e-paper displays)
        - PNG output (800x480 for Waveshare 7.5" display)
    """

    def __init__(self) -> None:
        """Initialize WeasyPrint renderer."""
        self._template_directory: Optional[Path] = None
        self._jinja_env: Optional[Environment] = None

        logger.info("WeasyPrintRenderer initialized")

    def render_html_string(
        self,
        html_content: str,
        css_content: Optional[str] = None,
        width: int = 800,
        height: int = 480,
    ) -> Image.Image:
        """
        Render HTML string to PNG image using WeasyPrint.

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
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: {width}x{height}")

        try:
            # Build CSS with viewport size
            viewport_css = f"""
            @page {{
                size: {width}px {height}px;
                margin: 0;
            }}
            body {{
                margin: 0;
                padding: 0;
                width: {width}px;
                height: {height}px;
            }}
            """

            # Combine with user CSS
            if css_content:
                full_css = viewport_css + "\n" + css_content
            else:
                full_css = viewport_css

            # Render HTML with WeasyPrint
            html = HTML(string=html_content)
            css_obj = CSS(string=full_css)

            # Render to PNG in memory
            png_bytes = html.write_png(stylesheets=[css_obj])

            # Convert to PIL Image
            image = Image.open(BytesIO(png_bytes))

            # Ensure RGB mode (WeasyPrint outputs RGBA, we need RGB for post-processing)
            if image.mode == "RGBA":
                # Create white background
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
                image = rgb_image
            elif image.mode != "RGB":
                image = image.convert("RGB")

            logger.info(f"Rendered HTML to {image.width}x{image.height} image")
            return image

        except Exception as e:
            logger.error(f"Failed to render HTML: {e}")
            raise RenderError(f"WeasyPrint rendering failed: {e}")

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
        if self._jinja_env is None:
            raise RenderError("Template directory not set. Call set_template_directory() first.")

        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: {width}x{height}")

        try:
            # Load template
            template = self._jinja_env.get_template(template_name)

            # Render template with context
            html_content = template.render(**context)

            # Load associated CSS if exists
            css_content = None
            css_filename = template_name.replace(".html", ".css")
            css_path = self._template_directory / css_filename

            if css_path.exists():
                css_content = css_path.read_text()
                logger.debug(f"Loaded CSS from {css_filename}")

            # Render HTML with WeasyPrint
            return self.render_html_string(html_content, css_content, width, height)

        except jinja2.exceptions.TemplateNotFound as e:
            logger.error(f"Template not found: {template_name}")
            raise TemplateNotFoundError(f"Template not found: {template_name}")
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise RenderError(f"Template rendering failed: {e}")

    def set_template_directory(self, directory: Path) -> None:
        """
        Set directory for loading HTML templates.

        Args:
            directory: Path to template directory

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Template directory not found: {directory}")

        self._template_directory = directory

        # Initialize Jinja2 environment
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(directory)),
            autoescape=True,  # Auto-escape for security
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info(f"Template directory set to: {directory}")

    def get_capabilities(self) -> dict:
        """
        Get WeasyPrint renderer capabilities.

        Returns:
            dict with renderer capabilities
        """
        return {
            "max_width": 10000,  # WeasyPrint can handle large images
            "max_height": 10000,
            "supported_formats": ["PNG"],  # We only expose PNG
            "css_version": "CSS 2.1 + partial CSS 3",
            "memory_estimate_mb": 50.0,  # Peak memory during rendering (per research.md)
        }
