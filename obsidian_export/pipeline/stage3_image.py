"""Stage 3c: Convert non-SVG images unsupported by the target format to PNG.

PDF (LaTeX/tectonic) natively supports: PNG, JPG/JPEG, PDF.
DOCX (pandoc) natively supports: PNG, JPG/JPEG, GIF, BMP, TIFF.

This stage converts any other image formats (WebP, AVIF, GIF-for-PDF,
BMP-for-PDF, TIFF-for-PDF) to PNG using Pillow so that downstream
pandoc/tectonic can consume them.
"""

import re
from pathlib import Path

from PIL import Image

from obsidian_export.exceptions import ImageConversionError
from obsidian_export.pipeline.path_guards import assert_within_root

PDF_NATIVE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".pdf"})
DOCX_NATIVE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".tif"})

_IMG_REF_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _needs_conversion(ext: str, native_extensions: frozenset[str]) -> bool:
    """Return True if the extension is not natively supported by the target format."""
    return ext.lower() not in native_extensions


def convert_images(
    body: str,
    tmpdir: Path,
    resource_path: Path | None,
    native_extensions: frozenset[str],
) -> str:
    """Find image references unsupported by the target and convert them to PNG.

    Only processes local file paths (not URLs, not SVGs which are handled by
    stage3_svg). Each unsupported image is converted to PNG in tmpdir, and
    the markdown reference is updated.
    """
    counter = 0

    def replace_image(m: re.Match) -> str:
        """Replace a single image reference with a PNG-converted version if needed.

        Receives a match with group(1) as alt text and group(2) as the image path.
        Skips URLs, SVGs, and natively supported formats. For unsupported formats,
        converts the image to PNG in tmpdir and returns an updated markdown reference.
        Increments the outer ``counter`` for unique filenames.
        """
        nonlocal counter
        alt_text = m.group(1)
        img_raw = m.group(2)

        if img_raw.startswith(("http://", "https://")):
            return m.group(0)

        img_path = Path(img_raw)
        ext = img_path.suffix.lower()

        # Skip SVGs (handled by stage3_svg) and natively supported formats
        if ext == ".svg" or not _needs_conversion(ext, native_extensions):
            return m.group(0)

        if not img_path.is_absolute() and resource_path is not None:
            img_path = resource_path / img_path

        if resource_path is not None:
            assert_within_root(img_path, resource_path, "Image")

        if not img_path.exists():
            raise ImageConversionError(f"Image file not found: {img_path}")

        counter += 1
        out_path = tmpdir / f"img_{counter}.png"

        try:
            with Image.open(img_path) as im:
                im.save(out_path, format="PNG")
        except (OSError, ValueError) as exc:
            raise ImageConversionError(
                f"Failed to convert {img_path} to PNG: {exc}. Ensure Pillow supports the {ext} format."
            ) from exc

        return f"![{alt_text}]({out_path})"

    return _IMG_REF_RE.sub(replace_image, body)


def convert_images_for_pdf(
    body: str,
    tmpdir: Path,
    resource_path: Path | None,
) -> str:
    """Convert images unsupported by LaTeX/tectonic to PNG."""
    return convert_images(body, tmpdir, resource_path, PDF_NATIVE_EXTENSIONS)


def convert_images_for_docx(
    body: str,
    tmpdir: Path,
    resource_path: Path | None,
) -> str:
    """Convert images unsupported by pandoc DOCX to PNG."""
    return convert_images(body, tmpdir, resource_path, DOCX_NATIVE_EXTENSIONS)
