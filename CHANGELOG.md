# Changelog

## [0.4.2](https://github.com/neuralsignal/obsidian-export/compare/v0.4.1...v0.4.2) (2026-03-20)


### Bug Fixes

* wrap rsvg-convert subprocess in SVGConversionError handler ([#63](https://github.com/neuralsignal/obsidian-export/issues/63)) ([fc2bca8](https://github.com/neuralsignal/obsidian-export/commit/fc2bca8613ba883c77db1a6f9b05d649ed374039))

## [0.4.1](https://github.com/neuralsignal/obsidian-export/compare/v0.4.0...v0.4.1) (2026-03-18)


### Bug Fixes

* auto-fix CI failures (attempt 1) ([b7afe6e](https://github.com/neuralsignal/obsidian-export/commit/b7afe6e3ca2e11337b9efc324f60ff2e0b0cc180))
* escape double quotes in callout titles before Pandoc interpolation ([3c9a55f](https://github.com/neuralsignal/obsidian-export/commit/3c9a55fa08e985deade48cd6cea90fc7d9d3f410))
* escape double quotes in callout titles before Pandoc interpolation ([908b501](https://github.com/neuralsignal/obsidian-export/commit/908b50189d520432c885aebd73f66cbd8d0248be)), closes [#57](https://github.com/neuralsignal/obsidian-export/issues/57)

## [0.4.0](https://github.com/neuralsignal/obsidian-export/compare/v0.3.0...v0.4.0) (2026-03-17)


### Features

* redesign factory dashboard from append-only to edit-in-place ([096e24b](https://github.com/neuralsignal/obsidian-export/commit/096e24b5a619c555cb1ac33332137dec2162b833))
* redesign factory dashboard to edit-in-place ([497fd99](https://github.com/neuralsignal/obsidian-export/commit/497fd994ec9f8dd85030d1875d03acb91941afd5))


### Bug Fixes

* add vault boundary check for SVG paths in stage3_svg ([#35](https://github.com/neuralsignal/obsidian-export/issues/35)) ([c50c550](https://github.com/neuralsignal/obsidian-export/commit/c50c550390485dbab5026e83657fbe07c12de97c))
* regenerate pixi.lock in release-please PR ([9999c1d](https://github.com/neuralsignal/obsidian-export/commit/9999c1db73a6a7c57ceaed4425929a295239b37e))
* regenerate pixi.lock in release-please PR ([d9914c7](https://github.com/neuralsignal/obsidian-export/commit/d9914c743b16ef7c98fad5108b3312a7775f3e14))
* replace broken plugin approach in pr-code-review with direct prompt + post step ([351f2ec](https://github.com/neuralsignal/obsidian-export/commit/351f2ec19e47eea9baf32e049c06ac35fc136cd6))


### Documentation

* add agentic engineering and missing constitution principles to CLAUDE.md ([8fc9345](https://github.com/neuralsignal/obsidian-export/commit/8fc93457a45b6cf2a3fcf8bcac118f6dd5eeb1f5))
* add agentic engineering, change safety, and missing constitution principles to CLAUDE.md ([e12e3bb](https://github.com/neuralsignal/obsidian-export/commit/e12e3bb9aa39016d396aa1f78a949212d30e6481))
* sync documentation with codebase ([e6373e9](https://github.com/neuralsignal/obsidian-export/commit/e6373e9eef21157035b1d83565e8dfad83dd327c))
* sync documentation with codebase changes ([a34c2ff](https://github.com/neuralsignal/obsidian-export/commit/a34c2ffb477606eb437d94fd3eb68c11c0cebc4d))

## 0.3.0 (2026-03-09)

- Feat: DOCX output now applies Lua filters for callout boxes, footnote promotion, and page breaks
- Feat: SVG images are converted to PNG for DOCX compatibility
- Feat: optional `reference_doc` support for custom DOCX styling via `--reference-doc`
- Feat: `url_footnote_threshold` metadata injected into DOCX output for long-URL footnote promotion
- Docs: add MkDocs + Material documentation site with auto-generated API reference
- Docs: deploy to GitHub Pages at neuralsignal.github.io/obsidian-export/

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
