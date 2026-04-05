"""Configuration module for obsidian-export pipeline.

Re-exports all public and test-visible names so that
``from obsidian_export.config import X`` continues to work.
"""

from obsidian_export.config.loader import (
    _build_config,
    _deep_merge,
    _load_default_yaml,
    _parse_brand_colors,
    _parse_heading_styles,
    _parse_title_style,
    _parse_unicode_chars,
    _resolve_path,
    default_config,
    load_config,
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
    _validate_from_format,
    _validate_pandoc_variable,
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
    "_build_config",
    "_deep_merge",
    "_load_default_yaml",
    "_parse_brand_colors",
    "_parse_heading_styles",
    "_parse_title_style",
    "_parse_unicode_chars",
    "_resolve_path",
    "_validate_from_format",
    "_validate_pandoc_variable",
    "default_config",
    "load_config",
]
