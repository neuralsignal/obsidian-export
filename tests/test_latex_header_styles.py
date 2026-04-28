"""Tests for LaTeX heading/title style blocks and string processing."""

import dataclasses

import pytest

from obsidian_export.config import HeadingStyle, StyleConfig, TitleStyle, default_config
from obsidian_export.exceptions import UnsafeLatexError
from obsidian_export.pipeline.latex_header import (
    _build_heading_styles_block,
    _build_title_style_block,
    _escape_latex,
    _substitute_placeholders,
    _truncate_title,
)


def _make_style(**overrides) -> StyleConfig:
    """Build StyleConfig from default_config(), applying overrides."""
    base = default_config().style
    fields = {f.name: getattr(base, f.name) for f in dataclasses.fields(base)}
    fields.update(overrides)
    return StyleConfig(**fields)


class TestBuildHeadingStylesBlock:
    def test_empty_returns_empty(self) -> None:
        assert _build_heading_styles_block(()) == ""

    def test_single_level(self) -> None:
        styles = (HeadingStyle(level="section", size="Large", bold=True, sans=True, color="petrol", uppercase=False),)
        result = _build_heading_styles_block(styles)
        assert "\\usepackage{titlesec}" in result
        assert "\\titleformat{\\section}" in result
        assert "\\Large" in result
        assert "\\bfseries" in result
        assert "\\sffamily" in result
        assert "\\color{petrol}" in result

    def test_uppercase_flag(self) -> None:
        styles = (HeadingStyle(level="subsection", size="large", bold=True, sans=True, color="turkis", uppercase=True),)
        result = _build_heading_styles_block(styles)
        assert "\\MakeUppercase" in result

    def test_no_uppercase(self) -> None:
        styles = (HeadingStyle(level="section", size="Large", bold=True, sans=False, color="", uppercase=False),)
        result = _build_heading_styles_block(styles)
        assert "\\MakeUppercase" not in result
        assert "\\sffamily" not in result

    def test_all_three_levels(self) -> None:
        styles = (
            HeadingStyle(level="section", size="Large", bold=True, sans=True, color="petrol", uppercase=False),
            HeadingStyle(level="subsection", size="large", bold=True, sans=True, color="turkis", uppercase=True),
            HeadingStyle(
                level="subsubsection", size="normalsize", bold=True, sans=True, color="petrol", uppercase=False
            ),
        )
        result = _build_heading_styles_block(styles)
        assert "\\titleformat{\\section}" in result
        assert "\\titleformat{\\subsection}" in result
        assert "\\titleformat{\\subsubsection}" in result

    def test_invalid_level_rejected(self) -> None:
        styles = (
            HeadingStyle(
                level="section}\\write18{cmd", size="Large", bold=False, sans=False, color="", uppercase=False
            ),
        )
        with pytest.raises(UnsafeLatexError, match="heading_styles.level"):
            _build_heading_styles_block(styles)

    def test_unknown_level_rejected(self) -> None:
        styles = (HeadingStyle(level="write18", size="Large", bold=False, sans=False, color="", uppercase=False),)
        with pytest.raises(UnsafeLatexError, match="heading_styles.level"):
            _build_heading_styles_block(styles)

    def test_dangerous_macro_in_size_rejected(self) -> None:
        styles = (HeadingStyle(level="section", size="write18", bold=False, sans=False, color="", uppercase=False),)
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_heading_styles_block(styles)

    def test_injection_in_size_rejected(self) -> None:
        styles = (
            HeadingStyle(
                level="section", size="Large}\\write18{cmd", bold=False, sans=False, color="", uppercase=False
            ),
        )
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_heading_styles_block(styles)

    def test_injection_in_color_escaped(self) -> None:
        styles = (
            HeadingStyle(
                level="section", size="Large", bold=False, sans=False, color="petrol}\\write18{cmd", uppercase=False
            ),
        )
        result = _build_heading_styles_block(styles)
        assert "\\write18" not in result

    def test_valid_levels_accepted(self) -> None:
        for level in ("section", "subsection", "subsubsection", "paragraph", "subparagraph"):
            styles = (HeadingStyle(level=level, size="Large", bold=False, sans=False, color="", uppercase=False),)
            result = _build_heading_styles_block(styles)
            assert f"\\titleformat{{\\{level}}}" in result


