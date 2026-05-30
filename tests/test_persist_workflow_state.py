# Tests for extensions/python/tool_execute_after/_10_persist_workflow_state.py
#
# Covers: state written after skills_tool:load, state written after
# plan/goal/phase updates, no-op for irrelevant tools, safe with missing
# project folder, top-level try/except, config disabled behavior.

from __future__ import annotations

import ast
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Module loaders
# ---------------------------------------------------------------------------

_ws_module = None
_ext_module = None


def _load_workflow_state():
    """Load helpers.workflow_state via importlib from plugin root."""
    global _ws_module
    if _ws_module is not None:
        # Re-register after conftest _clean_sys_modules cleanup
        sys.modules["helpers.workflow_state"] = _ws_module
        return _ws_module

    import importlib.util

    plugin_root = Path(__file__).parent.parent
    ws_path = plugin_root / "helpers" / "workflow_state.py"
    spec = importlib.util.spec_from_file_location("helpers.workflow_state", str(ws_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules["helpers.workflow_state"] = mod
    _ws_module = mod
    return mod


def _load_extension():
    """Load the persist extension module."""
    global _ext_module
    if _ext_module is not None:
        # Re-register after conftest _clean_sys_modules cleanup
        mod_name = "extensions.python.tool_execute_after._10_persist_workflow_state"
        sys.modules[mod_name] = _ext_module
        return _ext_module

    import importlib.util

    plugin_root = Path(__file__).parent.parent
    ext_path = (plugin_root / "extensions" / "python" / "tool_execute_after" /
                "_10_persist_workflow_state.py")
    spec = importlib.util.spec_from_file_location(
        "extensions.python.tool_execute_after._10_persist_workflow_state",
        str(ext_path),
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _ext_module = mod
    return mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _setup_modules():
    _load_workflow_state()
    _load_extension()


@pytest.fixture
def tmp_project(tmp_path):
    proj = tmp_path / "test_project"
    proj.mkdir()
    return proj


def _make_agent(tmp_project, skills=None, config=None):
    """Create a mock agent with project resolution and loop_data."""
    agent = MagicMock()
    agent.context = MagicMock()
    agent.data = {"loaded_skills": skills or ["incremental-implementation"]}

    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = "test_project"
    projects_mock.get_project_folder.return_value = str(tmp_project)

    cfg = config if config is not None else {"workflow_state_enabled": True}
    plugins_mock = MagicMock()
    plugins_mock.get_plugin_config.return_value = cfg

    helpers_mock = MagicMock()
    helpers_mock.projects = projects_mock
    helpers_mock.plugins = plugins_mock

    sys.modules["helpers"] = helpers_mock
    sys.modules["helpers.projects"] = projects_mock
    sys.modules["helpers.plugins"] = plugins_mock
    sys.modules["helpers.skills"] = MagicMock()

    # Set up loop_data
    current_tool = MagicMock()
    current_tool.method = "load"
    current_tool.args = {"skill_name": "test-skill"}
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool

    return agent


@pytest.fixture
def mock_agent(tmp_project):
    return _make_agent(tmp_project)


@pytest.fixture
def no_project_agent():
    """Mock agent where project resolution fails."""
    agent = MagicMock()
    agent.context = None
    agent.data = {"loaded_skills": ["test-skill"]}

    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = None

    plugins_mock = MagicMock()
    plugins_mock.get_plugin_config.return_value = {"workflow_state_enabled": True}

    helpers_mock = MagicMock()
    helpers_mock.projects = projects_mock
    helpers_mock.plugins = plugins_mock

    sys.modules["helpers"] = helpers_mock
    sys.modules["helpers.projects"] = projects_mock
    sys.modules["helpers.plugins"] = plugins_mock

    current_tool = MagicMock()
    current_tool.method = "load"
    current_tool.args = {"skill_name": "test-skill"}
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool

    return agent


def _make_ext(agent):
    """Create a PersistWorkflowState instance with the given agent."""
    ext_mod = _load_extension()
    ext = ext_mod.PersistWorkflowState.__new__(ext_mod.PersistWorkflowState)
    ext.agent = agent
    return ext


# ---------------------------------------------------------------------------
# State written after skills_tool:load
# ---------------------------------------------------------------------------

class TestSkillsToolLoad:
    @pytest.mark.asyncio
    async def test_saves_loaded_skills_on_skill_load(self, mock_agent, tmp_project):
        ext = _make_ext(mock_agent)
        await ext.execute(tool_name="skills_tool", tool_args={"action": "load", "skill_name": "test-skill"})

        ws = _load_workflow_state()
        result = ws.read_loaded_skills(mock_agent)
        assert result is not None
        assert any(s["name"] == "incremental-implementation" for s in result["skills"])

    @pytest.mark.asyncio
    async def test_appends_progress_event_on_skill_load(self, mock_agent, tmp_project):
        ext = _make_ext(mock_agent)
        await ext.execute(tool_name="skills_tool", tool_args={"action": "load"})

        ws = _load_workflow_state()
        log = ws.read_progress_log(mock_agent)
        assert len(log) > 0
        skill_events = [e for e in log if e["event"] == "skill_loaded"]
        assert len(skill_events) > 0

    @pytest.mark.asyncio
    async def test_regenerates_handoff_on_skill_load(self, mock_agent, tmp_project):
        ext = _make_ext(mock_agent)
        await ext.execute(tool_name="skills_tool", tool_args={"action": "load"})

        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(mock_agent)
        assert os.path.exists(os.path.join(state_dir, "handoff.md"))


# ---------------------------------------------------------------------------
# State written after plan/goal/phase updates
# ---------------------------------------------------------------------------

class TestStateUpdates:
    @pytest.mark.asyncio
    async def test_saves_plan_when_plan_name_in_args(self, mock_agent, tmp_project):
        ext = _make_ext(mock_agent)
        # Need a tool that triggers state detection
        mock_agent.loop_data.current_tool.method = "execute"
        mock_agent.loop_data.current_tool.args = {"plan_name": "test-plan"}

        await ext.execute(tool_name="code_execution_tool",
                         tool_args={"plan_name": "test-plan", "plan_path": "docs/plan.md"})

        ws = _load_workflow_state()
        plan = ws.read_active_plan(mock_agent)
        assert plan is not None
        assert plan["plan_name"] == "test-plan"

    @pytest.mark.asyncio
    async def test_saves_goal_when_goal_in_args(self, mock_agent, tmp_project):
        ext = _make_ext(mock_agent)
        mock_agent.loop_data.current_tool.args = {"goal": "Build it now"}

        await ext.execute(tool_name="code_execution_tool",
                         tool_args={"goal": "Build it now"})

        ws = _load_workflow_state()
        goal = ws.read_active_goal(mock_agent)
        assert goal is not None
        assert goal["goal"] == "Build it now"

    @pytest.mark.asyncio
    async def test_saves_phase_when_phase_in_args(self, mock_agent, tmp_project):
        ext = _make_ext(mock_agent)
        mock_agent.loop_data.current_tool.args = {"phase": "BUILD"}

        await ext.execute(tool_name="code_execution_tool",
                         tool_args={"phase": "BUILD", "phases_completed": ["DEFINE", "PLAN"]})

        ws = _load_workflow_state()
        phase = ws.read_current_phase(mock_agent)
        assert phase is not None
        assert phase["phase"] == "BUILD"
        assert phase["phases_completed"] == ["DEFINE", "PLAN"]

    @pytest.mark.asyncio
    async def test_progress_events_appended_for_state_changes(self, mock_agent, tmp_project):
        ext = _make_ext(mock_agent)
        mock_agent.loop_data.current_tool.args = {"phase": "VERIFY"}

        await ext.execute(tool_name="code_execution_tool",
                         tool_args={"phase": "VERIFY"})

        ws = _load_workflow_state()
        log = ws.read_progress_log(mock_agent)
        phase_events = [e for e in log if e["event"] == "phase_change"]
        assert len(phase_events) > 0
        assert phase_events[0]["to"] == "VERIFY"


# ---------------------------------------------------------------------------
# No-op for irrelevant tools
# ---------------------------------------------------------------------------

class TestNoOp:
    @pytest.mark.parametrize("tool_name,tool_args", [
        ("browser", {"action": "open", "url": "http://example.com"}),
        ("search_engine", {"query": "test"}),
        ("response", {"text": "hello"}),
        ("memory_save", {"text": "test"}),
        ("scheduler", {"action": "list_tasks"}),
    ])
    @pytest.mark.asyncio
    async def test_no_state_written_for_irrelevant_tools(self, mock_agent, tmp_project,
                                                          tool_name, tool_args):
        ext = _make_ext(mock_agent)
        mock_agent.loop_data.current_tool.method = "execute"
        mock_agent.loop_data.current_tool.args = tool_args

        await ext.execute(tool_name=tool_name, tool_args=tool_args)

        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(mock_agent)
        # State dir should not exist (no writes happened)
        assert not os.path.exists(state_dir)

    @pytest.mark.asyncio
    async def test_no_op_when_tool_name_is_none(self, mock_agent, tmp_project):
        ext = _make_ext(mock_agent)
        # Should not raise
        await ext.execute(tool_name=None)

        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(mock_agent)
        assert not os.path.exists(state_dir)


# ---------------------------------------------------------------------------
# Safe with missing project folder
# ---------------------------------------------------------------------------

class TestMissingProject:
    @pytest.mark.asyncio
    async def test_no_error_with_missing_project_folder(self, no_project_agent):
        ext = _make_ext(no_project_agent)
        # Should not raise
        await ext.execute(tool_name="skills_tool", tool_args={"action": "load"})


# ---------------------------------------------------------------------------
# Top-level try/except pattern
# ---------------------------------------------------------------------------

class TestFailSafe:
    @pytest.mark.asyncio
    async def test_extension_never_raises(self):
        """Even with a completely broken agent, extension must not raise."""
        ext_mod = _load_extension()
        ext = ext_mod.PersistWorkflowState.__new__(ext_mod.PersistWorkflowState)
        ext.agent = None  # will cause attribute errors inside
        # Must not raise
        await ext.execute(tool_name="skills_tool", tool_args={"action": "load"})

    def test_source_has_top_level_try_except(self):
        """Verify the extension source contains a top-level try/except in execute."""
        ext_path = (
            Path(__file__).parent.parent / "extensions" / "python" /
            "tool_execute_after" / "_10_persist_workflow_state.py"
        )
        source = ext_path.read_text()
        tree = ast.parse(source)

        # Find the PersistWorkflowState class
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "execute":
                # First statement should be a try
                assert len(node.body) > 0
                assert isinstance(node.body[0], ast.Try), \
                    "execute() body must start with a try/except"
                return
        pytest.fail("execute() method not found")


# ---------------------------------------------------------------------------
# Config disabled
# ---------------------------------------------------------------------------

class TestConfigDisabled:
    @pytest.mark.asyncio
    async def test_no_state_written_when_disabled(self, tmp_project):
        agent = _make_agent(tmp_project, config={"workflow_state_enabled": False})
        ext = _make_ext(agent)

        await ext.execute(tool_name="skills_tool", tool_args={"action": "load"})

        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(agent)
        assert state_dir is not None or state_dir is None  # resolves but nothing written
        if state_dir:
            assert not os.path.exists(state_dir)

    @pytest.mark.asyncio
    async def test_no_state_written_when_config_false_string(self, tmp_project):
        agent = _make_agent(tmp_project, config={"workflow_state_enabled": "false"})
        ext = _make_ext(agent)

        await ext.execute(tool_name="skills_tool", tool_args={"action": "load"})

        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(agent)
        if state_dir:
            assert not os.path.exists(state_dir)
