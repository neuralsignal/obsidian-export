"""Custom exceptions for obsidian-export."""


class ObsidianExportError(Exception):
    """Base exception for obsidian-export."""


class EmbedNotFoundError(ObsidianExportError):
    """A ![[embed]] reference could not be resolved."""


class CircularEmbedError(ObsidianExportError):
    """Circular embed chain detected."""


class SVGConversionError(ObsidianExportError):
    """SVG file not found or conversion failed."""


class ImageConversionError(ObsidianExportError):
    """Non-SVG image conversion failed (e.g. WebP/AVIF/BMP/TIFF to PNG)."""


class ProfileNameError(ObsidianExportError):
    """Profile name is invalid or contains path traversal sequences."""


class PathTraversalError(ObsidianExportError):
    """Embed path resolves outside the vault root (path traversal attempt)."""


class UnsupportedFormatError(ObsidianExportError):
    """Output format is not supported (must be 'pdf' or 'docx')."""
