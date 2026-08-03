"""Generate rendered LaTeX header from style config and template."""

from pathlib import Path

from obsidian_export.config import HeadingStyle, StyleConfig, TitleStyle
from obsidian_export.pipeline.latex_escape import (
    escape_latex,
    substitute_placeholders,
    validate_header_footer_values,
    validate_latex_value,
)


def render_header(style: StyleConfig, template_path: Path, title: str) -> str:
    """Read header.tex template and substitute config values.

    Returns the fully rendered LaTeX preamble string.

    Magic placeholders in header/footer strings:
      {doc_title} → the document title
      {logo_path} → absolute path to logo file (from style.logo) or empty
    """
    template = template_path.read_text(encoding="utf-8")

    # Logo path is now resolved to absolute during config loading
    logo_path = style.logo if style.logo else ""
    header_left = substitute_placeholders(style.header_left, title, logo_path)
    header_right = substitute_placeholders(style.header_right, title, logo_path)
    footer_left = substitute_placeholders(style.footer_left, title, logo_path)
    footer_center = substitute_placeholders(style.footer_center, title, logo_path)
    footer_right = substitute_placeholders(style.footer_right, title, logo_path)

    unicode_char_block = _build_unicode_char_block(style.unicode_chars)
    font_block = _build_font_block(style.mainfont, style.sansfont, style.monofont)
    greek_fallback_block = _build_greek_fallback_block(style.greek_font)
    line_spacing_block = _build_line_spacing_block(style.line_spacing)
    header_footer_block = _build_header_footer_block(
        header_left, header_right, footer_left, footer_center, footer_right
    )
    brand_colors_block = _build_brand_colors_block(style.brand_colors)
    heading_styles_block = _build_heading_styles_block(style.heading_styles)
    title_style_block = _build_title_style_block(style.title_style)
    code_block = _build_code_block(style.code_fontsize)

    cc = style.callout_colors
    return template.format(
        image_max_height_ratio=style.image_max_height_ratio,
        note_r=cc.note[0],
        note_g=cc.note[1],
        note_b=cc.note[2],
        tip_r=cc.tip[0],
        tip_g=cc.tip[1],
        tip_b=cc.tip[2],
        warn_r=cc.warning[0],
        warn_g=cc.warning[1],
        warn_b=cc.warning[2],
        danger_r=cc.danger[0],
        danger_g=cc.danger[1],
        danger_b=cc.danger[2],
        unicode_char_block=unicode_char_block,
        font_block=font_block,
        greek_fallback_block=greek_fallback_block,
        line_spacing_block=line_spacing_block,
        header_footer_block=header_footer_block,
        brand_colors_block=brand_colors_block,
        heading_styles_block=heading_styles_block,
        title_style_block=title_style_block,
        code_block=code_block,
    )


def _build_unicode_char_block(unicode_chars: tuple[tuple[str, str], ...]) -> str:
    """Generate \\newunicodechar lines from config tuples."""
    if not unicode_chars:
        return ""
    lines = []
    for char, latex in unicode_chars:
        validate_latex_value(latex, f"unicode_chars['{char}']")
        lines.append(f"\\newunicodechar{{{char}}}{{{latex}}}")
    return "\n".join(lines)


def _build_font_block(mainfont: str, sansfont: str, monofont: str) -> str:
    """Generate \\setmainfont/\\setsansfont/\\setmonofont lines for non-empty font settings."""
    lines = []
    if mainfont:
        lines.append(f"\\setmainfont{{{escape_latex(mainfont)}}}")
    if sansfont:
        lines.append(f"\\setsansfont{{{escape_latex(sansfont)}}}")
    if monofont:
        lines.append(f"\\setmonofont{{{escape_latex(monofont)}}}")
    return "\n".join(lines)


def _build_greek_fallback_block(greek_font: str) -> str:
    """Route Greek-script glyphs to a covering font via ucharclasses.

    XeTeX performs no cross-font fallback: when the main and sans fonts lack
    Greek coverage, Greek characters are dropped silently. ucharclasses switches
    to greek_font on entering the Greek Unicode block and restores the roman
    family on exit. An empty greek_font yields no block, so Latin-only documents
    are unaffected.
    """
    if not greek_font:
        return ""
    escaped = escape_latex(greek_font)
    return (
        "\\usepackage{ucharclasses}\n"
        f"\\newfontfamily\\greekfallbackfont{{{escaped}}}\n"
        "\\setTransitionsForGreek{\\greekfallbackfont}{\\rmfamily}"
    )


