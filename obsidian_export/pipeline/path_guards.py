"""Path validation guards for pipeline stages."""

from pathlib import Path

from obsidian_export.exceptions import PathTraversalError


def assert_within_root(path: Path, root: Path, label: str) -> None:
    """Raise PathTraversalError if path does not resolve within root."""
    resolved = path.resolve()
    root_resolved = root.resolve()
    if not resolved.is_relative_to(root_resolved):
        raise PathTraversalError(f"{label} path escapes document root: resolved to {path}")
