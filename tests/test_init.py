"""Tests for obsidian_export.__init__ — _resolve_style_dir and run()."""

from pathlib import Path
from unittest.mock import patch

import pytest

from obsidian_export import _resolve_style_dir, run
from obsidian_export.config import (
    CalloutColors,
    StyleConfig,
)
from obsidian_export.exceptions import UnsupportedFormatError


def _make_style(
    name: str,
    style_dir: str,
) -> StyleConfig:
    """Build a minimal StyleConfig for testing resolution logic."""
    return StyleConfig(
        name=name,
        geometry="a4paper",
        fontsize="11pt",
        mainfont="serif",
        sansfont="sans",
        monofont="mono",
        linkcolor="blue",
        urlcolor="blue",
        line_spacing=1.0,
        table_fontsize="10pt",
        image_max_height_ratio=0.4,
        url_footnote_threshold=60,
        header_left="",
        header_right="",
        footer_left="",
        footer_center="",
        footer_right="",
        callout_colors=CalloutColors(
            note=(0, 0, 0),
            tip=(0, 0, 0),
            warning=(0, 0, 0),
            danger=(0, 0, 0),
        ),
        unicode_chars=(),
        logo="",
        style_dir=style_dir,
        brand_colors=(),
        heading_styles=(),
        title_style=None,
    )


class TestResolveStyleDirExplicit:
    """Lines 37-40: explicit style_dir that does not exist."""

    def test_existing_style_dir(self, tmp_path: Path) -> None:
        style = _make_style(name="x", style_dir=str(tmp_path))
        assert _resolve_style_dir(style) == tmp_path

    def test_nonexistent_style_dir_raises(self, tmp_path: Path) -> None:
        missing = tmp_path / "no-such-dir"
        style = _make_style(name="x", style_dir=str(missing))
        with pytest.raises(FileNotFoundError, match="Style dir not found"):
            _resolve_style_dir(style)


class TestResolveStyleDirBuiltin:
    """Lines 45-47: built-in style resolution."""

    def test_builtin_style(self) -> None:
        style = _make_style(name="default", style_dir="")
        result = _resolve_style_dir(style)
        expected = Path(__file__).resolve().parent.parent / "obsidian_export" / "assets" / "styles" / "default"
        assert result == expected


class TestResolveStyleDirUserStyles:
    """Lines 50-59: user-styles path, path-as-name fallback, final error."""

    def test_user_styles_dir(self, tmp_path: Path) -> None:
        user_styles = tmp_path / "styles"
        style_subdir = user_styles / "my-theme"
        style_subdir.mkdir(parents=True)

        style = _make_style(name="my-theme", style_dir="")
        with patch("obsidian_export.USER_STYLES_DIR", user_styles):
            assert _resolve_style_dir(style) == style_subdir

    def test_path_as_name_fallback(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        theme_dir = tmp_path / "custom-theme"
        theme_dir.mkdir()

        # Use a relative path so Path(parent) / name doesn't collapse to the
        # absolute path (which would match the builtin check instead).
        monkeypatch.chdir(tmp_path)
        style = _make_style(name="custom-theme", style_dir="")
        with patch("obsidian_export.USER_STYLES_DIR", tmp_path / "no-user-styles"):
            assert _resolve_style_dir(style) == Path("custom-theme")

    def test_unknown_style_raises(self, tmp_path: Path) -> None:
        style = _make_style(name="nonexistent-style-xyz", style_dir="")
        with (
            patch("obsidian_export.USER_STYLES_DIR", tmp_path / "no-user-styles"),
            pytest.raises(FileNotFoundError, match="Style not found"),
        ):
            _resolve_style_dir(style)

    def test_resolve_style_dir_all_paths_fail(self, tmp_path: Path) -> None:
        """Error message names all three checked locations."""
        name = "totally-unknown-style"
        style = _make_style(name=name, style_dir="")
        user_dir = tmp_path / "no-user-styles"
        with (
            patch("obsidian_export.USER_STYLES_DIR", user_dir),
            pytest.raises(FileNotFoundError, match=name) as exc_info,
        ):
            _resolve_style_dir(style)
        msg = str(exc_info.value)
        assert "styles" in msg
        assert str(user_dir / name) in msg
        assert name in msg


class TestRunUnsupportedFormat:
    """Line 77: UnsupportedFormatError for unsupported output_format."""

    def test_unsupported_format_raises(self, tmp_path: Path) -> None:
        dummy_input = tmp_path / "note.md"
        dummy_input.write_text("hello")
        dummy_output = tmp_path / "out.html"

        with pytest.raises(UnsupportedFormatError, match="Unsupported output format"):
            run(
                input_path=dummy_input,
                output_path=dummy_output,
                output_format="html",
                config=None,  # type: ignore[arg-type]  # never reached
            )
