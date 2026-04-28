"""YAML loading, merging, parsing, and config building."""

from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from obsidian_export.config.models import (
    CalloutColors,
    ConvertConfig,
    HeadingStyle,
    MermaidConfig,
    ObsidianConfig,
    PandocConfig,
    StyleConfig,
    TitleStyle,
)
from obsidian_export.config.validators import validate_from_format, validate_pandoc_variable, validate_url_strategy


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base. override wins on conflicts."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_default_yaml() -> dict[str, Any]:
    """Load the bundled default.yaml."""
    ref = resources.files("obsidian_export") / "defaults" / "default.yaml"
    return yaml.safe_load(ref.read_text(encoding="utf-8"))


def resolve_path(raw_path: str, config_dir: Path | None) -> str:
    """Resolve a relative path string against config_dir. Return as string."""
    if raw_path and config_dir and not Path(raw_path).is_absolute():
        return str((config_dir / raw_path).resolve())
    return raw_path


def parse_brand_colors(raw: dict[str, Any]) -> tuple[tuple[str, int, int, int], ...]:
    """Parse brand_colors dict {name: [r,g,b]} into tuple of (name, r, g, b)."""
    return tuple((name, int(rgb[0]), int(rgb[1]), int(rgb[2])) for name, rgb in raw.items())


def parse_heading_styles(raw: list[dict[str, Any]]) -> tuple[HeadingStyle, ...]:
    """Parse list of heading style dicts into tuple of HeadingStyle."""
    return tuple(
        HeadingStyle(
            level=h["level"],
            size=h["size"],
            bold=bool(h.get("bold", False)),
            sans=bool(h.get("sans", False)),
            color=h.get("color", ""),
            uppercase=bool(h.get("uppercase", False)),
        )
        for h in raw
    )


def parse_title_style(raw: dict[str, Any] | None) -> TitleStyle | None:
    """Parse title style dict into TitleStyle, or None if absent."""
    if not raw:
        return None
    return TitleStyle(
        size=raw["size"],
        bold=bool(raw.get("bold", False)),
        sans=bool(raw.get("sans", False)),
        color=raw.get("color", ""),
        date_visible=bool(raw.get("date_visible", True)),
        vskip_after=raw.get("vskip_after", ""),
    )


def parse_unicode_chars(raw: dict[str, str]) -> tuple[tuple[str, str], ...]:
    """Parse unicode_chars dict {char: latex} into tuple of (char, latex)."""
    return tuple((char, latex) for char, latex in raw.items())


def build_mermaid_config(raw: dict[str, Any], config_dir: Path | None) -> MermaidConfig:
    """Build MermaidConfig, resolving relative paths against config_dir."""
    puppeteer_config_raw = raw.get("puppeteer_config")
    puppeteer_config: Path | None = None
    if puppeteer_config_raw:
        puppeteer_config = Path(resolve_path(puppeteer_config_raw, config_dir))

    return MermaidConfig(
        mmdc_bin=Path(resolve_path(raw["mmdc_bin"], config_dir)),
        scale=raw["scale"],
        puppeteer_config=puppeteer_config,
    )


def build_style_config(raw: dict[str, Any], config_dir: Path | None) -> StyleConfig:
    """Build StyleConfig from raw style dict."""
    cc_raw = raw["callout_colors"]
    return StyleConfig(
        name=raw["name"],
        geometry=raw["geometry"],
        fontsize=raw["fontsize"],
        mainfont=raw["mainfont"],
        sansfont=raw["sansfont"],
        monofont=raw["monofont"],
        linkcolor=raw["linkcolor"],
        urlcolor=raw["urlcolor"],
        line_spacing=float(raw["line_spacing"]),
        table_fontsize=raw["table_fontsize"],
        code_fontsize=raw["code_fontsize"],
        image_max_height_ratio=float(raw["image_max_height_ratio"]),
        url_footnote_threshold=int(raw["url_footnote_threshold"]),
        header_left=raw["header_left"],
        header_right=raw["header_right"],
        footer_left=raw["footer_left"],
        footer_center=raw["footer_center"],
        footer_right=raw["footer_right"],
        callout_colors=CalloutColors(
            note=tuple(cc_raw["note"]),
            tip=tuple(cc_raw["tip"]),
            warning=tuple(cc_raw["warning"]),
            danger=tuple(cc_raw["danger"]),
        ),
        unicode_chars=parse_unicode_chars(raw.get("unicode_chars", {})),
        logo=resolve_path(raw["logo"], config_dir),
        style_dir=resolve_path(raw["style_dir"], config_dir),
        brand_colors=parse_brand_colors(raw.get("brand_colors", {}) or {}),
        heading_styles=parse_heading_styles(raw.get("heading_styles", []) or []),
        title_style=parse_title_style(raw.get("title_style")),
    )


def build_config(raw: dict[str, Any], config_dir: Path | None) -> ConvertConfig:
    """Build ConvertConfig from a raw dict. Resolve relative paths if config_dir given."""
    if config_dir is not None and not config_dir.is_absolute():
        config_dir = config_dir.resolve()

    from_format = raw["pandoc"]["from_format"]
    validate_from_format(from_format)

    style = build_style_config(raw["style"], config_dir)
    validate_pandoc_variable("geometry", style.geometry)
    validate_pandoc_variable("fontsize", style.fontsize)
    validate_pandoc_variable("linkcolor", style.linkcolor)
    validate_pandoc_variable("urlcolor", style.urlcolor)
    validate_pandoc_variable("code_fontsize", style.code_fontsize)
    validate_pandoc_variable("table_fontsize", style.table_fontsize)

    validate_url_strategy(raw["obsidian"]["url_strategy"])

    return ConvertConfig(
        mermaid=build_mermaid_config(raw["mermaid"], config_dir),
        obsidian=ObsidianConfig(
            url_strategy=raw["obsidian"]["url_strategy"],
            url_length_threshold=raw["obsidian"]["url_length_threshold"],
            max_embed_depth=int(raw["obsidian"]["max_embed_depth"]),
        ),
        pandoc=PandocConfig(
            from_format=from_format,
        ),
        style=style,
    )


def default_config() -> ConvertConfig:
    """Return ConvertConfig with all defaults from bundled default.yaml."""
    return build_config(load_default_yaml(), config_dir=None)


def load_config(path: Path) -> ConvertConfig:
    """Load config from YAML file, merging on top of bundled defaults.

    Users can write minimal YAML with only overrides. Relative paths in
    config are resolved relative to the config file's directory.
    """
    user_raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not user_raw:
        user_raw = {}
    base = load_default_yaml()
    merged = deep_merge(base, user_raw)
    return build_config(merged, config_dir=path.parent)
