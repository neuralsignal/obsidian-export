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
        "max_embed_depth": 10,
    },
    "pandoc": {
        "from_format": "gfm-tex_math_dollars+footnotes",
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
        "unicode_chars": {
            "⚠": "\\ensuremath{\\triangle}",
            "✅": "\\ensuremath{\\checkmark}",
        },
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
    assert result.pandoc.from_format == "gfm-tex_math_dollars+footnotes"
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
    assert result.obsidian.max_embed_depth == 10


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
    assert result.style.logo == str(tmp_path / "brand_logo.png")


def test_unicode_chars_loaded(tmp_path: Path) -> None:
    cfg = _write_config(tmp_path, VALID_DATA)
    result = load_config(cfg)
    assert isinstance(result.style.unicode_chars, tuple)
    assert ("⚠", "\\ensuremath{\\triangle}") in result.style.unicode_chars
    assert ("✅", "\\ensuremath{\\checkmark}") in result.style.unicode_chars


def test_unicode_chars_from_defaults() -> None:
    result = default_config()
    chars_dict = dict(result.style.unicode_chars)
    assert "⚠" in chars_dict
    assert "→" in chars_dict
    assert chars_dict["≥"] == "\\ensuremath{\\geq}"


def test_unicode_chars_override_merges(tmp_path: Path) -> None:
    """User config with unicode_chars overrides default via deep merge."""
    data = dict(VALID_DATA)
    data["style"] = {
        **VALID_DATA["style"],
        "unicode_chars": {"⚠": "\\ensuremath{\\bigtriangleup}"},
    }
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    chars_dict = dict(result.style.unicode_chars)
    # Override applied
    assert chars_dict["⚠"] == "\\ensuremath{\\bigtriangleup}"
    # Other defaults inherited via deep merge
    assert "→" in chars_dict


def test_style_dir_field_loaded(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "style_dir": "/custom/styles/brand"}
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.style_dir == "/custom/styles/brand"


# ── brand_colors ───────────────────────────────────────────────────────────


def test_brand_colors_empty_by_default() -> None:
    result = default_config()
    assert result.style.brand_colors == ()


def test_brand_colors_parsed(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {
        **VALID_DATA["style"],
        "brand_colors": {"petrol": [20, 75, 95], "turkis": [0, 152, 160]},
    }
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert ("petrol", 20, 75, 95) in result.style.brand_colors
    assert ("turkis", 0, 152, 160) in result.style.brand_colors


def test_brand_colors_frozen(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {
        **VALID_DATA["style"],
        "brand_colors": {"red": [255, 0, 0]},
    }
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    with pytest.raises(AttributeError):
        result.style.brand_colors = ()  # type: ignore[misc]


# ── heading_styles ─────────────────────────────────────────────────────────


def test_heading_styles_empty_by_default() -> None:
    result = default_config()
    assert result.style.heading_styles == ()


def test_heading_styles_parsed(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {
        **VALID_DATA["style"],
        "heading_styles": [
            {"level": "section", "size": "Large", "bold": True, "sans": True, "color": "petrol", "uppercase": False},
            {"level": "subsection", "size": "large", "bold": True, "sans": True, "color": "turkis", "uppercase": True},
        ],
    }
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert len(result.style.heading_styles) == 2
    assert result.style.heading_styles[0] == ("section", "Large", True, True, "petrol", False)
    assert result.style.heading_styles[1] == ("subsection", "large", True, True, "turkis", True)


# ── title_style ────────────────────────────────────────────────────────────


def test_title_style_none_by_default() -> None:
    result = default_config()
    assert result.style.title_style is None


def test_title_style_parsed(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {
        **VALID_DATA["style"],
        "title_style": {
            "size": "huge",
            "bold": True,
            "sans": True,
            "color": "petrol",
            "date_visible": True,
            "vskip_after": "2em",
        },
    }
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.title_style == ("huge", True, True, "petrol", True, "2em")


def test_title_style_date_hidden(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {
        **VALID_DATA["style"],
        "title_style": {
            "size": "LARGE",
            "bold": False,
            "sans": False,
            "color": "",
            "date_visible": False,
            "vskip_after": "",
        },
    }
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.title_style == ("LARGE", False, False, "", False, "")


def test_logo_resolved_to_absolute(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "logo": "images/logo.png"}
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.logo == str(tmp_path / "images/logo.png")


def test_logo_absolute_preserved(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "logo": "/absolute/path/logo.png"}
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.logo == "/absolute/path/logo.png"
