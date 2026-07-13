"""Shared image-conversion scaffolding for stage 3 pipeline modules."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from obsidian_export.exceptions import ObsidianExportError
from obsidian_export.pipeline.path_guards import assert_within_root


@dataclass(frozen=True)
class ImageConversionSpec:
    """Groups format-specific parameters for image reference conversion."""

    pattern: re.Pattern[str]
    convert_fn: Callable[[Path, Path], None]
    out_prefix: str
    out_ext: str
    label: str
    not_found_error: type[ObsidianExportError]
    pre_filter: Callable[[re.Match[str]], str | None]


def _is_url(raw_path: str) -> bool:
    """Return True if raw_path is an HTTP(S) URL."""
    return raw_path.startswith(("http://", "https://"))


def _resolve_image_path(
    img_raw: str,
    resource_path: Path | None,
    label: str,
) -> Path:
    """Resolve a raw image path against resource_path and validate root containment."""
    img_path = Path(img_raw)

    if not img_path.is_absolute() and resource_path is not None:
        img_path = resource_path / img_path

    if resource_path is not None:
        assert_within_root(img_path, resource_path, label)

    return img_path


def _replace_image_match(
    m: re.Match[str],
    resource_path: Path | None,
    tmpdir: Path,
    spec: ImageConversionSpec,
    counter: list[int],
) -> str:
    """Process a single image-reference match through the resolve-guard-convert flow.

    counter is a single-element list used as a mutable accumulator for output numbering.
    """
    alt_text = m.group(1)
    img_raw = m.group(2)

    if _is_url(img_raw):
        return m.group(0)

    filtered = spec.pre_filter(m)
    if filtered is not None:
        return filtered

    img_path = _resolve_image_path(img_raw, resource_path, spec.label)

    if not img_path.exists():
        raise spec.not_found_error(f"{spec.label} file not found: {img_path}")

    counter[0] += 1
    out_path = tmpdir / f"{spec.out_prefix}{counter[0]}{spec.out_ext}"

    spec.convert_fn(img_path, out_path)

    return f"![{alt_text}]({out_path})"


def convert_image_references(
    body: str,
    tmpdir: Path,
    resource_path: Path | None,
    spec: ImageConversionSpec,
) -> str:
    """Scan body for image references matching spec.pattern and convert each.

    spec.pre_filter receives each non-URL match before path resolution. Return a
    string to use as the replacement (skipping conversion), or None to proceed
    with the standard resolve-guard-convert flow.
    """
    counter = [0]

    return spec.pattern.sub(
        lambda m: _replace_image_match(m, resource_path, tmpdir, spec, counter),
        body,
    )
