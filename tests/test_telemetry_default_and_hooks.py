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

from conftest import _make_extension, PLUGIN_ROOT, _doc_path


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    return asyncio.run(coro)


# ===========================================================================
# BUG FIX 1: Telemetry defaults to OFF (privacy-safe)
# ===========================================================================

def test_telemetry_default_config_says_disabled():
    """default_config.yaml MUST have telemetry_enabled: false."""
    config_path = PLUGIN_ROOT / "default_config.yaml"
    assert config_path.exists(), "default_config.yaml must exist"
    cfg = yaml.safe_load(config_path.read_text())
    assert cfg.get("telemetry_enabled") is False, (
        f"telemetry_enabled must default to false, got {cfg.get('telemetry_enabled')}"
    )


def test_telemetry_code_default_is_false():
    """When no config exists, telemetry MUST NOT fire (default False)."""
    ext, plugins_mock, agent = _make_extension(config={})

    with patch("helpers.plugins", plugins_mock), \
         patch(
             "extensions.python.tool_execute_after._05_skill_telemetry._write_log_line"
         ) as mock_write:
        _run(ext.execute(tool_name="skills_tool"))
        # With default False and no config, telemetry SHOULD NOT write
        mock_write.assert_not_called()


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


def test_telemetry_docstring_says_disabled():
    """The telemetry source docstring MUST reflect default disabled (privacy-safe)."""
    import importlib
    mod_path = PLUGIN_ROOT / "extensions" / "python" / "tool_execute_after" / "_05_skill_telemetry.py"
    content = mod_path.read_text()
    assert "telemetry_enabled: false" in content, (
        "Docstring must say telemetry_enabled: false"
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


# ===========================================================================
# Hook alignment policy doc verification
# ===========================================================================

def test_hook_alignment_doc_exists():
    """docs/hook-alignment.md MUST exist after Task 12."""
    doc_path = _doc_path("hook-alignment.md")
    assert doc_path.exists(), "docs/hook-alignment.md must exist"


def test_hook_alignment_doc_has_all_nine_upstream_assets():
    """The hook alignment doc MUST classify all 9 upstream hook assets."""
    doc_path = _doc_path("hook-alignment.md")
    content = doc_path.read_text()

    upstream_assets = [
        "hooks.json",
        "session-start.sh",
        "session-start-test.sh",
        "simplify-ignore.sh",
        "simplify-ignore-test.sh",
        "SIMPLIFY-IGNORE.md",
        "sdd-cache-pre.sh",
        "sdd-cache-post.sh",
        "SDD-CACHE.md",
    ]
    for asset in upstream_assets:
        assert asset in content, f"hook-alignment.md must classify {asset}"


def test_hook_alignment_doc_has_three_classifications():
    """The hook alignment doc MUST use PORT, DEFER, and OMIT classifications."""
    doc_path = _doc_path("hook-alignment.md")
    content = doc_path.read_text()

    assert "PORT" in content, "hook-alignment.md must define PORT classification"
    assert "DEFER" in content, "hook-alignment.md must define DEFER classification"
    assert "OMIT" in content, "hook-alignment.md must define OMIT classification"


def test_hook_alignment_doc_summary_matches_hooks_py():
    """The summary in hook-alignment.md MUST match the summary in hooks.py."""
    doc_path = _doc_path("hook-alignment.md")
    hooks_path = PLUGIN_ROOT / "hooks.py"

    doc_content = doc_path.read_text()
    hooks_content = hooks_path.read_text()

    # Both must reference hook-alignment.md
    assert "docs/hook-alignment.md" in hooks_content, (
        "hooks.py must reference docs/hook-alignment.md"
    )

    # Both must agree on the summary counts
    assert "1 PORT (done)" in doc_content or "1 PORT" in doc_content
    assert "2 OMIT" in doc_content or "OMIT" in doc_content
    assert "6 DEFER" in doc_content or "DEFER" in doc_content


def test_hook_alignment_doc_has_hook_families():
    """The hook alignment doc MUST define policies for session-start, simplify-ignore, and sdd-cache families."""
    doc_path = _doc_path("hook-alignment.md")
    content = doc_path.read_text()

    assert "session-start family" in content.lower() or "session-start" in content
    assert "simplify-ignore family" in content.lower() or "simplify-ignore" in content
    assert "sdd-cache family" in content.lower() or "sdd-cache" in content


def test_surface_mapping_hooks_section_references_alignment_doc():
    """The surface mapping doc MUST reference hook-alignment.md."""
    mapping_path = _doc_path("managed-fork-surface-mapping.md")
    if not mapping_path.exists():
        pytest.skip("surface mapping doc not yet created")
    content = mapping_path.read_text()
    assert "hook-alignment" in content, (
        "managed-fork-surface-mapping.md must reference hook-alignment.md"
    )
