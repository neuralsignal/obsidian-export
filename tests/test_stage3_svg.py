"""Tests for stage3_svg: SVG -> PDF conversion of image references."""

import shutil
import tempfile
from pathlib import Path

import pytest

from obsidian_export.pipeline.stage3_svg import convert_svg_images

MINIMAL_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
    '<circle cx="50" cy="50" r="40" fill="blue"/>'
    "</svg>"
)

HAS_RSVG = shutil.which("rsvg-convert") is not None


def test_no_svg_refs_unchanged():
    text = "# Hello\n\nSome text without any images.\n\n![photo](pic.png)\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = convert_svg_images(text, Path(tmpdir))
    assert result == text


def test_missing_svg_file_unchanged():
    text = "![diagram](/tmp/nonexistent_abc123.svg)\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = convert_svg_images(text, Path(tmpdir))
    assert result == text


def test_url_svg_unchanged():
    text = "![logo](https://example.com/foo.svg)\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = convert_svg_images(text, Path(tmpdir))
    assert result == text


def test_http_url_svg_unchanged():
    text = "![logo](http://example.com/bar.svg)\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = convert_svg_images(text, Path(tmpdir))
    assert result == text


@pytest.mark.skipif(not HAS_RSVG, reason="rsvg-convert not installed")
def test_svg_ref_replaced_when_file_exists():
    with tempfile.TemporaryDirectory() as workdir:
        workdir = Path(workdir)
        svg_file = workdir / "figure.svg"
        svg_file.write_text(MINIMAL_SVG)

        tmpdir = workdir / "out"
        tmpdir.mkdir()

        text = f"![my diagram]({svg_file})\n"
        result = convert_svg_images(text, tmpdir)

        assert "figure.svg" not in result
        assert "svg_1.pdf" in result

        # Verify the PDF file was actually created
        pdf_path = tmpdir / "svg_1.pdf"
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0


@pytest.mark.skipif(not HAS_RSVG, reason="rsvg-convert not installed")
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
        result = convert_svg_images(text, tmpdir)

        assert "svg_1.pdf" in result
        assert "svg_2.pdf" in result
        assert (tmpdir / "svg_1.pdf").exists()
        assert (tmpdir / "svg_2.pdf").exists()
