# Quick Start

## CLI Usage

```bash
# Convert with default settings
obsidian-export convert --input my_note.md --format pdf --output my_note.pdf

# Convert to DOCX
obsidian-export convert --input my_note.md --format docx --output my_note.docx

# Use a custom profile
obsidian-export convert --input my_note.md --format pdf --output my_note.pdf --profile my_brand
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

## Check Dependencies

Verify that all required external tools are installed:

```bash
obsidian-export doctor
```

This checks for pandoc, tectonic, librsvg (`rsvg-convert`), and optionally mermaid-cli (`mmdc`).
