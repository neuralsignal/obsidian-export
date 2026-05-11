"""Tests for obsidian_export.pipeline.latex_header."""

import dataclasses
from pathlib import Path

import pytest

from obsidian_export.config import CalloutColors, HeadingStyle, StyleConfig, TitleStyle, default_config
from obsidian_export.exceptions import ConfigValueError, UnsafeLatexError
from obsidian_export.pipeline.latex_header import (
    _build_brand_colors_block,
    _build_code_block,
    _build_font_block,
    _build_header_footer_block,
    _build_heading_styles_block,
    _build_line_spacing_block,
    _build_title_style_block,
    _build_unicode_char_block,
    _escape_latex,
    _substitute_placeholders,
    _truncate_title,
    _validate_latex_value,
    render_header,
)

DEFAULT_TEMPLATE = Path(__file__).parent.parent / "obsidian_export" / "assets" / "styles" / "default" / "header.tex"


def _make_style(**overrides) -> StyleConfig:
    """Build StyleConfig from default_config(), applying overrides."""
    base = default_config().style
    fields = {f.name: getattr(base, f.name) for f in dataclasses.fields(base)}
    fields.update(overrides)
    return StyleConfig(**fields)


def _default_style() -> StyleConfig:
    return _make_style(footer_center="\\thepage")


class TestBuildUnicodeCharBlock:
    def test_empty_returns_empty(self) -> None:
        assert _build_unicode_char_block(()) == ""

    def test_single_char(self) -> None:
        result = _build_unicode_char_block((("⚠", "\\ensuremath{\\triangle}"),))
        assert result == "\\newunicodechar{⚠}{\\ensuremath{\\triangle}}"

    def test_multiple_chars(self) -> None:
        chars = (
            ("⚠", "\\ensuremath{\\triangle}"),
            ("✅", "\\ensuremath{\\checkmark}"),
        )
        result = _build_unicode_char_block(chars)
        assert "\\newunicodechar{⚠}{\\ensuremath{\\triangle}}" in result
        assert "\\newunicodechar{✅}{\\ensuremath{\\checkmark}}" in result
        assert result.count("\n") == 1  # two lines, one newline

    def test_box_drawing_chars(self) -> None:
        chars = (("└", "└"),)
        result = _build_unicode_char_block(chars)
        assert result == "\\newunicodechar{└}{└}"

    def test_rejects_input_macro(self) -> None:
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_unicode_char_block((("⚠", "\\input{/etc/passwd}"),))

    def test_rejects_write18(self) -> None:
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_unicode_char_block((("⚠", "\\write18{rm -rf /}"),))

    def test_rejects_include(self) -> None:
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_unicode_char_block((("⚠", "\\include{secrets}"),))

    def test_rejects_def(self) -> None:
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_unicode_char_block((("⚠", "\\def\\foo{bar}"),))

    def test_rejects_catcode(self) -> None:
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_unicode_char_block((("⚠", "\\catcode`\\@=11"),))

    def test_rejects_directlua(self) -> None:
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_unicode_char_block((("⚠", "\\directlua{os.execute('id')}"),))

    def test_rejects_case_insensitive(self) -> None:
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_unicode_char_block((("⚠", "\\INPUT{/etc/passwd}"),))

    def test_allows_safe_macros(self) -> None:
        safe_chars = (
            ("⚠", "\\ensuremath{\\triangle}"),
            ("✅", "\\ensuremath{\\checkmark}"),
            ("→", "\\textrightarrow{}"),
        )
        result = _build_unicode_char_block(safe_chars)
        assert "\\newunicodechar{⚠}" in result
        assert "\\newunicodechar{✅}" in result
        assert "\\newunicodechar{→}" in result


class TestValidateLatexValue:
    @pytest.mark.parametrize(
        "latex",
        [
            "\\input{file}",
            "\\include{file}",
            "\\write18{cmd}",
            "\\immediate\\write18{cmd}",
            "\\openin1=file",
            "\\openout1=file",
            "\\read1 to \\x",
            "\\closein1",
            "\\closeout1",
            "\\catcode`\\@=11",
            "\\def\\x{y}",
            "\\edef\\x{y}",
            "\\gdef\\x{y}",
            "\\xdef\\x{y}",
            "\\let\\x=\\y",
            "\\csname evil\\endcsname",
            "\\newwrite\\myfile",
            "\\directlua{os.execute('id')}",
            "\\luaexec{os.execute('id')}",
            "\\luadirect{os.execute('id')}",
        ],
    )
    def test_rejects_dangerous_macros(self, latex: str) -> None:
        with pytest.raises(UnsafeLatexError):
            _validate_latex_value(latex, "⚠")

    @pytest.mark.parametrize(
        "latex",
        [
            "\\ensuremath{\\triangle}",
            "\\textbf{bold}",
            "\\textrightarrow{}",
            "\\ensuremath{\\checkmark}",
            "└",
            "\\ding{52}",
        ],
    )
    def test_allows_safe_macros(self, latex: str) -> None:
        _validate_latex_value(latex, "⚠")


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

    def test_injection_in_mainfont_escaped(self) -> None:
        result = _build_font_block("}\\write18{rm -rf /}", "", "")
        assert "\\write18" not in result
        assert "\\textbackslash" in result

    def test_injection_in_sansfont_escaped(self) -> None:
        result = _build_font_block("", "}\\write18{bad}", "")
        assert "\\write18" not in result

    def test_injection_in_monofont_escaped(self) -> None:
        result = _build_font_block("", "", "font$hack")
        assert "\\$" in result


