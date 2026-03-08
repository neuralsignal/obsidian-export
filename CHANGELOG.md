# Changelog

## 0.1.0 (2026-03-08)

Initial release.

- 5-stage pipeline: vault operations, preprocessing, Mermaid rendering, SVG conversion, Pandoc output
- Obsidian syntax stripping: wikilinks, embeds, callouts, Relations sections
- Frontmatter cleaning with tag-to-keyword conversion
- Recursive embed resolution with circular reference detection
- Mermaid diagram rendering via mmdc
- SVG-to-PDF conversion via rsvg-convert
- Profile management CLI (`obsidian-export profile create/list/show/delete`)
- User styles directory (`~/.obsidian-export/styles/`)
- Config merging: user YAML overrides bundled defaults
- `obsidian-export doctor` command for dependency checking
- PDF output via tectonic (XeLaTeX)
- DOCX output via pandoc
