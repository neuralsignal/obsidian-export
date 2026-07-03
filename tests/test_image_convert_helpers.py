"""Tests for extracted helpers in image_convert module."""

import re
import tempfile
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from obsidian_export.exceptions import ObsidianExportError, PathTraversalError
from obsidian_export.pipeline.image_convert import (
    ImageConversionSpec,
    _is_url,
    _replace_image_match,
    _resolve_image_path,
)

_IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


class _TestImageError(ObsidianExportError):
    pass


def _noop_convert(src: Path, dst: Path) -> None:
    dst.write_bytes(b"converted")


def _noop_pre_filter(_m: re.Match[str]) -> None:
    return None


def _make_spec(
    pre_filter=_noop_pre_filter,
    convert_fn=_noop_convert,
) -> ImageConversionSpec:
    return ImageConversionSpec(
        pattern=_IMG_RE,
        convert_fn=convert_fn,
        out_prefix="test_",
        out_ext=".out",
        label="Test",
        not_found_error=_TestImageError,
        pre_filter=pre_filter,
    )


# ── _is_url ──────────────────────────────────────────────────────────────────


class TestIsUrl:
    def test_https_url(self) -> None:
        assert _is_url("https://example.com/image.png")

    def test_http_url(self) -> None:
        assert _is_url("http://example.com/image.png")

    def test_relative_path(self) -> None:
        assert not _is_url("images/photo.png")

    def test_absolute_path(self) -> None:
        assert not _is_url("/home/user/photo.png")

    @given(path=st.text(min_size=0, max_size=50))
    def test_only_http_prefixes_match(self, path: str) -> None:
        result = _is_url(path)
        if result:
            assert path.startswith(("http://", "https://"))


# ── _resolve_image_path ──────────────────────────────────────────────────────


class TestResolveImagePath:
    def test_absolute_path_returned_as_is(self) -> None:
        result = _resolve_image_path("/tmp/img.png", resource_path=None, label="Test")
        assert result == Path("/tmp/img.png")

    def test_relative_path_resolved_against_resource_path(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            resource = Path(workdir)
            result = _resolve_image_path("sub/img.png", resource_path=resource, label="Test")
            assert result == resource / "sub/img.png"

    def test_relative_path_without_resource_path_stays_relative(self) -> None:
        result = _resolve_image_path("img.png", resource_path=None, label="Test")
        assert result == Path("img.png")

    def test_path_outside_root_raises(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            vault = Path(workdir) / "vault"
            vault.mkdir()
            with pytest.raises(PathTraversalError):
                _resolve_image_path("../outside.png", resource_path=vault, label="Test")

    def test_path_inside_root_succeeds(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            vault = Path(workdir)
            (vault / "img.png").touch()
            result = _resolve_image_path("img.png", resource_path=vault, label="Test")
            assert result == vault / "img.png"


# ── _replace_image_match ─────────────────────────────────────────────────────


def _match_from(text: str) -> re.Match[str]:
    m = _IMG_RE.search(text)
    assert m is not None
    return m


class TestReplaceImageMatch:
    def test_url_returns_original(self) -> None:
        text = "![alt](https://example.com/pic.png)"
        m = _match_from(text)
        result = _replace_image_match(m, None, Path("/tmp"), _make_spec(), [0])
        assert result == text

    def test_pre_filter_short_circuits(self) -> None:
        def pre_filter(_m: re.Match[str]) -> str:
            return "FILTERED"

        text = "![alt](local.png)"
        m = _match_from(text)
        result = _replace_image_match(m, None, Path("/tmp"), _make_spec(pre_filter=pre_filter), [0])
        assert result == "FILTERED"

    def test_missing_file_raises(self) -> None:
        text = "![alt](/tmp/nonexistent_xyz_999.png)"
        m = _match_from(text)
        with pytest.raises(_TestImageError, match="file not found"):
            _replace_image_match(m, None, Path("/tmp"), _make_spec(), [0])

    def test_successful_conversion(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir_path = Path(workdir)
            img = workdir_path / "photo.png"
            img.write_bytes(b"fake image")
            tmpdir = workdir_path / "out"
            tmpdir.mkdir()

            text = f"![photo]({img})"
            m = _match_from(text)
            counter: list[int] = [0]
            result = _replace_image_match(m, None, tmpdir, _make_spec(), counter)

            assert counter[0] == 1
            assert "test_1.out" in result
            assert (tmpdir / "test_1.out").exists()

    def test_counter_increments(self) -> None:
        with tempfile.TemporaryDirectory() as workdir:
            workdir_path = Path(workdir)
            img = workdir_path / "photo.png"
            img.write_bytes(b"fake image")
            tmpdir = workdir_path / "out"
            tmpdir.mkdir()

            text = f"![photo]({img})"
            m = _match_from(text)
            counter: list[int] = [5]
            _replace_image_match(m, None, tmpdir, _make_spec(), counter)
            assert counter[0] == 6

    def test_convert_fn_called_with_correct_paths(self) -> None:
        called_with: list[tuple[Path, Path]] = []

        def tracking_convert(src: Path, dst: Path) -> None:
            called_with.append((src, dst))
            dst.write_bytes(b"converted")

        with tempfile.TemporaryDirectory() as workdir:
            workdir_path = Path(workdir)
            img = workdir_path / "photo.png"
            img.write_bytes(b"fake image")
            tmpdir = workdir_path / "out"
            tmpdir.mkdir()

            text = f"![photo]({img})"
            m = _match_from(text)
            _replace_image_match(m, None, tmpdir, _make_spec(convert_fn=tracking_convert), [0])

            assert len(called_with) == 1
            assert called_with[0][0] == img
            assert called_with[0][1] == tmpdir / "test_1.out"
