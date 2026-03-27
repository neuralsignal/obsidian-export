"""Stage 3b: Convert SVG image references for LaTeX (PDF) and DOCX compatibility."""

import re
import subprocess
from pathlib import Path

from obsidian_export.exceptions import SVGConversionError
from obsidian_export.pipeline.path_guards import assert_within_root

_IMG_REF_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+\.svg)\)")


def _convert_svg_images(body: str, tmpdir: Path, resource_path: Path | None, rsvg_format: str, file_ext: str) -> str:
    """Find SVG image references in markdown and convert them via rsvg-convert.

    Only processes local file paths (not URLs). Each SVG is converted
    to a file in tmpdir using the given rsvg_format and file_ext, and the
    reference is updated. Relative SVG paths are resolved against resource_path.
    """
    counter = 0

    def replace_svg(m: re.Match) -> str:
        """Replace an SVG image reference with a rsvg-converted version.

        Receives a match with group(1) as alt text and group(2) as the SVG path.
        Skips URLs. Converts the SVG via rsvg-convert into tmpdir and returns an
        updated markdown image reference. Increments the outer ``counter`` for
        unique filenames.
        """
        nonlocal counter
        alt_text = m.group(1)
        svg_raw = m.group(2)

        # Skip URLs
        if svg_raw.startswith(("http://", "https://")):
            return m.group(0)

        svg_path = Path(svg_raw)

        # Resolve relative paths against resource_path
        if not svg_path.is_absolute() and resource_path is not None:
            svg_path = resource_path / svg_path

        if resource_path is not None:
            assert_within_root(svg_path, resource_path, "SVG")

        if not svg_path.exists():
            raise SVGConversionError(f"SVG file not found: {svg_path}")

        counter += 1
        out_path = tmpdir / f"svg_{counter}{file_ext}"

        try:
            subprocess.run(
                [
                    "rsvg-convert",
                    f"--format={rsvg_format}",
                    f"--output={out_path}",
                    str(svg_path),
                ],
                check=True,
                capture_output=True,
            )
        except FileNotFoundError as exc:
            raise SVGConversionError("rsvg-convert not found: is librsvg installed?") from exc
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else "(no stderr)"
            raise SVGConversionError(f"rsvg-convert failed for {svg_path} (exit {exc.returncode}): {stderr}") from exc

        return f"![{alt_text}]({out_path})"

    return _IMG_REF_RE.sub(replace_svg, body)


def convert_svg_images(body: str, tmpdir: Path, resource_path: Path | None) -> str:
    """Find SVG image references and convert to PDF for LaTeX/PDF output."""
    return _convert_svg_images(body, tmpdir, resource_path, "pdf", ".pdf")


def convert_svg_images_to_png(body: str, tmpdir: Path, resource_path: Path | None) -> str:
    """Find SVG image references and convert to PNG for DOCX output."""
    return _convert_svg_images(body, tmpdir, resource_path, "png", ".png")
