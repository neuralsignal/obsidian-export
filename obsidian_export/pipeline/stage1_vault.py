"""Stage 1: Vault operations — frontmatter, embed resolution, Obsidian syntax stripping."""

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from obsidian_export.exceptions import CircularEmbedError, EmbedNotFoundError, PathTraversalError

_log = logging.getLogger(__name__)

_OBSIDIAN_KEYS = frozenset(["aliases", "tags", "cssclass", "publish", "banner", "cssclasses"])

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)---\s*\n", re.DOTALL)
_EMBED_RE = re.compile(r"!\[\[([^\]]+)\]\]")
_SECTION_EMBED_RE = re.compile(r"^([^#]+)#(.+)$")
_WIKILINK_PIPE_RE = re.compile(r"\[\[([^\]|]+)\|([^\]]+)\]\]")
_WIKILINK_BARE_RE = re.compile(r"\[\[([^\]]+)\]\]")
_RELATIONS_RE = re.compile(r"\n## Relations\b.*", re.DOTALL | re.IGNORECASE)

IMAGE_EXTENSIONS = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".webp",
        ".bmp",
        ".tiff",
        ".tif",
        ".avif",
    }
)


@dataclass(frozen=True)
class EmbedContext:
    """Immutable context for recursive embed resolution."""

    vault_root: Path
    current_file: Path
    visited: frozenset[Path]
    depth: int
    max_embed_depth: int


def _quote_yaml_values(raw: str) -> str:
    """Quote unquoted YAML values that contain colons.

    Obsidian allows ``title: Memory: stuff`` which is invalid YAML
    (the second colon starts a nested mapping).  This function detects
    ``key: value: more`` lines and wraps the value in double quotes.
    """
    fixed_lines: list[str] = []
    for line in raw.splitlines(keepends=True):
        stripped = line.lstrip()
        # Only fix top-level simple key-value lines (no leading whitespace
        # beyond what the original line has, not list items, etc.).
        if stripped and not stripped.startswith("-") and not stripped.startswith("#"):
            kv = re.match(r"^(\s*\w[\w\s]*?):\s+(.+)$", line)
            if kv:
                value = kv.group(2).rstrip("\n")
                # If the value itself contains an unquoted colon, wrap it.
                if ":" in value and not (value.startswith('"') or value.startswith("'")):
                    line = f'{kv.group(1)}: "{value}"\n'
        fixed_lines.append(line)
    return "".join(fixed_lines)


def parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Extract YAML frontmatter. Returns (metadata_dict, body_text)."""
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    raw = m.group(1)
    try:
        fm = yaml.safe_load(raw) or {}
    except yaml.YAMLError:
        _log.warning("YAML frontmatter parse failed, retrying with auto-quoted colons:\n%s", raw)
        fm = yaml.safe_load(_quote_yaml_values(raw)) or {}
    body = text[m.end() :]
    return fm, body


def clean_frontmatter(fm: dict[str, Any]) -> dict[str, Any]:
    """Strip Obsidian-only keys; convert tags list to keywords string for Pandoc."""
    cleaned = {k: v for k, v in fm.items() if k not in _OBSIDIAN_KEYS}
    if "tags" in fm:
        tags = fm["tags"]
        if isinstance(tags, list):
            cleaned["keywords"] = ", ".join(str(t) for t in tags)
        elif isinstance(tags, str):
            cleaned["keywords"] = tags
    return cleaned


def _extract_section(text: str, heading: str) -> str:
    """Extract content under a specific heading from markdown text."""
    pattern = re.compile(
        r"^(#{1,6})\s+" + re.escape(heading) + r"\s*$",
        re.MULTILINE | re.IGNORECASE,
    )
    m = pattern.search(text)
    if not m:
        return f"[Section '{heading}' not found]"
    level = len(m.group(1))
    start = m.end()
    # Find next heading of same or higher level
    end_pattern = re.compile(r"^#{1," + str(level) + r"}\s+", re.MULTILINE)
    end_m = end_pattern.search(text, start)
    if end_m:
        return text[start : end_m.start()].strip()
    return text[start:].strip()


def resolve_embeds(
    content: str,
    vault_root: Path,
    current_file: Path,
    max_embed_depth: int,
) -> str:
    """Recursively resolve ![[embed]] blocks with cycle detection.

    - Text embeds: resolved inline (with depth cap)
    - Section embeds (![[note#Heading]]): extract section
    - Image embeds (extensions in IMAGE_EXTENSIONS): converted to ![]() refs
    - Missing embeds: raise EmbedNotFoundError
    - Circular embeds: raise CircularEmbedError
    """
    ctx = EmbedContext(
        vault_root=vault_root,
        current_file=current_file,
        visited=frozenset(),
        depth=0,
        max_embed_depth=max_embed_depth,
    )
    return _resolve_embeds_recursive(content, ctx)


def _resolve_image_embed(raw: str, vault_root: Path, vault_resolved: Path) -> str:
    """Resolve an image embed to a markdown image reference."""
    img_path = (vault_root / raw).resolve()
    if not img_path.is_relative_to(vault_resolved):
        raise PathTraversalError(f"Embed path escapes vault root: {raw!r} resolved to {img_path}")
    if img_path.exists():
        return f"![]({img_path})"
    # Obsidian resolves by filename anywhere in vault — search subdirs
    matches = list(vault_root.rglob(raw))
    if matches:
        return f"![]({matches[0]})"
    return f"![{raw}]({vault_root / raw})"


def _resolve_note_path(note_slug: str, vault_root: Path, current_file: Path) -> Path:
    """Find a note file in the vault with fallback to current file's directory."""
    note_path = vault_root / f"{note_slug}.md"
    if note_path.exists():
        return note_path
    note_path = current_file.parent / f"{note_slug}.md"
    if note_path.exists():
        return note_path
    raise EmbedNotFoundError(f"Embed not found: {note_slug!r}. Searched: {vault_root}, {current_file.parent}")


def _resolve_note_embed(raw: str, ctx: EmbedContext, vault_resolved: Path) -> str:
    """Resolve a text or section embed, with cycle detection and recursion."""
    section_match = _SECTION_EMBED_RE.match(raw)
    if section_match:
        note_slug = section_match.group(1).strip()
        heading: str | None = section_match.group(2).strip()
    else:
        note_slug = raw
        heading = None

    note_path = _resolve_note_path(note_slug, ctx.vault_root, ctx.current_file).resolve()
    if not note_path.is_relative_to(vault_resolved):
        raise PathTraversalError(f"Embed path escapes vault root: {raw!r} resolved to {note_path}")
    if note_path in ctx.visited:
        raise CircularEmbedError(f"Circular embed chain detected: {raw!r}")

    note_text = note_path.read_text(encoding="utf-8")
    _, note_body = parse_frontmatter(note_text)

    if heading:
        note_body = _extract_section(note_body, heading)

    child_ctx = EmbedContext(
        vault_root=ctx.vault_root,
        current_file=note_path,
        visited=ctx.visited | {note_path},
        depth=ctx.depth + 1,
        max_embed_depth=ctx.max_embed_depth,
    )
    return _resolve_embeds_recursive(note_body, child_ctx).strip()


def _resolve_embeds_recursive(
    content: str,
    ctx: EmbedContext,
) -> str:
    """Internal recursive embed resolution with cycle detection."""
    if ctx.depth > ctx.max_embed_depth:
        return content

    vault_resolved = ctx.vault_root.resolve()

    def replace_embed(m: re.Match) -> str:
        """Replace a single ``![[...]]`` embed with its resolved content.

        Receives a match whose group(1) is the embed target (filename, note#section,
        or note#^block-id). Returns the replacement markdown string — an image
        reference, the transcluded note/section content, or the original wikilink
        when the target cannot be found.
        """
        raw = m.group(1).strip()
        suffix = Path(raw).suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            return _resolve_image_embed(raw, ctx.vault_root, vault_resolved)
        return _resolve_note_embed(raw, ctx, vault_resolved)

    return _EMBED_RE.sub(replace_embed, content)


def strip_leading_title(body: str, title: str) -> str:
    """Remove the first h1 heading if it matches the document title."""
    m = re.match(r"^\s*#\s+(.+?)(?:\s*\{[^}]*\})?\s*\n", body)
    if m and m.group(1).strip() == title.strip():
        return body[m.end() :]
    return body


def strip_obsidian_syntax(text: str) -> str:
    """Remove/simplify Obsidian-specific syntax for export.

    - ![[embed]] → removed (use resolve_embeds first for inline resolution)
    - [[Entity|Display]] → Display
    - [[Entity]] → Entity
    - ## Relations section → removed with all content below

    Callout syntax (> [!type]) is preserved for downstream processing by stage2.
    """
    # Remove bare embeds (not already resolved)
    text = _EMBED_RE.sub("", text)
    # Pipe wikilinks → display text
    text = _WIKILINK_PIPE_RE.sub(lambda m: m.group(2), text)
    # Bare wikilinks → entity name
    text = _WIKILINK_BARE_RE.sub(lambda m: m.group(1), text)
    # Remove Relations section
    text = _RELATIONS_RE.sub("", text)
    return text
