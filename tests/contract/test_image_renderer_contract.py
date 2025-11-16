"""
Contract test for IImageRenderer interface.

Purpose: Verify that all implementations of IImageRenderer comply with the interface contract.
This test should be run against WeasyPrintRenderer and MockRenderer.

TDD: This test is written FIRST and should FAIL until implementations exist.
"""

import pytest
from pathlib import Path
from PIL import Image
from typing import Type
from src.kalendar.domain.interfaces.IImageRenderer import (
    IImageRenderer,
    RenderError,
    TemplateNotFoundError,
)


class IImageRendererContractTest:
    """
    Base contract test for IImageRenderer implementations.

    Subclass this test for each implementation and provide the implementation instance.
    """

    @pytest.fixture
    def renderer(self) -> IImageRenderer:
        """Override in subclass to provide renderer implementation."""
        raise NotImplementedError("Subclass must provide renderer fixture")

    @pytest.fixture
    def template_dir(self, tmp_path: Path) -> Path:
        """Create temporary template directory with test template."""
        template_dir = tmp_path / "templates"
        template_dir.mkdir()

        # Create a simple test template
        template_file = template_dir / "test_template.html"
        template_file.write_text(
            """
            <html>
                <head>
                    <style>
                        body { background: white; color: black; margin: 0; padding: 20px; }
                        h1 { color: red; }
                    </style>
                </head>
                <body>
                    <h1>{{ title }}</h1>
                    <p>{{ content }}</p>
                </body>
            </html>
            """
        )

        return template_dir

    def test_render_html_string_returns_image(self, renderer: IImageRenderer) -> None:
        """render_html_string should return a PIL Image object."""
        # Arrange
        html = "<html><body><h1>Test</h1></body></html>"

        # Act
        result = renderer.render_html_string(html)

        # Assert
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_render_html_string_respects_dimensions(self, renderer: IImageRenderer) -> None:
        """render_html_string should create image with specified dimensions."""
        # Arrange
        html = "<html><body><h1>Test</h1></body></html>"
        width, height = 800, 480

        # Act
        result = renderer.render_html_string(html, width=width, height=height)

        # Assert
        assert result.width == width
        assert result.height == height

    def test_render_html_string_with_css(self, renderer: IImageRenderer) -> None:
        """render_html_string should accept optional CSS content."""
        # Arrange
        html = '<html><body><h1 class="red">Test</h1></body></html>'
        css = "h1.red { color: red; }"

        # Act
        result = renderer.render_html_string(html, css_content=css)

        # Assert
        assert isinstance(result, Image.Image)

    def test_render_html_string_invalid_dimensions_raises_error(
        self, renderer: IImageRenderer
    ) -> None:
        """render_html_string should raise ValueError for invalid dimensions."""
        # Arrange
        html = "<html><body><h1>Test</h1></body></html>"

        # Act & Assert
        with pytest.raises(ValueError):
            renderer.render_html_string(html, width=0, height=480)

        with pytest.raises(ValueError):
            renderer.render_html_string(html, width=800, height=-100)

    def test_set_template_directory(
        self, renderer: IImageRenderer, template_dir: Path
    ) -> None:
        """set_template_directory should accept a valid directory path."""
        # Act & Assert - should not raise
        renderer.set_template_directory(template_dir)

    def test_set_template_directory_invalid_path_raises_error(
        self, renderer: IImageRenderer, tmp_path: Path
    ) -> None:
        """set_template_directory should raise FileNotFoundError for invalid path."""
        # Arrange
        invalid_path = tmp_path / "nonexistent_directory"

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            renderer.set_template_directory(invalid_path)

    def test_render_template_returns_image(
        self, renderer: IImageRenderer, template_dir: Path
    ) -> None:
        """render_template should return a PIL Image object."""
        # Arrange
        renderer.set_template_directory(template_dir)
        context = {"title": "Test Title", "content": "Test content"}

        # Act
        result = renderer.render_template("test_template.html", context)

        # Assert
        assert isinstance(result, Image.Image)
        assert result.mode == "RGB"

    def test_render_template_respects_dimensions(
        self, renderer: IImageRenderer, template_dir: Path
    ) -> None:
        """render_template should create image with specified dimensions."""
        # Arrange
        renderer.set_template_directory(template_dir)
        context = {"title": "Test", "content": "Content"}
        width, height = 400, 300

        # Act
        result = renderer.render_template("test_template.html", context, width, height)

        # Assert
        assert result.width == width
        assert result.height == height

    def test_render_template_not_found_raises_error(
        self, renderer: IImageRenderer, template_dir: Path
    ) -> None:
        """render_template should raise TemplateNotFoundError for missing template."""
        # Arrange
        renderer.set_template_directory(template_dir)
        context = {"title": "Test", "content": "Content"}

        # Act & Assert
        with pytest.raises(TemplateNotFoundError):
            renderer.render_template("nonexistent_template.html", context)

    def test_get_capabilities_returns_dict(self, renderer: IImageRenderer) -> None:
        """get_capabilities should return a dictionary with required keys."""
        # Act
        capabilities = renderer.get_capabilities()

        # Assert
        assert isinstance(capabilities, dict)
        assert "max_width" in capabilities
        assert "max_height" in capabilities
        assert "supported_formats" in capabilities
        assert "css_version" in capabilities
        assert "memory_estimate_mb" in capabilities

        # Validate types
        assert isinstance(capabilities["max_width"], int)
        assert isinstance(capabilities["max_height"], int)
        assert isinstance(capabilities["supported_formats"], list)
        assert isinstance(capabilities["css_version"], str)
        assert isinstance(capabilities["memory_estimate_mb"], (int, float))

    def test_get_capabilities_reasonable_limits(self, renderer: IImageRenderer) -> None:
        """get_capabilities should return reasonable dimension limits."""
        # Act
        capabilities = renderer.get_capabilities()

        # Assert
        assert capabilities["max_width"] >= 800  # Should support e-paper width
        assert capabilities["max_height"] >= 480  # Should support e-paper height
        assert "PNG" in capabilities["supported_formats"]  # Must support PNG

    def test_render_html_produces_rgb_image(self, renderer: IImageRenderer) -> None:
        """Rendered images should be in RGB mode for post-processing."""
        # Arrange
        html = "<html><body style='background: white;'><h1>Test</h1></body></html>"

        # Act
        result = renderer.render_html_string(html, width=100, height=100)

        # Assert
        assert result.mode == "RGB", "Image must be RGB for color separation"
        assert result.size == (100, 100)

    def test_render_complex_html(self, renderer: IImageRenderer) -> None:
        """Should render complex HTML with multiple elements."""
        # Arrange
        html = """
        <html>
            <head>
                <style>
                    body { background: white; color: black; padding: 10px; }
                    .red { color: red; }
                    .grid { display: block; }
                </style>
            </head>
            <body>
                <h1 class="red">Title</h1>
                <div class="grid">
                    <span>Item 1</span>
                    <span>Item 2</span>
                </div>
            </body>
        </html>
        """

        # Act
        result = renderer.render_html_string(html, width=800, height=480)

        # Assert
        assert isinstance(result, Image.Image)
        assert result.size == (800, 480)


# Test against MockRenderer (implementation in next task)
class TestMockRendererContract(IImageRendererContractTest):
    """Contract test for MockRenderer."""

    @pytest.fixture
    def renderer(self) -> IImageRenderer:
        """Create MockRenderer instance."""
        # This will fail until MockRenderer is implemented
        from tests.fixtures.mock_renderer import MockRenderer

        return MockRenderer()


# Placeholder for WeasyPrintRenderer contract test
# Uncomment when WeasyPrintRenderer is implemented
# class TestWeasyPrintRendererContract(IImageRendererContractTest):
#     @pytest.fixture
#     def renderer(self) -> IImageRenderer:
#         from src.kalendar.infrastructure.rendering.weasyprint_renderer import (
#             WeasyPrintRenderer,
#         )
#         return WeasyPrintRenderer()
