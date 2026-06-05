"""Runtime integration tests for extension dispatch and plugin hook routing."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

A0_ROOT = Path("/a0")
PLUGIN_DIR = Path(__file__).resolve().parents[1]
EXTENSIONS_DIR = PLUGIN_DIR / "extensions" / "python"

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
    _clear_runtime_caches()
    yield
    _clear_runtime_caches()


class FakeLog:
    def __init__(self):
        self.logs = []

    def log(self, *args, **kwargs):
        self.logs.append((args, kwargs))


class FakeContext:
    id = "runtime-test"

    def __init__(self):
        self.log = FakeLog()

    def get_data(self, key, default=None):
        return default


class FakeAgent:
    def __init__(self):
        self.agent_name = "agent0"
        self.number = 0
        self.config = SimpleNamespace(profile="agent0")
        self.data = {}
        self.context = FakeContext()

    def hist_add_ai_response(self, *args, **kwargs):  # pragma: no cover - guard method
        raise AssertionError("meta-skill extension must not inject history content")


def _extension_paths_for(point: str):
    folder = EXTENSIONS_DIR / point
    return [str(folder)] if folder.is_dir() else []


@pytest.mark.runtime_integration
def test_extension_dispatch_loads_plugin_agent_init_extension(monkeypatch):
    from helpers import extension, subagents

    monkeypatch.setattr(
        subagents,
        "get_paths",
        lambda agent, *parts: _extension_paths_for(parts[-1]),
    )

    agent = FakeAgent()
    assert "loaded_skills" not in agent.data

    extension.call_extensions_sync("agent_init", agent=agent)
    assert agent.data["loaded_skills"] == ["using-agent-skills"]

    extension.call_extensions_sync("agent_init", agent=agent)
    assert agent.data["loaded_skills"] == ["using-agent-skills"]


@pytest.mark.runtime_integration
@pytest.mark.parametrize(
    ("point", "expected_modules", "kwargs"),
    [
        ("tool_execute_before", {"_10_sdd_cache", "_20_simplify_ignore"}, {"tool_name": "not_browser", "tool_args": {}}),
        ("tool_execute_after", {"_10_sdd_cache"}, {"tool_name": "not_browser", "tool_args": {}, "result": None}),
        ("text_editor_patch_after", {"_10_simplify_ignore"}, {"path": "/tmp/not-simplify-ignore.txt"}),
        ("text_editor_write_after", {"_10_simplify_ignore"}, {"path": "/tmp/not-simplify-ignore.txt"}),
        ("monologue_end", {"_10_simplify_ignore"}, {}),
    ],
)
def test_extension_dispatch_loads_remaining_plugin_extension_points(monkeypatch, point, expected_modules, kwargs):
    from helpers import extension, subagents

    monkeypatch.setattr(
        subagents,
        "get_paths",
        lambda agent, *parts: _extension_paths_for(parts[-1]),
    )

    classes = extension._get_extension_classes(point, agent=None)
    module_names = {cls.__module__.split(".")[-1] for cls in classes}
    assert expected_modules.issubset(module_names)

    agent = FakeAgent()
    extension.call_extensions_sync(point, agent=agent, **kwargs)


@pytest.mark.runtime_integration
def test_plugin_helpers_resolve_plugin_and_route_lifecycle_hooks():
    from helpers import plugins

    plugins_list = plugins.get_plugins_list()
    assert "a0_agent_skills" in plugins_list

    plugin_dir = Path(plugins.find_plugin_dir("a0_agent_skills")).resolve()
    assert plugin_dir == PLUGIN_DIR.resolve()

    enabled_skills = [Path(p).resolve() for p in plugins.get_enabled_plugin_paths(None, "skills")]
    enabled_agents = [Path(p).resolve() for p in plugins.get_enabled_plugin_paths(None, "agents")]
    enabled_commands = [Path(p).resolve() for p in plugins.get_enabled_plugin_paths(None, "commands")]
    assert (PLUGIN_DIR / "skills").resolve() in enabled_skills
    assert (PLUGIN_DIR / "agents").resolve() in enabled_agents
    assert (PLUGIN_DIR / "commands").resolve() in enabled_commands

    assert plugins.call_plugin_hook("a0_agent_skills", "install", default="sentinel") is None
    assert plugins.call_plugin_hook("a0_agent_skills", "uninstall", default="sentinel") is None
    assert plugins.call_plugin_hook("a0_agent_skills", "not_a_hook", default="sentinel") == "sentinel"
    assert plugins.call_plugin_hook("not_a_real_plugin", "install", default="sentinel") == "sentinel"
