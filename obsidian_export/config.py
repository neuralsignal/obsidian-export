"""Configuration dataclasses for obsidian-export pipeline."""

from dataclasses import dataclass
from importlib import resources
from pathlib import Path

import yaml


@dataclass(frozen=True)
class MermaidConfig:
    mmdc_bin: Path
    scale: int


@dataclass(frozen=True)
class ObsidianConfig:
    wikilink_strategy: str
    url_strategy: str
    url_length_threshold: int


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
    image_max_height_ratio: float
    url_footnote_threshold: int
    header_left: str
    header_right: str
    footer_left: str
    footer_center: str
    footer_right: str
    callout_colors: CalloutColors
    logo: str
    style_dir: str


@dataclass(frozen=True)
class ConvertConfig:
    mermaid: MermaidConfig
    obsidian: ObsidianConfig
    pandoc: PandocConfig
    style: StyleConfig


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. override wins on conflicts."""
    merged = dict(base)
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_default_yaml() -> dict:
    """Load the bundled default.yaml."""
    ref = resources.files("obsidian_export") / "defaults" / "default.yaml"
    return yaml.safe_load(ref.read_text(encoding="utf-8"))


def _build_config(raw: dict, config_dir: Path | None) -> ConvertConfig:
    """Build ConvertConfig from a raw dict. Resolve relative paths if config_dir given."""
    mermaid_raw = raw["mermaid"]
    mmdc_bin_raw = Path(mermaid_raw["mmdc_bin"])
    if config_dir and not mmdc_bin_raw.is_absolute():
        mmdc_bin_raw = config_dir / mmdc_bin_raw

    style_raw = raw["style"]
    cc_raw = style_raw["callout_colors"]

    # Resolve relative style_dir against config_dir (same as mmdc_bin)
    style_dir_raw = style_raw["style_dir"]
    if style_dir_raw and config_dir and not Path(style_dir_raw).is_absolute():
        style_dir_raw = str(config_dir / style_dir_raw)

    return ConvertConfig(
        mermaid=MermaidConfig(
            mmdc_bin=mmdc_bin_raw,
            scale=mermaid_raw["scale"],
        ),
        obsidian=ObsidianConfig(
            wikilink_strategy=raw["obsidian"]["wikilink_strategy"],
            url_strategy=raw["obsidian"]["url_strategy"],
            url_length_threshold=raw["obsidian"]["url_length_threshold"],
        ),
        pandoc=PandocConfig(
            from_format=raw["pandoc"]["from_format"],
        ),
        style=StyleConfig(
            name=style_raw["name"],
            geometry=style_raw["geometry"],
            fontsize=style_raw["fontsize"],
            mainfont=style_raw["mainfont"],
            sansfont=style_raw["sansfont"],
            monofont=style_raw["monofont"],
            linkcolor=style_raw["linkcolor"],
            urlcolor=style_raw["urlcolor"],
            line_spacing=float(style_raw["line_spacing"]),
            table_fontsize=style_raw["table_fontsize"],
            image_max_height_ratio=float(style_raw["image_max_height_ratio"]),
            url_footnote_threshold=int(style_raw["url_footnote_threshold"]),
            header_left=style_raw["header_left"],
            header_right=style_raw["header_right"],
            footer_left=style_raw["footer_left"],
            footer_center=style_raw["footer_center"],
            footer_right=style_raw["footer_right"],
            callout_colors=CalloutColors(
                note=tuple(cc_raw["note"]),
                tip=tuple(cc_raw["tip"]),
                warning=tuple(cc_raw["warning"]),
                danger=tuple(cc_raw["danger"]),
            ),
            logo=style_raw["logo"],
            style_dir=style_dir_raw,
        ),
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
