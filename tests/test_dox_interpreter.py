"""Tests for the DOX interpreter system-prompt extension and scaffold template.

Split into:
- TestDoxInterpreterStructure: structural checks (plugin venv)
- TestDoxInterpreterIsolated: mock-based extension dispatch (plugin venv)
- TestDoxInterpreterRuntime: real framework dispatch (A0 runtime only)
"""

from __future__ import annotations

import asyncio
import hashlib
import importlib
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

PLUGIN_DIR = Path(__file__).resolve().parents[1]
SYSTEM_PROMPT_DIR = PLUGIN_DIR / "extensions" / "python" / "system_prompt"
EXT_DIR = str(SYSTEM_PROMPT_DIR)
PROMPT_PATH = PLUGIN_DIR / "prompts" / "agent.system.dox_interpreter.md"
TEMPLATE_PATH = PLUGIN_DIR / "templates" / "dox" / "AGENTS.md"
SOURCE_DOX_PATH = Path("/a0/usr/projects/a0_agent_skills/source_dox/_AGENTS.md")


# ---------------------------------------------------------------------------
# Structural tests (plugin venv, no framework deps)
# ---------------------------------------------------------------------------


class TestDoxInterpreterStructure:
    """Validate shipped DOX interpreter assets."""

    def test_system_prompt_extension_exists(self):
        assert (SYSTEM_PROMPT_DIR / "_10a_dox_interpreter.py").is_file()

    def test_interpreter_prompt_exists_and_nonempty(self):
        assert PROMPT_PATH.is_file()
        assert PROMPT_PATH.read_text(encoding="utf-8").strip()

    def test_interpreter_prompt_contains_core_rules(self):
        content = PROMPT_PATH.read_text(encoding="utf-8")
        assert "Child `AGENTS.md` files are **not** auto-injected" in content
        assert "read the applicable `AGENTS.md` chain" in content
        assert "Refresh affected Child DOX Index entries" in content
        assert "canonical DOX scaffold shipped with this plugin" in content

    def test_canonical_template_exists_and_nonempty(self):
        assert TEMPLATE_PATH.is_file()
        assert TEMPLATE_PATH.read_text(encoding="utf-8").strip()

    def test_canonical_template_matches_source_dox(self):
        if not SOURCE_DOX_PATH.is_file():
            pytest.skip("source_dox AGENTS.md not available")

        shipped_hash = hashlib.sha256(TEMPLATE_PATH.read_bytes()).hexdigest()
        source_hash = hashlib.sha256(SOURCE_DOX_PATH.read_bytes()).hexdigest()
        assert shipped_hash == source_hash


# ---------------------------------------------------------------------------
# Isolated mock tests (plugin venv, mocked framework)
# ---------------------------------------------------------------------------


def _import_extension():
    """Import the extension module with mocked framework dependencies."""

    class MockExtension:
        def __init__(self):
            self.agent = None

    mock_ext = MagicMock()
    mock_ext.Extension = MockExtension

    with patch.dict(sys.modules, {
        "helpers": MagicMock(),
        "helpers.extension": mock_ext,
        "agent": MagicMock(),
    }):
        if "_10a_dox_interpreter" in sys.modules:
            del sys.modules["_10a_dox_interpreter"]
        sys.path.insert(0, EXT_DIR)
        try:
            mod = importlib.import_module("_10a_dox_interpreter")
            return mod
        finally:
            if EXT_DIR in sys.path:
                sys.path.remove(EXT_DIR)


class TestDoxInterpreterIsolated:
    """Mock-based extension dispatch tests (no framework deps)."""

    def test_agent_none_silent_return(self):
        """If self.agent is None, execute() returns silently."""
        mod = _import_extension()
        ext = mod.DoxInterpreter()
        ext.agent = None
        # Should not raise
        asyncio.run(ext.execute(system_prompt=[]))

    def test_appends_prompt_when_agent_present(self):
        """When agent exists and read_prompt returns content, it is appended."""
        mod = _import_extension()
        ext = mod.DoxInterpreter()
        ext.agent = MagicMock()
        ext.agent.read_prompt.return_value = "DOX INTERPRETER PROMPT"

        system_prompt = []
        asyncio.run(ext.execute(system_prompt=system_prompt))

        ext.agent.read_prompt.assert_called_once_with("agent.system.dox_interpreter.md")
        assert system_prompt == ["DOX INTERPRETER PROMPT"]

    def test_no_append_when_prompt_empty(self):
        """When read_prompt returns empty/falsy, nothing is appended."""
        mod = _import_extension()
        ext = mod.DoxInterpreter()
        ext.agent = MagicMock()
        ext.agent.read_prompt.return_value = ""

        system_prompt = []
        asyncio.run(ext.execute(system_prompt=system_prompt))

        assert system_prompt == []


# ---------------------------------------------------------------------------
# Runtime integration tests (A0 runtime only)
# ---------------------------------------------------------------------------

A0_ROOT = Path("/a0")

if str(A0_ROOT) not in sys.path:
    sys.path.insert(0, str(A0_ROOT))


def _clear_runtime_caches():
    from helpers import cache

    for area in ("*(plugins)*", "*(extensions)*", "*(subagent)*"):
        try:
            cache.clear(area)
        except Exception:
            pass


@pytest.fixture(autouse=True)
def clear_caches():
    # Only clear caches if framework helpers are importable
    try:
        _clear_runtime_caches()
    except ImportError:
        pass
    yield
    try:
        _clear_runtime_caches()
    except ImportError:
        pass


class FakeContext:
    id = "runtime-test"

    def __init__(self):
        self.log = SimpleNamespace(logs=[])

    def get_data(self, key, default=None):
        return default


class FakeAgent:
    def __init__(self):
        self.agent_name = "agent0"
        self.number = 0
        self.config = SimpleNamespace(profile="agent0")
        self.data = {}
        self.context = FakeContext()

    def read_prompt(self, name, **kwargs):
        if name == "agent.system.dox_interpreter.md":
            return "DOX INTERPRETER PROMPT"
        return ""


def _can_import_langchain_core():
    """Check if langchain_core is available (A0 runtime venv only)."""
    try:
        import langchain_core  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.mark.runtime_integration
@pytest.mark.skipif(not _can_import_langchain_core(), reason="langchain_core not available")
def test_system_prompt_extension_dispatch_appends_dox_interpreter(monkeypatch):
    from helpers import extension, subagents

    monkeypatch.setattr(
        subagents,
        "get_paths",
        lambda agent, *parts: [str(SYSTEM_PROMPT_DIR)] if parts[-1] == "system_prompt" else [],
    )

    classes = extension._get_extension_classes("system_prompt", agent=None)
    module_names = {cls.__module__.split(".")[-1] for cls in classes}
    assert "_10a_dox_interpreter" in module_names

    agent = FakeAgent()
    system_prompt = []
    asyncio.run(
        extension.call_extensions_async(
            "system_prompt",
            agent=agent,
            system_prompt=system_prompt,
            loop_data=SimpleNamespace(),
        )
    )

    assert system_prompt == ["DOX INTERPRETER PROMPT"]
