"""Tests for config parser functions: resolve_path, parse_* helpers."""

from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from obsidian_export.config import (
    HeadingStyle,
    TitleStyle,
    parse_brand_colors,
    parse_heading_styles,
    parse_title_style,
    parse_unicode_chars,
    resolve_path,
)

# ── resolve_path ──────────────────────────────────────────────────────────


def testresolve_path_empty_string() -> None:
    assert resolve_path("", Path("/some/dir")) == ""


def testresolve_path_absolute_unchanged() -> None:
    assert resolve_path("/abs/file.txt", Path("/some/dir")) == "/abs/file.txt"


def testresolve_path_relative_resolved(tmp_path: Path) -> None:
    result = resolve_path("sub/file.txt", tmp_path)
    assert result == str((tmp_path / "sub/file.txt").resolve())


def testresolve_path_no_config_dir() -> None:
    assert resolve_path("relative/path", None) == "relative/path"


# ── parse_brand_colors ───────────────────────────────────────────────────


def testparse_brand_colors_empty() -> None:
    assert parse_brand_colors({}) == ()


def testparse_brand_colors_single() -> None:
    result = parse_brand_colors({"red": [255, 0, 0]})
    assert result == (("red", 255, 0, 0),)


def testparse_brand_colors_coerces_to_int() -> None:
    result = parse_brand_colors({"x": [1.9, 2.1, 3.7]})
    assert result == (("x", 1, 2, 3),)


@given(
    name=st.text(min_size=1, max_size=10),
    r=st.integers(0, 255),
    g=st.integers(0, 255),
    b=st.integers(0, 255),
)
def testparse_brand_colors_property(name: str, r: int, g: int, b: int) -> None:
    result = parse_brand_colors({name: [r, g, b]})
    assert len(result) == 1
    assert result[0] == (name, r, g, b)


# ── parse_heading_styles ─────────────────────────────────────────────────


def testparse_heading_styles_empty() -> None:
    assert parse_heading_styles([]) == ()


def testparse_heading_styles_defaults_optional_fields() -> None:
    result = parse_heading_styles([{"level": "section", "size": "Large"}])
    assert result == (HeadingStyle(level="section", size="Large", bold=False, sans=False, color="", uppercase=False),)


def testparse_heading_styles_all_fields() -> None:
    raw = [{"level": "sub", "size": "small", "bold": True, "sans": True, "color": "red", "uppercase": True}]
    result = parse_heading_styles(raw)
    assert result[0].bold is True
    assert result[0].uppercase is True
    assert result[0].color == "red"


@given(
    level=st.text(min_size=1, max_size=20),
    size=st.text(min_size=1, max_size=20),
    bold=st.booleans(),
    sans=st.booleans(),
    uppercase=st.booleans(),
)
def testparse_heading_styles_property(level: str, size: str, bold: bool, sans: bool, uppercase: bool) -> None:
    raw = [{"level": level, "size": size, "bold": bold, "sans": sans, "color": "", "uppercase": uppercase}]
    result = parse_heading_styles(raw)
    assert len(result) == 1
    assert result[0].level == level
    assert result[0].bold == bold


# ── parse_title_style ────────────────────────────────────────────────────


def testparse_title_style_none() -> None:
    assert parse_title_style(None) is None


def testparse_title_style_empty_dict() -> None:
    assert parse_title_style({}) is None


def testparse_title_style_full() -> None:
    raw = {"size": "huge", "bold": True, "sans": True, "color": "blue", "date_visible": False, "vskip_after": "1em"}
    result = parse_title_style(raw)
    assert result == TitleStyle(size="huge", bold=True, sans=True, color="blue", date_visible=False, vskip_after="1em")


def testparse_title_style_defaults_optional() -> None:
    result = parse_title_style({"size": "large"})
    assert result is not None
    assert result.bold is False
    assert result.sans is False
    assert result.color == ""
    assert result.date_visible is True
    assert result.vskip_after == ""


# ── parse_unicode_chars ──────────────────────────────────────────────────


def testparse_unicode_chars_empty() -> None:
    assert parse_unicode_chars({}) == ()


def testparse_unicode_chars_round_trip() -> None:
    raw = {"⚠": "\\triangle", "→": "\\to"}
    result = parse_unicode_chars(raw)
    assert dict(result) == raw


@given(data=st.dictionaries(st.text(min_size=1, max_size=3), st.text(min_size=1, max_size=30), max_size=10))
def testparse_unicode_chars_property(data: dict[str, str]) -> None:
    result = parse_unicode_chars(data)
    assert len(result) == len(data)
    assert dict(result) == data
