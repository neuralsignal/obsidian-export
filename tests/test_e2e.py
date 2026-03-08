"""End-to-end pipeline tests with diverse fixtures."""

import dataclasses
import shutil
from pathlib import Path

import pytest

from obsidian_export import run
from obsidian_export.config import (
    ConvertConfig,
    StyleConfig,
    default_config,
)
from obsidian_export.exceptions import EmbedNotFoundError
from obsidian_export.pipeline.latex_header import render_header
from obsidian_export.pipeline.stage1_vault import (
    parse_frontmatter,
    resolve_embeds,
    strip_leading_title,
    strip_obsidian_syntax,
)
from obsidian_export.pipeline.stage2_preprocess import preprocess

PANDOC_AVAILABLE = shutil.which("pandoc") is not None
TECTONIC_AVAILABLE = shutil.which("tectonic") is not None

FIXTURES = Path(__file__).parent / "fixtures"
ALL_FIXTURES = sorted(FIXTURES.glob("*.md"))
ASSETS_DIR = Path(__file__).parent.parent / "obsidian_export" / "assets"
FILTERS_DIR = ASSETS_DIR / "filters"
DEFAULT_STYLE_DIR = ASSETS_DIR / "styles" / "default"


@pytest.fixture(params=ALL_FIXTURES, ids=lambda p: p.name)
def fixture_md(request: pytest.FixtureRequest) -> Path:
    return request.param


def _make_style_config(**overrides) -> StyleConfig:
    base = default_config().style
    fields = {f.name: getattr(base, f.name) for f in dataclasses.fields(base)}
    fields.update(overrides)
    return StyleConfig(**fields)


def _make_full_pipeline_config() -> ConvertConfig:
    """Build a ConvertConfig suitable for full-pipeline E2E tests."""
    cfg = default_config()
    mmdc_path = shutil.which("mmdc")
    if mmdc_path is None:
        # Check local npm install location (pixi run setup-mmdc)
        local_mmdc = Path(__file__).parent.parent / ".mmdc" / "node_modules" / ".bin" / "mmdc"
        if local_mmdc.exists():
            mmdc_path = str(local_mmdc)
    if mmdc_path is not None:
        cfg = dataclasses.replace(
            cfg,
            mermaid=dataclasses.replace(cfg.mermaid, mmdc_bin=Path(mmdc_path)),
        )
    return cfg


def _make_branded_style() -> StyleConfig:
    return _make_style_config(
        brand_colors=(
            ("petrol", 20, 75, 95),
            ("turkis", 0, 152, 160),
        ),
        heading_styles=(
            ("section", "Large", True, True, "petrol", False),
            ("subsection", "large", True, True, "turkis", True),
        ),
        title_style=("huge", True, True, "petrol", True, "2em"),
    )


class TestPipelineStages:
    """Test preprocessing stages on all fixtures — no external tools needed."""

    def test_preprocess_all_fixtures(self, fixture_md: Path) -> None:
        """Every fixture should survive preprocessing without errors."""
        text = fixture_md.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        config = default_config()
        result = preprocess(body, config.obsidian)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_embed_resolution(self, tmp_path: Path) -> None:
        """Embeds should resolve from fixture files."""
        # Copy embed fixtures to tmp_path (simulates vault)
        embed_src = FIXTURES / "embeds.md"
        target_src = FIXTURES / "embed_target.md"
        embed_dst = tmp_path / "embeds.md"
        target_dst = tmp_path / "embed_target.md"
        embed_dst.write_text(embed_src.read_text(encoding="utf-8"), encoding="utf-8")
        target_dst.write_text(target_src.read_text(encoding="utf-8"), encoding="utf-8")

        text = embed_dst.read_text(encoding="utf-8")
        _, body = parse_frontmatter(text)
        body = strip_leading_title(body, "Embed Tests")
        result = resolve_embeds(body, tmp_path, embed_dst, 10)
        # Should have inlined content from embed_target
        assert "embed_target" not in result or len(result) > len(body)

    def test_missing_embed_raises(self, tmp_path: Path) -> None:
        """Missing embeds should raise EmbedNotFoundError."""
        md = tmp_path / "test.md"
        md.write_text("![[nonexistent_note]]", encoding="utf-8")
        with pytest.raises(EmbedNotFoundError, match="nonexistent_note"):
            resolve_embeds("![[nonexistent_note]]", tmp_path, md, 10)

    def test_strip_obsidian_syntax(self, fixture_md: Path) -> None:
        """Obsidian syntax stripping should not crash on any fixture."""
        text = fixture_md.read_text(encoding="utf-8")
        _, body = parse_frontmatter(text)
        result = strip_obsidian_syntax(body)
        assert isinstance(result, str)


@pytest.mark.skipif(not PANDOC_AVAILABLE, reason="pandoc not installed")
class TestDocxE2E:
    """DOCX conversion tests using the full pipeline."""

    def test_produces_valid_docx(self, fixture_md: Path, tmp_path: Path) -> None:
        config = _make_full_pipeline_config()
        out = tmp_path / "output.docx"
        run(fixture_md, out, "docx", config)
        assert out.exists()
        assert out.stat().st_size > 0
        # DOCX is a zip file
        assert out.read_bytes()[:2] == b"PK"


@pytest.mark.skipif(
    not (PANDOC_AVAILABLE and TECTONIC_AVAILABLE),
    reason="pandoc and/or tectonic not installed",
)
class TestPdfE2E:
    """PDF conversion tests — requires pandoc + tectonic."""

    def test_produces_valid_pdf(self, fixture_md: Path, tmp_path: Path) -> None:
        """Full pipeline E2E: all 5 stages including mermaid + SVG rendering."""
        config = _make_full_pipeline_config()
        out = tmp_path / "output.pdf"
        run(fixture_md, out, "pdf", config)
        assert out.exists()
        assert out.read_bytes()[:5] == b"%PDF-"

    def test_branded_pdf(self, tmp_path: Path) -> None:
        """PDF with brand colors, heading styles, and title style."""
        style = _make_branded_style()
        rendered_header = render_header(style, DEFAULT_STYLE_DIR / "header.tex", "Branded Test")
        # Verify brand elements in header
        assert "\\definecolor{petrol}{RGB}{20,75,95}" in rendered_header
        assert "\\definecolor{turkis}{RGB}{0,152,160}" in rendered_header
        assert "\\usepackage{titlesec}" in rendered_header
        assert "\\titleformat{\\section}" in rendered_header
        assert "\\makeatletter" in rendered_header

        config = _make_full_pipeline_config()
        text = "# Branded Test\n\nThis tests brand styling.\n\n## Section Two\n\nMore content.\n"
        body = preprocess(text, config.obsidian)
        out = tmp_path / "branded.pdf"
        from obsidian_export.pipeline.stage4_pandoc import convert_to_pdf

        convert_to_pdf(
            body,
            "Branded Test",
            config.pandoc,
            style,
            rendered_header,
            FILTERS_DIR,
            out,
            resource_path=None,
        )
        assert out.exists()
        assert out.read_bytes()[:5] == b"%PDF-"
