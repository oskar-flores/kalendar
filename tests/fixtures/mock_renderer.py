"""
Mock Image Renderer for testing.

Purpose: Provides deterministic image rendering without WeasyPrint dependency.
Returns simple test images for fast test execution.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import Dict, Any, Optional
from src.kalendar.domain.interfaces.IImageRenderer import (
    IImageRenderer,
    RenderError,
    TemplateNotFoundError,
)


class MockRenderer(IImageRenderer):
    """
    Mock implementation of IImageRenderer for testing.

    Creates simple images with text labels instead of complex HTML rendering.
    Useful for fast tests that don't need actual rendering.
    """

    def __init__(self) -> None:
        """Initialize MockRenderer."""
        self._template_directory: Optional[Path] = None

    def render_html_string(
        self,
        html_content: str,
        css_content: Optional[str] = None,
        width: int = 800,
        height: int = 480,
    ) -> Image.Image:
        """
        Mock render HTML string to simple test image.

        Args:
            html_content: HTML markup (used to extract text for label)
            css_content: Optional CSS (ignored in mock)
            width: Target image width
            height: Target image height

        Returns:
            Simple RGB image with dimensions
        """
        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: {width}x{height}")

        # Create white background image
        image = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(image)

        # Extract title from HTML if possible (simple regex)
        import re

        title_match = re.search(r"<h1[^>]*>(.*?)</h1>", html_content, re.DOTALL)
        text = title_match.group(1) if title_match else "Mock Render"

        # Draw text label
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Draw centered text
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2

        draw.text((text_x, text_y), text, fill="black", font=font)

        # Draw border to indicate dimensions
        draw.rectangle([0, 0, width - 1, height - 1], outline="black", width=2)

        return image

    def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        width: int = 800,
        height: int = 480,
    ) -> Image.Image:
        """
        Mock render template with context data.

        Args:
            template_name: Name of template file
            context: Dictionary of template variables
            width: Target image width
            height: Target image height

        Returns:
            Simple RGB image with template name as label
        """
        if self._template_directory is None:
            raise RenderError("Template directory not set")

        template_path = self._template_directory / template_name
        if not template_path.exists():
            raise TemplateNotFoundError(f"Template not found: {template_name}")

        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions: {width}x{height}")

        # Create white background image
        image = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(image)

        # Use context title if available
        title = context.get("title", template_name)

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Draw title
        text_bbox = draw.textbbox((0, 0), title, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2

        draw.text((text_x, text_y), title, fill="black", font=font)

        # Draw template name at bottom
        template_label = f"Template: {template_name}"
        label_bbox = draw.textbbox((0, 0), template_label, font=font)
        label_width = label_bbox[2] - label_bbox[0]
        label_x = (width - label_width) // 2
        label_y = height - 30

        draw.text((label_x, label_y), template_label, fill="gray", font=font)

        # Draw border
        draw.rectangle([0, 0, width - 1, height - 1], outline="black", width=2)

        return image

    def set_template_directory(self, directory: Path) -> None:
        """
        Set directory for loading templates.

        Args:
            directory: Path to template directory

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        if not directory.exists() or not directory.is_dir():
            raise FileNotFoundError(f"Template directory not found: {directory}")

        self._template_directory = directory

    def get_capabilities(self) -> dict:
        """
        Get mock renderer capabilities.

        Returns:
            dict with mock renderer capabilities
        """
        return {
            "max_width": 10000,
            "max_height": 10000,
            "supported_formats": ["PNG", "JPEG", "BMP"],
            "css_version": "Mock CSS",
            "memory_estimate_mb": 1.0,  # Very lightweight
        }
