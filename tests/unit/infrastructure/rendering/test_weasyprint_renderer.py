"""
Unit tests for WeasyPrintRenderer.

Purpose: Test WeasyPrintRenderer render_html_string implementation.

TDD: These tests are written FIRST and should FAIL until the cairo fix is implemented.
"""

import pytest
from PIL import Image
from io import BytesIO

from src.kalendar.infrastructure.rendering.weasyprint_renderer import WeasyPrintRenderer
from src.kalendar.domain.interfaces.IImageRenderer import RenderError


class TestWeasyPrintRendererUnit:
    """Unit tests for WeasyPrintRenderer PNG rendering."""

    @pytest.fixture
    def renderer(self):
        """Create WeasyPrintRenderer instance."""
        return WeasyPrintRenderer()

    def test_render_html_string_returns_valid_png(self, renderer):
        """
        render_html_string should return a valid PIL Image in RGB mode.

        TDD: This test will FAIL with 'HTML' object has no attribute 'write_png'
        until we implement the cairocffi fix.
        """
        # Arrange
        html = """
        <html>
            <head>
                <style>
                    body { background: white; color: black; margin: 0; }
                </style>
            </head>
            <body>
                <h1>Test</h1>
            </body>
        </html>
        """

        # Act
        result = renderer.render_html_string(html, width=100, height=100)

        # Assert
        assert isinstance(result, Image.Image), "Should return PIL Image"
        assert result.mode == "RGB", "Image must be RGB mode"
        assert result.size == (100, 100), "Image should match requested dimensions"

    def test_render_html_string_with_css(self, renderer):
        """
        render_html_string should accept CSS and produce valid PNG.

        TDD: This test will FAIL until cairocffi fix is implemented.
        """
        # Arrange
        html = '<html><body><h1 class="red">Test</h1></body></html>'
        css = ".red { color: red; }"

        # Act
        result = renderer.render_html_string(html, css_content=css, width=200, height=150)

        # Assert
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"
        assert result.size == (200, 150)

    def test_render_html_string_custom_dimensions(self, renderer):
        """
        render_html_string should respect custom dimensions.

        TDD: This test will FAIL until cairocffi fix is implemented.
        """
        # Arrange
        html = "<html><body><p>Content</p></body></html>"
        width, height = 800, 480

        # Act
        result = renderer.render_html_string(html, width=width, height=height)

        # Assert
        assert result.width == width
        assert result.height == height

    def test_render_html_string_produces_valid_image_bytes(self, renderer):
        """
        The rendered image should be convertible to PNG bytes.

        TDD: This test will FAIL until cairocffi fix is implemented.
        """
        # Arrange
        html = "<html><body><h1>Test</h1></body></html>"

        # Act
        result = renderer.render_html_string(html, width=100, height=100)

        # Assert - Should be able to save as PNG
        buffer = BytesIO()
        result.save(buffer, format="PNG")
        png_bytes = buffer.getvalue()

        assert len(png_bytes) > 0, "Should produce valid PNG bytes"
        assert png_bytes[:8] == b'\x89PNG\r\n\x1a\n', "Should have valid PNG header"

    def test_render_html_string_invalid_dimensions_raises_error(self, renderer):
        """render_html_string should validate dimensions."""
        # Arrange
        html = "<html><body>Test</body></html>"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid dimensions"):
            renderer.render_html_string(html, width=0, height=100)

        with pytest.raises(ValueError, match="Invalid dimensions"):
            renderer.render_html_string(html, width=100, height=-50)
