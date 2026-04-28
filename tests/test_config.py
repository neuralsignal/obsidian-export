"""Tests for obsidian_export.config."""

from pathlib import Path

import pytest
import yaml
from hypothesis import given
from hypothesis import strategies as st

from obsidian_export.config import (
    CalloutColors,
    ConvertConfig,
    HeadingStyle,
    MermaidConfig,
    ObsidianConfig,
    PandocConfig,
    StyleConfig,
    TitleStyle,
    build_config,
    deep_merge,
    default_config,
    load_config,
    parse_brand_colors,
    parse_heading_styles,
    parse_title_style,
    parse_unicode_chars,
    resolve_path,
    validate_from_format,
    validate_pandoc_variable,
)
from obsidian_export.exceptions import ConfigValueError


def _write_config(tmp_path: Path, data: dict) -> Path:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.dump(data), encoding="utf-8")
    return cfg


VALID_DATA = {
    "mermaid": {"mmdc_bin": ".mmdc/node_modules/.bin/mmdc", "scale": 3},
    "obsidian": {
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
        "code_fontsize": "footnotesize",
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


def test_default_config_code_fontsize() -> None:
    result = default_config()
    assert result.style.code_fontsize == "footnotesize"


def test_code_fontsize_override(tmp_path: Path) -> None:
    partial = {"style": {"code_fontsize": "small"}}
    cfg = _write_config(tmp_path, partial)
    result = load_config(cfg)
    assert result.style.code_fontsize == "small"
    assert result.style.table_fontsize == "small"  # default unchanged


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
    cfg = _write_config(tmp_path, data)
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
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.style.title_style == TitleStyle(
        size="LARGE", bold=False, sans=False, color="", date_visible=False, vskip_after=""
    )


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


# ── _resolve_path ──────────────────────────────────────────────────────────


def test_resolve_path_empty_string() -> None:
    assert resolve_path("", Path("/some/dir")) == ""


def test_resolve_path_absolute_unchanged() -> None:
    assert resolve_path("/abs/file.txt", Path("/some/dir")) == "/abs/file.txt"


def test_resolve_path_relative_resolved(tmp_path: Path) -> None:
    result = resolve_path("sub/file.txt", tmp_path)
    assert result == str((tmp_path / "sub/file.txt").resolve())


def test_resolve_path_no_config_dir() -> None:
    assert resolve_path("relative/path", None) == "relative/path"


# ── _parse_brand_colors ───────────────────────────────────────────────────


def test_parse_brand_colors_empty() -> None:
    assert parse_brand_colors({}) == ()


def test_parse_brand_colors_single() -> None:
    result = parse_brand_colors({"red": [255, 0, 0]})
    assert result == (("red", 255, 0, 0),)


def test_parse_brand_colors_coerces_to_int() -> None:
    result = parse_brand_colors({"x": [1.9, 2.1, 3.7]})
    assert result == (("x", 1, 2, 3),)


@given(
    name=st.text(min_size=1, max_size=10),
    r=st.integers(0, 255),
    g=st.integers(0, 255),
    b=st.integers(0, 255),
)
def test_parse_brand_colors_property(name: str, r: int, g: int, b: int) -> None:
    result = parse_brand_colors({name: [r, g, b]})
    assert len(result) == 1
    assert result[0] == (name, r, g, b)


# ── _parse_heading_styles ─────────────────────────────────────────────────


def test_parse_heading_styles_empty() -> None:
    assert parse_heading_styles([]) == ()


def test_parse_heading_styles_defaults_optional_fields() -> None:
    result = parse_heading_styles([{"level": "section", "size": "Large"}])
    assert result == (HeadingStyle(level="section", size="Large", bold=False, sans=False, color="", uppercase=False),)


def test_parse_heading_styles_all_fields() -> None:
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
def test_parse_heading_styles_property(level: str, size: str, bold: bool, sans: bool, uppercase: bool) -> None:
    raw = [{"level": level, "size": size, "bold": bold, "sans": sans, "color": "", "uppercase": uppercase}]
    result = parse_heading_styles(raw)
    assert len(result) == 1
    assert result[0].level == level
    assert result[0].bold == bold


# ── _parse_title_style ────────────────────────────────────────────────────


def test_parse_title_style_none() -> None:
    assert parse_title_style(None) is None


def test_parse_title_style_empty_dict() -> None:
    assert parse_title_style({}) is None


def test_parse_title_style_full() -> None:
    raw = {"size": "huge", "bold": True, "sans": True, "color": "blue", "date_visible": False, "vskip_after": "1em"}
    result = parse_title_style(raw)
    assert result == TitleStyle(size="huge", bold=True, sans=True, color="blue", date_visible=False, vskip_after="1em")


def test_parse_title_style_defaults_optional() -> None:
    result = parse_title_style({"size": "large"})
    assert result is not None
    assert result.bold is False
    assert result.sans is False
    assert result.color == ""
    assert result.date_visible is True
    assert result.vskip_after == ""


# ── _parse_unicode_chars ──────────────────────────────────────────────────


def test_parse_unicode_chars_empty() -> None:
    assert parse_unicode_chars({}) == ()


def test_parse_unicode_chars_round_trip() -> None:
    raw = {"⚠": "\\triangle", "→": "\\to"}
    result = parse_unicode_chars(raw)
    assert dict(result) == raw


@given(data=st.dictionaries(st.text(min_size=1, max_size=3), st.text(min_size=1, max_size=30), max_size=10))
def test_parse_unicode_chars_property(data: dict[str, str]) -> None:
    result = parse_unicode_chars(data)
    assert len(result) == len(data)
    assert dict(result) == data


# ── puppeteer_config resolution ────────────────────────────────────────────


def test_load_config_puppeteer_config_relative_resolved(tmp_path: Path) -> None:
    """Relative puppeteer_config is resolved against the config file directory."""
    data = dict(VALID_DATA)
    data["mermaid"] = {
        **VALID_DATA["mermaid"],
        "puppeteer_config": "puppeteer-config.json",
    }
    cfg = _write_config(tmp_path, data)
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
    cfg = _write_config(tmp_path, data)
    result = load_config(cfg)
    assert result.mermaid.puppeteer_config == Path("/etc/puppeteer.json")


# ── _build_config with relative config_dir ─────────────────────────────────


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


# ── _validate_from_format ────────────────────────────────────────────────


class TestValidateFromFormat:
    def test_default_format_accepted(self) -> None:
        validate_from_format("gfm-tex_math_dollars+footnotes")

    def test_plain_base_format_accepted(self) -> None:
        validate_from_format("gfm")
        validate_from_format("markdown")
        validate_from_format("commonmark")
        validate_from_format("commonmark_x")

    def test_multiple_extensions_accepted(self) -> None:
        validate_from_format("gfm+footnotes-smart+pipe_tables")

    def test_unsupported_base_format_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Unsupported pandoc base format"):
            validate_from_format("html")

    def test_dangerous_extension_raw_html_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Dangerous pandoc extension.*raw_html"):
            validate_from_format("gfm+raw_html")

    def test_dangerous_extension_raw_attribute_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Dangerous pandoc extension.*raw_attribute"):
            validate_from_format("markdown+raw_attribute")

    def test_disabling_dangerous_extension_accepted(self) -> None:
        validate_from_format("gfm-raw_html")

    def test_malformed_extension_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Malformed pandoc extension"):
            validate_from_format("gfm+123bad")

    @given(base=st.sampled_from(["gfm", "markdown", "commonmark", "commonmark_x"]))
    def test_safe_base_formats_always_accepted(self, base: str) -> None:
        validate_from_format(base)


class TestValidateFromFormatIntegration:
    """Verify that load_config rejects unsafe from_format values."""

    def test_load_config_rejects_raw_html(self, tmp_path: Path) -> None:
        data = dict(VALID_DATA)
        data["pandoc"] = {"from_format": "gfm+raw_html+footnotes"}
        cfg = _write_config(tmp_path, data)
        with pytest.raises(ConfigValueError, match="raw_html"):
            load_config(cfg)

    def test_load_config_rejects_unsupported_format(self, tmp_path: Path) -> None:
        data = dict(VALID_DATA)
        data["pandoc"] = {"from_format": "rst"}
        cfg = _write_config(tmp_path, data)
        with pytest.raises(ConfigValueError, match="Unsupported pandoc base format"):
            load_config(cfg)


# ── _validate_pandoc_variable ────────────────────────────────────────────


class TestValidatePandocVariable:
    def test_safe_geometry_accepted(self) -> None:
        validate_pandoc_variable("geometry", "a4paper,margin=25mm")

    def test_safe_fontsize_accepted(self) -> None:
        validate_pandoc_variable("fontsize", "10pt")

    def test_safe_color_accepted(self) -> None:
        validate_pandoc_variable("linkcolor", "NavyBlue")

    def test_empty_string_accepted(self) -> None:
        validate_pandoc_variable("linkcolor", "")

    def test_shell_metachar_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Invalid characters"):
            validate_pandoc_variable("geometry", "a4paper;rm -rf /")

    def test_backtick_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Invalid characters"):
            validate_pandoc_variable("fontsize", "`malicious`")

    def test_braces_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Invalid characters"):
            validate_pandoc_variable("geometry", "a4paper{evil}")

    @given(value=st.from_regex(r"^[a-zA-Z0-9,=._\- ]+$", fullmatch=True))
    def test_safe_values_always_accepted(self, value: str) -> None:
        validate_pandoc_variable("test_field", value)

    @given(
        value=st.text(
            alphabet=st.sampled_from(list(";|&`${}()[]!@#%^*<>?'\"\\\n\t")),
            min_size=1,
            max_size=5,
        )
    )
    def test_dangerous_chars_always_rejected(self, value: str) -> None:
        with pytest.raises(ConfigValueError):
            validate_pandoc_variable("test_field", value)


class TestValidatePandocVariableIntegration:
    """Verify that load_config rejects unsafe style variable values."""

    def test_load_config_rejects_malicious_geometry(self, tmp_path: Path) -> None:
        partial = {"style": {"geometry": "a4paper;$(evil)"}}
        cfg = _write_config(tmp_path, partial)
        with pytest.raises(ConfigValueError, match="geometry"):
            load_config(cfg)
