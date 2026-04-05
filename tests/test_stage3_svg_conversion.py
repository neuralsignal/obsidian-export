"""Tests for SVG conversion basics, path traversal, and PNG variant."""

import tempfile
from pathlib import Path

import pytest

from obsidian_export.exceptions import PathTraversalError, SVGConversionError
from obsidian_export.pipeline.stage3_svg import (
    convert_svg_images,
    convert_svg_images_to_png,
)

MINIMAL_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
    '<circle cx="50" cy="50" r="40" fill="blue"/>'
    "</svg>"
)


def test_no_svg_refs_unchanged():
    text = "# Hello\n\nSome text without any images.\n\n![photo](pic.png)\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = convert_svg_images(text, Path(tmpdir), resource_path=None)
    assert result == text


def test_missing_svg_file_raises():
    text = "![diagram](/tmp/nonexistent_abc123.svg)\n"
    with tempfile.TemporaryDirectory() as tmpdir, pytest.raises(SVGConversionError, match="SVG file not found"):
        convert_svg_images(text, Path(tmpdir), resource_path=None)


def test_url_svg_unchanged():
    text = "![logo](https://example.com/foo.svg)\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = convert_svg_images(text, Path(tmpdir), resource_path=None)
    assert result == text


def test_http_url_svg_unchanged():
    text = "![logo](http://example.com/bar.svg)\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = convert_svg_images(text, Path(tmpdir), resource_path=None)
    assert result == text


def test_svg_ref_replaced_when_file_exists():
    with tempfile.TemporaryDirectory() as workdir:
        workdir = Path(workdir)
        svg_file = workdir / "figure.svg"
        svg_file.write_text(MINIMAL_SVG)

        tmpdir = workdir / "out"
        tmpdir.mkdir()

        text = f"![my diagram]({svg_file})\n"
        result = convert_svg_images(text, tmpdir, resource_path=None)

        assert "figure.svg" not in result
        assert "svg_1.pdf" in result

        # Verify the PDF file was actually created
        pdf_path = tmpdir / "svg_1.pdf"
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0


def test_multiple_svgs_converted():
    with tempfile.TemporaryDirectory() as workdir:
        workdir = Path(workdir)

        svg_a = workdir / "a.svg"
        svg_b = workdir / "b.svg"
        svg_a.write_text(MINIMAL_SVG)
        svg_b.write_text(MINIMAL_SVG)

        tmpdir = workdir / "out"
        tmpdir.mkdir()

        text = f"![first]({svg_a})\n\nSome text.\n\n![second]({svg_b})\n"
        result = convert_svg_images(text, tmpdir, resource_path=None)

        assert "svg_1.pdf" in result
        assert "svg_2.pdf" in result
        assert (tmpdir / "svg_1.pdf").exists()
        assert (tmpdir / "svg_2.pdf").exists()


class TestPathTraversal:
    def test_relative_path_escaping_vault_raises(self):
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            outside = workdir / "outside.svg"
            outside.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = "![escape](../outside.svg)\n"
            with pytest.raises(PathTraversalError, match="SVG path escapes document root"):
                convert_svg_images(text, tmpdir, resource_path=vault)

    def test_absolute_path_outside_vault_raises(self):
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            outside = workdir / "outside.svg"
            outside.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![escape]({outside})\n"
            with pytest.raises(PathTraversalError, match="SVG path escapes document root"):
                convert_svg_images(text, tmpdir, resource_path=vault)

    def test_path_within_vault_allowed(self):
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            svg_file = vault / "figure.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = "![ok](figure.svg)\n"
            result = convert_svg_images(text, tmpdir, resource_path=vault)
            assert "svg_1.pdf" in result

    def test_png_path_traversal_raises(self):
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            outside = workdir / "outside.svg"
            outside.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = "![escape](../outside.svg)\n"
            with pytest.raises(PathTraversalError, match="SVG path escapes document root"):
                convert_svg_images_to_png(text, tmpdir, resource_path=vault)


class TestConvertSvgImagesToPng:
    def test_no_svg_refs_unchanged(self):
        text = "# Hello\n\nSome text without any images.\n\n![photo](pic.png)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = convert_svg_images_to_png(text, Path(tmpdir), resource_path=None)
        assert result == text

    def test_missing_svg_file_raises(self):
        text = "![diagram](/tmp/nonexistent_abc123.svg)\n"
        with tempfile.TemporaryDirectory() as tmpdir, pytest.raises(SVGConversionError, match="SVG file not found"):
            convert_svg_images_to_png(text, Path(tmpdir), resource_path=None)

    def test_url_svg_unchanged(self):
        text = "![logo](https://example.com/foo.svg)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = convert_svg_images_to_png(text, Path(tmpdir), resource_path=None)
        assert result == text

    def test_svg_ref_replaced_with_png(self):
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            svg_file = workdir / "figure.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![my diagram]({svg_file})\n"
            result = convert_svg_images_to_png(text, tmpdir, resource_path=None)

            assert "figure.svg" not in result
            assert "svg_1.png" in result

            png_path = tmpdir / "svg_1.png"
            assert png_path.exists()
            assert png_path.stat().st_size > 0
