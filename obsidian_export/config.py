"""Configuration dataclasses for obsidian-export pipeline."""

import re
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from obsidian_export.exceptions import ConfigValueError


@dataclass(frozen=True)
class MermaidConfig:
    mmdc_bin: Path
    scale: int
    puppeteer_config: Path | None = None


@dataclass(frozen=True)
class ObsidianConfig:
    wikilink_strategy: str
    url_strategy: str
    url_length_threshold: int
    max_embed_depth: int


@dataclass(frozen=True)
class PandocConfig:
    from_format: str


@dataclass(frozen=True)
class CalloutColors:
    note: tuple[int, int, int]
    tip: tuple[int, int, int]
    warning: tuple[int, int, int]
    danger: tuple[int, int, int]


@dataclass(frozen=True)
class HeadingStyle:
    level: str
    size: str
    bold: bool
    sans: bool
    color: str
    uppercase: bool


@dataclass(frozen=True)
class TitleStyle:
    size: str
    bold: bool
    sans: bool
    color: str
    date_visible: bool
    vskip_after: str


@dataclass(frozen=True)
class StyleConfig:
    name: str
    geometry: str
    fontsize: str
    mainfont: str
    sansfont: str
    monofont: str
    linkcolor: str
    urlcolor: str
    line_spacing: float
    table_fontsize: str
    code_fontsize: str
    image_max_height_ratio: float
    url_footnote_threshold: int
    header_left: str
    header_right: str
    footer_left: str
    footer_center: str
    footer_right: str
    callout_colors: CalloutColors
    unicode_chars: tuple[tuple[str, str], ...]
    logo: str
    style_dir: str
    brand_colors: tuple[tuple[str, int, int, int], ...]
    heading_styles: tuple[HeadingStyle, ...]
    title_style: TitleStyle | None


@dataclass(frozen=True)
class ConvertConfig:
    mermaid: MermaidConfig
    obsidian: ObsidianConfig
    pandoc: PandocConfig
    style: StyleConfig


_SAFE_PANDOC_FORMATS: frozenset[str] = frozenset(
    {
        "commonmark",
        "commonmark_x",
        "gfm",
        "markdown",
        "markdown_mmd",
        "markdown_phpextra",
        "markdown_strict",
    }
)

_DANGEROUS_EXTENSIONS: frozenset[str] = frozenset(
    {
        "raw_html",
        "raw_attribute",
    }
)

_PANDOC_EXTENSION_RE: re.Pattern[str] = re.compile(r"^[a-z][a-z0-9_]*$")

_PANDOC_VARIABLE_RE: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9,=._\- ]+$")


def _validate_from_format(value: str) -> None:
    """Validate pandoc from_format against safe base formats and extensions.

    Raises ConfigValueError if the base format is not allowlisted,
    any extension name is malformed, or a dangerous extension is enabled.
    """
    parts = re.split(r"(?=[+-])", value, maxsplit=1)
    base_format = parts[0]
    if base_format not in _SAFE_PANDOC_FORMATS:
        raise ConfigValueError(
            f"Unsupported pandoc base format: {base_format!r}. Allowed: {sorted(_SAFE_PANDOC_FORMATS)}"
        )

    if len(parts) < 2:
        return

    ext_string = parts[1]
    for match in re.finditer(r"([+-])([^+-]+)", ext_string):
        sign, ext_name = match.group(1), match.group(2)
        if not _PANDOC_EXTENSION_RE.match(ext_name):
            raise ConfigValueError(f"Malformed pandoc extension name: {ext_name!r} in from_format {value!r}")
        if sign == "+" and ext_name in _DANGEROUS_EXTENSIONS:
            raise ConfigValueError(
                f"Dangerous pandoc extension enabled: +{ext_name} in from_format {value!r}. "
                f"Blocked extensions: {sorted(_DANGEROUS_EXTENSIONS)}"
            )


