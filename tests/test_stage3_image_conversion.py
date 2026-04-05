"""Tests for image conversion, path traversal, and error handling."""

import tempfile
from pathlib import Path

import pytest
from PIL import Image

from obsidian_export.exceptions import ImageConversionError, PathTraversalError
from obsidian_export.pipeline.stage3_image import (
    DOCX_NATIVE_EXTENSIONS,
    PDF_NATIVE_EXTENSIONS,
    _needs_conversion,
    convert_images,
    convert_images_for_docx,
    convert_images_for_pdf,
)


def _create_test_image(path: Path, fmt: str) -> None:
    """Create a minimal test image at the given path in the given format."""
    img = Image.new("RGB", (10, 10), color="red")
    img.save(path, format=fmt)


# ── _needs_conversion ────────────────────────────────────────────────────────


class TestNeedsConversion:
    def test_png_not_needed_for_pdf(self) -> None:
        assert not _needs_conversion(".png", PDF_NATIVE_EXTENSIONS)

    def test_jpg_not_needed_for_pdf(self) -> None:
        assert not _needs_conversion(".jpg", PDF_NATIVE_EXTENSIONS)

    def test_webp_needed_for_pdf(self) -> None:
        assert _needs_conversion(".webp", PDF_NATIVE_EXTENSIONS)

    def test_gif_needed_for_pdf(self) -> None:
        assert _needs_conversion(".gif", PDF_NATIVE_EXTENSIONS)

    def test_bmp_needed_for_pdf(self) -> None:
        assert _needs_conversion(".bmp", PDF_NATIVE_EXTENSIONS)

    def test_tiff_needed_for_pdf(self) -> None:
        assert _needs_conversion(".tiff", PDF_NATIVE_EXTENSIONS)

    def test_webp_needed_for_docx(self) -> None:
        assert _needs_conversion(".webp", DOCX_NATIVE_EXTENSIONS)

    def test_gif_not_needed_for_docx(self) -> None:
        assert not _needs_conversion(".gif", DOCX_NATIVE_EXTENSIONS)

    def test_bmp_not_needed_for_docx(self) -> None:
        assert not _needs_conversion(".bmp", DOCX_NATIVE_EXTENSIONS)

    def test_case_insensitive(self) -> None:
        assert not _needs_conversion(".PNG", PDF_NATIVE_EXTENSIONS)


# ── convert_images ───────────────────────────────────────────────────────────


