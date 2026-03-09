# Custom Styles

Styles are LaTeX header templates that control the visual appearance of PDF output: fonts, colors, headers/footers, heading formats, and page geometry.

## Style Resolution

When a style name is specified in the config, obsidian-export looks for the corresponding `header.tex` template in this order:

1. **`style_dir` field in config** — explicit path to a style directory
2. **Built-in styles** — bundled with the package (e.g., `default`)
3. **User styles** — `~/.obsidian-export/styles/<name>/header.tex`
4. **Filesystem path** — treat the style name as a direct path

## Creating a Custom Style

Place your custom style in `~/.obsidian-export/styles/<name>/header.tex`:

```
~/.obsidian-export/
  styles/
    my_brand/
      header.tex
      logo.png       # optional logo file
```

The `header.tex` file is a LaTeX preamble template. It supports placeholder variables that are substituted at render time:

- `{doc_title}` — the document title (from frontmatter or filename)
- `{logo_path}` — absolute path to the logo file

## Style Configuration

Styles are configured via the `style` section in your config YAML. You can customize fonts, colors, headers/footers, heading formats, and more without writing LaTeX directly:

```yaml
style:
  name: "default"
  fontsize: "12pt"
  mainfont: "Georgia"
  sansfont: "Helvetica"
  monofont: "Source Code Pro"
  geometry: "a4paper,margin=25mm"
  line_spacing: 1.5
  linkcolor: "NavyBlue"
  urlcolor: "NavyBlue"
```

## Brand Colors

Define named colors for use in heading styles and title blocks:

```yaml
style:
  brand_colors:
    petrol: [20, 75, 95]
    turkis: [0, 152, 160]
```

Colors are specified as RGB triplets (0-255).

## Heading Styles

Customize the appearance of section headings:

```yaml
style:
  heading_styles:
    - level: "section"
      size: "Large"
      bold: true
      sans: true
      color: "petrol"
      uppercase: false
    - level: "subsection"
      size: "large"
      bold: true
      sans: true
      color: "turkis"
      uppercase: true
```

Available sizes (LaTeX): `huge`, `LARGE`, `Large`, `large`, `normalsize`, `small`.

## Title Style

Customize the document title block:

```yaml
style:
  title_style:
    size: "huge"
    bold: true
    sans: true
    color: "petrol"
    date_visible: true
    vskip_after: "2em"
```

## Headers and Footers

Configure page headers and footers with placeholder support:

```yaml
style:
  header_left: "{doc_title}"
  header_right: "My Company"
  footer_left: ""
  footer_center: "\\thepage"
  footer_right: ""
  logo: "logo.png"
```

The `{doc_title}` and `{logo_path}` placeholders are replaced at render time.
