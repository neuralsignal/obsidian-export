"""Stage 4: Pandoc invocation for PDF and DOCX output."""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

from obsidian_export.config import PandocConfig, StyleConfig


@dataclass(frozen=True)
class PandocInvocation:
    """Groups the parameters shared by PDF and DOCX pandoc conversions."""

    text: str
    title: str
    pandoc_config: PandocConfig
    style_config: StyleConfig
    filters_dir: Path
    output_path: Path
    resource_path: Path | None


def _yaml_metadata_block(metadata: dict) -> str:
    """Build a pandoc YAML metadata block from a dict.

    This safely handles values containing colons, quotes, and other
    characters that would break ``--metadata=key:value`` CLI syntax.
    """
    return "---\n" + yaml.dump(metadata, allow_unicode=True, default_flow_style=False) + "---\n\n"


def _run_pandoc(
    invocation: PandocInvocation,
    lua_filter_names: list[str],
    metadata: dict,
    extra_args: list[str],
) -> None:
    """Shared scaffolding for pandoc conversion.

    Validates lua filters, creates output directories, prepends a YAML
    metadata block, and invokes pandoc as a subprocess.
    """
    lua_filters = [invocation.filters_dir / name for name in lua_filter_names]
    for f in lua_filters:
        if not f.exists():
            raise FileNotFoundError(f"Lua filter not found: {f}")

    invocation.output_path.parent.mkdir(parents=True, exist_ok=True)

    text = _yaml_metadata_block(metadata) + invocation.text

    cmd = [
        "pandoc",
        f"--from={invocation.pandoc_config.from_format}",
        *extra_args,
        f"--output={invocation.output_path}",
    ]
    if invocation.resource_path is not None:
        cmd.append(f"--resource-path={invocation.resource_path}")
    for f in lua_filters:
        cmd.append(f"--lua-filter={f}")

    subprocess.run(
        cmd,
        input=text,
        text=True,
        encoding="utf-8",
        check=True,
    )


def convert_to_pdf(
    invocation: PandocInvocation,
    rendered_header: str,
) -> None:
    """Convert preprocessed markdown text to PDF via pandoc + tectonic."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False, encoding="utf-8") as hf:
        hf.write(rendered_header)
        header_tmp_path = Path(hf.name)

    try:
        metadata = {
            "title": invocation.title,
            "table_fontsize": invocation.style_config.table_fontsize,
            "url_footnote_threshold": invocation.style_config.url_footnote_threshold,
        }
        extra_args = [
            "--to=pdf",
            "--pdf-engine=tectonic",
            f"--include-in-header={header_tmp_path}",
            f"--variable=geometry:{invocation.style_config.geometry}",
            f"--variable=fontsize:{invocation.style_config.fontsize}",
            f"--variable=linkcolor:{invocation.style_config.linkcolor}",
            f"--variable=urlcolor:{invocation.style_config.urlcolor}",
        ]
        lua_filter_names = [
            "center_figures.lua",
            "fix_tables.lua",
            "escape_strings.lua",
            "callout_boxes.lua",
            "promote_footnotes.lua",
            "newpage_on_rule.lua",
        ]
        _run_pandoc(invocation, lua_filter_names, metadata, extra_args)
    finally:
        header_tmp_path.unlink(missing_ok=True)


def convert_to_docx(
    invocation: PandocInvocation,
    reference_doc: Path | None,
) -> None:
    """Convert preprocessed markdown text to DOCX via pandoc.

    Applies DOCX-specific Lua filters (callout boxes, footnote promotion,
    page breaks) from the invocation's filters_dir. If *reference_doc* is
    provided, it is passed as ``--reference-doc`` to inject custom styles.
    """
    metadata = {
        "title": invocation.title,
        "url_footnote_threshold": invocation.style_config.url_footnote_threshold,
    }
    extra_args = ["--to=docx"]
    if reference_doc is not None:
        extra_args.append(f"--reference-doc={reference_doc}")
    lua_filter_names = [
        "callout_boxes_docx.lua",
        "promote_footnotes.lua",
        "newpage_on_rule_docx.lua",
    ]
    _run_pandoc(invocation, lua_filter_names, metadata, extra_args)
