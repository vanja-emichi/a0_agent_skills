"""
Tests verifying two bug fixes:
  1. Telemetry defaults to ENABLED (not disabled)
  2. hooks.py has proper documentation explaining why stubs are empty

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_telemetry_default_and_hooks.py -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import asyncio
import yaml
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from conftest import _make_extension, PLUGIN_ROOT


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    return asyncio.run(coro)


# ===========================================================================
# BUG FIX 1: Telemetry defaults to ON
# ===========================================================================

def test_telemetry_default_config_says_enabled():
    """default_config.yaml MUST have telemetry_enabled: true."""
    config_path = PLUGIN_ROOT / "default_config.yaml"
    assert config_path.exists(), "default_config.yaml must exist"
    cfg = yaml.safe_load(config_path.read_text())
    assert cfg.get("telemetry_enabled") is True, (
        f"telemetry_enabled must default to true, got {cfg.get('telemetry_enabled')}"
    )


def test_telemetry_code_default_is_true():
    """When no config exists, telemetry MUST still fire (default True)."""
    ext, plugins_mock, agent = _make_extension(config={})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write, \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
             return_value="/tmp/test.jsonl",
         ):
        _run(ext.execute(tool_name="skills_tool"))
        # With default True and no config, telemetry SHOULD attempt to write
        mock_write.assert_called_once()


def test_telemetry_explicit_disable_respected():
    """When user sets telemetry_enabled: false, it MUST be respected."""
    ext, plugins_mock, agent = _make_extension(config={"telemetry_enabled": False})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write:
        _run(ext.execute(tool_name="skills_tool"))
        mock_write.assert_not_called()


def test_telemetry_string_false_disables():
    """When user writes telemetry_enabled: "false" (YAML quoted string), it MUST disable telemetry."""
    ext, plugins_mock, agent = _make_extension(config={"telemetry_enabled": "false"})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write:
        _run(ext.execute(tool_name="skills_tool"))
        mock_write.assert_not_called()


def test_telemetry_string_true_enables():
    """When telemetry_enabled is string 'true', telemetry MUST still fire."""
    ext, plugins_mock, agent = _make_extension(config={"telemetry_enabled": "true"})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write, \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
             return_value="/tmp/test.jsonl",
         ):
        _run(ext.execute(tool_name="skills_tool"))
        mock_write.assert_called_once()


def test_telemetry_docstring_says_enabled():
    """The telemetry source docstring MUST reflect default enabled."""
    import importlib
    mod_path = PLUGIN_ROOT / "extensions" / "python" / "tool_execute_after" / "_05_skill_telemetry.py"
    content = mod_path.read_text()
    assert "telemetry_enabled: true" in content, (
        "Docstring must say telemetry_enabled: true"
    )
    assert "telemetry_enabled: false" not in content, (
        "Default should be true, not false"
    )


# ===========================================================================
# BUG FIX 2: hooks.py has documentation
# ===========================================================================

def test_hooks_dot_py_exists():
    """hooks.py MUST exist in the plugin root."""
    hooks_path = PLUGIN_ROOT / "hooks.py"
    assert hooks_path.exists(), "hooks.py must exist"


def test_hooks_dot_py_has_module_docstring():
    """hooks.py MUST have a module docstring explaining why stubs are empty."""
    hooks_path = PLUGIN_ROOT / "hooks.py"
    content = hooks_path.read_text()

    # Must have a module docstring
    assert content.strip().startswith('"""'), (
        "hooks.py must have a module docstring"
    )

    # Must explain the routing moved
    assert "system_prompt" in content, (
        "hooks.py docstring must mention system_prompt extension"
    )
    assert "_15_agent_skills_routing" in content, (
        "hooks.py docstring must reference the routing extension file"
    )

    # Must explain WHY stubs are empty
    assert "promptinclude" in content.lower() or "project is active" in content.lower(), (
        "hooks.py docstring must explain why promptinclude approach was abandoned"
    )


def test_hooks_dot_py_has_three_functions():
    """hooks.py MUST define install(), uninstall(), and pre_update()."""
    hooks_path = PLUGIN_ROOT / "hooks.py"
    content = hooks_path.read_text()

    for func in ["install", "uninstall", "pre_update"]:
        assert f"def {func}" in content, (
            f"hooks.py must define {func}()"
        )


def test_hooks_dot_py_stubs_are_pass():
    """All three hook functions MUST be pass stubs (no side effects)."""
    hooks_path = PLUGIN_ROOT / "hooks.py"
    content = hooks_path.read_text()

    # Count 'pass' statements — should have at least 3 (one per function)
    pass_count = content.count("    pass")
    assert pass_count >= 3, (
        f"Expected at least 3 'pass' statements (one per hook), found {pass_count}"
    )


# ===========================================================================
# #5: String coercion completeness
# ===========================================================================

def test_telemetry_string_1_enables():
    """When telemetry_enabled is string '1', telemetry MUST still fire."""
    ext, plugins_mock, agent = _make_extension(config={"telemetry_enabled": "1"})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write, \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
             return_value="/tmp/test.jsonl",
         ):
        _run(ext.execute(tool_name="skills_tool"))
        mock_write.assert_called_once()


def test_telemetry_string_yes_enables():
    """When telemetry_enabled is string 'yes', telemetry MUST still fire."""
    ext, plugins_mock, agent = _make_extension(config={"telemetry_enabled": "yes"})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write, \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
             return_value="/tmp/test.jsonl",
         ):
        _run(ext.execute(tool_name="skills_tool"))
        mock_write.assert_called_once()


@pytest.mark.parametrize("value", ["TRUE", "True", "tRuE"])
def test_telemetry_string_case_insensitive_enables(value):
    """Case-insensitive 'true' variants MUST enable telemetry."""
    ext, plugins_mock, agent = _make_extension(config={"telemetry_enabled": value})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write, \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
             return_value="/tmp/test.jsonl",
         ):
        _run(ext.execute(tool_name="skills_tool"))
        mock_write.assert_called_once()


@pytest.mark.parametrize("value", ["False", "FALSE", "fAlSe", "NO", "No", "no"])
def test_telemetry_string_case_insensitive_disables(value):
    """Case-insensitive disabling strings MUST disable telemetry."""
    ext, plugins_mock, agent = _make_extension(config={"telemetry_enabled": value})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write:
        _run(ext.execute(tool_name="skills_tool"))
        mock_write.assert_not_called()


def test_telemetry_integer_one_enables():
    """When telemetry_enabled is int 1 (truthy), telemetry MUST fire."""
    ext, plugins_mock, agent = _make_extension(config={"telemetry_enabled": 1})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write, \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._resolve_log_file",
             return_value="/tmp/test.jsonl",
         ):
        _run(ext.execute(tool_name="skills_tool"))
        mock_write.assert_called_once()


def test_telemetry_integer_zero_disables():
    """When telemetry_enabled is int 0 (falsy), telemetry MUST NOT fire."""
    ext, plugins_mock, agent = _make_extension(config={"telemetry_enabled": 0})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write:
        _run(ext.execute(tool_name="skills_tool"))
        mock_write.assert_not_called()
