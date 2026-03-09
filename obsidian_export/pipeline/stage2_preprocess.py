"""Stage 2: Text-level pre-processing before Pandoc parses the document."""

import re

from obsidian_export.config import ObsidianConfig

# Matches fenced code blocks (``` or ~~~) to skip during transforms
_FENCED_CODE_RE = re.compile(r"(```+[^\n]*\n.*?```+|~~~+[^\n]*\n.*?~~~+)", re.DOTALL)
# Display math $$...$$
_DISPLAY_MATH_RE = re.compile(r"\$\$.*?\$\$", re.DOTALL)
# Inline math $...$  (no digits/space after opening $, no $ in content)
_INLINE_MATH_RE = re.compile(r"\$([^$\s][^$]*?)\$")
# Currency: $ followed by a digit or space then digit (e.g. $25 or $ 25)
_CURRENCY_RE = re.compile(r"\$(?=[\d\s])")
# Obsidian callout: > [!TYPE] Optional title
_CALLOUT_HEADER_RE = re.compile(
    r"^((?:> ?)+)\[!([\w]+)\][ \t]*([^\n]*)\n((?:(?:> ?)[^\n]*\n?)*)",
    re.MULTILINE,
)
# Bare URL (not already in markdown link syntax)
_BARE_URL_RE = re.compile(
    r"(?<![(<\[`])(https?://[^\s<>\"\)\]\,]+)",
)


def _split_preserve_code(text: str) -> list[tuple[bool, str]]:
    """Split text into (is_code_block, segment) pairs.

    Code blocks and display math are flagged is_code_block=True and
    skipped by transforms that should not touch code.
    """
    parts: list[tuple[bool, str]] = []
    pos = 0
    combined = re.compile(
        r"(```+[^\n]*\n.*?```+|~~~+[^\n]*\n.*?~~~+|\$\$.*?\$\$)",
        re.DOTALL,
    )
    for m in combined.finditer(text):
        if m.start() > pos:
            parts.append((False, text[pos : m.start()]))
        parts.append((True, m.group()))
        pos = m.end()
    if pos < len(text):
        parts.append((False, text[pos:]))
    return parts


def escape_dollar_signs(text: str) -> str:
    """Escape currency dollar signs to \\$.

    Skips fenced code blocks, display math ($$...$$), and patterns that
    look like intentional inline math (no digit immediately after $).
    Belt-and-suspenders alongside --from=gfm-tex_math_dollars.
    """
    segments = _split_preserve_code(text)
    result = []
    for is_code, segment in segments:
        if is_code:
            result.append(segment)
            continue
        # Replace $digit or $ digit (currency) with \$
        result.append(_CURRENCY_RE.sub(r"\\$", segment))
    return "".join(result)


def _callout_replacement(m: re.Match) -> str:
    """Convert Obsidian callout block to Pandoc fenced div."""
    prefix = m.group(1)  # The "> " prefix characters
    callout_type = m.group(2).lower()
    title = m.group(3).strip()
    body_raw = m.group(4)

    # Strip the "> " prefix from body lines
    prefix_re = re.compile(r"^" + re.escape(prefix), re.MULTILINE)
    body = prefix_re.sub("", body_raw).rstrip()

    if not title:
        title = callout_type.capitalize()

    div_class = f".{callout_type}"
    return f':::{{{div_class} title="{title}"}}\n{body}\n:::\n\n'


def convert_callouts(text: str) -> str:
    """Transform Obsidian callout blocks to Pandoc fenced divs.

    Input:  > [!NOTE] Title
            > content line
    Output: :::{.note title="Title"}
            content line
            :::
    """
    return _CALLOUT_HEADER_RE.sub(_callout_replacement, text)


def process_urls(text: str, strategy: str, threshold: int) -> str:
    """Handle bare URLs in text according to strategy.

    Strategies:
      keep          — leave as-is
      footnote_long — move URLs longer than threshold to footnotes
      footnote_all  — move all URLs to footnotes
      strip         — remove bare URLs entirely
    """
    if strategy == "keep":
        return text

    def replace_url(m: re.Match) -> str:
        url = m.group(1)
        if strategy == "strip":
            return url  # return just URL text without full URL — actually strip means remove
        if strategy == "footnote_all" or (strategy == "footnote_long" and len(url) > threshold):
            # Pandoc footnote syntax: [^N] — but inline footnotes are cleaner
            return f"[link]({url})[^url-{abs(hash(url)) % 100000}]\n\n[^url-{abs(hash(url)) % 100000}]: <{url}>"
        return m.group(0)

    if strategy == "strip":
        # Remove bare URLs entirely
        return _BARE_URL_RE.sub("", text)

    # For footnote strategies, wrap in angle brackets first (Pandoc autolinks)
    segments = _split_preserve_code(text)
    result = []
    for is_code, segment in segments:
        if is_code:
            result.append(segment)
            continue
        result.append(_BARE_URL_RE.sub(replace_url, segment))
    return "".join(result)


def normalize_line_endings(text: str) -> str:
    """Normalize line endings to LF and strip trailing whitespace per line."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    return "\n".join(line.rstrip() for line in lines)


# U+FE0F is the emoji variation selector-16 (forces emoji rendering).
# TeX engines have no emoji font bundled, so this invisible codepoint
# causes "Missing character" warnings. Strip it unconditionally.
_VARIATION_SELECTOR_RE = re.compile(r"\ufe0f")


def strip_variation_selectors(text: str) -> str:
    """Remove Unicode variation selectors (U+FE0F) that TeX cannot render."""
    return _VARIATION_SELECTOR_RE.sub("", text)


def count_headings(text: str) -> int:
    """Count the number of markdown headings (lines starting with #) in text."""
    return sum(1 for line in text.split("\n") if line.lstrip().startswith("#"))


def preprocess(text: str, config: ObsidianConfig) -> str:
    """Apply all Stage 2 transforms in order."""
    text = normalize_line_endings(text)
    text = strip_variation_selectors(text)
    text = escape_dollar_signs(text)
    text = convert_callouts(text)
    text = process_urls(text, config.url_strategy, config.url_length_threshold)
    return text
