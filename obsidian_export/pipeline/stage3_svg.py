"""Stage 3b: Convert SVG image references to PDF for LaTeX compatibility."""

import re
import subprocess
import warnings
from pathlib import Path

_IMG_REF_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+\.svg)\)")


def convert_svg_images(body: str, tmpdir: Path) -> str:
    """Find SVG image references in markdown and convert them to PDF.

    Only processes local file paths (not URLs). Each SVG is converted
    via rsvg-convert to a PDF file in tmpdir, and the reference is updated.
    """
    counter = 0

    def replace_svg(m: re.Match) -> str:
        nonlocal counter
        alt_text = m.group(1)
        svg_path = Path(m.group(2))

        # Skip URLs
        if str(svg_path).startswith(("http://", "https://")):
            return m.group(0)

        if not svg_path.exists():
            warnings.warn(f"SVG file not found: {svg_path}", stacklevel=2)
            return m.group(0)

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
