"""Tests for obsidian_export.pipeline.latex_header."""

from pathlib import Path

import pytest

from obsidian_export.config import CalloutColors, StyleConfig
from obsidian_export.pipeline.latex_header import (
    _build_font_block,
    _build_header_footer_block,
    _build_line_spacing_block,
    _escape_latex,
    _substitute_placeholders,
    _truncate_title,
    render_header,
)

DEFAULT_TEMPLATE = Path(__file__).parent.parent / "obsidian_export" / "assets" / "styles" / "default" / "header.tex"


def _make_style(
    name: str = "default",
    geometry: str = "a4paper,margin=25mm",
    fontsize: str = "10pt",
    mainfont: str = "",
    sansfont: str = "",
    monofont: str = "",
    linkcolor: str = "NavyBlue",
    urlcolor: str = "NavyBlue",
    line_spacing: float = 1.0,
    table_fontsize: str = "small",
    image_max_height_ratio: float = 0.40,
    url_footnote_threshold: int = 60,
    header_left: str = "",
    header_right: str = "",
    footer_left: str = "",
    footer_center: str = "",
    footer_right: str = "",
    callout_colors: CalloutColors | None = None,
    logo: str = "",
    style_dir: str = "",
) -> StyleConfig:
    if callout_colors is None:
        callout_colors = DEFAULT_CALLOUT
    return StyleConfig(
        name=name,
        geometry=geometry,
        fontsize=fontsize,
        mainfont=mainfont,
        sansfont=sansfont,
        monofont=monofont,
        linkcolor=linkcolor,
        urlcolor=urlcolor,
        line_spacing=line_spacing,
        table_fontsize=table_fontsize,
        image_max_height_ratio=image_max_height_ratio,
        url_footnote_threshold=url_footnote_threshold,
        header_left=header_left,
        header_right=header_right,
        footer_left=footer_left,
        footer_center=footer_center,
        footer_right=footer_right,
        callout_colors=callout_colors,
        logo=logo,
        style_dir=style_dir,
    )


DEFAULT_CALLOUT = CalloutColors(
    note=(219, 234, 254),
    tip=(220, 252, 231),
    warning=(254, 243, 199),
    danger=(254, 226, 226),
)


def _default_style() -> StyleConfig:
    return _make_style(footer_center="\\thepage")


class TestBuildFontBlock:
    def test_empty_fonts_returns_empty(self) -> None:
        assert _build_font_block("", "", "") == ""

    def test_mainfont_only(self) -> None:
        result = _build_font_block("Montserrat", "", "")
        assert result == "\\setmainfont{Montserrat}"

    def test_all_fonts(self) -> None:
        result = _build_font_block("Montserrat", "Helvetica", "Fira Code")
        assert "\\setmainfont{Montserrat}" in result
        assert "\\setsansfont{Helvetica}" in result
        assert "\\setmonofont{Fira Code}" in result

    def test_sansfont_only(self) -> None:
        result = _build_font_block("", "Arial", "")
        assert result == "\\setsansfont{Arial}"

    def test_monofont_only(self) -> None:
        result = _build_font_block("", "", "Courier New")
        assert result == "\\setmonofont{Courier New}"


class TestBuildLineSpacingBlock:
    def test_one_point_zero_returns_empty(self) -> None:
        assert _build_line_spacing_block(1.0) == ""

    def test_one_point_five_returns_setspace(self) -> None:
        result = _build_line_spacing_block(1.5)
        assert "\\usepackage{setspace}" in result
        assert "\\setstretch{1.5}" in result

    def test_one_point_two_returns_setspace(self) -> None:
        result = _build_line_spacing_block(1.2)
        assert "\\setstretch{1.2}" in result


class TestBuildHeaderFooterBlock:
    def test_all_empty_returns_empty(self) -> None:
        assert _build_header_footer_block("", "", "", "", "") == ""

    def test_footer_center_only(self) -> None:
        result = _build_header_footer_block("", "", "", "\\thepage", "")
        assert "\\usepackage{fancyhdr}" in result
        assert "\\pagestyle{fancy}" in result
        assert "\\fancyfoot[C]{\\thepage}" in result
        assert "\\fancyhead[L]" not in result
        assert "\\fancyhead[R]" not in result

    def test_header_left_and_right(self) -> None:
        result = _build_header_footer_block("Left Text", "Right Text", "", "", "")
        assert "\\fancyhead[L]{Left Text}" in result
        assert "\\fancyhead[R]{Right Text}" in result
        assert "\\fancyfoot[C]" not in result

    def test_all_five(self) -> None:
        result = _build_header_footer_block("HL", "HR", "FL", "FC", "FR")
        assert "\\fancyhead[L]{HL}" in result
        assert "\\fancyhead[R]{HR}" in result
        assert "\\fancyfoot[L]{FL}" in result
        assert "\\fancyfoot[C]{FC}" in result
        assert "\\fancyfoot[R]{FR}" in result
        assert "\\renewcommand{\\headrulewidth}{0pt}" in result

    def test_footer_left_and_right(self) -> None:
        result = _build_header_footer_block("", "", "Left", "", "Right")
        assert "\\fancyfoot[L]{Left}" in result
        assert "\\fancyfoot[R]{Right}" in result
        assert "\\fancyfoot[C]" not in result

    def test_no_head_rule(self) -> None:
        result = _build_header_footer_block("L", "", "", "", "")
        assert "\\renewcommand{\\headrulewidth}{0pt}" in result


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


