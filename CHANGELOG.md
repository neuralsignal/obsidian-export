# Changelog

## 0.2.4 (2026-03-09)

- Feat: add conda-forge recipe (`recipe/recipe.yaml`) -- `conda install obsidian-export` pulls pandoc, tectonic, and librsvg automatically
- Docs: rewrite Installation section with conda-forge/pixi as primary install method

## 0.2.3 (2026-03-09)

- CI: add factory-orchestrator workflow to sweep orphaned issues (GITHUB_TOKEN cascade fix)
- CI: increase dep-audit max-turns from 20 to 30 (match template default)
- CI: add auto-tag workflow for automatic releases on merge to main

## 0.2.2 (2026-03-08)

- Chore: sync pixi.toml version to match pyproject.toml

## 0.2.1 (2026-03-08)

- Fix: bump version for PyPI release

## 0.2.0 (2026-03-08)

- Fix: callouts now render as colored tcolorbox boxes instead of plain blockquotes — stage1 no longer strips `[!TYPE]` labels, allowing stage2's `convert_callouts()` to process them correctly
- Fix: footnotes (`[^name]` / `[^name]:`) now render properly — added `+footnotes` extension to `gfm-tex_math_dollars` format string
- Fix: pass `--resource-path` to pandoc so relative image paths resolve from the document's directory
- Enhancement: added unicode character mappings for `√`, `·`, and box-drawing characters (`└├─│`)

## 0.1.1 (2026-03-08)

- Fix: escape LaTeX special characters (`_`, `$`, `&`, `%`, `#`, etc.) in document titles injected into header/footer preamble blocks — prevents "Missing $ inserted" errors when filenames contain underscores

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
