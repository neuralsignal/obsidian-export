"""Configuration dataclasses for obsidian-export pipeline."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MermaidConfig:
    mmdc_bin: Path
    scale: int
    puppeteer_config: Path | None


@dataclass(frozen=True)
class ObsidianConfig:
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
