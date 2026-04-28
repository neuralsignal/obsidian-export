"""Shared image-conversion scaffolding for stage 3 pipeline modules."""

import re
from collections.abc import Callable
from pathlib import Path

from obsidian_export.exceptions import ObsidianExportError
from obsidian_export.pipeline.path_guards import assert_within_root


def convert_image_references(
    body: str,
    tmpdir: Path,
    resource_path: Path | None,
    pattern: re.Pattern[str],
    convert_fn: Callable[[Path, Path], None],
    out_prefix: str,
    out_ext: str,
    label: str,
    not_found_error: type[ObsidianExportError],
    pre_filter: Callable[[re.Match[str]], str | None],
) -> str:
    """Scan body for image references matching pattern and convert each via convert_fn.

    pre_filter receives each non-URL match before path resolution. Return a
    string to use as the replacement (skipping conversion), or None to proceed
    with the standard resolve-guard-convert flow.
    """
    counter = 0

    def replace_match(m: re.Match[str]) -> str:
        nonlocal counter
        alt_text = m.group(1)
        img_raw = m.group(2)

        if img_raw.startswith(("http://", "https://")):
            return m.group(0)

        filtered = pre_filter(m)
        if filtered is not None:
            return filtered

        img_path = Path(img_raw)

        if not img_path.is_absolute() and resource_path is not None:
            img_path = resource_path / img_path

        if resource_path is not None:
            assert_within_root(img_path, resource_path, label)

        if not img_path.exists():
            raise not_found_error(f"{label} file not found: {img_path}")

        counter += 1
        out_path = tmpdir / f"{out_prefix}{counter}{out_ext}"

        convert_fn(img_path, out_path)

        return f"![{alt_text}]({out_path})"

    return pattern.sub(replace_match, body)
