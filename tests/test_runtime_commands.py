"""Runtime integration tests for a0_agent_skills command registration."""

from __future__ import annotations

import asyncio
import os
import sys
import types
from pathlib import Path

import pytest

A0_ROOT = Path("/a0")
PLUGIN_DIR = Path(__file__).resolve().parents[1]
COMMANDS_DIR = PLUGIN_DIR / "commands"

if str(A0_ROOT) not in sys.path:
    sys.path.insert(0, str(A0_ROOT))

EXPECTED_COMMANDS = {
    "build",
    "code-simplify",
    "plan",
    "review",
    "ship",
    "spec",
    "test",
}


def _clear_framework_caches():
    from helpers import cache

    for area in ("*(plugins)*", "*(extensions)*", "*(commands)*"):
        try:
            cache.clear(area)
        except Exception:
            pass


@pytest.fixture(autouse=True)
def clear_caches():
    _clear_framework_caches()
    yield
    _clear_framework_caches()


@pytest.fixture()
def isolated_plugin_commands(monkeypatch):
    # The Commands helper only needs agent.AgentContext for optional chat-history
    # extraction. Stub it so these tests exercise command discovery/resolution
    # without importing the full Agent runtime and model stack.
    fake_agent = types.ModuleType("agent")
    for name in ("Agent", "AgentConfig", "AgentContext", "AgentContextType", "LoopData"):
        setattr(fake_agent, name, type(name, (), {}))
    monkeypatch.setitem(sys.modules, "agent", fake_agent)

    # Commands discovery/rendering does not need real project chat persistence.
    # Stub helpers.projects to avoid importing the full app/model stack.
    fake_projects = types.ModuleType("helpers.projects")
    fake_projects.PROJECT_META_DIR = ".a0proj"
    fake_projects.get_project_meta = lambda *args, **kwargs: ""
    fake_projects.get_context_project_name = lambda *args, **kwargs: ""
    monkeypatch.setitem(sys.modules, "helpers.projects", fake_projects)
    import helpers
    monkeypatch.setattr(helpers, "projects", fake_projects, raising=False)
    sys.modules.pop("usr.plugins.commands.helpers.commands", None)

    from usr.plugins.commands.helpers import commands

    def fake_get_plugins_list():
        return ["commands", "a0_agent_skills"]

    def fake_find_plugin_dir(plugin_name: str):
        if plugin_name == "a0_agent_skills":
            return str(PLUGIN_DIR)
        if plugin_name == "commands":
            return "/a0/usr/plugins/commands"
        return ""

    monkeypatch.setattr(commands.plugins, "get_plugins_list", fake_get_plugins_list)
    monkeypatch.setattr(commands.plugins, "find_plugin_dir", fake_find_plugin_dir)
    return commands


@pytest.mark.runtime_integration
def test_commands_plugin_discovers_a0_agent_skills_commands(isolated_plugin_commands):
    commands = isolated_plugin_commands

    effective, _scope = commands.list_effective_commands()
    by_name = {cmd["name"]: cmd for cmd in effective}

    assert EXPECTED_COMMANDS.issubset(by_name)
    for name in EXPECTED_COMMANDS:
        command = by_name[name]
        path = Path(command["path"]).resolve()
        assert path.parent == COMMANDS_DIR.resolve()
        assert command.get("source_plugin") == "a0_agent_skills"

    assert by_name["ship"]["command_type"] == "script"
    assert Path(by_name["ship"]["content_path"]).name == "ship.py"
    assert by_name["spec"]["command_type"] == "text"
    assert Path(by_name["spec"]["content_path"]).name == "spec.txt"


@pytest.mark.runtime_integration
def test_get_command_loads_plugin_command_and_resolves_content_path(isolated_plugin_commands):
    commands = isolated_plugin_commands

    spec = commands.get_command(str(COMMANDS_DIR / "spec.command.yaml"))
    assert spec["name"] == "spec"
    assert spec["command_type"] == "text"
    assert Path(spec["content_path"]).resolve() == (COMMANDS_DIR / "spec.txt").resolve()
    assert os.path.isfile(spec["content_path"])
    assert spec.get("source_plugin") == "a0_agent_skills"

    ship = commands.get_command(str(COMMANDS_DIR / "ship.command.yaml"))
    assert ship["name"] == "ship"
    assert ship["command_type"] == "script"
    assert Path(ship["content_path"]).resolve() == (COMMANDS_DIR / "ship.py").resolve()
    assert os.path.isfile(ship["content_path"])
    assert ship.get("source_plugin") == "a0_agent_skills"


@pytest.mark.runtime_integration
def test_resolve_command_invocation_renders_text_command_without_agent_boot(isolated_plugin_commands):
    commands = isolated_plugin_commands

    result = asyncio.run(
        commands.resolve_command_invocation(
            path=str(COMMANDS_DIR / "spec.command.yaml"),
            slash_text="/spec build a runtime integration test plan",
        )
    )

    assert result["command"]["name"] == "spec"
    assert result["invocation"]["command_name"] == "spec"
    rendered = result["result"]["text"]
    assert isinstance(rendered, str)
    assert "runtime integration test plan" in rendered
    assert "spec" in rendered.lower()
    assert result["result"]["effects"] == []
