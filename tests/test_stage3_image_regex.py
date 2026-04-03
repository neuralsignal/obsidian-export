"""Tests for image reference regex and IMAGE_EXTENSIONS coverage."""

from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st
from PIL import Image

from obsidian_export.pipeline.stage3_image import _IMG_REF_RE


def _create_test_image(path: Path, fmt: str) -> None:
    """Create a minimal test image at the given path in the given format."""
    img = Image.new("RGB", (10, 10), color="red")
    img.save(path, format=fmt)


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