class TestConvertImages:
    def test_no_images_unchanged(self) -> None:
        text = "# Hello\n\nSome text without any images.\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = convert_images(text, Path(tmpdir), resource_path=None, native_extensions=PDF_NATIVE_EXTENSIONS)
        assert result == text

    def test_native_png_unchanged_for_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img = workdir / "photo.png"
            _create_test_image(img, "PNG")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![photo]({img})\n"
            result = convert_images(text, tmpdir, resource_path=None, native_extensions=PDF_NATIVE_EXTENSIONS)
            assert result == text

    def test_svg_skipped(self) -> None:
        text = "![diagram](figure.svg)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = convert_images(text, Path(tmpdir), resource_path=None, native_extensions=PDF_NATIVE_EXTENSIONS)
        assert result == text

    def test_url_image_unchanged(self) -> None:
        text = "![photo](https://example.com/pic.webp)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = convert_images(text, Path(tmpdir), resource_path=None, native_extensions=PDF_NATIVE_EXTENSIONS)
        assert result == text

    def test_webp_converted_for_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img = workdir / "photo.webp"
            _create_test_image(img, "WEBP")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![my photo]({img})\n"
            result = convert_images_for_pdf(text, tmpdir, resource_path=None)

            assert "photo.webp" not in result
            assert "img_1.png" in result
            png_path = tmpdir / "img_1.png"
            assert png_path.exists()
            assert png_path.stat().st_size > 0

    def test_gif_converted_for_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img = workdir / "anim.gif"
            _create_test_image(img, "GIF")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![animation]({img})\n"
            result = convert_images_for_pdf(text, tmpdir, resource_path=None)

            assert "anim.gif" not in result
            assert "img_1.png" in result

    def test_bmp_converted_for_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img = workdir / "image.bmp"
            _create_test_image(img, "BMP")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![bitmap]({img})\n"
            result = convert_images_for_pdf(text, tmpdir, resource_path=None)

            assert "image.bmp" not in result
            assert "img_1.png" in result

    def test_tiff_converted_for_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img = workdir / "scan.tiff"
            _create_test_image(img, "TIFF")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![scan]({img})\n"
            result = convert_images_for_pdf(text, tmpdir, resource_path=None)

            assert "scan.tiff" not in result
            assert "img_1.png" in result

    def test_gif_not_converted_for_docx(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img = workdir / "anim.gif"
            _create_test_image(img, "GIF")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![animation]({img})\n"
            result = convert_images_for_docx(text, tmpdir, resource_path=None)

            assert result == text

    def test_webp_converted_for_docx(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img = workdir / "photo.webp"
            _create_test_image(img, "WEBP")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![photo]({img})\n"
            result = convert_images_for_docx(text, tmpdir, resource_path=None)

            assert "photo.webp" not in result
            assert "img_1.png" in result

    def test_multiple_images_converted(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img_a = workdir / "a.webp"
            img_b = workdir / "b.bmp"
            _create_test_image(img_a, "WEBP")
            _create_test_image(img_b, "BMP")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![first]({img_a})\n\nSome text.\n\n![second]({img_b})\n"
            result = convert_images_for_pdf(text, tmpdir, resource_path=None)

            assert "img_1.png" in result
            assert "img_2.png" in result
            assert (tmpdir / "img_1.png").exists()
            assert (tmpdir / "img_2.png").exists()

    def test_relative_path_resolved_against_resource_path(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img = workdir / "photo.webp"
            _create_test_image(img, "WEBP")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = "![photo](photo.webp)\n"
            result = convert_images_for_pdf(text, tmpdir, resource_path=workdir)

            assert "img_1.png" in result


# ── Path traversal ───────────────────────────────────────────────────────────


class TestPathTraversal:
    def test_relative_path_escaping_root_raises(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            outside = workdir / "outside.webp"
            _create_test_image(outside, "WEBP")

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = "![escape](../outside.webp)\n"
            with pytest.raises(PathTraversalError, match="Image path escapes document root"):
                convert_images_for_pdf(text, tmpdir, resource_path=vault)

    def test_absolute_path_outside_root_raises(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            outside = workdir / "outside.webp"
            _create_test_image(outside, "WEBP")

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![escape]({outside})\n"
            with pytest.raises(PathTraversalError, match="Image path escapes document root"):
                convert_images_for_pdf(text, tmpdir, resource_path=vault)

    def test_path_within_root_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            img = vault / "photo.webp"
            _create_test_image(img, "WEBP")

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = "![ok](photo.webp)\n"
            result = convert_images_for_pdf(text, tmpdir, resource_path=vault)
            assert "img_1.png" in result


# ── Error handling ───────────────────────────────────────────────────────────


class TestErrorHandling:
    def test_missing_file_raises_image_conversion_error(self) -> None:
        text = "![photo](/tmp/nonexistent_abc123.webp)\n"
        with tempfile.TemporaryDirectory() as tmpdir, pytest.raises(ImageConversionError, match="Image file not found"):
            convert_images_for_pdf(text, Path(tmpdir), resource_path=None)

    def test_pillow_failure_raises_image_conversion_error(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img = workdir / "corrupt.webp"
            img.write_bytes(b"not a real image")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![broken]({img})\n"
            with pytest.raises(ImageConversionError, match="Failed to convert"):
                convert_images_for_pdf(text, tmpdir, resource_path=None)

    def test_error_chains_original(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            img = workdir / "corrupt.webp"
            img.write_bytes(b"not a real image")
            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![broken]({img})\n"
            with pytest.raises(ImageConversionError) as exc_info:
                convert_images_for_pdf(text, tmpdir, resource_path=None)
            assert exc_info.value.__cause__ is not None
