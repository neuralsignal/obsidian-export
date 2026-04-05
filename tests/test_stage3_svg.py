"""Tests for stage3_svg: SVG -> PDF/PNG conversion of image references."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from obsidian_export.exceptions import PathTraversalError, SVGConversionError
from obsidian_export.pipeline.stage3_svg import (
    _IMG_REF_RE,
    convert_svg_images,
    convert_svg_images_to_png,
)

MINIMAL_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">'
    '<circle cx="50" cy="50" r="40" fill="blue"/>'
    "</svg>"
)


def test_no_svg_refs_unchanged():
    text = "# Hello\n\nSome text without any images.\n\n![photo](pic.png)\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = convert_svg_images(text, Path(tmpdir), resource_path=None)
    assert result == text


def test_missing_svg_file_raises():
    text = "![diagram](/tmp/nonexistent_abc123.svg)\n"
    with tempfile.TemporaryDirectory() as tmpdir, pytest.raises(SVGConversionError, match="SVG file not found"):
        convert_svg_images(text, Path(tmpdir), resource_path=None)


def test_url_svg_unchanged():
    text = "![logo](https://example.com/foo.svg)\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = convert_svg_images(text, Path(tmpdir), resource_path=None)
    assert result == text


def test_http_url_svg_unchanged():
    text = "![logo](http://example.com/bar.svg)\n"
    with tempfile.TemporaryDirectory() as tmpdir:
        result = convert_svg_images(text, Path(tmpdir), resource_path=None)
    assert result == text


def test_svg_ref_replaced_when_file_exists():
    with tempfile.TemporaryDirectory() as workdir:
        workdir = Path(workdir)
        svg_file = workdir / "figure.svg"
        svg_file.write_text(MINIMAL_SVG)

        tmpdir = workdir / "out"
        tmpdir.mkdir()

        text = f"![my diagram]({svg_file})\n"
        result = convert_svg_images(text, tmpdir, resource_path=None)

        assert "figure.svg" not in result
        assert "svg_1.pdf" in result

        # Verify the PDF file was actually created
        pdf_path = tmpdir / "svg_1.pdf"
        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 0


def test_multiple_svgs_converted():
    with tempfile.TemporaryDirectory() as workdir:
        workdir = Path(workdir)

        svg_a = workdir / "a.svg"
        svg_b = workdir / "b.svg"
        svg_a.write_text(MINIMAL_SVG)
        svg_b.write_text(MINIMAL_SVG)

        tmpdir = workdir / "out"
        tmpdir.mkdir()

        text = f"![first]({svg_a})\n\nSome text.\n\n![second]({svg_b})\n"
        result = convert_svg_images(text, tmpdir, resource_path=None)

        assert "svg_1.pdf" in result
        assert "svg_2.pdf" in result
        assert (tmpdir / "svg_1.pdf").exists()
        assert (tmpdir / "svg_2.pdf").exists()


class TestPathTraversal:
    def test_relative_path_escaping_vault_raises(self):
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            outside = workdir / "outside.svg"
            outside.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = "![escape](../outside.svg)\n"
            with pytest.raises(PathTraversalError, match="SVG path escapes document root"):
                convert_svg_images(text, tmpdir, resource_path=vault)

    def test_absolute_path_outside_vault_raises(self):
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            outside = workdir / "outside.svg"
            outside.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![escape]({outside})\n"
            with pytest.raises(PathTraversalError, match="SVG path escapes document root"):
                convert_svg_images(text, tmpdir, resource_path=vault)

    def test_path_within_vault_allowed(self):
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            svg_file = vault / "figure.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = "![ok](figure.svg)\n"
            result = convert_svg_images(text, tmpdir, resource_path=vault)
            assert "svg_1.pdf" in result

    def test_png_path_traversal_raises(self):
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            vault = workdir / "vault"
            vault.mkdir()
            outside = workdir / "outside.svg"
            outside.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = "![escape](../outside.svg)\n"
            with pytest.raises(PathTraversalError, match="SVG path escapes document root"):
                convert_svg_images_to_png(text, tmpdir, resource_path=vault)


class TestConvertSvgImagesToPng:
    def test_no_svg_refs_unchanged(self):
        text = "# Hello\n\nSome text without any images.\n\n![photo](pic.png)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = convert_svg_images_to_png(text, Path(tmpdir), resource_path=None)
        assert result == text

    def test_missing_svg_file_raises(self):
        text = "![diagram](/tmp/nonexistent_abc123.svg)\n"
        with tempfile.TemporaryDirectory() as tmpdir, pytest.raises(SVGConversionError, match="SVG file not found"):
            convert_svg_images_to_png(text, Path(tmpdir), resource_path=None)

    def test_url_svg_unchanged(self):
        text = "![logo](https://example.com/foo.svg)\n"
        with tempfile.TemporaryDirectory() as tmpdir:
            result = convert_svg_images_to_png(text, Path(tmpdir), resource_path=None)
        assert result == text

    def test_svg_ref_replaced_with_png(self):
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            svg_file = workdir / "figure.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            text = f"![my diagram]({svg_file})\n"
            result = convert_svg_images_to_png(text, tmpdir, resource_path=None)

            assert "figure.svg" not in result
            assert "svg_1.png" in result

            png_path = tmpdir / "svg_1.png"
            assert png_path.exists()
            assert png_path.stat().st_size > 0


class TestSubprocessErrors:
    """Regression tests for subprocess error handling in rsvg-convert calls."""

    def test_called_process_error_raises_svg_conversion_error(self):
        """CalledProcessError from rsvg-convert is wrapped in SVGConversionError."""
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            svg_file = workdir / "bad.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            error = subprocess.CalledProcessError(
                returncode=1,
                cmd=["rsvg-convert"],
                stderr=b"conversion failed",
            )
            text = f"![diagram]({svg_file})\n"
            with (
                patch("obsidian_export.pipeline.stage3_svg.subprocess.run", side_effect=error),
                pytest.raises(SVGConversionError, match=r"rsvg-convert failed.*exit 1.*conversion failed"),
            ):
                convert_svg_images(text, tmpdir, resource_path=None)

    def test_called_process_error_no_stderr(self):
        """CalledProcessError with no stderr still produces a useful message."""
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            svg_file = workdir / "bad.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            error = subprocess.CalledProcessError(
                returncode=2,
                cmd=["rsvg-convert"],
                stderr=None,
            )
            text = f"![diagram]({svg_file})\n"
            with (
                patch("obsidian_export.pipeline.stage3_svg.subprocess.run", side_effect=error),
                pytest.raises(SVGConversionError, match=r"rsvg-convert failed.*\(no stderr\)"),
            ):
                convert_svg_images(text, tmpdir, resource_path=None)

    def test_called_process_error_chains_original(self):
        """SVGConversionError chains the original CalledProcessError via __cause__."""
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            svg_file = workdir / "bad.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            error = subprocess.CalledProcessError(
                returncode=1,
                cmd=["rsvg-convert"],
                stderr=b"oops",
            )
            text = f"![diagram]({svg_file})\n"
            with (
                patch("obsidian_export.pipeline.stage3_svg.subprocess.run", side_effect=error),
                pytest.raises(SVGConversionError) as exc_info,
            ):
                convert_svg_images(text, tmpdir, resource_path=None)
            assert exc_info.value.__cause__ is error

    def test_file_not_found_error_raises_svg_conversion_error(self):
        """FileNotFoundError (missing rsvg-convert) is wrapped in SVGConversionError."""
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            svg_file = workdir / "figure.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            error = FileNotFoundError("No such file or directory: 'rsvg-convert'")
            text = f"![diagram]({svg_file})\n"
            with (
                patch("obsidian_export.pipeline.stage3_svg.subprocess.run", side_effect=error),
                pytest.raises(SVGConversionError, match="rsvg-convert not found"),
            ):
                convert_svg_images(text, tmpdir, resource_path=None)

    def test_file_not_found_error_chains_original(self):
        """SVGConversionError chains the original FileNotFoundError via __cause__."""
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            svg_file = workdir / "figure.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            error = FileNotFoundError("No such file or directory: 'rsvg-convert'")
            text = f"![diagram]({svg_file})\n"
            with (
                patch("obsidian_export.pipeline.stage3_svg.subprocess.run", side_effect=error),
                pytest.raises(SVGConversionError) as exc_info,
            ):
                convert_svg_images(text, tmpdir, resource_path=None)
            assert exc_info.value.__cause__ is error

    def test_png_called_process_error_raises_svg_conversion_error(self):
        """CalledProcessError is also handled in the PNG conversion path."""
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            svg_file = workdir / "bad.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            error = subprocess.CalledProcessError(
                returncode=1,
                cmd=["rsvg-convert"],
                stderr=b"png failed",
            )
            text = f"![diagram]({svg_file})\n"
            with (
                patch("obsidian_export.pipeline.stage3_svg.subprocess.run", side_effect=error),
                pytest.raises(SVGConversionError, match="rsvg-convert failed"),
            ):
                convert_svg_images_to_png(text, tmpdir, resource_path=None)

    def test_png_file_not_found_error_raises_svg_conversion_error(self):
        """FileNotFoundError is also handled in the PNG conversion path."""
        with tempfile.TemporaryDirectory() as workdir:
            workdir = Path(workdir)
            svg_file = workdir / "figure.svg"
            svg_file.write_text(MINIMAL_SVG)

            tmpdir = workdir / "out"
            tmpdir.mkdir()

            error = FileNotFoundError("No such file or directory: 'rsvg-convert'")
            text = f"![diagram]({svg_file})\n"
            with (
                patch("obsidian_export.pipeline.stage3_svg.subprocess.run", side_effect=error),
                pytest.raises(SVGConversionError, match="rsvg-convert not found"),
            ):
                convert_svg_images_to_png(text, tmpdir, resource_path=None)


class TestImgRefRegex:
    """Property-based tests for the _IMG_REF_RE regex pattern."""

    def test_concrete_match(self):
        m = _IMG_REF_RE.search("![alt](path/to/file.svg)")
        assert m is not None
        assert m.group(1) == "alt"
        assert m.group(2) == "path/to/file.svg"

    def test_concrete_no_match_png(self):
        assert _IMG_REF_RE.search("![alt](image.png)") is None

    @given(alt=st.text(alphabet=st.characters(blacklist_characters="]"), min_size=0, max_size=30))
    def test_any_alt_text_matches(self, alt: str):
        """Any alt text (without ']') in an SVG image ref is matched."""
        text = f"![{alt}](diagram.svg)"
        m = _IMG_REF_RE.search(text)
        assert m is not None
        assert m.group(1) == alt
        assert m.group(2) == "diagram.svg"

    @given(
        name=st.from_regex(r"[a-zA-Z0-9_-]+", fullmatch=True).filter(lambda s: len(s) <= 30),
        dirs=st.lists(
            st.from_regex(r"[a-zA-Z0-9_-]+", fullmatch=True).filter(lambda s: len(s) <= 15),
            min_size=0,
            max_size=3,
        ),
    )
    def test_any_local_svg_path_matches(self, name: str, dirs: list[str]) -> None:
        """Any local .svg file path is captured by the regex."""
        path = "/".join([*dirs, f"{name}.svg"])
        text = f"![img]({path})"
        m = _IMG_REF_RE.search(text)
        assert m is not None
        assert m.group(2) == path

    @given(ext=st.sampled_from([".png", ".jpg", ".jpeg", ".gif", ".webp", ".pdf"]))
    def test_non_svg_extensions_do_not_match(self, ext: str) -> None:
        """Non-.svg extensions are not matched by the regex."""
        text = f"![alt](image{ext})"
        assert _IMG_REF_RE.search(text) is None

    @given(
        scheme=st.sampled_from(["http://", "https://"]),
        domain=st.from_regex(r"[a-z]{3,10}\.[a-z]{2,4}", fullmatch=True),
    )
    def test_url_svgs_still_match_regex(self, scheme: str, domain: str) -> None:
        """URLs with .svg are matched by the regex (skipping is done in the function, not the regex)."""
        text = f"![logo]({scheme}{domain}/icon.svg)"
        m = _IMG_REF_RE.search(text)
        assert m is not None

    @given(
        body=st.text(alphabet=st.characters(blacklist_characters="![]()", min_codepoint=32), min_size=0, max_size=100)
    )
    def test_text_without_image_syntax_never_matches(self, body: str) -> None:
        """Plain text without markdown image syntax never triggers the regex."""
        assert _IMG_REF_RE.search(body) is None