def _validate_pandoc_variable(name: str, value: str) -> None:
    """Validate a string that will be passed as a pandoc --variable value.

    Allows alphanumeric characters and limited punctuation (commas, equals,
    dots, hyphens, underscores, spaces). Raises ConfigValueError on mismatch.
    """
    if not value:
        return
    if not _PANDOC_VARIABLE_RE.match(value):
        raise ConfigValueError(
            f"Invalid characters in style config {name!r}: {value!r}. "
            f"Only alphanumeric characters and ,=._- are allowed."
        )


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge override into base. override wins on conflicts."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_default_yaml() -> dict[str, Any]:
    """Load the bundled default.yaml."""
    ref = resources.files("obsidian_export") / "defaults" / "default.yaml"
    return yaml.safe_load(ref.read_text(encoding="utf-8"))


def _resolve_path(raw_path: str, config_dir: Path | None) -> str:
    """Resolve a relative path string against config_dir. Return as string."""
    if raw_path and config_dir and not Path(raw_path).is_absolute():
        return str((config_dir / raw_path).resolve())
    return raw_path


def _parse_brand_colors(raw: dict[str, Any]) -> tuple[tuple[str, int, int, int], ...]:
    """Parse brand_colors dict {name: [r,g,b]} into tuple of (name, r, g, b)."""
    return tuple((name, int(rgb[0]), int(rgb[1]), int(rgb[2])) for name, rgb in raw.items())


def _parse_heading_styles(raw: list[dict[str, Any]]) -> tuple[HeadingStyle, ...]:
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


def _parse_title_style(raw: dict[str, Any] | None) -> TitleStyle | None:
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


def _parse_unicode_chars(raw: dict[str, str]) -> tuple[tuple[str, str], ...]:
    """Parse unicode_chars dict {char: latex} into tuple of (char, latex)."""
    return tuple((char, latex) for char, latex in raw.items())


def _build_mermaid_config(raw: dict[str, Any], config_dir: Path | None) -> MermaidConfig:
    """Build MermaidConfig, resolving relative paths against config_dir."""
    mmdc_bin = Path(raw["mmdc_bin"])
    if config_dir and not mmdc_bin.is_absolute():
        mmdc_bin = config_dir / mmdc_bin

    puppeteer_config_raw = raw.get("puppeteer_config")
    puppeteer_config: Path | None = None
    if puppeteer_config_raw:
        puppeteer_config = Path(puppeteer_config_raw)
        if config_dir and not puppeteer_config.is_absolute():
            puppeteer_config = config_dir / puppeteer_config

    return MermaidConfig(
        mmdc_bin=mmdc_bin,
        scale=raw["scale"],
        puppeteer_config=puppeteer_config,
    )


def _build_style_config(raw: dict[str, Any], config_dir: Path | None) -> StyleConfig:
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
        unicode_chars=_parse_unicode_chars(raw.get("unicode_chars", {})),
        logo=_resolve_path(raw["logo"], config_dir),
        style_dir=_resolve_path(raw["style_dir"], config_dir),
        brand_colors=_parse_brand_colors(raw.get("brand_colors", {}) or {}),
        heading_styles=_parse_heading_styles(raw.get("heading_styles", []) or []),
        title_style=_parse_title_style(raw.get("title_style")),
    )


def _build_config(raw: dict, config_dir: Path | None) -> ConvertConfig:
    """Build ConvertConfig from a raw dict. Resolve relative paths if config_dir given."""
    if config_dir is not None and not config_dir.is_absolute():
        config_dir = config_dir.resolve()

    from_format = raw["pandoc"]["from_format"]
    _validate_from_format(from_format)

    style = _build_style_config(raw["style"], config_dir)
    _validate_pandoc_variable("geometry", style.geometry)
    _validate_pandoc_variable("fontsize", style.fontsize)
    _validate_pandoc_variable("linkcolor", style.linkcolor)
    _validate_pandoc_variable("urlcolor", style.urlcolor)

    return ConvertConfig(
        mermaid=_build_mermaid_config(raw["mermaid"], config_dir),
        obsidian=ObsidianConfig(
            wikilink_strategy=raw["obsidian"]["wikilink_strategy"],
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
    return _build_config(_load_default_yaml(), config_dir=None)


def load_config(path: Path) -> ConvertConfig:
    """Load config from YAML file, merging on top of bundled defaults.

    Users can write minimal YAML with only overrides. Relative paths in
    config are resolved relative to the config file's directory.
    """
    user_raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not user_raw:
        user_raw = {}
    base = _load_default_yaml()
    merged = _deep_merge(base, user_raw)
    return _build_config(merged, config_dir=path.parent)
