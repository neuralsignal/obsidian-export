"""Profile management for obsidian-export."""

from pathlib import Path

import yaml

from obsidian_export.config import ConvertConfig, load_config

PROFILE_DIR = Path.home() / ".obsidian-export" / "profiles"
USER_STYLES_DIR = Path.home() / ".obsidian-export" / "styles"


def init_user_dir() -> Path:
    """Create ~/.obsidian-export/ directory structure."""
    base = Path.home() / ".obsidian-export"
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    USER_STYLES_DIR.mkdir(parents=True, exist_ok=True)
    return base


def list_profiles() -> list[str]:
    """List available profile names."""
    if not PROFILE_DIR.exists():
        return []
    return sorted(p.stem for p in PROFILE_DIR.glob("*.yaml"))


def get_profile_path(name: str) -> Path:
    """Get the path to a profile YAML file."""
    return PROFILE_DIR / f"{name}.yaml"


def load_profile(name: str) -> ConvertConfig:
    """Load a profile by name from ~/.obsidian-export/profiles/."""
    path = get_profile_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {name!r} (expected at {path})")
    return load_config(path)


def save_profile(name: str, config_dict: dict) -> Path:
    """Save a profile YAML to ~/.obsidian-export/profiles/."""
    init_user_dir()
    path = get_profile_path(name)
    path.write_text(yaml.dump(config_dict, default_flow_style=False, sort_keys=False), encoding="utf-8")
    return path


def delete_profile(name: str) -> None:
    """Delete a profile by name."""
    path = get_profile_path(name)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {name!r} (expected at {path})")
    path.unlink()
