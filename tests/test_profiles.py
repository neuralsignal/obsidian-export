"""Tests for obsidian_export.profiles."""

from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from hypothesis import given
from hypothesis import strategies as st

from obsidian_export.config import ConvertConfig
from obsidian_export.exceptions import ProfileNameError
from obsidian_export.profiles import (
    delete_profile,
    get_profile_path,
    init_user_dir,
    list_profiles,
    load_profile,
    save_profile,
)


def test_get_profile_path_valid_name(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    with patch("obsidian_export.profiles.PROFILE_DIR", profile_dir):
        path = get_profile_path("my-profile_1")
    assert path == (profile_dir / "my-profile_1.yaml").resolve()


def test_get_profile_path_rejects_path_traversal(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        pytest.raises(ProfileNameError, match="Invalid profile name"),
    ):
        get_profile_path("../../.ssh/authorized_keys")


def test_get_profile_path_rejects_slash(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        pytest.raises(ProfileNameError, match="Invalid profile name"),
    ):
        get_profile_path("sub/dir")


def test_get_profile_path_rejects_dot(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        pytest.raises(ProfileNameError, match="Invalid profile name"),
    ):
        get_profile_path("../sibling")


def test_get_profile_path_rejects_empty(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        pytest.raises(ProfileNameError, match="Invalid profile name"),
    ):
        get_profile_path("")


def test_get_profile_path_rejects_special_chars(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        pytest.raises(ProfileNameError, match="Invalid profile name"),
    ):
        get_profile_path("name with spaces")


def test_get_profile_path_traversal_after_resolve(tmp_path: Path) -> None:
    """Cover the defence-in-depth guard on line 46: a name passes the regex but resolve() escapes PROFILE_DIR."""
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    escaped_path = tmp_path / "elsewhere" / "evil.yaml"
    original_resolve = Path.resolve

    def fake_resolve(self: Path) -> Path:
        if self.name == "legit-name.yaml":
            return escaped_path
        return original_resolve(self)

    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        patch.object(Path, "resolve", fake_resolve),
        pytest.raises(ProfileNameError, match="path traversal detected"),
    ):
        get_profile_path("legit-name")


# --- init_user_dir ---


def test_init_user_dir_creates_directories(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    styles_dir = tmp_path / "styles"
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        patch("obsidian_export.profiles.USER_STYLES_DIR", styles_dir),
        patch("pathlib.Path.home", return_value=tmp_path),
    ):
        base = init_user_dir()
    assert profile_dir.is_dir()
    assert styles_dir.is_dir()
    assert base == tmp_path / ".obsidian-export"


def test_init_user_dir_idempotent(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    styles_dir = tmp_path / "styles"
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        patch("obsidian_export.profiles.USER_STYLES_DIR", styles_dir),
        patch("pathlib.Path.home", return_value=tmp_path),
    ):
        init_user_dir()
        init_user_dir()
    assert profile_dir.is_dir()
    assert styles_dir.is_dir()


# --- list_profiles ---


def test_list_profiles_empty_when_dir_missing(tmp_path: Path) -> None:
    profile_dir = tmp_path / "nonexistent"
    with patch("obsidian_export.profiles.PROFILE_DIR", profile_dir):
        assert list_profiles() == []


def test_list_profiles_returns_sorted_stems(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    (profile_dir / "zebra.yaml").write_text("", encoding="utf-8")
    (profile_dir / "alpha.yaml").write_text("", encoding="utf-8")
    (profile_dir / "not-a-profile.txt").write_text("", encoding="utf-8")
    with patch("obsidian_export.profiles.PROFILE_DIR", profile_dir):
        result = list_profiles()
    assert result == ["alpha", "zebra"]


@given(names=st.lists(st.from_regex(r"[a-zA-Z0-9_-]{1,20}", fullmatch=True), min_size=0, max_size=10, unique=True))
def test_list_profiles_returns_sorted_stems_property(names: list[str]) -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        profile_dir = Path(td) / "profiles"
        profile_dir.mkdir()
        for name in names:
            (profile_dir / f"{name}.yaml").write_text("", encoding="utf-8")
        with patch("obsidian_export.profiles.PROFILE_DIR", profile_dir):
            result = list_profiles()
        assert result == sorted(names)


# --- load_profile ---


def test_load_profile_happy_path(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    profile_yaml = profile_dir / "test.yaml"
    profile_yaml.write_text(
        yaml.dump({"style": {"name": "custom"}}),
        encoding="utf-8",
    )
    with patch("obsidian_export.profiles.PROFILE_DIR", profile_dir):
        config = load_profile("test")
    assert isinstance(config, ConvertConfig)
    assert config.style.name == "custom"


def test_load_profile_missing_raises(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        pytest.raises(FileNotFoundError, match="Profile not found"),
    ):
        load_profile("nonexistent")


# --- save_profile ---


def test_save_profile_writes_yaml(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    styles_dir = tmp_path / "styles"
    config_dict = {"style": {"name": "saved"}}
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        patch("obsidian_export.profiles.USER_STYLES_DIR", styles_dir),
        patch("pathlib.Path.home", return_value=tmp_path),
    ):
        path = save_profile("myprofile", config_dict)
    assert path.exists()
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert loaded == config_dict


# --- delete_profile ---


def test_delete_profile_happy_path(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    profile_file = profile_dir / "doomed.yaml"
    profile_file.write_text("", encoding="utf-8")
    with patch("obsidian_export.profiles.PROFILE_DIR", profile_dir):
        delete_profile("doomed")
    assert not profile_file.exists()


def test_delete_profile_missing_raises(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir()
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        pytest.raises(FileNotFoundError, match="Profile not found"),
    ):
        delete_profile("ghost")
