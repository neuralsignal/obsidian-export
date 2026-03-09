# Pipeline

The conversion pipeline is composed of independent stages, each implemented as a separate module.

| Stage | Module | Purpose |
|-------|--------|---------|
| 1 | [`stage1_vault`](stage1_vault.md) | Obsidian vault operations (frontmatter, embeds, wikilinks) |
| 2 | [`stage2_preprocess`](stage2_preprocess.md) | Text preprocessing (dollar signs, callouts, URLs) |
| 3 | [`stage3_mermaid`](stage3_mermaid.md) | Mermaid diagram rendering |
| 3b | [`stage3_svg`](stage3_svg.md) | SVG to PDF conversion |
| 4 | [`stage4_pandoc`](stage4_pandoc.md) | Final document generation (PDF/DOCX) |

Supporting modules:

- [`latex_header`](latex_header.md) — LaTeX header template rendering