def _build_line_spacing_block(line_spacing: float) -> str:
    """Generate setspace package usage and \\setstretch call, or empty string if spacing is 1.0."""
    if line_spacing == 1.0:
        return ""
    return f"\\usepackage{{setspace}}\n\\setstretch{{{line_spacing}}}"


def _build_brand_colors_block(brand_colors: tuple[tuple[str, int, int, int], ...]) -> str:
    """Generate \\definecolor lines for brand colors."""
    if not brand_colors:
        return ""
    lines = []
    for name, r, g, b in brand_colors:
        lines.append(f"\\definecolor{{{escape_latex(name)}}}{{RGB}}{{{r},{g},{b}}}")
    return "\n".join(lines)


def _build_format_parts(size: str, bold: bool, sans: bool, color: str) -> list[str]:
    """Build LaTeX font-format command fragments from style fields."""
    parts = [f"\\{size}"]
    if bold:
        parts.append("\\bfseries")
    if sans:
        parts.append("\\sffamily")
    if color:
        parts.append(f"\\color{{{escape_latex(color)}}}")
    return parts


def _build_heading_styles_block(heading_styles: tuple[HeadingStyle, ...]) -> str:
    """Generate titlesec heading format commands."""
    if not heading_styles:
        return ""
    lines = ["\\usepackage{titlesec}"]
    for h in heading_styles:
        validate_latex_value(f"\\{h.size}", "heading_styles.size")
        parts = ["\\normalfont"] + _build_format_parts(h.size, h.bold, h.sans, h.color)
        fmt = "".join(parts)
        content_arg = "{\\MakeUppercase}" if h.uppercase else "{}"
        lines.append(f"\\titleformat{{\\{h.level}}}\n  {{{fmt}}}\n  {{\\the{h.level}}}{{1em}}{content_arg}")
    return "\n\n".join(lines)


def _build_title_style_block(title_style: TitleStyle | None) -> str:
    """Generate custom \\maketitle definition."""
    if title_style is None:
        return ""
    validate_latex_value(f"\\{title_style.size}", "title_style.size")
    title_fmt = "".join(_build_format_parts(title_style.size, title_style.bold, title_style.sans, title_style.color))

    lines = [
        "\\makeatletter",
        "\\renewcommand{\\maketitle}{%",
        "  \\begin{center}%",
        f"    {{{title_fmt}\\@title\\par}}%",
    ]
    if title_style.date_visible:
        lines.append("    \\vskip 1em%")
        lines.append("    {\\large\\@date\\par}%")
    lines.append("  \\end{center}%")
    if title_style.vskip_after:
        lines.append(f"  \\vskip {title_style.vskip_after}%")
    lines.append("}")
    lines.append("\\makeatother")
    return "\n".join(lines)


def _build_code_block(code_fontsize: str) -> str:
    """Generate fvextra setup for code block line-wrapping and font size control."""
    cmd = f"\\{code_fontsize}"
    validate_latex_value(cmd, "code_fontsize")
    return (
        "\\usepackage{fvextra}\n"
        f"\\fvset{{breaklines=true, fontsize={cmd}}}\n"
        f"\\DefineVerbatimEnvironment{{verbatim}}{{Verbatim}}"
        f"{{breaklines=true, fontsize={cmd}}}"
    )


def _build_header_footer_block(
    header_left: str,
    header_right: str,
    footer_left: str,
    footer_center: str,
    footer_right: str,
) -> str:
    """Generate fancyhdr package setup with configured header/footer fields."""
    fields = {
        "header_left": header_left,
        "header_right": header_right,
        "footer_left": footer_left,
        "footer_center": footer_center,
        "footer_right": footer_right,
    }
    validate_header_footer_values(fields)

    if not any(fields.values()):
        return ""
    lines = [
        "\\usepackage{fancyhdr}",
        "\\pagestyle{fancy}",
        "\\fancyhf{}",
    ]
    if header_left:
        lines.append(f"\\fancyhead[L]{{{header_left}}}")
    if header_right:
        lines.append(f"\\fancyhead[R]{{{header_right}}}")
    if footer_left:
        lines.append(f"\\fancyfoot[L]{{{footer_left}}}")
    if footer_center:
        lines.append(f"\\fancyfoot[C]{{{footer_center}}}")
    if footer_right:
        lines.append(f"\\fancyfoot[R]{{{footer_right}}}")
    lines.append("\\renewcommand{\\headrulewidth}{0pt}")
    return "\n".join(lines)
