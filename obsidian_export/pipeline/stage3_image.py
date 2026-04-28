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
from obsidian_export.pipeline.image_convert import convert_image_references
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

    def _pre_filter(m: re.Match[str]) -> str | None:
        img_path = Path(m.group(2))
        ext = img_path.suffix.lower()

        if ext == ".svg":
            return m.group(0)

        if not _needs_conversion(ext, native_extensions):
            if not img_path.is_absolute() and resource_path is not None:
                abs_path = resource_path / img_path
                assert_within_root(abs_path, resource_path, "Image")
                return f"![{m.group(1)}]({abs_path})"
            return m.group(0)

        return None

    def _do_convert(src: Path, dst: Path) -> None:
        ext = src.suffix.lower()
        try:
            with Image.open(src) as im:
                im.save(dst, format="PNG")
        except (OSError, ValueError) as exc:
            raise ImageConversionError(
                f"Failed to convert {src} to PNG: {exc}. Ensure Pillow supports the {ext} format."
            ) from exc

    return convert_image_references(
        body,
        tmpdir,
        resource_path,
        _IMG_REF_RE,
        _do_convert,
        "img_",
        ".png",
        "Image",
        ImageConversionError,
        _pre_filter,
    )


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
