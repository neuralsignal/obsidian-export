"""Generate rendered LaTeX header from style config and template."""

from pathlib import Path

from obsidian_export.config import StyleConfig


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
    header_left = _substitute_placeholders(style.header_left, title, logo_path)
    header_right = _substitute_placeholders(style.header_right, title, logo_path)
    footer_left = _substitute_placeholders(style.footer_left, title, logo_path)
    footer_center = _substitute_placeholders(style.footer_center, title, logo_path)
    footer_right = _substitute_placeholders(style.footer_right, title, logo_path)

    unicode_char_block = _build_unicode_char_block(style.unicode_chars)
    font_block = _build_font_block(style.mainfont, style.sansfont, style.monofont)
    line_spacing_block = _build_line_spacing_block(style.line_spacing)
    header_footer_block = _build_header_footer_block(
        header_left, header_right, footer_left, footer_center, footer_right
    )
    brand_colors_block = _build_brand_colors_block(style.brand_colors)
    heading_styles_block = _build_heading_styles_block(style.heading_styles)
    title_style_block = _build_title_style_block(style.title_style)

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
        line_spacing_block=line_spacing_block,
        header_footer_block=header_footer_block,
        brand_colors_block=brand_colors_block,
        heading_styles_block=heading_styles_block,
        title_style_block=title_style_block,
    )


def _truncate_title(title: str) -> str:
    """Shorten title for header use — cut before first em-dash or colon."""
    for sep in (" — ", " – ", " - ", ": "):
        pos = title.find(sep)
        if pos != -1:
            return title[:pos].strip()
    return title


def _escape_latex(text: str) -> str:
    """Escape LaTeX special characters in plain text for safe preamble insertion."""
    # Order matters: & must come before others that might produce &
    replacements = [
        ("\\", "\\textbackslash{}"),
        ("&", "\\&"),
        ("%", "\\%"),
        ("$", "\\$"),
        ("#", "\\#"),
        ("_", "\\_"),
        ("{", "\\{"),
        ("}", "\\}"),
        ("~", "\\textasciitilde{}"),
        ("^", "\\textasciicircum{}"),
    ]
    for char, escaped in replacements:
        text = text.replace(char, escaped)
    return text


def _substitute_placeholders(value: str, title: str, logo_path: str) -> str:
    """Replace {doc_title} and {logo_path} in a header/footer config string."""
    if not value:
        return value
    short_title = _escape_latex(_truncate_title(title))
    return value.replace("{doc_title}", short_title).replace("{logo_path}", logo_path)


def _build_unicode_char_block(unicode_chars: tuple[tuple[str, str], ...]) -> str:
    """Generate \\newunicodechar lines from config tuples."""
    if not unicode_chars:
        return ""
    lines = []
    for char, latex in unicode_chars:
        lines.append(f"\\newunicodechar{{{char}}}{{{latex}}}")
    return "\n".join(lines)


def _build_font_block(mainfont: str, sansfont: str, monofont: str) -> str:
    lines = []
    if mainfont:
        lines.append(f"\\setmainfont{{{mainfont}}}")
    if sansfont:
        lines.append(f"\\setsansfont{{{sansfont}}}")
    if monofont:
        lines.append(f"\\setmonofont{{{monofont}}}")
    return "\n".join(lines)


def _build_line_spacing_block(line_spacing: float) -> str:
    if line_spacing == 1.0:
        return ""
    return f"\\usepackage{{setspace}}\n\\setstretch{{{line_spacing}}}"


def _build_brand_colors_block(brand_colors: tuple[tuple[str, int, int, int], ...]) -> str:
    """Generate \\definecolor lines for brand colors."""
    if not brand_colors:
        return ""
    lines = []
    for name, r, g, b in brand_colors:
        lines.append(f"\\definecolor{{{name}}}{{RGB}}{{{r},{g},{b}}}")
    return "\n".join(lines)


def _build_heading_styles_block(heading_styles: tuple[tuple[str, str, bool, bool, str, bool], ...]) -> str:
    """Generate titlesec heading format commands."""
    if not heading_styles:
        return ""
    lines = ["\\usepackage{titlesec}"]
    for level, size, bold, sans, color, uppercase in heading_styles:
        parts = ["\\normalfont"]
        parts.append(f"\\{size}")
        if bold:
            parts.append("\\bfseries")
        if sans:
            parts.append("\\sffamily")
        if color:
            parts.append(f"\\color{{{color}}}")
        fmt = "".join(parts)
        # For the content argument (last {}), use \\MakeUppercase if uppercase
        content_arg = "{\\MakeUppercase}" if uppercase else "{}"
        lines.append(f"\\titleformat{{\\{level}}}\n  {{{fmt}}}\n  {{\\the{level}}}{{1em}}{content_arg}")
    return "\n\n".join(lines)


def _build_title_style_block(title_style: tuple[str, bool, bool, str, bool, str] | None) -> str:
    """Generate custom \\maketitle definition."""
    if title_style is None:
        return ""
    size, bold, sans, color, date_visible, vskip_after = title_style
    title_parts = []
    title_parts.append(f"\\{size}")
    if bold:
        title_parts.append("\\bfseries")
    if sans:
        title_parts.append("\\sffamily")
    if color:
        title_parts.append(f"\\color{{{color}}}")
    title_fmt = "".join(title_parts)

    lines = [
        "\\makeatletter",
        "\\renewcommand{\\maketitle}{%",
        "  \\begin{center}%",
        f"    {{{title_fmt}\\@title\\par}}%",
    ]
    if date_visible:
        lines.append("    \\vskip 1em%")
        lines.append("    {\\large\\@date\\par}%")
    lines.append("  \\end{center}%")
    if vskip_after:
        lines.append(f"  \\vskip {vskip_after}%")
    lines.append("}")
    lines.append("\\makeatother")
    return "\n".join(lines)


def _build_header_footer_block(
    header_left: str,
    header_right: str,
    footer_left: str,
    footer_center: str,
    footer_right: str,
) -> str:
    if not any([header_left, header_right, footer_left, footer_center, footer_right]):
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