class TestRenderHeader:
    def test_renders_default_template(self) -> None:
        style = _default_style()
        result = render_header(style, DEFAULT_TEMPLATE, "Test Doc")
        assert "\\definecolor{noteblue}{RGB}{219,234,254}" in result
        assert "\\definecolor{tipgreen}{RGB}{220,252,231}" in result
        assert "\\definecolor{warnyellow}{RGB}{254,243,199}" in result
        assert "\\definecolor{dangerred}{RGB}{254,226,226}" in result

    def test_renders_image_ratio(self) -> None:
        style = _default_style()
        result = render_header(style, DEFAULT_TEMPLATE, "Test Doc")
        assert "0.4\\textheight" in result

    def test_custom_image_ratio(self) -> None:
        style = _make_style(image_max_height_ratio=0.60)
        result = render_header(style, DEFAULT_TEMPLATE, "Test Doc")
        assert "0.6\\textheight" in result

    def test_custom_callout_colors(self) -> None:
        cc = CalloutColors(
            note=(100, 200, 255),
            tip=(0, 255, 0),
            warning=(255, 255, 0),
            danger=(255, 0, 0),
        )
        style = _make_style(callout_colors=cc)
        result = render_header(style, DEFAULT_TEMPLATE, "Test Doc")
        assert "\\definecolor{noteblue}{RGB}{100,200,255}" in result
        assert "\\definecolor{tipgreen}{RGB}{0,255,0}" in result

    def test_font_block_included_when_set(self) -> None:
        style = _make_style(mainfont="Montserrat")
        result = render_header(style, DEFAULT_TEMPLATE, "Test Doc")
        assert "\\setmainfont{Montserrat}" in result

    def test_no_font_block_when_empty(self) -> None:
        style = _default_style()
        result = render_header(style, DEFAULT_TEMPLATE, "Test Doc")
        assert "\\setmainfont" not in result
        assert "\\setsansfont" not in result
        assert "\\setmonofont" not in result

    def test_line_spacing_block_when_not_one(self) -> None:
        style = _make_style(line_spacing=1.5)
        result = render_header(style, DEFAULT_TEMPLATE, "Test Doc")
        assert "\\usepackage{setspace}" in result
        assert "\\setstretch{1.5}" in result

    def test_header_footer_block_when_set(self) -> None:
        style = _make_style(
            header_left="My Doc",
            header_right="2026",
            footer_center="\\thepage",
        )
        result = render_header(style, DEFAULT_TEMPLATE, "Test Doc")
        assert "\\fancyhead[L]{My Doc}" in result
        assert "\\fancyhead[R]{2026}" in result
        assert "\\fancyfoot[C]{\\thepage}" in result

    def test_doc_title_substituted_in_header(self) -> None:
        style = _make_style(header_left="\\sffamily {doc_title}")
        result = render_header(style, DEFAULT_TEMPLATE, "My Report")
        assert "\\sffamily My Report" in result
        assert "{doc_title}" not in result

    def test_logo_path_substituted_when_logo_set(self, tmp_path: Path) -> None:
        template = tmp_path / "header.tex"
        template.write_text(
            "ratio={image_max_height_ratio} "
            "note={note_r},{note_g},{note_b} "
            "tip={tip_r},{tip_g},{tip_b} "
            "warn={warn_r},{warn_g},{warn_b} "
            "danger={danger_r},{danger_g},{danger_b} "
            "{font_block} {line_spacing_block} {header_footer_block}",
            encoding="utf-8",
        )
        style = _make_style(
            footer_center="\\includegraphics{{logo_path}}",
            logo="my_logo.png",
        )
        result = render_header(style, template, "Test")
        assert "\\includegraphics{" in result
        assert "my_logo.png" in result
        assert "{logo_path}" not in result

    def test_logo_path_empty_when_no_logo(self) -> None:
        style = _make_style(
            footer_center="\\includegraphics{{logo_path}}",
        )
        result = render_header(style, DEFAULT_TEMPLATE, "Test")
        assert "\\includegraphics{}" in result

    def test_missing_template_raises(self) -> None:
        style = _default_style()
        with pytest.raises(FileNotFoundError):
            render_header(style, Path("/nonexistent/header.tex"), "Test")

    def test_uses_custom_template(self, tmp_path: Path) -> None:
        template = tmp_path / "header.tex"
        template.write_text(
            "ratio={image_max_height_ratio} "
            "note={note_r},{note_g},{note_b} "
            "tip={tip_r},{tip_g},{tip_b} "
            "warn={warn_r},{warn_g},{warn_b} "
            "danger={danger_r},{danger_g},{danger_b} "
            "{font_block} {line_spacing_block} {header_footer_block}",
            encoding="utf-8",
        )
        style = _default_style()
        result = render_header(style, template, "Test Doc")
        assert "ratio=0.4" in result
        assert "note=219,234,254" in result
