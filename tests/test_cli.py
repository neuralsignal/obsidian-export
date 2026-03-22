"""Tests for obsidian_export.cli."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml
from click.testing import CliRunner

from obsidian_export.cli import main


def test_init_creates_directory(tmp_path: Path) -> None:
    profile_dir = tmp_path / "profiles"
    styles_dir = tmp_path / "styles"
    with (
        patch("obsidian_export.profiles.PROFILE_DIR", profile_dir),
        patch("obsidian_export.profiles.USER_STYLES_DIR", styles_dir),
        patch("obsidian_export.cli.init_user_dir") as mock_init,
        patch("obsidian_export.cli.get_profile_path") as mock_path,
        patch("obsidian_export.cli.save_profile"),
    ):
        mock_init.return_value = tmp_path
        mock_path.return_value = tmp_path / "profiles" / "default.yaml"
        runner = CliRunner()
        result = runner.invoke(main, ["init"])
        assert result.exit_code == 0
        assert "Initialized" in result.output


def test_doctor_runs() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["doctor"])
    # Doctor may succeed or fail depending on system, but should not crash
    assert result.exit_code in (0, 1)
    assert "pandoc" in result.output


def test_profile_list_empty(tmp_path: Path) -> None:
    with patch("obsidian_export.cli.list_profiles", return_value=[]):
        runner = CliRunner()
        result = runner.invoke(main, ["profile", "list"])
        assert result.exit_code == 0
        assert "No profiles" in result.output


def test_profile_list_with_profiles(tmp_path: Path) -> None:
    with patch("obsidian_export.cli.list_profiles", return_value=["default", "custom"]):
        runner = CliRunner()
        result = runner.invoke(main, ["profile", "list"])
        assert result.exit_code == 0
        assert "default" in result.output
        assert "custom" in result.output


def test_profile_create(tmp_path: Path) -> None:
    profile_path = tmp_path / "test.yaml"
    with (
        patch("obsidian_export.cli.get_profile_path", return_value=profile_path),
        patch("obsidian_export.cli.save_profile", return_value=profile_path),
    ):
        runner = CliRunner()
        result = runner.invoke(main, ["profile", "create", "test"])
        assert result.exit_code == 0
        assert "Created profile" in result.output


def test_profile_create_already_exists(tmp_path: Path) -> None:
    profile_path = tmp_path / "test.yaml"
    profile_path.write_text("exists", encoding="utf-8")
    with patch("obsidian_export.cli.get_profile_path", return_value=profile_path):
        runner = CliRunner()
        result = runner.invoke(main, ["profile", "create", "test"])
        assert result.exit_code == 1
        assert "already exists" in result.output


def test_profile_delete_with_yes(tmp_path: Path) -> None:
    profile_path = tmp_path / "test.yaml"
    profile_path.write_text("exists", encoding="utf-8")
    with (
        patch("obsidian_export.cli.get_profile_path", return_value=profile_path),
        patch("obsidian_export.cli.delete_profile") as mock_delete,
    ):
        runner = CliRunner()
        result = runner.invoke(main, ["profile", "delete", "test", "--yes"])
        assert result.exit_code == 0
        mock_delete.assert_called_once_with("test")


def test_profile_show(tmp_path: Path) -> None:
    profile_path = tmp_path / "test.yaml"
    profile_path.write_text("style:\n  name: custom\n", encoding="utf-8")
    with patch("obsidian_export.cli.get_profile_path", return_value=profile_path):
        runner = CliRunner()
        result = runner.invoke(main, ["profile", "show", "test"])
        assert result.exit_code == 0
        assert "custom" in result.output


def test_convert_missing_input() -> None:
    runner = CliRunner()
    result = runner.invoke(
        main, ["convert", "--input", "/nonexistent.md", "--format", "pdf", "--output", "/tmp/out.pdf"]
    )
    assert result.exit_code != 0


def test_convert_with_profile_name(tmp_path: Path) -> None:
    input_file = tmp_path / "note.md"
    input_file.write_text("# Hello", encoding="utf-8")
    output_file = tmp_path / "out.pdf"
    mock_config = MagicMock()
    with (
        patch("obsidian_export.cli.load_profile", return_value=mock_config) as mock_load,
        patch("obsidian_export.cli.run") as mock_run,
    ):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "convert",
                "--input",
                str(input_file),
                "--format",
                "pdf",
                "--output",
                str(output_file),
                "--profile",
                "default",
            ],
        )
        assert result.exit_code == 0, result.output
        mock_load.assert_called_once_with("default")
        mock_run.assert_called_once_with(Path(str(input_file)), Path(str(output_file)), "pdf", mock_config)


def test_convert_with_profile_file(tmp_path: Path) -> None:
    input_file = tmp_path / "note.md"
    input_file.write_text("# Hello", encoding="utf-8")
    config_file = tmp_path / "custom.yaml"
    config_file.write_text(yaml.dump({"style": {"name": "test"}}), encoding="utf-8")
    output_file = tmp_path / "out.pdf"
    mock_config = MagicMock()
    with (
        patch("obsidian_export.cli.load_config", return_value=mock_config) as mock_load_config,
        patch("obsidian_export.cli.run") as mock_run,
    ):
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "convert",
                "--input",
                str(input_file),
                "--format",
                "pdf",
                "--output",
                str(output_file),
                "--profile",
                str(config_file),
            ],
        )
        assert result.exit_code == 0, result.output
        mock_load_config.assert_called_once_with(config_file)
        mock_run.assert_called_once()


def test_profile_create_from_file(tmp_path: Path) -> None:
    from_file = tmp_path / "source.yaml"
    from_file.write_text(yaml.dump({"style": {"name": "imported"}}), encoding="utf-8")
    profile_path = tmp_path / "new.yaml"
    with (
        patch("obsidian_export.cli.get_profile_path", return_value=profile_path),
        patch("obsidian_export.cli.save_profile", return_value=profile_path) as mock_save,
    ):
        runner = CliRunner()
        result = runner.invoke(main, ["profile", "create", "new", "--from", str(from_file)])
        assert result.exit_code == 0, result.output
        assert "Created profile" in result.output
        saved_dict = mock_save.call_args[0][1]
        assert saved_dict["style"]["name"] == "imported"


def test_profile_show_not_found(tmp_path: Path) -> None:
    profile_path = tmp_path / "nonexistent.yaml"
    with patch("obsidian_export.cli.get_profile_path", return_value=profile_path):
        runner = CliRunner()
        result = runner.invoke(main, ["profile", "show", "nonexistent"])
        assert result.exit_code == 1
        assert "Profile not found" in result.output


def test_profile_delete_not_found(tmp_path: Path) -> None:
    profile_path = tmp_path / "nonexistent.yaml"
    with patch("obsidian_export.cli.get_profile_path", return_value=profile_path):
        runner = CliRunner()
        result = runner.invoke(main, ["profile", "delete", "nonexistent", "--yes"])
        assert result.exit_code == 1
        assert "Profile not found" in result.output


def test_profile_delete_prompts_without_yes(tmp_path: Path) -> None:
    profile_path = tmp_path / "test.yaml"
    profile_path.write_text("exists", encoding="utf-8")
    with (
        patch("obsidian_export.cli.get_profile_path", return_value=profile_path),
        patch("obsidian_export.cli.delete_profile") as mock_delete,
    ):
        runner = CliRunner()
        result = runner.invoke(main, ["profile", "delete", "test"], input="y\n")
        assert result.exit_code == 0
        mock_delete.assert_called_once_with("test")
        assert "Deleted profile" in result.output


def test_doctor_missing_deps() -> None:
    def fake_which(cmd: str) -> str | None:
        return None

    with patch("obsidian_export.cli.shutil.which", side_effect=fake_which):
        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])
        assert result.exit_code == 1
        assert "MISSING" in result.output
        assert "Some required dependencies are missing" in result.output
