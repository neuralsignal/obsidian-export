"""Tests for obsidian_export.pipeline.stage1_vault."""

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from obsidian_export.exceptions import CircularEmbedError, EmbedNotFoundError, PathTraversalError
from obsidian_export.pipeline.stage1_vault import (
    _extract_section,
    clean_frontmatter,
    parse_frontmatter,
    resolve_embeds,
    strip_leading_title,
    strip_obsidian_syntax,
)

# ── parse_frontmatter ────────────────────────────────────────────────────────


class TestParseFrontmatter:
    def test_no_frontmatter(self) -> None:
        text = "# Hello\n\nSome content."
        fm, body = parse_frontmatter(text)
        assert fm == {}
        assert body == text

    def test_extracts_title(self) -> None:
        text = "---\ntitle: My Note\n---\nBody text."
        fm, body = parse_frontmatter(text)
        assert fm["title"] == "My Note"
        assert body == "Body text."

    def test_extracts_date(self) -> None:
        import datetime

        text = "---\ndate: 2026-03-05\n---\nBody."
        fm, _ = parse_frontmatter(text)
        assert fm["date"] == datetime.date(2026, 3, 5)

    def test_strips_frontmatter_from_body(self) -> None:
        text = "---\ntitle: T\n---\nContent here."
        _, body = parse_frontmatter(text)
        assert "---" not in body
        assert "title:" not in body

    def test_empty_frontmatter(self) -> None:
        text = "---\n---\nBody."
        fm, body = parse_frontmatter(text)
        assert fm == {} or fm is None or fm == {}
        assert "Body." in body

    def test_list_values(self) -> None:
        text = "---\ntags:\n  - ai\n  - engineering\n---\nBody."
        fm, _ = parse_frontmatter(text)
        assert fm["tags"] == ["ai", "engineering"]

    def test_non_frontmatter_dashes_not_consumed(self) -> None:
        text = "# Heading\n\n---\n\nHR divider."
        fm, body = parse_frontmatter(text)
        assert fm == {}
        assert "---" in body

    def test_returns_empty_dict_on_no_frontmatter(self) -> None:
        fm, _ = parse_frontmatter("No frontmatter here.")
        assert isinstance(fm, dict)

    def test_title_with_colon(self) -> None:
        """Obsidian allows unquoted colons in values — parser must handle this."""
        text = "---\ntitle: Memory: Knowledge folder consolidation\ntype: memory\n---\nBody."
        fm, body = parse_frontmatter(text)
        assert fm["title"] == "Memory: Knowledge folder consolidation"
        assert fm["type"] == "memory"
        assert "Body." in body

    def test_title_with_colon_and_dash(self) -> None:
        text = "---\ntitle: Memory: Azure Setup — Obungi CSP & MTF\n---\nBody."
        fm, body = parse_frontmatter(text)
        assert fm["title"] == "Memory: Azure Setup — Obungi CSP & MTF"
        assert "Body." in body

    def test_valid_yaml_with_colon_not_broken(self) -> None:
        """Ensure properly quoted values still work after the fix."""
        text = '---\ntitle: "Already: Quoted"\n---\nBody.'
        fm, _ = parse_frontmatter(text)
        assert fm["title"] == "Already: Quoted"


# ── clean_frontmatter ────────────────────────────────────────────────────────


class TestCleanFrontmatter:
    def test_strips_obsidian_keys(self) -> None:
        fm = {"title": "T", "aliases": ["a", "b"], "tags": ["x"], "cssclass": "wide"}
        cleaned = clean_frontmatter(fm)
        assert "aliases" not in cleaned
        assert "cssclass" not in cleaned

    def test_keeps_title(self) -> None:
        fm = {"title": "Keep Me", "tags": []}
        cleaned = clean_frontmatter(fm)
        assert cleaned["title"] == "Keep Me"

    def test_converts_tag_list_to_keywords(self) -> None:
        fm = {"tags": ["ai", "engineering", "phase1"]}
        cleaned = clean_frontmatter(fm)
        assert "keywords" in cleaned
        assert "ai" in cleaned["keywords"]

    def test_converts_tag_string_to_keywords(self) -> None:
        fm = {"tags": "ai"}
        cleaned = clean_frontmatter(fm)
        assert cleaned["keywords"] == "ai"

    def test_strips_banner(self) -> None:
        fm = {"title": "T", "banner": "some/image.png"}
        cleaned = clean_frontmatter(fm)
        assert "banner" not in cleaned


