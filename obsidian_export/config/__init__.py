"""Configuration module for obsidian-export pipeline.

Re-exports all public names so that
``from obsidian_export.config import X`` continues to work.
"""

from obsidian_export.config.loader import (
    build_config,
    deep_merge,
    default_config,
    load_config,
    load_default_yaml,
    parse_brand_colors,
    parse_heading_styles,
    parse_title_style,
    parse_unicode_chars,
    resolve_path,
)
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
from obsidian_export.config.validators import (
    validate_from_format,
    validate_pandoc_variable,
    validate_url_strategy,
)

__all__ = [
    "CalloutColors",
    "ConvertConfig",
    "HeadingStyle",
    "MermaidConfig",
    "ObsidianConfig",
    "PandocConfig",
    "StyleConfig",
    "TitleStyle",
    "build_config",
    "deep_merge",
    "default_config",
    "load_config",
    "load_default_yaml",
    "parse_brand_colors",
    "parse_heading_styles",
    "parse_title_style",
    "parse_unicode_chars",
    "resolve_path",
    "validate_from_format",
    "validate_pandoc_variable",
    "validate_url_strategy",
]
