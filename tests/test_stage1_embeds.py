"""Tests for stage1_vault: embed resolution, image embeds, note paths, section extraction."""

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from obsidian_export.exceptions import CircularEmbedError, EmbedNotFoundError, PathTraversalError
from obsidian_export.pipeline.stage1_vault import (
    _extract_section,
    _resolve_image_embed,
    _resolve_note_path,
    resolve_embeds,
)

# ── resolve_embeds ────────────────────────────────────────────────────────────


class TestResolveEmbeds:
    def test_no_embeds_unchanged(self, tmp_path: Path) -> None:
        text = "# Heading\n\nContent without embeds."
        result = resolve_embeds(text, tmp_path, tmp_path / "note.md", 10)
        assert result == text

    def test_resolves_existing_note(self, tmp_path: Path) -> None:
        (tmp_path / "other.md").write_text("# Other\n\nOther content.", encoding="utf-8")
        text = "Before ![[other]] After"
        result = resolve_embeds(text, tmp_path, tmp_path / "note.md", 10)
        assert "Other content." in result
        assert "![[" not in result

    def test_missing_embed_raises(self, tmp_path: Path) -> None:
        text = "![[nonexistent]]"
        with pytest.raises(EmbedNotFoundError, match="nonexistent"):
            resolve_embeds(text, tmp_path, tmp_path / "note.md", 10)

    def test_circular_embed_raises(self, tmp_path: Path) -> None:
        # a embeds b, b embeds a
        (tmp_path / "a.md").write_text("A content ![[b]]", encoding="utf-8")
        (tmp_path / "b.md").write_text("B content ![[a]]", encoding="utf-8")
        text = "![[a]]"
        with pytest.raises(CircularEmbedError, match="Circular embed"):
            resolve_embeds(text, tmp_path, tmp_path / "root.md", 10)

    def test_image_embed_becomes_markdown_image(self, tmp_path: Path) -> None:
        img = tmp_path / "diagram.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG header
        text = "![[diagram.png]]"
        result = resolve_embeds(text, tmp_path, tmp_path / "note.md", 10)
        assert "![](" in result
        assert "![[" not in result

    def test_section_embed_extracts_section(self, tmp_path: Path) -> None:
        (tmp_path / "doc.md").write_text(
            "# Intro\nIntro text.\n\n## Section A\nSection A content.\n\n## Section B\nSection B content.",
            encoding="utf-8",
        )
        text = "![[doc#Section A]]"
        result = resolve_embeds(text, tmp_path, tmp_path / "note.md", 10)
        assert "Section A content." in result
        assert "Section B content." not in result

    def test_path_traversal_note_raises(self, tmp_path: Path) -> None:
        """Embed paths that escape vault root must raise PathTraversalError."""
        vault = tmp_path / "vault"
        vault.mkdir()
        outside = tmp_path / "secret.md"
        outside.write_text("secret contents", encoding="utf-8")
        text = "![[../secret]]"
        with pytest.raises(PathTraversalError):
            resolve_embeds(text, vault, vault / "note.md", 10)

    def test_path_traversal_image_raises(self, tmp_path: Path) -> None:
        """Image embed paths that escape vault root must raise PathTraversalError."""
        vault = tmp_path / "vault"
        vault.mkdir()
        outside = tmp_path / "secret.png"
        outside.write_bytes(b"\x89PNG\r\n\x1a\n")
        text = "![[../secret.png]]"
        with pytest.raises(PathTraversalError):
            resolve_embeds(text, vault, vault / "note.md", 10)

    def test_depth_exceeded_returns_content_unchanged(self, tmp_path: Path) -> None:
        """When recursion depth exceeds max_embed_depth, embeds are not resolved."""
        (tmp_path / "a.md").write_text("A content ![[b]]", encoding="utf-8")
        (tmp_path / "b.md").write_text("B content", encoding="utf-8")
        # max_embed_depth=0 means the very first recursive call (depth=1) exceeds the cap
        text = "![[a]]"
        result = resolve_embeds(text, tmp_path, tmp_path / "root.md", max_embed_depth=0)
        # The top-level call (depth=0) resolves a.md, but a.md's embed of b is not resolved
        assert "A content" in result
        assert "![[b]]" in result

    def test_image_embed_rglob_fallback(self, tmp_path: Path) -> None:
        """Image not at direct path but found via rglob in a subdirectory."""
        subdir = tmp_path / "assets" / "images"
        subdir.mkdir(parents=True)
        img = subdir / "photo.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n")
        # Embed references just the filename, not the subdirectory path
        text = "![[photo.png]]"
        result = resolve_embeds(text, tmp_path, tmp_path / "note.md", max_embed_depth=10)
        assert f"![]({img})" == result

    def test_image_embed_missing_fallback(self, tmp_path: Path) -> None:
        """Image not found anywhere returns a broken image ref without raising."""
        text = "![[nonexistent.png]]"
        result = resolve_embeds(text, tmp_path, tmp_path / "note.md", max_embed_depth=10)
        assert "![nonexistent.png](" in result
        assert "nonexistent.png)" in result


