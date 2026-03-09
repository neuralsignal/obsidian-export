# obsidian-export

Convert Obsidian-flavored Markdown to PDF and DOCX.

[![PyPI](https://img.shields.io/pypi/v/obsidian-export)](https://pypi.org/project/obsidian-export/)
[![License](https://img.shields.io/github/license/neuralsignal/obsidian-export)](https://github.com/neuralsignal/obsidian-export/blob/main/LICENSE)

Handles wikilinks, embeds, callouts, Mermaid diagrams, and frontmatter — producing clean, professional documents via a 5-stage pipeline.

## Features

- **Obsidian syntax stripping** — wikilinks, embeds, callouts, Relations sections
- **Mermaid diagram rendering** — via mermaid-cli (mmdc)
- **Custom styles** — LaTeX header templates with fonts, colors, and branding
- **Profile management** — save and reuse conversion configs
- **PDF and DOCX output** — via pandoc + tectonic (XeLaTeX)

## Quick links

- [Installation](getting-started/installation.md)
- [Quick Start](getting-started/quickstart.md)
- [API Reference](reference/api.md)
- [Changelog](changelog.md)
