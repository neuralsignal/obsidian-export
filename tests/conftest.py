"""Shared fixtures and data for config tests."""

from pathlib import Path

import yaml


def write_config(tmp_path: Path, data: dict) -> Path:
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
