"""Tests for obsidian_export.pipeline.stage2_preprocess."""

import dataclasses

from hypothesis import given, settings
from hypothesis import strategies as st

from obsidian_export.config import ObsidianConfig, default_config
from obsidian_export.pipeline.stage2_preprocess import (
    _footnote_bare_urls,
    _should_footnote_url,
    _strip_bare_urls,
    convert_callouts,
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

    def test_title_with_double_quotes_escaped(self) -> None:
        text = '> [!NOTE] My "important" note\n> Content.\n'
        result = convert_callouts(text)
        assert "&quot;" in result
        assert 'title="My &quot;important&quot; note"' in result

    def test_title_with_backslash_escaped(self) -> None:
        text = "> [!NOTE] Path C:\\Users\n> Content.\n"
        result = convert_callouts(text)
        assert "C:\\\\Users" in result


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

    def test_footnote_all_moves_url(self) -> None:
        text = "See https://example.com for details."
        result = process_urls(text, "footnote_all", 60)
        assert result != text

    def test_footnote_all_no_duplicate_definitions(self) -> None:
        url = "https://example.com/page"
        text = f"First {url} and second {url} reference."
        result = process_urls(text, "footnote_all", 60)
        definition = f"[^url-1]: <{url}>"
        assert result.count(definition) == 1
        assert result.count("[^url-1]") == 3  # 2 refs + 1 def

    def test_footnote_long_no_duplicate_definitions(self) -> None:
        url = "https://docs.microsoft.com/en-us/azure/cognitive-search/search-what-is-azure-search-very-long"
        text = f"First {url} then {url} again."
        result = process_urls(text, "footnote_long", 60)
        definition = f"[^url-1]: <{url}>"
        assert result.count(definition) == 1

    def test_footnote_definitions_appended_at_end(self) -> None:
        url = "https://example.com"
        text = f"See {url} for details."
        result = process_urls(text, "footnote_all", 60)
        definition = f"[^url-1]: <{url}>"
        assert result.rstrip().endswith(definition)

    def test_footnote_ids_are_sequential(self) -> None:
        url_a = "https://example.com/alpha"
        url_b = "https://example.com/beta"
        text = f"First {url_a} then {url_b} here."
        result = process_urls(text, "footnote_all", 60)
        assert "[^url-1]" in result
        assert "[^url-2]" in result
        assert f"[^url-1]: <{url_a}>" in result
        assert f"[^url-2]: <{url_b}>" in result

    def test_footnote_ids_are_deterministic_across_calls(self) -> None:
        url = "https://example.com/stable"
        text = f"See {url} for details."
        result1 = process_urls(text, "footnote_all", 60)
        result2 = process_urls(text, "footnote_all", 60)
        assert result1 == result2


# ── _should_footnote_url ─────────────────────────────────────────────────────


class TestShouldFootnoteUrl:
    def test_footnote_all_always_true(self) -> None:
        assert _should_footnote_url("https://x.io", "footnote_all", 9999) is True

    def test_footnote_long_above_threshold(self) -> None:
        url = "https://example.com/" + "a" * 100
        assert _should_footnote_url(url, "footnote_long", 60) is True

    def test_footnote_long_below_threshold(self) -> None:
        assert _should_footnote_url("https://x.io", "footnote_long", 60) is False

    def test_footnote_long_at_threshold(self) -> None:
        url = "a" * 60
        assert _should_footnote_url(url, "footnote_long", 60) is False

    def test_other_strategy_always_false(self) -> None:
        assert _should_footnote_url("https://x.io", "keep", 60) is False


# ── _strip_bare_urls ─────────────────────────────────────────────────────────


class TestStripBareUrls:
    def test_removes_bare_url(self) -> None:
        result = _strip_bare_urls("See https://example.com for info.")
        assert "https://" not in result

    def test_preserves_non_url_text(self) -> None:
        text = "No URLs here, just text."
        assert _strip_bare_urls(text) == text


# ── _footnote_bare_urls ──────────────────────────────────────────────────────


class TestFootnoteBareUrls:
    def test_creates_footnote_reference(self) -> None:
        result = _footnote_bare_urls("See https://example.com here.", "footnote_all", 60)
        assert "[^url-1]" in result
        assert "[^url-1]: <https://example.com>" in result

    def test_skips_code_blocks(self) -> None:
        text = "```\nhttps://example.com\n```"
        result = _footnote_bare_urls(text, "footnote_all", 60)
        assert "[^url-" not in result

    def test_deduplicates_same_url(self) -> None:
        url = "https://example.com/page"
        text = f"First {url} and second {url} end."
        result = _footnote_bare_urls(text, "footnote_all", 60)
        assert result.count(f"[^url-1]: <{url}>") == 1
        assert "[^url-2]" not in result


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


@given(
    url=st.from_regex(r"https?://[a-z0-9]{1,50}", fullmatch=True),
    strategy=st.sampled_from(["footnote_all", "footnote_long", "keep", "strip"]),
    threshold=st.integers(min_value=0, max_value=500),
)
@settings(max_examples=200)
def test_should_footnote_url_is_pure_bool(url: str, strategy: str, threshold: int) -> None:
    result = _should_footnote_url(url, strategy, threshold)
    assert isinstance(result, bool)


@given(
    url=st.from_regex(r"https?://[a-z0-9]{1,50}", fullmatch=True),
    threshold=st.integers(min_value=0, max_value=500),
)
@settings(max_examples=200)
def test_footnote_all_always_footnotes(url: str, threshold: int) -> None:
    assert _should_footnote_url(url, "footnote_all", threshold) is True


@given(
    url=st.from_regex(r"https?://[a-z0-9]{1,50}", fullmatch=True),
    threshold=st.integers(min_value=0, max_value=500),
)
@settings(max_examples=200)
def test_footnote_long_respects_threshold(url: str, threshold: int) -> None:
    result = _should_footnote_url(url, "footnote_long", threshold)
    assert result == (len(url) > threshold)


@given(st.text())
@settings(max_examples=100)
def test_strip_bare_urls_never_raises(text: str) -> None:
    _strip_bare_urls(text)


@given(st.text())
@settings(max_examples=100)
def test_footnote_bare_urls_never_raises(text: str) -> None:
    _footnote_bare_urls(text, "footnote_all", 60)
