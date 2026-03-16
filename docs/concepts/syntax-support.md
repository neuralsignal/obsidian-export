# Syntax Support

obsidian-export handles these Obsidian-specific syntax elements during conversion:

| Obsidian Syntax | Result |
|----------------|--------|
| `![[embed]]` | Resolved inline (content inlined) |
| `[[Entity\|Display]]` | Replaced with `Display` |
| `[[Entity]]` | Replaced with `Entity` |
| `> [!note]` callouts | Colored boxes (PDF) or blockquotes (DOCX) |
| `` ```mermaid `` | Rendered to PNG |
| `## Relations` section | Removed |
| YAML frontmatter | Title extracted, tags converted to keywords, rest removed |
| `$25/user` | Safe literal dollar sign (no LaTeX math) |

## Wikilink Handling

Wikilinks are converted to plain text. The display text is preserved when available:

- `[[My Note]]` becomes `My Note`
- `[[My Note|Custom Text]]` becomes `Custom Text`

## Embed Resolution

Embeds (`![[filename]]`) are recursively resolved — the referenced file's content is inlined at the embed location. Circular references are detected and raise a `CircularEmbedError`.

## Callout Styles

Callout types (`note`, `tip`, `warning`, `danger`) each render with a distinct background color in PDF output. Colors are configurable via `style.callout_colors` in the config.

## URL Handling

URLs can be processed with different strategies via `obsidian.url_strategy`:

| Strategy | Behavior |
|----------|----------|
| `keep` | Leave URLs inline as-is |
| `footnote_long` | Move URLs longer than threshold to footnotes |
| `footnote_all` | Move all URLs to footnotes |
| `strip` | Remove URLs entirely |
