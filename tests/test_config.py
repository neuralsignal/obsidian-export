"""Tests for obsidian_export.config."""

from pathlib import Path

import pytest
import yaml

from obsidian_export.config import (
    CalloutColors,
    ConvertConfig,
    MermaidConfig,
    ObsidianConfig,
    PandocConfig,
    StyleConfig,
    _deep_merge,
    default_config,
    load_config,
)


def _write_config(tmp_path: Path, data: dict) -> Path:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.dump(data), encoding="utf-8")
    return cfg


VALID_DATA = {
    "mermaid": {"mmdc_bin": ".mmdc/node_modules/.bin/mmdc", "scale": 3},
    "obsidian": {
        "wikilink_strategy": "text",
        "url_strategy": "footnote_long",
        "url_length_threshold": 60,
    },
    "pandoc": {
        "from_format": "gfm-tex_math_dollars",
    },
    "style": {
        "name": "default",
        "geometry": "a4paper,margin=25mm",
        "fontsize": "11pt",
        "mainfont": "",
        "sansfont": "",
        "monofont": "",
        "linkcolor": "NavyBlue",
        "urlcolor": "NavyBlue",
        "line_spacing": 1.0,
        "table_fontsize": "small",
        "image_max_height_ratio": 0.40,
        "url_footnote_threshold": 60,
        "header_left": "",
        "header_right": "",
        "footer_left": "",
        "footer_center": "\\thepage",
        "footer_right": "",
        "logo": "",
        "style_dir": "",
        "callout_colors": {
            "note": [219, 234, 254],
            "tip": [220, 252, 231],
            "warning": [254, 243, 199],
            "danger": [254, 226, 226],
        },
    },
}


def test_load_config_returns_convert_config(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert isinstance(result, ConvertConfig)
    assert isinstance(result.mermaid, MermaidConfig)
    assert isinstance(result.obsidian, ObsidianConfig)
    assert isinstance(result.pandoc, PandocConfig)
    assert isinstance(result.style, StyleConfig)


def test_load_config_relative_mmdc_resolved(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert result.mermaid.mmdc_bin == tmp_path / ".mmdc/node_modules/.bin/mmdc"


def test_load_config_absolute_mmdc_preserved(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["mermaid"] = {**VALID_DATA["mermaid"], "mmdc_bin": "/usr/local/bin/mmdc"}
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.mermaid.mmdc_bin == Path("/usr/local/bin/mmdc")


def test_load_config_scale_is_int(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert result.mermaid.scale == 3


def test_config_is_frozen(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    with pytest.raises(AttributeError):
        result.mermaid = result.mermaid  # type: ignore[misc]


def test_pandoc_config_only_has_from_format(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert result.pandoc.from_format == "gfm-tex_math_dollars"
    assert not hasattr(result.pandoc, "geometry")


def test_style_config_loaded(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert result.style.name == "default"
    assert result.style.geometry == "a4paper,margin=25mm"
    assert result.style.fontsize == "11pt"
    assert result.style.linkcolor == "NavyBlue"
    assert result.style.urlcolor == "NavyBlue"
    assert result.style.line_spacing == 1.0
    assert result.style.table_fontsize == "small"
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
    cfg = _write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    cc = result.style.callout_colors
    assert isinstance(cc, CalloutColors)
    assert cc.note == (219, 234, 254)
    assert cc.tip == (220, 252, 231)
    assert cc.warning == (254, 243, 199)
    assert cc.danger == (254, 226, 226)


def test_callout_colors_frozen(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    with pytest.raises(AttributeError):
        result.style.callout_colors = result.style.callout_colors  # type: ignore[misc]


def test_style_config_frozen(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    with pytest.raises(AttributeError):
        result.style = result.style  # type: ignore[misc]


def test_line_spacing_float_conversion(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "line_spacing": 1}  # int in yaml
    cfg = _write_config(tmp_path, data)
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


# ── deep merge ──────────────────────────────────────────────────────────────


def test_deep_merge_shallow_override() -> None:
    base = {"a": 1, "b": 2}
    override = {"b": 3, "c": 4}
    result = _deep_merge(base, override)
    assert result == {"a": 1, "b": 3, "c": 4}


def test_deep_merge_nested_dict() -> None:
    base = {"style": {"name": "default", "fontsize": "10pt"}}
    override = {"style": {"fontsize": "12pt"}}
    result = _deep_merge(base, override)
    assert result["style"]["name"] == "default"
    assert result["style"]["fontsize"] == "12pt"


def test_deep_merge_base_unchanged() -> None:
    base = {"a": {"b": 1}}
    override = {"a": {"b": 2}}
    _deep_merge(base, override)
    assert base["a"]["b"] == 1


# ── partial config (merges with defaults) ───────────────────────────────────


def test_partial_config_merges_with_defaults(tmp_path: Path) -> None:
    """A minimal YAML with only overrides should produce a valid config."""
    partial = {"style": {"fontsize": "12pt"}}
    cfg = _write_config(tmp_path, partial)
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


def test_logo_field_loaded(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "logo": "brand_logo.png"}
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.logo == "brand_logo.png"


def test_style_dir_field_loaded(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "style_dir": "/custom/styles/brand"}
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.style_dir == "/custom/styles/brand"
