# Configuration

A config YAML can override any subset of defaults. Only include fields you want to change:

```yaml
# Minimal override — everything else uses defaults
style:
  fontsize: "12pt"
  mainfont: "Georgia"
  line_spacing: 1.5
```

## Config Loading

Configuration is merged on top of built-in defaults. You only need to specify the values you want to override. The merge is recursive — nested sections are merged independently.

### CLI

```bash
# Use a config file
obsidian-export convert --input note.md --format pdf --output note.pdf --config my_config.yaml

# Use a named profile
obsidian-export convert --input note.md --format pdf --output note.pdf --profile my_brand
```

### Python API

```python
from pathlib import Path
from obsidian_export.config import load_config, default_config

# Load from file (merges with defaults)
config = load_config(Path("my_config.yaml"))

# Use pure defaults
config = default_config()
```

## Full Config Reference

```yaml
mermaid:
  mmdc_bin: "mmdc"          # Path to Mermaid CLI binary
  scale: 3                  # PNG render scale

obsidian:
  wikilink_strategy: "text"           # How to handle [[wikilinks]]
  url_strategy: "footnote_long"       # bare URL handling: keep|footnote_long|footnote_all|strip
  url_length_threshold: 60            # URL length for footnote_long strategy

pandoc:
  from_format: "gfm-tex_math_dollars+footnotes" # Pandoc input format

style:
  name: "default"                     # Style name (resolves to header.tex template)
  geometry: "a4paper,margin=25mm"     # Page geometry
  fontsize: "10pt"                    # Base font size
  mainfont: ""                        # Main font (XeLaTeX)
  sansfont: ""                        # Sans font
  monofont: ""                        # Mono font
  linkcolor: "NavyBlue"              # Internal link color
  urlcolor: "NavyBlue"               # URL color
  line_spacing: 1.0                  # Line spacing multiplier
  table_fontsize: "small"            # Font size in tables
  image_max_height_ratio: 0.40       # Max image height as fraction of page
  url_footnote_threshold: 60         # URL length threshold for footnoting
  header_left: ""                    # Left header (supports {doc_title}, {logo_path})
  header_right: ""                   # Right header
  footer_left: ""                    # Left footer
  footer_center: "\\thepage"         # Center footer
  footer_right: ""                   # Right footer
  logo: ""                           # Logo filename (relative to config dir)
  style_dir: ""                      # Explicit style directory path
  unicode_chars:                     # Unicode -> LaTeX substitutions
    "\u26a0": "\\ensuremath{\\triangle}"
    "\u2705": "\\ensuremath{\\checkmark}"
    "\u274c": "\\ensuremath{\\times}"
    # ... see default.yaml for full list
  callout_colors:
    note: [219, 234, 254]
    tip: [220, 252, 231]
    warning: [254, 243, 199]
    danger: [254, 226, 226]
  brand_colors:                      # Custom named colors (empty = none)
    petrol: [20, 75, 95]
    turkis: [0, 152, 160]
  heading_styles:                    # Custom heading formats (empty = default)
    - level: "section"               # LaTeX level: section, subsection, subsubsection
      size: "Large"                  # LaTeX size: huge, LARGE, Large, large, normalsize
      bold: true
      sans: true                     # Use sans-serif font
      color: "petrol"               # Reference to brand_colors name or LaTeX color
      uppercase: false
    - level: "subsection"
      size: "large"
      bold: true
      sans: true
      color: "turkis"
      uppercase: true                # Render heading text in UPPERCASE
  title_style: null                  # Custom title block (null = default)
    # size: "huge"
    # bold: true
    # sans: true
    # color: "petrol"
    # date_visible: true
    # vskip_after: "2em"
```

## Section Reference

### `mermaid`

Controls Mermaid diagram rendering. Requires [mermaid-cli](https://github.com/mermaid-js/mermaid-cli) (`mmdc`) to be installed.

| Field | Type | Description |
|-------|------|-------------|
| `mmdc_bin` | string | Path to the mmdc binary |
| `scale` | integer | PNG render scale factor |

### `obsidian`

Controls Obsidian-specific syntax handling.

| Field | Type | Description |
|-------|------|-------------|
| `wikilink_strategy` | string | How to convert wikilinks (`text`) |
| `url_strategy` | string | URL handling: `keep`, `footnote_long`, `footnote_all`, `strip` |
| `url_length_threshold` | integer | URL length threshold for `footnote_long` strategy |

### `pandoc`

Controls pandoc conversion settings.

| Field | Type | Description |
|-------|------|-------------|
| `from_format` | string | Pandoc input format string |

### `style`

Controls the visual appearance of the output. See [Custom Styles](custom-styles.md) for detailed guidance on fonts, colors, headers/footers, and heading formats.
