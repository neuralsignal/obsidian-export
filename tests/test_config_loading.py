"""Tests for config loading, defaults, partial merging, and path resolution."""

from pathlib import Path

import pytest
from conftest import VALID_DATA, write_config

from obsidian_export.config import (
    CalloutColors,
    ConvertConfig,
    MermaidConfig,
    ObsidianConfig,
    PandocConfig,
    StyleConfig,
    build_config,
    default_config,
    load_config,
)


def test_load_config_returns_convert_config(tmp_path: Path) -> None:
    cfg = write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert isinstance(result, ConvertConfig)
    assert isinstance(result.mermaid, MermaidConfig)
    assert isinstance(result.obsidian, ObsidianConfig)
    assert isinstance(result.pandoc, PandocConfig)
    assert isinstance(result.style, StyleConfig)


def test_load_config_relative_mmdc_resolved(tmp_path: Path) -> None:
    cfg = write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert result.mermaid.mmdc_bin == tmp_path / ".mmdc/node_modules/.bin/mmdc"


def test_load_config_absolute_mmdc_preserved(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["mermaid"] = {**VALID_DATA["mermaid"], "mmdc_bin": "/usr/local/bin/mmdc"}
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.mermaid.mmdc_bin == Path("/usr/local/bin/mmdc")


def test_load_config_scale_is_int(tmp_path: Path) -> None:
    cfg = write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert result.mermaid.scale == 3


def test_config_is_frozen(tmp_path: Path) -> None:
    cfg = write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    with pytest.raises(AttributeError):
        result.mermaid = result.mermaid  # type: ignore[misc]


def test_pandoc_config_only_has_from_format(tmp_path: Path) -> None:
    cfg = write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert result.pandoc.from_format == "gfm-tex_math_dollars+footnotes"
    assert not hasattr(result.pandoc, "geometry")


def test_style_config_loaded(tmp_path: Path) -> None:
    cfg = write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert result.style.name == "default"
    assert result.style.geometry == "a4paper,margin=25mm"
    assert result.style.fontsize == "11pt"
    assert result.style.linkcolor == "NavyBlue"
    assert result.style.urlcolor == "NavyBlue"
    assert result.style.line_spacing == 1.0
    assert result.style.table_fontsize == "small"
    assert result.style.code_fontsize == "footnotesize"
    assert result.style.image_max_height_ratio == 0.40
    assert result.style.url_footnote_threshold == 60
    assert result.style.mainfont == ""
    assert result.style.sansfont == ""
    assert result.style.monofont == ""
    assert result.style.header_left == ""
    assert result.style.header_right == ""
    assert result.style.footer_left == ""
    assert result.style.footer_center == "\\thepage"
    assert result.style.footer_right == ""
    assert result.style.logo == ""
    assert result.style.style_dir == ""


def test_callout_colors_loaded(tmp_path: Path) -> None:
    cfg = write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    cc = result.style.callout_colors
    assert isinstance(cc, CalloutColors)
    assert cc.note == (219, 234, 254)
    assert cc.tip == (220, 252, 231)
    assert cc.warning == (254, 243, 199)
    assert cc.danger == (254, 226, 226)


def test_callout_colors_frozen(tmp_path: Path) -> None:
    cfg = write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    with pytest.raises(AttributeError):
        result.style.callout_colors = result.style.callout_colors  # type: ignore[misc]


def test_style_config_frozen(tmp_path: Path) -> None:
    cfg = write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    with pytest.raises(AttributeError):
        result.style = result.style  # type: ignore[misc]


def test_line_spacing_float_conversion(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "line_spacing": 1}  # int in yaml
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert isinstance(result.style.line_spacing, float)
    assert result.style.line_spacing == 1.0


# ── default_config ──────────────────────────────────────────────────────────


def test_default_config_returns_convert_config() -> None:
    result = default_config()
    assert isinstance(result, ConvertConfig)
    assert result.style.name == "default"
    assert result.style.fontsize == "10pt"
    assert result.mermaid.scale == 3
    assert result.obsidian.max_embed_depth == 10


def test_default_config_code_fontsize() -> None:
    result = default_config()
    assert result.style.code_fontsize == "footnotesize"


def test_code_fontsize_override(tmp_path: Path) -> None:
    partial = {"style": {"code_fontsize": "small"}}
    cfg = write_config(tmp_path, partial)
    result = load_config(cfg)
    assert result.style.code_fontsize == "small"
    assert result.style.table_fontsize == "small"  # default unchanged


# ── partial config (merges with defaults) ───────────────────────────────────


def test_partial_config_merges_with_defaults(tmp_path: Path) -> None:
    """A minimal YAML with only overrides should produce a valid config."""
    partial = {"style": {"fontsize": "12pt"}}
    cfg = write_config(tmp_path, partial)
    result = load_config(cfg)
    assert result.style.fontsize == "12pt"
    assert result.style.name == "default"  # from defaults
    assert result.mermaid.scale == 3  # from defaults


def test_empty_config_uses_all_defaults(tmp_path: Path) -> None:
    cfg = tmp_path / "config.yaml"
    cfg.write_text("", encoding="utf-8")
    result = load_config(cfg)
    assert isinstance(result, ConvertConfig)
    assert result.style.name == "default"


# ── puppeteer_config resolution ────────────────────────────────────────────


def test_load_config_puppeteer_config_relative_resolved(tmp_path: Path) -> None:
    """Relative puppeteer_config is resolved against the config file directory."""
    data = dict(VALID_DATA)
    data["mermaid"] = {
        **VALID_DATA["mermaid"],
        "puppeteer_config": "puppeteer-config.json",
    }
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.mermaid.puppeteer_config == tmp_path / "puppeteer-config.json"
    assert result.mermaid.puppeteer_config.is_absolute()


def test_load_config_puppeteer_config_absolute_preserved(tmp_path: Path) -> None:
    """Absolute puppeteer_config is preserved as-is."""
    data = dict(VALID_DATA)
    data["mermaid"] = {
        **VALID_DATA["mermaid"],
        "puppeteer_config": "/etc/puppeteer.json",
    }
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.mermaid.puppeteer_config == Path("/etc/puppeteer.json")


# ── build_config with relative config_dir ─────────────────────────────────


def test_build_config_with_relative_config_dir(tmp_path: Path) -> None:
    """Passing a relative config_dir to build_config resolves it to absolute."""
    import os

    original_dir = os.getcwd()
    os.chdir(tmp_path)
    try:
        rel_dir = Path("subdir")
        rel_dir.mkdir()
        raw = {
            "mermaid": {"mmdc_bin": "mmdc", "scale": 3},
            "obsidian": {
                "url_strategy": "footnote_long",
                "url_length_threshold": 60,
                "max_embed_depth": 10,
            },
            "pandoc": {"from_format": "gfm"},
            "style": VALID_DATA["style"],
        }
        result = build_config(raw, config_dir=rel_dir)
        assert result.mermaid.mmdc_bin.is_absolute()
        assert str(result.mermaid.mmdc_bin) == str((tmp_path / "subdir" / "mmdc").resolve())
    finally:
        os.chdir(original_dir)
