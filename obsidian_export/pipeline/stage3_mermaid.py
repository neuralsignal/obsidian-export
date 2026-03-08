"""Stage 3: Extract and render Mermaid diagrams to PNG via mmdc."""

import re
import subprocess
from pathlib import Path

from obsidian_export.config import MermaidConfig

_MERMAID_BLOCK_RE = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)


def render_mermaid_blocks(body: str, config: MermaidConfig, tmpdir: Path) -> str:
    """Replace ```mermaid blocks with rendered PNG image references.

    Raises FileNotFoundError if mmdc binary is not found.
    Raises subprocess.CalledProcessError if mmdc rendering fails.
    """
    mmdc = config.mmdc_bin

    counter = 0

    def replace_block(m: re.Match) -> str:
        nonlocal counter
        if not mmdc.exists():
            raise FileNotFoundError(
                f"mmdc binary not found at {mmdc}. Install: npm install --prefix .mmdc @mermaid-js/mermaid-cli"
            )
        diagram_src = m.group(1)
        counter += 1

        src_file = tmpdir / f"diagram_{counter}.mmd"
        out_file = tmpdir / f"diagram_{counter}.png"
        src_file.write_text(diagram_src, encoding="utf-8")

        cmd = [
            str(mmdc),
            "--input",
            str(src_file),
            "--output",
            str(out_file),
            "--scale",
            str(config.scale),
            "--backgroundColor",
            "transparent",
        ]
        if config.puppeteer_config and config.puppeteer_config.exists():
            cmd.extend(["--puppeteerConfigFile", str(config.puppeteer_config)])

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode(errors="replace") if exc.stderr else "(no stderr)"
            raise RuntimeError(f"mmdc failed (exit {exc.returncode}) rendering diagram {counter}:\n{stderr}") from exc

        return f"![Diagram {counter}]({out_file})"

    return _MERMAID_BLOCK_RE.sub(replace_block, body)
