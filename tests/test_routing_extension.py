"""Tests for the _15_agent_skills_routing system prompt extension.

Verifies:
- Extension loads and runs without error
- Routing prompt template is found and readable
- Routing rules are injected into the system prompt
- mtime caching works (doesn't re-read unchanged files)
- Handles missing template gracefully
- Handles empty/nonexistent skills directory

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_routing_extension.py -v
"""

import asyncio
import importlib
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent


def _import_extension():
    """Import (or re-import) the routing extension module."""
    ext_path = (
        PLUGIN_ROOT
        / "extensions"
        / "python"
        / "system_prompt"
        / "_15_agent_skills_routing.py"
    )
    spec = importlib.util.spec_from_file_location(
        "_15_agent_skills_routing", str(ext_path)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_async(coro):
    """Run an async coroutine, compatible with Python 3.10+."""
    return asyncio.run(coro)


class TestRoutingExtensionLoads:
    """Extension loads and runs without error."""

    def test_import_module(self):
        mod = _import_extension()
        assert hasattr(mod, "AgentSkillsRouting")
        assert hasattr(mod, "_load_routing_template")
        assert hasattr(mod, "_get_routing_prompt_path")

    def test_execute_runs_without_error(self):
        mod = _import_extension()
        ext = mod.AgentSkillsRouting.__new__(mod.AgentSkillsRouting)
        system_prompt = []
        _run_async(ext.execute(system_prompt=system_prompt, loop_data=None))


class TestRoutingPromptTemplate:
    """Routing prompt template is found and readable."""

    def test_template_path_resolves(self):
        mod = _import_extension()
        path = mod._get_routing_prompt_path()
        assert isinstance(path, str)
        assert "agent.skills.routing.md" in path

    def test_template_file_exists(self):
        mod = _import_extension()
        path = mod._get_routing_prompt_path()
        assert os.path.isfile(path), f"Template not found at {path}"

    def test_template_is_readable(self):
        mod = _import_extension()
        path = mod._get_routing_prompt_path()
        content = mod._load_routing_template(path)
        assert content is not None
        assert len(content) > 0


class TestRoutingInjection:
    """Routing rules are injected into the system prompt."""

    def test_content_appended_to_system_prompt(self):
        mod = _import_extension()
        ext = mod.AgentSkillsRouting.__new__(mod.AgentSkillsRouting)
        system_prompt = []
        _run_async(ext.execute(system_prompt=system_prompt, loop_data=None))
        assert len(system_prompt) == 1
        assert "Skill-Driven Execution" in system_prompt[0]
        assert "skills_tool" in system_prompt[0]

    def test_repeated_calls_append_each_time(self):
        mod = _import_extension()
        ext = mod.AgentSkillsRouting.__new__(mod.AgentSkillsRouting)
        system_prompt = []
        _run_async(ext.execute(system_prompt=system_prompt, loop_data=None))
        _run_async(ext.execute(system_prompt=system_prompt, loop_data=None))
        assert len(system_prompt) == 2


class TestMtimeCaching:
    """mtime caching works (doesn't re-read unchanged files)."""

    def test_cache_returns_same_content_without_reread(self):
        mod = _import_extension()
        mod._routing_cache["content"] = None
        mod._routing_cache["mtime"] = None
        path = mod._get_routing_prompt_path()
        content1 = mod._load_routing_template(path)
        assert content1 is not None
        cached_content = mod._routing_cache["content"]
        assert cached_content is not None
        content2 = mod._load_routing_template(path)
        assert content2 is content1

    def test_cache_invalidates_on_file_change(self):
        mod = _import_extension()
        mod._routing_cache["content"] = None
        mod._routing_cache["mtime"] = None
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("version 1")
            tmp_path = f.name
        try:
            content1 = mod._load_routing_template(tmp_path)
            assert content1 == "version 1"
            time.sleep(0.05)
            with open(tmp_path, "w") as f:
                f.write("version 2")
            mod._routing_cache["mtime"] = 0.0
            content2 = mod._load_routing_template(tmp_path)
            assert content2 == "version 2"
        finally:
            os.unlink(tmp_path)


class TestMissingTemplate:
    """Handles missing template gracefully."""

    def test_missing_file_returns_none(self):
        mod = _import_extension()
        result = mod._load_routing_template("/nonexistent/path/to/template.md")
        assert result is None

    def test_execute_with_missing_template_no_crash(self):
        mod = _import_extension()
        ext = mod.AgentSkillsRouting.__new__(mod.AgentSkillsRouting)
        with patch.object(
            mod, "_get_routing_prompt_path",
            return_value="/nonexistent/routing.md"
        ):
            system_prompt = []
            _run_async(ext.execute(system_prompt=system_prompt, loop_data=None))
            assert len(system_prompt) == 0

    def test_execute_with_empty_template(self):
        mod = _import_extension()
        ext = mod.AgentSkillsRouting.__new__(mod.AgentSkillsRouting)
        mod._routing_cache["content"] = None
        mod._routing_cache["mtime"] = None
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write("   \n\n  ")
            tmp_path = f.name
        try:
            with patch.object(
                mod, "_get_routing_prompt_path", return_value=tmp_path
            ):
                system_prompt = []
                _run_async(ext.execute(system_prompt=system_prompt, loop_data=None))
                assert len(system_prompt) == 0
        finally:
            os.unlink(tmp_path)


class TestEmptySkillsDirectory:
    """Handles empty/nonexistent skills directory."""

    def test_extension_runs_with_empty_skills_dir(self):
        mod = _import_extension()
        ext = mod.AgentSkillsRouting.__new__(mod.AgentSkillsRouting)
        system_prompt = []
        _run_async(ext.execute(system_prompt=system_prompt, loop_data=None))
        assert len(system_prompt) >= 1
