"""Tests for obsidian_export.profiles path traversal protection."""

from pathlib import Path
from unittest.mock import patch

import pytest

from obsidian_export.exceptions import ProfileNameError
from obsidian_export.profiles import get_profile_path


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
