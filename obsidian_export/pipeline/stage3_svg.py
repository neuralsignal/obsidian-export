"""Stage 3b: Convert SVG image references for LaTeX (PDF) and DOCX compatibility."""

import re
import subprocess
from pathlib import Path

from obsidian_export.exceptions import SVGConversionError
from obsidian_export.pipeline.image_convert import ImageConversionSpec, convert_image_references

_IMG_REF_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+\.svg)\)")


def _convert_svg_images(body: str, tmpdir: Path, resource_path: Path | None, rsvg_format: str, file_ext: str) -> str:
    """Find SVG image references in markdown and convert them via rsvg-convert.

    Only processes local file paths (not URLs). Each SVG is converted
    to a file in tmpdir using the given rsvg_format and file_ext, and the
    reference is updated. Relative SVG paths are resolved against resource_path.
    """

    def _do_convert(src: Path, dst: Path) -> None:
        try:
            subprocess.run(
                [
                    "rsvg-convert",
                    f"--format={rsvg_format}",
                    f"--output={dst}",
                    str(src),
                ],
                check=True,
                capture_output=True,
            )
        except FileNotFoundError as exc:
            raise SVGConversionError("rsvg-convert not found: is librsvg installed?") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else "(no stderr)"
            raise SVGConversionError(f"rsvg-convert failed for {src} (exit {exc.returncode}): {stderr}") from exc

    spec = ImageConversionSpec(
        pattern=_IMG_REF_RE,
        convert_fn=_do_convert,
        out_prefix="svg_",
        out_ext=file_ext,
        label="SVG",
        not_found_error=SVGConversionError,
        pre_filter=lambda _m: None,
    )
    return convert_image_references(body, tmpdir, resource_path, spec)


def convert_svg_images(body: str, tmpdir: Path, resource_path: Path | None) -> str:
    """Find SVG image references and convert to PDF for LaTeX/PDF output."""
    return _convert_svg_images(body, tmpdir, resource_path, "pdf", ".pdf")


def convert_svg_images_to_png(body: str, tmpdir: Path, resource_path: Path | None) -> str:
    """Find SVG image references and convert to PNG for DOCX output."""
    return _convert_svg_images(body, tmpdir, resource_path, "png", ".png")
