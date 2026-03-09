"""Stage 4: Pandoc invocation for PDF and DOCX output."""

import subprocess
import tempfile
from pathlib import Path

import yaml

from obsidian_export.config import PandocConfig, StyleConfig


def _yaml_metadata_block(metadata: dict) -> str:
    """Build a pandoc YAML metadata block from a dict.

    This safely handles values containing colons, quotes, and other
    characters that would break ``--metadata=key:value`` CLI syntax.
    """
    return "---\n" + yaml.dump(metadata, allow_unicode=True, default_flow_style=False) + "---\n\n"


def convert_to_pdf(
    text: str,
    title: str,
    pandoc_config: PandocConfig,
    style_config: StyleConfig,
    rendered_header: str,
    filters_dir: Path,
    output_path: Path,
    resource_path: Path | None,
) -> None:
    """Convert preprocessed markdown text to PDF via pandoc + tectonic."""
    lua_filters = [
        filters_dir / "center_figures.lua",
        filters_dir / "fix_tables.lua",
        filters_dir / "escape_strings.lua",
        filters_dir / "callout_boxes.lua",
        filters_dir / "promote_footnotes.lua",
        filters_dir / "newpage_on_rule.lua",
    ]
    for f in lua_filters:
        if not f.exists():
            raise FileNotFoundError(f"Lua filter not found: {f}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write rendered header to a temp file for pandoc --include-in-header
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tex", delete=False, encoding="utf-8") as hf:
        hf.write(rendered_header)
        header_tmp_path = Path(hf.name)

    try:
        metadata_block = _yaml_metadata_block(
            {
                "title": title,
                "table_fontsize": style_config.table_fontsize,
                "url_footnote_threshold": style_config.url_footnote_threshold,
            }
        )
        text = metadata_block + text

        cmd = [
            "pandoc",
            f"--from={pandoc_config.from_format}",
            "--to=pdf",
            "--pdf-engine=tectonic",
            f"--include-in-header={header_tmp_path}",
            f"--variable=geometry:{style_config.geometry}",
            f"--variable=fontsize:{style_config.fontsize}",
            f"--variable=linkcolor:{style_config.linkcolor}",
            f"--variable=urlcolor:{style_config.urlcolor}",
            f"--output={output_path}",
        ]
        if resource_path is not None:
            cmd.append(f"--resource-path={resource_path}")
        for f in lua_filters:
            cmd.append(f"--lua-filter={f}")

        subprocess.run(
            cmd,
            input=text,
            text=True,
            encoding="utf-8",
            check=True,
        )
    finally:
        header_tmp_path.unlink(missing_ok=True)


def convert_to_docx(
    text: str,
    title: str,
    pandoc_config: PandocConfig,
    style_config: StyleConfig,
    filters_dir: Path,
    reference_doc: Path | None,
    output_path: Path,
    resource_path: Path | None,
) -> None:
    """Convert preprocessed markdown text to DOCX via pandoc."""
    lua_filters = [
        filters_dir / "callout_boxes_docx.lua",
        filters_dir / "promote_footnotes.lua",
        filters_dir / "newpage_on_rule_docx.lua",
    ]
    for f in lua_filters:
        if not f.exists():
            raise FileNotFoundError(f"Lua filter not found: {f}")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    metadata_block = _yaml_metadata_block(
        {
            "title": title,
            "url_footnote_threshold": style_config.url_footnote_threshold,
        }
    )
    text = metadata_block + text

    cmd = [
        "pandoc",
        f"--from={pandoc_config.from_format}",
        "--to=docx",
        f"--output={output_path}",
    ]
    if reference_doc is not None:
        cmd.append(f"--reference-doc={reference_doc}")
    if resource_path is not None:
        cmd.append(f"--resource-path={resource_path}")
    for f in lua_filters:
        cmd.append(f"--lua-filter={f}")

    subprocess.run(
        cmd,
        input=text,
        text=True,
        encoding="utf-8",
        check=True,
    )
