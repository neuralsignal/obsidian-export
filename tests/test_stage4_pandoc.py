"""Tests for obsidian_export.pipeline.stage4_pandoc."""

import shutil
from pathlib import Path

import pytest

from obsidian_export.config import CalloutColors, PandocConfig, StyleConfig
from obsidian_export.pipeline.latex_header import render_header
from obsidian_export.pipeline.stage4_pandoc import convert_to_docx, convert_to_pdf

PANDOC_AVAILABLE = shutil.which("pandoc") is not None
TECTONIC_AVAILABLE = shutil.which("tectonic") is not None

pytestmark = pytest.mark.skipif(not PANDOC_AVAILABLE, reason="pandoc not installed -- skipping pandoc tests")

ASSETS_DIR = Path(__file__).parent.parent / "obsidian_export" / "assets"
FILTERS_DIR = ASSETS_DIR / "filters"
DEFAULT_STYLE_DIR = ASSETS_DIR / "styles" / "default"


def _make_pandoc_config() -> PandocConfig:
    return PandocConfig(
        from_format="gfm-tex_math_dollars",
    )


def _make_style_config() -> StyleConfig:
    return StyleConfig(
        name="default",
        geometry="a4paper,margin=25mm",
        fontsize="11pt",
        mainfont="",
        sansfont="",
        monofont="",
        linkcolor="NavyBlue",
        urlcolor="NavyBlue",
        line_spacing=1.0,
        table_fontsize="small",
        image_max_height_ratio=0.40,
        url_footnote_threshold=60,
        header_left="",
        header_right="",
        footer_left="",
        footer_center="\\thepage",
        footer_right="",
        logo="",
        style_dir="",
        callout_colors=CalloutColors(
            note=(219, 234, 254),
            tip=(220, 252, 231),
            warning=(254, 243, 199),
            danger=(254, 226, 226),
        ),
    )


def _render_default_header() -> str:
    style = _make_style_config()
    return render_header(style, DEFAULT_STYLE_DIR / "header.tex", "Test Document")


SAMPLE_TEXT = "# Test Document\n\nThis is a test.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"


class TestConvertToDocx:
    def test_produces_file(self, tmp_path: Path) -> None:
        config = _make_pandoc_config()
        out = tmp_path / "output.docx"
        convert_to_docx(SAMPLE_TEXT, "Test Document", config, out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        config = _make_pandoc_config()
        out = tmp_path / "nested" / "dir" / "output.docx"
        convert_to_docx(SAMPLE_TEXT, "Test", config, out)
        assert out.exists()

    def test_output_is_docx_format(self, tmp_path: Path) -> None:
        config = _make_pandoc_config()
        out = tmp_path / "output.docx"
        convert_to_docx(SAMPLE_TEXT, "Test", config, out)
        # DOCX files start with PK (zip format)
        header = out.read_bytes()[:2]
        assert header == b"PK"


@pytest.mark.skipif(not TECTONIC_AVAILABLE, reason="tectonic not installed -- skipping PDF tests")
class TestConvertToPdf:
    def test_produces_file(self, tmp_path: Path) -> None:
        pandoc_config = _make_pandoc_config()
        style_config = _make_style_config()
        rendered_header = _render_default_header()
        out = tmp_path / "output.pdf"
        convert_to_pdf(
            SAMPLE_TEXT,
            "Test Document",
            pandoc_config,
            style_config,
            rendered_header,
            FILTERS_DIR,
            out,
        )
        assert out.exists()
        assert out.stat().st_size > 1000

    def test_output_is_pdf_format(self, tmp_path: Path) -> None:
        pandoc_config = _make_pandoc_config()
        style_config = _make_style_config()
        rendered_header = _render_default_header()
        out = tmp_path / "output.pdf"
        convert_to_pdf(
            SAMPLE_TEXT,
            "Test Document",
            pandoc_config,
            style_config,
            rendered_header,
            FILTERS_DIR,
            out,
        )
        header = out.read_bytes()[:5]
        assert header == b"%PDF-"

    def test_missing_filter_raises(self, tmp_path: Path) -> None:
        pandoc_config = _make_pandoc_config()
        style_config = _make_style_config()
        rendered_header = _render_default_header()
        out = tmp_path / "output.pdf"
        with pytest.raises(FileNotFoundError, match="Lua filter not found"):
            convert_to_pdf(
                SAMPLE_TEXT,
                "Test",
                pandoc_config,
                style_config,
                rendered_header,
                tmp_path / "nonexistent",
                out,
            )

    def test_dollar_sign_safe(self, tmp_path: Path) -> None:
        """Ensure $25/user/month doesn't break PDF compilation."""
        pandoc_config = _make_pandoc_config()
        style_config = _make_style_config()
        rendered_header = _render_default_header()
        out = tmp_path / "output.pdf"
        text = "Price: \\$25/user/month and \\$100/year.\n"
        # Should not raise
        convert_to_pdf(
            text,
            "Price Test",
            pandoc_config,
            style_config,
            rendered_header,
            FILTERS_DIR,
            out,
        )
        assert out.exists()