# ── _resolve_image_embed ─────────────────────────────────────────────────────


class TestResolveImageEmbed:
    def test_existing_image_resolved(self, tmp_path: Path) -> None:
        img = tmp_path / "photo.png"
        img.write_bytes(b"\x89PNG")
        result = _resolve_image_embed("photo.png", tmp_path, tmp_path.resolve())
        assert result == f"![]({img.resolve()})"

    def test_rglob_fallback(self, tmp_path: Path) -> None:
        subdir = tmp_path / "assets"
        subdir.mkdir()
        img = subdir / "photo.png"
        img.write_bytes(b"\x89PNG")
        result = _resolve_image_embed("photo.png", tmp_path, tmp_path.resolve())
        assert result == f"![]({img})"

    def test_missing_image_returns_broken_ref(self, tmp_path: Path) -> None:
        result = _resolve_image_embed("gone.png", tmp_path, tmp_path.resolve())
        assert "![gone.png](" in result

    def test_traversal_raises(self, tmp_path: Path) -> None:
        vault = tmp_path / "vault"
        vault.mkdir()
        outside = tmp_path / "secret.png"
        outside.write_bytes(b"\x89PNG")
        with pytest.raises(PathTraversalError):
            _resolve_image_embed("../secret.png", vault, vault.resolve())


# ── _resolve_note_path ──────────────────────────────────────────────────────


class TestResolveNotePath:
    def test_finds_in_vault_root(self, tmp_path: Path) -> None:
        (tmp_path / "note.md").write_text("content", encoding="utf-8")
        result = _resolve_note_path("note", tmp_path, tmp_path / "other.md")
        assert result == tmp_path / "note.md"

    def test_falls_back_to_current_dir(self, tmp_path: Path) -> None:
        subdir = tmp_path / "sub"
        subdir.mkdir()
        (subdir / "local.md").write_text("content", encoding="utf-8")
        result = _resolve_note_path("local", tmp_path, subdir / "current.md")
        assert result == subdir / "local.md"

    def test_missing_raises(self, tmp_path: Path) -> None:
        with pytest.raises(EmbedNotFoundError, match="nope"):
            _resolve_note_path("nope", tmp_path, tmp_path / "current.md")


# ── _extract_section ─────────────────────────────────────────────────────────


class TestExtractSection:
    def test_heading_not_found(self) -> None:
        text = "# Intro\n\nSome content.\n\n## Other\n\nMore content."
        result = _extract_section(text, "Nonexistent")
        assert result == "[Section 'Nonexistent' not found]"

    def test_section_extends_to_eof(self) -> None:
        """Target heading has no subsequent same-level heading — content to EOF."""
        text = "# Intro\n\nIntro text.\n\n## Last Section\n\nFinal content here."
        result = _extract_section(text, "Last Section")
        assert result == "Final content here."

    def test_section_between_headings(self) -> None:
        text = "## A\n\nA content.\n\n## B\n\nB content.\n\n## C\n\nC content."
        result = _extract_section(text, "B")
        assert result == "B content."

    def test_case_insensitive_heading_match(self) -> None:
        text = "## my heading\n\nContent here.\n\n## Other\n\nOther content."
        result = _extract_section(text, "My Heading")
        assert result == "Content here."


# ── Property-based: _extract_section ─────────────────────────────────────────


@given(st.text(alphabet=st.characters(categories=("L", "N", "Z")), min_size=1, max_size=50))
@settings(max_examples=100)
def test_extract_section_not_found_returns_sentinel(heading: str) -> None:
    """For any heading not present in empty text, the sentinel string is returned."""
    result = _extract_section("No headings here.", heading)
    assert result == f"[Section '{heading}' not found]"
