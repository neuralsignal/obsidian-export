"""CLI for obsidian-export."""

import shutil
from pathlib import Path

import click
import yaml

from obsidian_export import run
from obsidian_export.config import default_config, load_config, load_default_yaml
from obsidian_export.profiles import (
    delete_profile,
    get_profile_path,
    init_user_dir,
    list_profiles,
    load_profile,
    save_profile,
)


@click.group()
def main() -> None:
    """Convert Obsidian-flavored Markdown to PDF and DOCX."""


@main.command()
@click.option("--input", "input_path", required=True, type=click.Path(exists=True), help="Source .md file")
@click.option("--format", "output_format", required=True, type=click.Choice(["pdf", "docx"]), help="Output format")
@click.option("--output", "output_path", required=True, type=click.Path(), help="Output file path")
@click.option("--profile", "profile_name", default=None, help="Profile name or path to config YAML")
def convert(input_path: str, output_format: str, output_path: str, profile_name: str | None) -> None:
    """Convert a Markdown file to PDF or DOCX."""
    if profile_name is None:
        config = default_config()
    elif Path(profile_name).is_file():
        config = load_config(Path(profile_name))
    else:
        config = load_profile(profile_name)

    run(Path(input_path), Path(output_path), output_format, config)


@main.group()
def profile() -> None:
    """Manage conversion profiles."""


@profile.command("create")
@click.argument("name")
@click.option("--from", "from_file", default=None, type=click.Path(exists=True), help="Copy from existing YAML")
def profile_create(name: str, from_file: str | None) -> None:
    """Create a new profile with default settings."""
    path = get_profile_path(name)
    if path.exists():
        click.echo(f"Profile already exists: {path}")
        raise SystemExit(1)

    if from_file:
        config_dict = yaml.safe_load(Path(from_file).read_text(encoding="utf-8"))
    else:
        config_dict = load_default_yaml()

    result = save_profile(name, config_dict)
    click.echo(f"Created profile: {result}")


@profile.command("list")
def profile_list() -> None:
    """List available profiles."""
    profiles = list_profiles()
    if not profiles:
        click.echo("No profiles found. Run 'obsidian-export init' first.")
        return
    for name in profiles:
        click.echo(name)


@profile.command("show")
@click.argument("name")
def profile_show(name: str) -> None:
    """Print profile YAML to stdout."""
    path = get_profile_path(name)
    if not path.exists():
        click.echo(f"Profile not found: {name}")
        raise SystemExit(1)
    click.echo(path.read_text(encoding="utf-8"))


@profile.command("delete")
@click.argument("name")
@click.option("--yes", is_flag=True, help="Skip confirmation")
def profile_delete(name: str, yes: bool) -> None:
    """Delete a profile."""
    path = get_profile_path(name)
    if not path.exists():
        click.echo(f"Profile not found: {name}")
        raise SystemExit(1)
    if not yes:
        click.confirm(f"Delete profile '{name}'?", abort=True)
    delete_profile(name)
    click.echo(f"Deleted profile: {name}")


@main.command("init")
def init() -> None:
    """Create ~/.obsidian-export/ directory structure with a default profile."""
    base = init_user_dir()
    # Write default profile if it doesn't exist
    default_path = get_profile_path("default")
    if not default_path.exists():
        save_profile("default", load_default_yaml())
        click.echo(f"Created default profile: {default_path}")
    click.echo(f"Initialized: {base}")


@main.command("doctor")
def doctor() -> None:
    """Check system dependencies."""
    deps = {
        "pandoc": "Markdown to PDF/DOCX conversion",
        "tectonic": "XeLaTeX PDF engine",
        "rsvg-convert": "SVG rendering (optional)",
        "mmdc": "Mermaid diagrams (optional, or use config mmdc_bin)",
        "node": "Node.js runtime for mmdc (optional)",
    }
    all_ok = True
    for cmd, purpose in deps.items():
        path = shutil.which(cmd)
        if path:
            click.echo(f"  {cmd}: {path}")
        else:
            marker = "MISSING" if cmd in ("pandoc", "tectonic") else "not found"
            click.echo(f"  {cmd}: {marker} — {purpose}")
            if cmd in ("pandoc", "tectonic"):
                all_ok = False

    if all_ok:
        click.echo("\nAll required dependencies found.")
    else:
        click.echo("\nSome required dependencies are missing.")
        raise SystemExit(1)
