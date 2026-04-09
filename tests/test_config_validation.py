"""Tests for config validation: _validate_from_format, _validate_pandoc_variable."""

from pathlib import Path

import pytest
from conftest import VALID_DATA, write_config
from hypothesis import given
from hypothesis import strategies as st

from obsidian_export.config import (
    _validate_from_format,
    _validate_pandoc_variable,
    load_config,
)
from obsidian_export.exceptions import ConfigValueError

# ── _validate_from_format ────────────────────────────────────────────────


class TestValidateFromFormat:
    def test_default_format_accepted(self) -> None:
        _validate_from_format("gfm-tex_math_dollars+footnotes")

    def test_plain_base_format_accepted(self) -> None:
        _validate_from_format("gfm")
        _validate_from_format("markdown")
        _validate_from_format("commonmark")
        _validate_from_format("commonmark_x")

    def test_multiple_extensions_accepted(self) -> None:
        _validate_from_format("gfm+footnotes-smart+pipe_tables")

    def test_unsupported_base_format_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Unsupported pandoc base format"):
            _validate_from_format("html")

    def test_dangerous_extension_raw_html_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Dangerous pandoc extension.*raw_html"):
            _validate_from_format("gfm+raw_html")

    def test_dangerous_extension_raw_attribute_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Dangerous pandoc extension.*raw_attribute"):
            _validate_from_format("markdown+raw_attribute")

    def test_disabling_dangerous_extension_accepted(self) -> None:
        _validate_from_format("gfm-raw_html")

    def test_malformed_extension_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Malformed pandoc extension"):
            _validate_from_format("gfm+123bad")

    @given(base=st.sampled_from(["gfm", "markdown", "commonmark", "commonmark_x"]))
    def test_safe_base_formats_always_accepted(self, base: str) -> None:
        _validate_from_format(base)


class TestValidateFromFormatIntegration:
    """Verify that load_config rejects unsafe from_format values."""

    def test_load_config_rejects_raw_html(self, tmp_path: Path) -> None:
        data = dict(VALID_DATA)
        data["pandoc"] = {"from_format": "gfm+raw_html+footnotes"}
        cfg = write_config(tmp_path, data)
        with pytest.raises(ConfigValueError, match="raw_html"):
            load_config(cfg)

    def test_load_config_rejects_unsupported_format(self, tmp_path: Path) -> None:
        data = dict(VALID_DATA)
        data["pandoc"] = {"from_format": "rst"}
        cfg = write_config(tmp_path, data)
        with pytest.raises(ConfigValueError, match="Unsupported pandoc base format"):
            load_config(cfg)


# ── _validate_pandoc_variable ────────────────────────────────────────────


class TestValidatePandocVariable:
    def test_safe_geometry_accepted(self) -> None:
        _validate_pandoc_variable("geometry", "a4paper,margin=25mm")

    def test_safe_fontsize_accepted(self) -> None:
        _validate_pandoc_variable("fontsize", "10pt")

    def test_safe_color_accepted(self) -> None:
        _validate_pandoc_variable("linkcolor", "NavyBlue")

    def test_empty_string_accepted(self) -> None:
        _validate_pandoc_variable("linkcolor", "")

    def test_shell_metachar_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Invalid characters"):
            _validate_pandoc_variable("geometry", "a4paper;rm -rf /")

    def test_backtick_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Invalid characters"):
            _validate_pandoc_variable("fontsize", "`malicious`")

    def test_braces_rejected(self) -> None:
        with pytest.raises(ConfigValueError, match="Invalid characters"):
            _validate_pandoc_variable("geometry", "a4paper{evil}")

    @given(value=st.from_regex(r"^[a-zA-Z0-9,=._\- ]+$", fullmatch=True))
    def test_safe_values_always_accepted(self, value: str) -> None:
        _validate_pandoc_variable("test_field", value)

    @given(
        value=st.text(
            alphabet=st.sampled_from(list(";|&`${}()[]!@#%^*<>?'\"\\\n\t")),
            min_size=1,
            max_size=5,
        )
    )
    def test_dangerous_chars_always_rejected(self, value: str) -> None:
        with pytest.raises(ConfigValueError):
            _validate_pandoc_variable("test_field", value)


class TestValidatePandocVariableIntegration:
    """Verify that load_config rejects unsafe style variable values."""

    def test_load_config_rejects_malicious_geometry(self, tmp_path: Path) -> None:
        partial = {"style": {"geometry": "a4paper;$(evil)"}}
        cfg = write_config(tmp_path, partial)
        with pytest.raises(ConfigValueError, match="geometry"):
            load_config(cfg)

    def test_load_config_rejects_malicious_code_fontsize(self, tmp_path: Path) -> None:
        partial = {"style": {"code_fontsize": r"small}\input{/etc/passwd}\ignorespaces{"}}
        cfg = write_config(tmp_path, partial)
        with pytest.raises(ConfigValueError, match="code_fontsize"):
            load_config(cfg)

    def test_load_config_rejects_malicious_table_fontsize(self, tmp_path: Path) -> None:
        partial = {"style": {"table_fontsize": r"small}\input{/etc/passwd}\ignorespaces{"}}
        cfg = write_config(tmp_path, partial)
        with pytest.raises(ConfigValueError, match="table_fontsize"):
            load_config(cfg)

    def test_load_config_accepts_valid_code_fontsize(self, tmp_path: Path) -> None:
        partial = {"style": {"code_fontsize": "footnotesize"}}
        cfg = write_config(tmp_path, partial)
        result = load_config(cfg)
        assert result.style.code_fontsize == "footnotesize"

    def test_load_config_accepts_valid_table_fontsize(self, tmp_path: Path) -> None:
        partial = {"style": {"table_fontsize": "small"}}
        cfg = write_config(tmp_path, partial)
        result = load_config(cfg)
        assert result.style.table_fontsize == "small"
