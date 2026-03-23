"""obsidian-export: Obsidian -> PDF/DOCX pipeline.

Public API:
    run(input_path, output_path, output_format, config) -> None
"""

import tempfile
from pathlib import Path

from obsidian_export.config import ConvertConfig, StyleConfig
from obsidian_export.pipeline.latex_header import render_header
from obsidian_export.pipeline.stage1_vault import (
    clean_frontmatter,
    parse_frontmatter,
    resolve_embeds,
    strip_leading_title,
    strip_obsidian_syntax,
)
from obsidian_export.pipeline.stage2_preprocess import preprocess
from obsidian_export.pipeline.stage3_image import convert_images_for_docx, convert_images_for_pdf
from obsidian_export.pipeline.stage3_mermaid import render_mermaid_blocks
from obsidian_export.pipeline.stage3_svg import convert_svg_images, convert_svg_images_to_png
from obsidian_export.pipeline.stage4_pandoc import PandocInvocation, convert_to_docx, convert_to_pdf
from obsidian_export.profiles import USER_STYLES_DIR


def _resolve_style_dir(style: StyleConfig) -> Path:
    """Resolve style directory.

    Resolution order:
    1. style.style_dir if set (absolute or relative path)
    2. Built-in assets/styles/<name>/
    3. ~/.obsidian-export/styles/<name>/
    4. Treat style.name as an absolute/relative path
    """
    # Explicit style_dir override
    if style.style_dir:
        candidate = Path(style.style_dir)
        if candidate.is_dir():
            return candidate
        raise FileNotFoundError(f"Style dir not found: {style.style_dir!r}")

    name = style.name

    # Built-in styles
    builtin = Path(__file__).parent / "assets" / "styles" / name
    if builtin.is_dir():
        return builtin

    # User styles
    user = USER_STYLES_DIR / name
    if user.is_dir():
        return user

    # Treat as path
    candidate = Path(name)
    if candidate.is_dir():
        return candidate

    raise FileNotFoundError(f"Style not found: {name!r} (checked {builtin}, {user}, and {candidate})")


def run(
    input_path: Path,
    output_path: Path,
    output_format: str,
    config: ConvertConfig,
) -> None:
    """Full pipeline: Stage 1 -> Stage 2 -> Stage 3 -> Stage 4.

    input_path:    absolute path to source .md file
    output_path:   absolute path for output file (parent dirs created automatically)
    output_format: "pdf" or "docx"
    config:        fully-populated ConvertConfig (no defaults)
    """
    if output_format not in ("pdf", "docx"):
        raise ValueError(f"Unsupported output format: {output_format!r}. Use 'pdf' or 'docx'.")

    source = input_path.read_text(encoding="utf-8")

    # Stage 1: Vault operations
    fm, body = parse_frontmatter(source)
    fm = clean_frontmatter(fm)
    # .get() intentional: title is genuinely optional in frontmatter;
    # many knowledge notes omit it, so we fall back to the filename stem.
    title = str(fm.get("title", input_path.stem))
    body = strip_leading_title(body, title)
    vault_root = input_path.parent
    body = resolve_embeds(body, vault_root, input_path, config.obsidian.max_embed_depth)
    body = strip_obsidian_syntax(body)

    # Stage 2: Text-level pre-processing
    body = preprocess(body, config.obsidian)

    # Stage 3: Mermaid diagram rendering
    with tempfile.TemporaryDirectory() as tmpdir:
        body = render_mermaid_blocks(body, config.mermaid, Path(tmpdir))

        # Stage 3b: SVG conversion for format compatibility
        if output_format == "pdf":
            body = convert_svg_images(body, Path(tmpdir), resource_path=input_path.parent)
        else:
            body = convert_svg_images_to_png(body, Path(tmpdir), resource_path=input_path.parent)

        # Stage 3c: Non-SVG image conversion for format compatibility
        if output_format == "pdf":
            body = convert_images_for_pdf(body, Path(tmpdir), resource_path=input_path.parent)
        else:
            body = convert_images_for_docx(body, Path(tmpdir), resource_path=input_path.parent)

        # Stage 4: Pandoc conversion
        style_dir = _resolve_style_dir(config.style)
        filters_dir = Path(__file__).parent / "assets" / "filters"

        invocation = PandocInvocation(
            text=body,
            title=title,
            pandoc_config=config.pandoc,
            style_config=config.style,
            filters_dir=filters_dir,
            output_path=output_path,
            resource_path=input_path.parent,
        )

        if output_format == "pdf":
            rendered_header = render_header(config.style, style_dir / "header.tex", title)
            convert_to_pdf(invocation, rendered_header)
        else:
            reference_doc_path = style_dir / "reference.docx"
            reference_doc = reference_doc_path if reference_doc_path.exists() else None
            convert_to_docx(invocation, reference_doc)
