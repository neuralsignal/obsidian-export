"""Tests for obsidian_export.pipeline.stage3_mermaid."""

import shutil
import stat
import textwrap
from pathlib import Path

import pytest

from obsidian_export.config import MermaidConfig
from obsidian_export.pipeline.stage3_mermaid import render_mermaid_blocks


def _make_config(mmdc_bin: Path, scale: int) -> MermaidConfig:
    return MermaidConfig(mmdc_bin=mmdc_bin, scale=scale)


def _make_fake_mmdc(tmp_path: Path) -> Path:
    """Create a fake mmdc script that writes a stub PNG file."""
    mmdc = tmp_path / "mmdc"
    mmdc.write_text(
        textwrap.dedent("""\
        #!/bin/bash
        # Fake mmdc: parse --output arg and write stub PNG
        while [[ $# -gt 0 ]]; do
          case "$1" in
            --output) out="$2"; shift 2;;
            *) shift;;
          esac
        done
        echo "fake png" > "$out"
        """),
        encoding="utf-8",
    )
    mmdc.chmod(mmdc.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return mmdc


class TestRenderMermaidBlocks:
    def test_no_blocks_unchanged(self, tmp_path: Path) -> None:
        mmdc = _make_fake_mmdc(tmp_path)
        config = _make_config(mmdc, 3)
        text = "# Heading\n\nParagraph with no diagrams."
        result = render_mermaid_blocks(text, config, tmp_path)
        assert result == text

    def test_single_block_replaced(self, tmp_path: Path) -> None:
        mmdc = _make_fake_mmdc(tmp_path)
        config = _make_config(mmdc, 3)
        text = "Before.\n\n```mermaid\ngraph TB\n    A --> B\n```\n\nAfter."
        result = render_mermaid_blocks(text, config, tmp_path)
        assert "```mermaid" not in result
        assert "![Diagram" in result
        assert ".png" in result

    def test_multiple_blocks_replaced(self, tmp_path: Path) -> None:
        mmdc = _make_fake_mmdc(tmp_path)
        config = _make_config(mmdc, 3)
        text = "```mermaid\ngraph TB\n    A --> B\n```\n\nMiddle text.\n\n```mermaid\ngraph LR\n    X --> Y\n```"
        result = render_mermaid_blocks(text, config, tmp_path)
        assert "```mermaid" not in result
        assert result.count("![Diagram") == 2

    def test_missing_mmdc_raises(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path / "nonexistent_mmdc", 3)
        with pytest.raises(FileNotFoundError, match="mmdc binary not found"):
            render_mermaid_blocks("```mermaid\ngraph TB\n    A-->B\n```", config, tmp_path)

    def test_image_files_written_to_tmpdir(self, tmp_path: Path) -> None:
        mmdc = _make_fake_mmdc(tmp_path)
        config = _make_config(mmdc, 3)
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        text = "```mermaid\ngraph TB\n    A --> B\n```"
        render_mermaid_blocks(text, config, out_dir)
        png_files = list(out_dir.glob("*.png"))
        assert len(png_files) == 1

    def test_scale_passed_to_mmdc(self, tmp_path: Path) -> None:
        """Verify that mmdc is called with the configured scale."""
        calls_log = tmp_path / "calls.txt"
        mmdc = tmp_path / "mmdc"
        mmdc.write_text(
            f'#!/bin/bash\necho "$@" >> {calls_log}\n'
            "while [[ $# -gt 0 ]]; do\n"
            '  case "$1" in\n'
            '    --output) out="$2"; shift 2;;\n'
            "    *) shift;;\n"
            "  esac\n"
            "done\n"
            'echo "fake png" > "$out"\n',
            encoding="utf-8",
        )
        mmdc.chmod(mmdc.stat().st_mode | stat.S_IEXEC)
        config = _make_config(mmdc, 5)
        text = "```mermaid\ngraph TB\n    A --> B\n```"
        render_mermaid_blocks(text, config, tmp_path)
        args = calls_log.read_text()
        assert "--scale" in args
        assert "5" in args


def test_render_with_real_mmdc(tmp_path: Path) -> None:
    mmdc_path = shutil.which("mmdc")
    if mmdc_path is None:
        pytest.skip("mmdc not installed — skipping integration test")
    config = _make_config(Path(mmdc_path), 2)
    text = "```mermaid\ngraph TB\n    A --> B\n```"
    result = render_mermaid_blocks(text, config, tmp_path)
    assert "![Diagram" in result
    png_files = list(tmp_path.glob("*.png"))
    assert len(png_files) == 1
    assert png_files[0].stat().st_size > 0