class TestBuildCodeBlock:
    def test_contains_fvextra(self) -> None:
        result = _build_code_block("footnotesize")
        assert "\\usepackage{fvextra}" in result

    def test_contains_breaklines(self) -> None:
        result = _build_code_block("footnotesize")
        assert "breaklines=true" in result

    def test_fontsize_cmd_in_fvset(self) -> None:
        result = _build_code_block("footnotesize")
        assert "\\footnotesize" in result

    def test_fontsize_cmd_small(self) -> None:
        result = _build_code_block("small")
        assert "\\small" in result
        assert "\\footnotesize" not in result

    def test_defines_verbatim_environment(self) -> None:
        result = _build_code_block("footnotesize")
        assert "\\DefineVerbatimEnvironment{verbatim}" in result

    def test_rejects_dangerous_macro(self) -> None:
        with pytest.raises(UnsafeLatexError, match="code_fontsize"):
            _build_code_block("write18")

    def test_rejects_input_macro(self) -> None:
        with pytest.raises(UnsafeLatexError, match="code_fontsize"):
            _build_code_block("input{/etc/passwd}")


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

    @pytest.mark.parametrize(
        ("field_idx", "field_name"),
        [
            (0, "header_left"),
            (1, "header_right"),
            (2, "footer_left"),
            (3, "footer_center"),
            (4, "footer_right"),
        ],
    )
    def test_rejects_dangerous_macro_in_each_field(self, field_idx: int, field_name: str) -> None:
        args = ["", "", "", "", ""]
        args[field_idx] = "\\input{/etc/passwd}"
        with pytest.raises(UnsafeLatexError, match=f"Config field '{field_name}'"):
            _build_header_footer_block(*args)

    def test_rejects_write18_in_header(self) -> None:
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_header_footer_block("\\write18{rm -rf /}", "", "", "", "")

    def test_rejects_directlua_in_footer(self) -> None:
        with pytest.raises(UnsafeLatexError, match="dangerous LaTeX macro"):
            _build_header_footer_block("", "", "", "\\directlua{os.execute('id')}", "")

    def test_allows_safe_header_footer_values(self) -> None:
        result = _build_header_footer_block("\\sffamily Title", "2026", "\\textbf{Footer}", "\\thepage", "v1.0")
        assert "\\fancyhead[L]{\\sffamily Title}" in result
        assert "\\fancyfoot[C]{\\thepage}" in result


class TestBuildBrandColorsBlock:
    def test_empty_returns_empty(self) -> None:
        assert _build_brand_colors_block(()) == ""

    def test_single_color(self) -> None:
        result = _build_brand_colors_block((("petrol", 20, 75, 95),))
        assert result == "\\definecolor{petrol}{RGB}{20,75,95}"

    def test_multiple_colors(self) -> None:
        colors = (
            ("petrol", 20, 75, 95),
            ("turkis", 0, 152, 160),
            ("mint", 109, 185, 160),
        )
        result = _build_brand_colors_block(colors)
        assert "\\definecolor{petrol}{RGB}{20,75,95}" in result
        assert "\\definecolor{turkis}{RGB}{0,152,160}" in result
        assert "\\definecolor{mint}{RGB}{109,185,160}" in result
        assert result.count("\n") == 2

    def test_injection_in_color_name_escaped(self) -> None:
        result = _build_brand_colors_block((("bad}\\write18{cmd", 0, 0, 0),))
        assert "\\write18" not in result
        assert "\\textbackslash" in result


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
        with pytest.raises(ConfigValueError, match="heading_styles.level"):
            _build_heading_styles_block(styles)

    def test_unknown_level_rejected(self) -> None:
        styles = (HeadingStyle(level="write18", size="Large", bold=False, sans=False, color="", uppercase=False),)
        with pytest.raises(ConfigValueError, match="heading_styles.level"):
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
            "{unicode_char_block} "
            "{brand_colors_block} {heading_styles_block} {title_style_block} "
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

    def test_unicode_char_block_in_default_template(self) -> None:
        style = _default_style()
        result = render_header(style, DEFAULT_TEMPLATE, "Test Doc")
        assert "\\newunicodechar{⚠}{\\ensuremath{\\triangle}}" in result
        assert "\\newunicodechar{✅}{\\ensuremath{\\checkmark}}" in result

    def test_uses_custom_template(self, tmp_path: Path) -> None:
        template = tmp_path / "header.tex"
        template.write_text(
            "ratio={image_max_height_ratio} "
            "note={note_r},{note_g},{note_b} "
            "tip={tip_r},{tip_g},{tip_b} "
            "warn={warn_r},{warn_g},{warn_b} "
            "danger={danger_r},{danger_g},{danger_b} "
            "{unicode_char_block} "
            "{brand_colors_block} {heading_styles_block} {title_style_block} "
            "{font_block} {line_spacing_block} {header_footer_block}",
            encoding="utf-8",
        )
        style = _default_style()
        result = render_header(style, template, "Test Doc")
        assert "ratio=0.4" in result
        assert "note=219,234,254" in result
