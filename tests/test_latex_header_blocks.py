"""Tests for individual LaTeX header block builders."""

import pytest

from obsidian_export.exceptions import UnsafeLatexError
from obsidian_export.pipeline.latex_header import (
    _build_brand_colors_block,
    _build_code_block,
    _build_font_block,
    _build_header_footer_block,
    _build_line_spacing_block,
    _build_unicode_char_block,
    _validate_latex_value,
)


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
