# obsidian-export

Convert Obsidian-flavored Markdown to PDF and DOCX. Handles wikilinks, embeds, callouts, Mermaid diagrams, and frontmatter — producing clean, professional documents via a 5-stage pipeline (vault ops → preprocess → mermaid → SVG → pandoc).

## Installation

### conda-forge (recommended)

Installs obsidian-export with all required system dependencies (pandoc, tectonic, librsvg) in one command:

```bash
conda install -c conda-forge obsidian-export
```

Or with [pixi](https://pixi.sh/):

```bash
pixi global install obsidian-export
```

> **Note:** The conda-forge package is pending review. Until it's accepted, install from source using pixi:
>
> ```bash
> git clone https://github.com/neuralsignal/obsidian-export.git
> cd obsidian-export
> pixi install
> pixi run obsidian-export --help
> ```

### pip

```bash
pip install obsidian-export
```

With pip, you must separately install [pandoc](https://pandoc.org/) >= 3.5, [tectonic](https://tectonic-typesetting.github.io/) >= 0.15, and [librsvg](https://wiki.gnome.org/Projects/LibRsvg). Run `obsidian-export doctor` to check.

### Mermaid Support (optional)

For Mermaid diagram rendering, install [Node.js](https://nodejs.org/) >= 20 and [mermaid-cli](https://github.com/mermaid-js/mermaid-cli):

```bash
npm install -g @mermaid-js/mermaid-cli
```

## Quick Start

```bash
# Convert with default settings
obsidian-export convert --input my_note.md --format pdf --output my_note.pdf

# Convert to DOCX
obsidian-export convert --input my_note.md --format docx --output my_note.docx

# Use a custom profile
obsidian-export convert --input my_note.md --format pdf --output my_note.pdf --profile my_brand
```

## Profile Management

Profiles are YAML config files stored in `~/.obsidian-export/profiles/`.

```bash
# Initialize directory structure and default profile
obsidian-export init

# Create a new profile (starts from defaults)
obsidian-export profile create my_brand

# Create from existing YAML
obsidian-export profile create my_brand --from existing_config.yaml

# List profiles
obsidian-export profile list

# Show profile contents
obsidian-export profile show my_brand

# Delete a profile
obsidian-export profile delete my_brand --yes
```

## Custom Styles

Styles are LaTeX header templates. Place custom styles in `~/.obsidian-export/styles/<name>/header.tex`.

Style resolution order:
1. `style_dir` field in config (explicit path)
2. Built-in styles (`default`)
3. User styles in `~/.obsidian-export/styles/<name>/`
4. Treat style name as a filesystem path

## Configuration

A config YAML can override any subset of defaults. Only include fields you want to change:

```yaml
# Minimal override — everything else uses defaults
style:
  fontsize: "12pt"
  mainfont: "Georgia"
  line_spacing: 1.5
```

### Full Config Reference

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
  unicode_chars:                     # Unicode → LaTeX substitutions
    "⚠": "\\ensuremath{\\triangle}"
    "✅": "\\ensuremath{\\checkmark}"
    "❌": "\\ensuremath{\\times}"
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

## Python API

```python
from pathlib import Path
from obsidian_export import run
from obsidian_export.config import default_config, load_config

# Using defaults
config = default_config()
run(Path("my_note.md"), Path("output.pdf"), "pdf", config)

# Using a config file
config = load_config(Path("my_config.yaml"))
run(Path("my_note.md"), Path("output.pdf"), "pdf", config)
```

## What It Does

| Obsidian Syntax | Result |
|----------------|--------|
| `![[embed]]` | Resolved inline (content inlined) |
| `[[Entity\|Display]]` | Replaced with `Display` |
| `[[Entity]]` | Replaced with `Entity` |
| `> [!note]` callouts | Colored boxes (PDF) or blockquotes (DOCX) |
| `` ```mermaid `` | Rendered to PNG |
| `## Relations` section | Removed |
| YAML frontmatter | Title extracted, tags → keywords, rest removed |
| `$25/user` | Safe literal dollar sign |

## License

MIT
