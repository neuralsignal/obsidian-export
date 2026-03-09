"""Custom exceptions for obsidian-export."""


class ObsidianExportError(Exception):
    """Base exception for obsidian-export."""


class EmbedNotFoundError(ObsidianExportError):
    """A ![[embed]] reference could not be resolved."""


class CircularEmbedError(ObsidianExportError):
    """Circular embed chain detected."""


class SVGConversionError(ObsidianExportError):
    """SVG file not found or conversion failed."""


class PathTraversalError(ObsidianExportError):
    """Embed path resolves outside the vault root (path traversal attempt)."""