class TestBuildTitleStyleBlock:
    def test_none_returns_empty(self) -> None:
        assert _build_title_style_block(None) == ""

    def test_with_style(self) -> None:
        ts = TitleStyle(size="huge", bold=True, sans=True, color="petrol", date_visible=True, vskip_after="2em")
        result = _build_title_style_block(ts)
        assert "\\makeatletter" in result
        assert "\\makeatother" in result
        assert "\\renewcommand{\\maketitle}" in result
        assert "\\huge" in result
        assert "\\bfseries" in result
        assert "\\sffamily" in result
        assert "\\color{petrol}" in result
        assert "\\@title" in result
        assert "\\@date" in result
        assert "\\vskip 2em" in result

    def test_date_hidden(self) -> None:
        ts = TitleStyle(size="LARGE", bold=False, sans=False, color="", date_visible=False, vskip_after="")
        result = _build_title_style_block(ts)
        assert "\\@date" not in result
        assert "\\bfseries" not in result
        assert "\\sffamily" not in result

    def test_color_applied(self) -> None:
        ts = TitleStyle(size="huge", bold=True, sans=True, color="turkis", date_visible=True, vskip_after="1em")
        result = _build_title_style_block(ts)
        assert "\\color{turkis}" in result

    def test_injection_in_size_rejected(self) -> None:
        ts = TitleStyle(size="huge}\\write18{cmd", bold=False, sans=False, color="", date_visible=False, vskip_after="")
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_title_style_block(ts)

    def test_dangerous_macro_in_size_rejected(self) -> None:
        ts = TitleStyle(size="write18", bold=False, sans=False, color="", date_visible=False, vskip_after="")
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_title_style_block(ts)

    def test_injection_in_color_escaped(self) -> None:
        ts = TitleStyle(
            size="huge", bold=False, sans=False, color="petrol}\\write18{cmd", date_visible=False, vskip_after=""
        )
        result = _build_title_style_block(ts)
        assert "\\write18" not in result


class TestTruncateTitle:
    def test_no_separator_unchanged(self) -> None:
        assert _truncate_title("Short Title") == "Short Title"

    def test_emdash_truncates(self) -> None:
        assert _truncate_title("AI Adoption — Getting Started") == "AI Adoption"

    def test_endash_truncates(self) -> None:
        assert _truncate_title("Financial AI – A Landscape") == "Financial AI"

    def test_hyphen_truncates(self) -> None:
        assert _truncate_title("Exec Summary - Agentic System") == "Exec Summary"

    def test_colon_truncates(self) -> None:
        assert _truncate_title("AI Strategy: Phase 1 Plan") == "AI Strategy"

    def test_emdash_checked_first(self) -> None:
        assert _truncate_title("Topic: Sub — Detail") == "Topic: Sub"

    def test_empty_string(self) -> None:
        assert _truncate_title("") == ""


class TestEscapeLatex:
    def test_plain_text_unchanged(self) -> None:
        assert _escape_latex("Hello World") == "Hello World"

    def test_underscores_escaped(self) -> None:
        assert _escape_latex("my_file_name") == "my\\_file\\_name"

    def test_dollar_escaped(self) -> None:
        assert _escape_latex("costs $50") == "costs \\$50"

    def test_ampersand_escaped(self) -> None:
        assert _escape_latex("A & B") == "A \\& B"

    def test_percent_escaped(self) -> None:
        assert _escape_latex("100%") == "100\\%"

    def test_hash_escaped(self) -> None:
        assert _escape_latex("item #1") == "item \\#1"

    def test_multiple_special_chars(self) -> None:
        result = _escape_latex("file_name $100 & 50%")
        assert "\\_" in result
        assert "\\$" in result
        assert "\\&" in result
        assert "\\%" in result

    def test_empty_string(self) -> None:
        assert _escape_latex("") == ""

    def test_tilde_escaped(self) -> None:
        assert _escape_latex("~") == "\\textasciitilde{}"

    def test_caret_escaped(self) -> None:
        assert _escape_latex("^") == "\\textasciicircum{}"


class TestSubstitutePlaceholders:
    def test_empty_string_unchanged(self) -> None:
        assert _substitute_placeholders("", "My Title", "/path/logo.png") == ""

    def test_doc_title_replaced(self) -> None:
        result = _substitute_placeholders("\\sffamily {doc_title}", "My Doc", "/x")
        assert result == "\\sffamily My Doc"

    def test_logo_path_replaced(self) -> None:
        result = _substitute_placeholders("\\includegraphics{{logo_path}}", "T", "/a/b.png")
        assert result == "\\includegraphics{/a/b.png}"

    def test_both_replaced(self) -> None:
        result = _substitute_placeholders("{doc_title} {logo_path}", "Title", "/logo.png")
        assert result == "Title /logo.png"

    def test_title_with_underscores_escaped(self) -> None:
        result = _substitute_placeholders("\\sffamily {doc_title}", "my_file_name", "/x")
        assert result == "\\sffamily my\\_file\\_name"

    def test_title_with_special_chars_escaped(self) -> None:
        result = _substitute_placeholders("{doc_title}", "costs $50 & 100%", "/x")
        assert "\\$" in result
        assert "\\&" in result
        assert "\\%" in result

    def test_no_placeholders_unchanged(self) -> None:
        result = _substitute_placeholders("\\thepage", "Title", "/logo.png")
        assert result == "\\thepage"