# ── strip_obsidian_syntax ────────────────────────────────────────────────────


class TestStripObsidianSyntax:
    def test_removes_embeds(self) -> None:
        assert "![[note]]" not in strip_obsidian_syntax("![[note]] text")

    def test_pipe_link_to_display(self) -> None:
        result = strip_obsidian_syntax("See [[Entity|Display Text]].")
        assert "Display Text" in result
        assert "[[" not in result

    def test_bare_link_to_entity(self) -> None:
        result = strip_obsidian_syntax("See [[Entity Name]].")
        assert "Entity Name" in result
        assert "[[" not in result

    def test_callout_label_preserved(self) -> None:
        text = "> [!NOTE] Title\n> Content here.\n"
        result = strip_obsidian_syntax(text)
        assert "[!NOTE]" in result
        assert "Content here." in result

    def test_relations_section_removed(self) -> None:
        text = "# Body\n\nContent.\n\n## Relations\n\n- relates_to [[goal]]\n"
        result = strip_obsidian_syntax(text)
        assert "Relations" not in result
        assert "relates_to" not in result

    def test_plain_markdown_unchanged(self) -> None:
        text = "# Heading\n\nParagraph with **bold** and *italic*.\n"
        result = strip_obsidian_syntax(text)
        assert result == text

    def test_multiple_embeds_removed(self) -> None:
        text = "![[a]] and ![[b]] and ![[c]]"
        result = strip_obsidian_syntax(text)
        assert "![[" not in result

    def test_multiple_links_resolved(self) -> None:
        text = "[[A]] and [[B|B display]]"
        result = strip_obsidian_syntax(text)
        assert "A" in result
        assert "B display" in result
        assert "[[" not in result

    def test_inline_hashtag_preserved(self) -> None:
        text = "Tagged with #ai and #engineering."
        result = strip_obsidian_syntax(text)
        assert "#ai" in result

    def test_relations_case_insensitive(self) -> None:
        text = "Body.\n\n## RELATIONS\n\nstuff"
        result = strip_obsidian_syntax(text)
        assert "RELATIONS" not in result


# ── strip_leading_title ─────────────────────────────────────────────────────


class TestStripLeadingTitle:
    def test_matching_h1_stripped(self) -> None:
        body = "# My Title\n\nBody text."
        result = strip_leading_title(body, "My Title")
        assert "# My Title" not in result
        assert "Body text." in result
        assert "# My Title" not in result

    def test_non_matching_h1_kept(self) -> None:
        body = "# Different Heading\n\nBody text."
        result = strip_leading_title(body, "My Title")
        assert result == body

    def test_no_h1_at_start(self) -> None:
        body = "Some paragraph.\n\n# Heading Later\n\nMore text."
        result = strip_leading_title(body, "Heading Later")
        assert result == body

    def test_title_from_stem_no_match(self) -> None:
        body = "# Actual Heading\n\nBody text."
        result = strip_leading_title(body, "20260303_exec_summary")
        assert result == body

    def test_leading_whitespace_before_h1(self) -> None:
        body = "\n\n# My Title\n\nBody text."
        result = strip_leading_title(body, "My Title")
        assert "# My Title" not in result
        assert "Body text." in result

    def test_h1_with_pandoc_attributes(self) -> None:
        body = "# My Title {.unnumbered}\n\nBody text."
        result = strip_leading_title(body, "My Title")
        assert "# My Title" not in result
        assert "Body text." in result


# ── Property-based tests ─────────────────────────────────────────────────────


@given(st.text())
@settings(max_examples=200)
def test_strip_never_raises(text: str) -> None:
    strip_obsidian_syntax(text)


@given(st.text())
@settings(max_examples=200)
def test_parse_never_raises(text: str) -> None:
    parse_frontmatter(text)


@given(st.text())
@settings(max_examples=100)
def test_strip_is_idempotent(text: str) -> None:
    once = strip_obsidian_syntax(text)
    twice = strip_obsidian_syntax(once)
    assert once == twice


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
