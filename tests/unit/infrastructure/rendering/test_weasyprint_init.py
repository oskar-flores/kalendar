"""Unit tests for WeasyPrintRenderer initialization.

Tests that WeasyPrintRenderer can be initialized with and without template_dir parameter.
"""

import pytest
from pathlib import Path

from kalendar.infrastructure.rendering.weasyprint_renderer import WeasyPrintRenderer


class TestWeasyPrintRendererInitialization:
    """Test WeasyPrintRenderer initialization with various parameters."""

    def test_init_without_arguments(self):
        """WeasyPrintRenderer should initialize without arguments."""
        renderer = WeasyPrintRenderer()

        assert renderer is not None
        assert isinstance(renderer, WeasyPrintRenderer)

    def test_init_with_template_dir_string(self):
        """WeasyPrintRenderer should accept template_dir as string."""
        template_dir = "src/kalendar/presentation/templates"

        renderer = WeasyPrintRenderer(template_dir=template_dir)

        assert renderer is not None
        # Template dir should be stored (even if not used immediately)
        assert hasattr(renderer, '_template_directory')

    def test_init_with_template_dir_path(self):
        """WeasyPrintRenderer should accept template_dir as Path object."""
        template_dir = Path("src/kalendar/presentation/templates")

        renderer = WeasyPrintRenderer(template_dir=template_dir)

        assert renderer is not None
        assert hasattr(renderer, '_template_directory')

    def test_init_stores_template_directory(self):
        """WeasyPrintRenderer should store the provided template directory."""
        template_dir = "my/custom/templates"

        renderer = WeasyPrintRenderer(template_dir=template_dir)

        # Template directory should be stored (converted to Path if needed)
        assert renderer._template_directory is not None

    def test_init_with_none_template_dir(self):
        """WeasyPrintRenderer should handle None template_dir."""
        renderer = WeasyPrintRenderer(template_dir=None)

        assert renderer is not None
        # None should be acceptable (template_dir set later via set_template_directory)

    def test_multiple_instances_with_different_template_dirs(self):
        """Multiple renderer instances should have independent template directories."""
        renderer1 = WeasyPrintRenderer(template_dir="templates1")
        renderer2 = WeasyPrintRenderer(template_dir="templates2")

        assert renderer1 is not renderer2
        # Each should maintain its own template directory
        assert hasattr(renderer1, '_template_directory')
        assert hasattr(renderer2, '_template_directory')
