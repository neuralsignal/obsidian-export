"""Tests for config deep merging and style field loading."""

from pathlib import Path

import pytest
from conftest import VALID_DATA, write_config

from obsidian_export.config import (
    HeadingStyle,
    TitleStyle,
    deep_merge,
    default_config,
    load_config,
)

# ── deep merge ──────────────────────────────────────────────────────────────


def test_deep_merge_shallow_override() -> None:
    base = {"a": 1, "b": 2}
    override = {"b": 3, "c": 4}
    result = deep_merge(base, override)
    assert result == {"a": 1, "b": 3, "c": 4}


def test_deep_merge_nested_dict() -> None:
    base = {"style": {"name": "default", "fontsize": "10pt"}}
    override = {"style": {"fontsize": "12pt"}}
    result = deep_merge(base, override)
    assert result["style"]["name"] == "default"
    assert result["style"]["fontsize"] == "12pt"


def test_deep_merge_base_unchanged() -> None:
    base = {"a": {"b": 1}}
    override = {"a": {"b": 2}}
    deep_merge(base, override)
    assert base["a"]["b"] == 1


# ── logo, unicode, style_dir ──────────────────────────────────────────────


def test_logo_field_loaded(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "logo": "brand_logo.png"}
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.logo == str(tmp_path / "brand_logo.png")


def test_unicode_chars_loaded(tmp_path: Path) -> None:
    cfg = write_config(tmp_path, VALID_DATA)
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
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    chars_dict = dict(result.style.unicode_chars)
    # Override applied
    assert chars_dict["⚠"] == "\\ensuremath{\\bigtriangleup}"
    # Other defaults inherited via deep merge
    assert "→" in chars_dict


def test_style_dir_field_loaded(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "style_dir": "/custom/styles/brand"}
    cfg = write_config(tmp_path, data)
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
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert ("petrol", 20, 75, 95) in result.style.brand_colors
    assert ("turkis", 0, 152, 160) in result.style.brand_colors


def test_brand_colors_frozen(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {
        **VALID_DATA["style"],
        "brand_colors": {"red": [255, 0, 0]},
    }
    cfg = write_config(tmp_path, data)
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
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert len(result.style.heading_styles) == 2
    assert result.style.heading_styles[0] == HeadingStyle(
        level="section", size="Large", bold=True, sans=True, color="petrol", uppercase=False
    )
    assert result.style.heading_styles[1] == HeadingStyle(
        level="subsection", size="large", bold=True, sans=True, color="turkis", uppercase=True
    )


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
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.title_style == TitleStyle(
        size="huge", bold=True, sans=True, color="petrol", date_visible=True, vskip_after="2em"
    )


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
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.title_style == TitleStyle(
        size="LARGE", bold=False, sans=False, color="", date_visible=False, vskip_after=""
    )


def test_logo_resolved_to_absolute(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "logo": "images/logo.png"}
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.logo == str(tmp_path / "images/logo.png")


def test_logo_absolute_preserved(tmp_path: Path) -> None:
    data = dict(VALID_DATA)
    data["style"] = {**VALID_DATA["style"], "logo": "/absolute/path/logo.png"}
    cfg = write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.logo == "/absolute/path/logo.png"
