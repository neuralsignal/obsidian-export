"""Tests for obsidian_export.pipeline.stage2_preprocess."""

import dataclasses

from hypothesis import given, settings
from hypothesis import strategies as st

from obsidian_export.config import ObsidianConfig, default_config
from obsidian_export.pipeline.stage2_preprocess import (
    convert_callouts,
    count_headings,
    escape_dollar_signs,
    normalize_line_endings,
    preprocess,
    process_urls,
)


def _make_config(**overrides) -> ObsidianConfig:
    """Build ObsidianConfig from default_config(), applying overrides."""
    base = default_config().obsidian
    fields = {f.name: getattr(base, f.name) for f in dataclasses.fields(base)}
    fields.update(overrides)
    return ObsidianConfig(**fields)


# ── escape_dollar_signs ───────────────────────────────────────────────────────


class TestEscapeDollarSigns:
    def test_currency_dollar_escaped(self) -> None:
        result = escape_dollar_signs("Price: $25/user/month")
        assert r"\$" in result

    def test_code_block_untouched(self) -> None:
        text = "```python\nprice = $25\n```"
        result = escape_dollar_signs(text)
        assert "$25" in result
        assert r"\$" not in result

    def test_display_math_untouched(self) -> None:
        text = "$$E = mc^2$$"
        result = escape_dollar_signs(text)
        assert "$$E = mc^2$$" in result

    def test_multiple_currency_signs(self) -> None:
        result = escape_dollar_signs("$10 and $20 and $30")
        assert result.count(r"\$") == 3

    def test_no_dollar_unchanged(self) -> None:
        text = "No dollar signs here."
        assert escape_dollar_signs(text) == text

    def test_table_with_prices(self) -> None:
        text = "| Plan | $25/mo |\n|------|--------|\n| Pro | $50/mo |"
        result = escape_dollar_signs(text)
        assert r"\$25" in result
        assert r"\$50" in result


# ── convert_callouts ──────────────────────────────────────────────────────────


class TestConvertCallouts:
    def test_note_callout_to_fenced_div(self) -> None:
        text = "> [!NOTE] Important\n> Content line.\n"
        result = convert_callouts(text)
        assert ":::" in result
        assert ".note" in result
        assert "Important" in result
        assert "Content line." in result

    def test_warning_callout(self) -> None:
        text = "> [!WARNING] Be Careful\n> Warning content.\n"
        result = convert_callouts(text)
        assert ".warning" in result
        assert "Be Careful" in result

    def test_plain_blockquote_unchanged(self) -> None:
        text = "> This is a regular blockquote.\n"
        result = convert_callouts(text)
        assert result == text

    def test_callout_without_title(self) -> None:
        text = "> [!TIP]\n> Tip content.\n"
        result = convert_callouts(text)
        assert ":::" in result
        assert ".tip" in result

    def test_multiple_callouts(self) -> None:
        text = "> [!NOTE] First\n> Content A.\n\n> [!WARNING] Second\n> Content B.\n"
        result = convert_callouts(text)
        assert result.count(":::") >= 2


# ── process_urls ──────────────────────────────────────────────────────────────


class TestProcessUrls:
    def test_keep_strategy_unchanged(self) -> None:
        text = "See https://example.com for details."
        assert process_urls(text, "keep", 60) == text

    def test_strip_removes_bare_url(self) -> None:
        text = "See https://example.com for details."
        result = process_urls(text, "strip", 60)
        assert "https://" not in result

    def test_footnote_long_moves_long_url(self) -> None:
        long_url = "https://docs.microsoft.com/en-us/azure/cognitive-search/search-what-is-azure-search-very-long"
        text = f"Check {long_url} for info."
        result = process_urls(text, "footnote_long", 60)
        # Long URL should appear in a footnote reference
        assert len(long_url) > 60
        # Result should be different from input
        assert result != text

    def test_footnote_long_keeps_short_url(self) -> None:
        short_url = "https://short.io/abc"
        text = f"See {short_url}."
        result = process_urls(text, "footnote_long", 60)
        assert short_url in result


# ── normalize_line_endings ────────────────────────────────────────────────────


class TestNormalizeLineEndings:
    def test_crlf_to_lf(self) -> None:
        result = normalize_line_endings("line1\r\nline2\r\n")
        assert "\r" not in result
        assert result == "line1\nline2\n"

    def test_trailing_whitespace_stripped(self) -> None:
        result = normalize_line_endings("line with spaces   \nclean line\n")
        lines = result.split("\n")
        assert lines[0] == "line with spaces"

    def test_content_preserved(self) -> None:
        text = "Hello\nWorld"
        result = normalize_line_endings(text)
        assert "Hello" in result
        assert "World" in result


# ── count_headings ───────────────────────────────────────────────────────────


class TestCountHeadings:
    def test_no_headings(self) -> None:
        assert count_headings("No headings here.\nJust text.") == 0

    def test_single_heading(self) -> None:
        assert count_headings("# Title\nSome text.") == 1

    def test_multiple_heading_levels(self) -> None:
        text = "# H1\n## H2\n### H3\ntext\n#### H4"
        assert count_headings(text) == 4

    def test_indented_heading(self) -> None:
        assert count_headings("  # Indented heading") == 1

    def test_empty_string(self) -> None:
        assert count_headings("") == 0

    def test_hash_in_code_counted(self) -> None:
        # count_headings is a simple text counter, not Markdown-aware
        text = "# Real heading\n```\n# comment in code\n```"
        assert count_headings(text) == 2


# ── preprocess (integration) ─────────────────────────────────────────────────


class TestPreprocess:
    def test_full_preprocess_runs(self) -> None:
        config = _make_config()
        text = "Price: $25/user/month\n\n> [!NOTE] Title\n> Content.\n"
        result = preprocess(text, config)
        assert r"\$" in result
        assert ":::" in result

    def test_code_blocks_not_modified(self) -> None:
        config = _make_config()
        text = "```python\nprice = $25  # keep this\n```"
        result = preprocess(text, config)
        assert "$25" in result


# ── Property-based tests ─────────────────────────────────────────────────────


@given(st.text())
@settings(max_examples=100)
def test_escape_never_raises(text: str) -> None:
    escape_dollar_signs(text)


@given(st.text())
@settings(max_examples=100)
def test_callout_never_raises(text: str) -> None:
    convert_callouts(text)


@given(st.text())
@settings(max_examples=100)
def test_normalize_never_raises(text: str) -> None:
    normalize_line_endings(text)
