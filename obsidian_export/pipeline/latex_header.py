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

    # Resolve logo path from style config
    style_dir = template_path.parent
    if style.logo:
        logo_path = str(style_dir / style.logo)
    else:
        logo_path = ""
    header_left = _substitute_placeholders(style.header_left, title, logo_path)
    header_right = _substitute_placeholders(style.header_right, title, logo_path)
    footer_left = _substitute_placeholders(style.footer_left, title, logo_path)
    footer_center = _substitute_placeholders(style.footer_center, title, logo_path)
    footer_right = _substitute_placeholders(style.footer_right, title, logo_path)

    font_block = _build_font_block(style.mainfont, style.sansfont, style.monofont)
    line_spacing_block = _build_line_spacing_block(style.line_spacing)
    header_footer_block = _build_header_footer_block(
        header_left, header_right, footer_left, footer_center, footer_right
    )

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
        font_block=font_block,
        line_spacing_block=line_spacing_block,
        header_footer_block=header_footer_block,
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
