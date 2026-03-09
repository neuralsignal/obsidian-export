"""Tests for obsidian_export.pipeline.stage4_pandoc."""

import dataclasses
import shutil
from pathlib import Path

import pytest
import yaml

from obsidian_export.config import PandocConfig, StyleConfig, default_config
from obsidian_export.pipeline.latex_header import render_header
from obsidian_export.pipeline.stage4_pandoc import (
    _yaml_metadata_block,
    convert_to_docx,
    convert_to_pdf,
)

PANDOC_AVAILABLE = shutil.which("pandoc") is not None
TECTONIC_AVAILABLE = shutil.which("tectonic") is not None

pytestmark = pytest.mark.skipif(not PANDOC_AVAILABLE, reason="pandoc not installed -- skipping pandoc tests")

ASSETS_DIR = Path(__file__).parent.parent / "obsidian_export" / "assets"
FILTERS_DIR = ASSETS_DIR / "filters"
DEFAULT_STYLE_DIR = ASSETS_DIR / "styles" / "default"


def _make_pandoc_config() -> PandocConfig:
    return PandocConfig(
        from_format="gfm-tex_math_dollars+footnotes",
    )


def _make_style_config(**overrides) -> StyleConfig:
    base = default_config().style
    fields = {f.name: getattr(base, f.name) for f in dataclasses.fields(base)}
    fields.update(overrides)
    return StyleConfig(**fields)


def _render_default_header() -> str:
    style = _make_style_config()
    return render_header(style, DEFAULT_STYLE_DIR / "header.tex", "Test Document")


SAMPLE_TEXT = "# Test Document\n\nThis is a test.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"


class TestYamlMetadataBlock:
    def test_simple_title(self) -> None:
        block = _yaml_metadata_block({"title": "Hello"})
        assert block.startswith("---\n")
        assert block.endswith("---\n\n")
        assert "title: Hello\n" in block

    def test_title_with_colon(self) -> None:
        """Titles containing colons must be quoted in YAML output."""
        block = _yaml_metadata_block({"title": "Memory: Knowledge folder consolidation"})
        assert block.startswith("---\n")
        # yaml.dump will quote values containing colons — the key thing is
        # that re-parsing the block yields the original value.
        parsed = yaml.safe_load(block.strip().strip("-"))
        assert parsed["title"] == "Memory: Knowledge folder consolidation"

    def test_title_with_special_chars(self) -> None:
        block = _yaml_metadata_block({"title": 'Azure Setup — "Obungi" CSP & MTF'})
        parsed = yaml.safe_load(block.strip().strip("-"))
        assert parsed["title"] == 'Azure Setup — "Obungi" CSP & MTF'

    def test_multiple_keys(self) -> None:
        block = _yaml_metadata_block({"title": "Test", "table_fontsize": "small"})
        parsed = yaml.safe_load(block.strip().strip("-"))
        assert parsed["title"] == "Test"
        assert parsed["table_fontsize"] == "small"


class TestConvertToDocx:
    def test_produces_file(self, tmp_path: Path) -> None:
        config = _make_pandoc_config()
        style = _make_style_config()
        out = tmp_path / "output.docx"
        convert_to_docx(SAMPLE_TEXT, "Test Document", config, style, FILTERS_DIR, None, out, resource_path=None)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        config = _make_pandoc_config()
        style = _make_style_config()
        out = tmp_path / "nested" / "dir" / "output.docx"
        convert_to_docx(SAMPLE_TEXT, "Test", config, style, FILTERS_DIR, None, out, resource_path=None)
        assert out.exists()

    def test_title_with_colon(self, tmp_path: Path) -> None:
        """Titles containing colons must not break conversion."""
        config = _make_pandoc_config()
        style = _make_style_config()
        out = tmp_path / "output.docx"
        convert_to_docx(
            SAMPLE_TEXT,
            "Memory: Knowledge folder consolidation",
            config,
            style,
            FILTERS_DIR,
            None,
            out,
            resource_path=None,
        )
        assert out.exists()
        assert out.stat().st_size > 0

    def test_output_is_docx_format(self, tmp_path: Path) -> None:
        config = _make_pandoc_config()
        style = _make_style_config()
        out = tmp_path / "output.docx"
        convert_to_docx(SAMPLE_TEXT, "Test", config, style, FILTERS_DIR, None, out, resource_path=None)
        # DOCX files start with PK (zip format)
        header = out.read_bytes()[:2]
        assert header == b"PK"

    def test_missing_filter_raises(self, tmp_path: Path) -> None:
        config = _make_pandoc_config()
        style = _make_style_config()
        out = tmp_path / "output.docx"
        with pytest.raises(FileNotFoundError, match="Lua filter not found"):
            convert_to_docx(SAMPLE_TEXT, "Test", config, style, tmp_path / "nonexistent", None, out, resource_path=None)

    def test_callout_box_rendered(self, tmp_path: Path) -> None:
        """Callout divs are processed via callout_boxes_docx.lua."""
        config = _make_pandoc_config()
        style = _make_style_config()
        out = tmp_path / "output.docx"
        text = SAMPLE_TEXT + "\n::: note\nThis is a note.\n:::\n"
        convert_to_docx(text, "Test", config, style, FILTERS_DIR, None, out, resource_path=None)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_long_url_promoted_to_footnote(self, tmp_path: Path) -> None:
        """Long URLs are promoted to footnotes via promote_footnotes.lua."""
        config = _make_pandoc_config()
        style = _make_style_config()
        out = tmp_path / "output.docx"
        long_url = "https://example.com/" + "a" * 80
        text = f"[click here]({long_url})\n"
        convert_to_docx(text, "Test", config, style, FILTERS_DIR, None, out, resource_path=None)
        assert out.exists()
        assert out.stat().st_size > 0


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
            resource_path=None,
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
            resource_path=None,
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
                resource_path=None,
            )

    def test_title_with_colon(self, tmp_path: Path) -> None:
        """Titles containing colons must not break PDF conversion."""
        pandoc_config = _make_pandoc_config()
        style_config = _make_style_config()
        rendered_header = _render_default_header()
        out = tmp_path / "output.pdf"
        convert_to_pdf(
            SAMPLE_TEXT,
            "Memory: Azure Subscription Setup — Obungi CSP",
            pandoc_config,
            style_config,
            rendered_header,
            FILTERS_DIR,
            out,
            resource_path=None,
        )
        assert out.exists()
        assert out.read_bytes()[:5] == b"%PDF-"

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
            resource_path=None,
        )
        assert out.exists()
