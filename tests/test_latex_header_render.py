"""Tests for render_header integration with templates."""

import dataclasses
from pathlib import Path

import pytest

from obsidian_export.config import CalloutColors, StyleConfig, default_config
from obsidian_export.pipeline.latex_header import render_header

DEFAULT_TEMPLATE = Path(__file__).parent.parent / "obsidian_export" / "assets" / "styles" / "default" / "header.tex"


def _make_style(**overrides) -> StyleConfig:
    """Build StyleConfig from default_config(), applying overrides."""
    base = default_config().style
    fields = {f.name: getattr(base, f.name) for f in dataclasses.fields(base)}
    fields.update(overrides)
    return StyleConfig(**fields)


def _default_style() -> StyleConfig:
    return _make_style(footer_center="\\thepage")


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
