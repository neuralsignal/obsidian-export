"""LaTeX string escaping, validation, and placeholder substitution.

Shared by any pipeline stage that interpolates config or document values into
LaTeX, so no stage has to reach into another stage's internals.
"""

import re

from obsidian_export.exceptions import UnsafeLatexError

_DANGEROUS_LATEX_RE = re.compile(
    r"\\(?:input|include|write\d*|immediate|openin|openout|read|closein|closeout"
    r"|catcode|def|edef|gdef|xdef|let|csname|newwrite|ShellEscape|directlua"
    r"|luaexec|luadirect)(?![a-zA-Z])",
    re.IGNORECASE,
)


def truncate_title(title: str) -> str:
    """Shorten title for header use — cut before first em-dash or colon."""
    for sep in (" — ", " – ", " - ", ": "):
        pos = title.find(sep)
        if pos != -1:
            return title[:pos].strip()
    return title


def escape_latex(text: str) -> str:
    """Escape LaTeX special characters in plain text for safe preamble insertion."""
    # Backslash must be replaced first, otherwise it would re-escape the
    # backslashes introduced by the later replacements.
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


def substitute_placeholders(value: str, title: str, logo_path: str) -> str:
    """Replace {doc_title} and {logo_path} in a header/footer config string."""
    if not value:
        return value
    short_title = escape_latex(truncate_title(title))
    return value.replace("{doc_title}", short_title).replace("{logo_path}", logo_path)


def validate_latex_value(latex: str, field_name: str) -> None:
    """Reject latex values containing dangerous macros.

    Raises UnsafeLatexError if the value contains macros that could read files,
    execute shell commands, or redefine TeX internals.
    """
    if _DANGEROUS_LATEX_RE.search(latex):
        msg = (
            f"Config field '{field_name}' contains a dangerous LaTeX macro: "
            f"'{latex}'. Remove or replace it with a safe alternative."
        )
        raise UnsafeLatexError(msg)


def validate_header_footer_values(fields: dict[str, str]) -> None:
    """Validate all header/footer values for dangerous LaTeX macros.

    Raises UnsafeLatexError if any value contains a dangerous macro.
    """
    for field_name, value in fields.items():
        if value:
            validate_latex_value(value, field_name)
