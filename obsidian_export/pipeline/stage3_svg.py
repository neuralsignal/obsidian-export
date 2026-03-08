"""Stage 3b: Convert SVG image references to PDF for LaTeX compatibility."""

import re
import subprocess
from pathlib import Path

from obsidian_export.exceptions import SVGConversionError

_IMG_REF_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+\.svg)\)")


def convert_svg_images(body: str, tmpdir: Path, resource_path: Path | None) -> str:
    """Find SVG image references in markdown and convert them to PDF.

    Only processes local file paths (not URLs). Each SVG is converted
    via rsvg-convert to a PDF file in tmpdir, and the reference is updated.
    Relative SVG paths are resolved against resource_path if provided.
    """
    counter = 0

    def replace_svg(m: re.Match) -> str:
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

        if not svg_path.exists():
            raise SVGConversionError(f"SVG file not found: {svg_path}")

        counter += 1
        pdf_path = tmpdir / f"svg_{counter}.pdf"

        subprocess.run(
            [
                "rsvg-convert",
                "--format=pdf",
                f"--output={pdf_path}",
                str(svg_path),
            ],
            check=True,
            capture_output=True,
        )

        return f"![{alt_text}]({pdf_path})"

    return _IMG_REF_RE.sub(replace_svg, body)
