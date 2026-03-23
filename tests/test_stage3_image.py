"""Tests for stage3_image: non-SVG image conversion to PNG."""

import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st
from PIL import Image

from obsidian_export.exceptions import ImageConversionError, PathTraversalError
from obsidian_export.pipeline.stage3_image import (
    _IMG_REF_RE,
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


# ── Regex tests ──────────────────────────────────────────────────────────────


class TestImgRefRegex:
    def test_matches_png(self) -> None:
        m = _IMG_REF_RE.search("![alt](path/to/file.png)")
        assert m is not None
        assert m.group(2) == "path/to/file.png"

    def test_matches_webp(self) -> None:
        m = _IMG_REF_RE.search("![alt](image.webp)")
        assert m is not None

    def test_matches_svg(self) -> None:
        m = _IMG_REF_RE.search("![alt](diagram.svg)")
        assert m is not None

    @given(
        ext=st.sampled_from([".png", ".jpg", ".webp", ".gif", ".bmp", ".tiff", ".avif", ".svg"]),
        alt=st.text(alphabet=st.characters(blacklist_characters="]"), min_size=0, max_size=20),
    )
    def test_any_image_extension_matched(self, ext: str, alt: str) -> None:
        text = f"![{alt}](image{ext})"
        m = _IMG_REF_RE.search(text)
        assert m is not None

    @given(
        body=st.text(alphabet=st.characters(blacklist_characters="![]()", min_codepoint=32), min_size=0, max_size=100)
    )
    def test_plain_text_never_matches(self, body: str) -> None:
        assert _IMG_REF_RE.search(body) is None


# ── Stage 1 IMAGE_EXTENSIONS tests ──────────────────────────────────────────


class TestImageExtensions:
    """Test that the IMAGE_EXTENSIONS constant in stage1_vault covers all expected formats."""

    def test_original_extensions_present(self) -> None:
        from obsidian_export.pipeline.stage1_vault import IMAGE_EXTENSIONS

        for ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"):
            assert ext in IMAGE_EXTENSIONS, f"{ext} missing from IMAGE_EXTENSIONS"

    def test_new_extensions_present(self) -> None:
        from obsidian_export.pipeline.stage1_vault import IMAGE_EXTENSIONS

        for ext in (".bmp", ".tiff", ".tif", ".avif"):
            assert ext in IMAGE_EXTENSIONS, f"{ext} missing from IMAGE_EXTENSIONS"

    def test_image_embed_bmp(self, tmp_path: Path) -> None:
        from obsidian_export.pipeline.stage1_vault import resolve_embeds

        img = tmp_path / "photo.bmp"
        _create_test_image(img, "BMP")
        text = "![[photo.bmp]]"
        result = resolve_embeds(text, tmp_path, tmp_path / "note.md", 10)
        assert "![](" in result
        assert "![[" not in result

    def test_image_embed_tiff(self, tmp_path: Path) -> None:
        from obsidian_export.pipeline.stage1_vault import resolve_embeds

        img = tmp_path / "scan.tiff"
        _create_test_image(img, "TIFF")
        text = "![[scan.tiff]]"
        result = resolve_embeds(text, tmp_path, tmp_path / "note.md", 10)
        assert "![](" in result

    def test_image_embed_avif(self, tmp_path: Path) -> None:
        from obsidian_export.pipeline.stage1_vault import resolve_embeds

        img = tmp_path / "photo.avif"
        # AVIF may not be supported by all Pillow builds, write raw bytes
        img.write_bytes(b"\x00\x00\x00\x00")
        text = "![[photo.avif]]"
        result = resolve_embeds(text, tmp_path, tmp_path / "note.md", 10)
        assert "![](" in result

    @given(ext=st.sampled_from([".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp", ".tiff", ".tif", ".avif"]))
    def test_all_image_extensions_recognized(self, ext: str) -> None:
        from obsidian_export.pipeline.stage1_vault import IMAGE_EXTENSIONS

        assert ext in IMAGE_EXTENSIONS
