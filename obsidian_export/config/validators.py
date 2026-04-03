"""Validation functions for configuration values."""

import re

from obsidian_export.exceptions import ConfigValueError

_SAFE_PANDOC_FORMATS: frozenset[str] = frozenset(
    {
        "commonmark",
        "commonmark_x",
        "gfm",
        "markdown",
        "markdown_mmd",
        "markdown_phpextra",
        "markdown_strict",
    }
)

_DANGEROUS_EXTENSIONS: frozenset[str] = frozenset(
    {
        "raw_html",
        "raw_attribute",
    }
)

_PANDOC_EXTENSION_RE: re.Pattern[str] = re.compile(r"^[a-z][a-z0-9_]*$")

_PANDOC_VARIABLE_RE: re.Pattern[str] = re.compile(r"^[a-zA-Z0-9,=._\- ]+$")


def _validate_from_format(value: str) -> None:
    """Validate pandoc from_format against safe base formats and extensions.

    Raises ConfigValueError if the base format is not allowlisted,
    any extension name is malformed, or a dangerous extension is enabled.
    """
    parts = re.split(r"(?=[+-])", value, maxsplit=1)
    base_format = parts[0]
    if base_format not in _SAFE_PANDOC_FORMATS:
        raise ConfigValueError(
            f"Unsupported pandoc base format: {base_format!r}. Allowed: {sorted(_SAFE_PANDOC_FORMATS)}"
        )

    if len(parts) < 2:
        return

    ext_string = parts[1]
    for match in re.finditer(r"([+-])([^+-]+)", ext_string):
        sign, ext_name = match.group(1), match.group(2)
        if not _PANDOC_EXTENSION_RE.match(ext_name):
            raise ConfigValueError(f"Malformed pandoc extension name: {ext_name!r} in from_format {value!r}")
        if sign == "+" and ext_name in _DANGEROUS_EXTENSIONS:
            raise ConfigValueError(
                f"Dangerous pandoc extension enabled: +{ext_name} in from_format {value!r}. "
                f"Blocked extensions: {sorted(_DANGEROUS_EXTENSIONS)}"
            )


def _validate_pandoc_variable(name: str, value: str) -> None:
    """Validate a string that will be passed as a pandoc --variable value.

    Allows alphanumeric characters and limited punctuation (commas, equals,
    dots, hyphens, underscores, spaces). Raises ConfigValueError on mismatch.
    """
    if not value:
        return
    if not _PANDOC_VARIABLE_RE.match(value):
        raise ConfigValueError(
            f"Invalid characters in style config {name!r}: {value!r}. "
            f"Only alphanumeric characters and ,=._- are allowed."
        )
