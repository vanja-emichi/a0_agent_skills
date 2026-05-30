# Tests for extensions/python/message_loop_prompts_after/_67_reattach_workflow_state.py
#
# Covers: state block appended when files exist, loop_data unmodified when no
# files exist, loop_data unmodified on errors, agent.data['loaded_skills']
# updated from rehydrated state, round-trip test, compatibility with
# skill_match.get_loaded_skills(), config disabled behavior.

from __future__ import annotations

import ast
import json
import os
import sys
import time
from collections import OrderedDict
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Lightweight LoopData mock (real agent.LoopData needs litellm)
# ---------------------------------------------------------------------------

class _LoopData:
    """Minimal LoopData stand-in that mirrors agent.LoopData extras_persistent."""

    def __init__(self):
        self.extras_persistent: OrderedDict[str, str] = OrderedDict()


# ---------------------------------------------------------------------------
# Module loaders
# ---------------------------------------------------------------------------

_ws_module = None
_ext_module = None


def _ensure_agent_stub():
    """Ensure 'agent' module is in sys.modules with a LoopData attribute.

    The extension does ``from agent import LoopData`` at import time, so the
    stub must be present *before* the extension module is loaded.
    """
    if "agent" not in sys.modules:
        agent_mod = MagicMock()
        agent_mod.LoopData = _LoopData
        sys.modules["agent"] = agent_mod
    else:
        sys.modules["agent"].LoopData = _LoopData


def _load_workflow_state():
    """Load helpers.workflow_state via importlib from plugin root."""
    global _ws_module
    if _ws_module is not None:
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
    """Load the rehydrate extension module."""
    global _ext_module
    if _ext_module is not None:
        mod_name = "extensions.python.message_loop_prompts_after._67_reattach_workflow_state"
        sys.modules[mod_name] = _ext_module
        return _ext_module

    import importlib.util

    # Must stub agent.LoopData before loading the extension module
    _ensure_agent_stub()

    plugin_root = Path(__file__).parent.parent
    ext_path = (plugin_root / "extensions" / "python" / "message_loop_prompts_after" /
                "_67_reattach_workflow_state.py")
    spec = importlib.util.spec_from_file_location(
        "extensions.python.message_loop_prompts_after._67_reattach_workflow_state",
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
    _ensure_agent_stub()
    _load_workflow_state()
    _load_extension()


@pytest.fixture
def tmp_project(tmp_path):
    proj = tmp_path / "test_project"
    proj.mkdir()
    return proj


def _make_agent(tmp_project, config=None):
    """Create a mock agent with project resolution."""
    agent = MagicMock()
    agent.context = MagicMock()
    agent.data = {"loaded_skills": []}

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

    return agent


@pytest.fixture
def mock_agent(tmp_project):
    return _make_agent(tmp_project)


def _make_ext(agent):
    """Create a ReattachWorkflowState instance with the given agent."""
    ext_mod = _load_extension()
    ext = ext_mod.ReattachWorkflowState.__new__(ext_mod.ReattachWorkflowState)
    ext.agent = agent
    return ext


# ---------------------------------------------------------------------------
# State block appended when files exist
# ---------------------------------------------------------------------------

class TestStateBlockAppended:
    @pytest.mark.asyncio
    async def test_appends_state_block_when_state_exists(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ws.save_active_plan(mock_agent, {"plan_name": "test-plan", "plan_path": "docs/plan.md",
                                          "current_task": "Task 1", "tasks_total": 3, "tasks_completed": 1})
        ws.save_active_goal(mock_agent, {"goal": "Build it"})
        ws.save_current_phase(mock_agent, {"phase": "BUILD", "phases_completed": ["DEFINE", "PLAN"]})

        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent["workflow_state"]
        assert "Durable Workflow State (Rehydrated)" in state_block
        assert "**Active Goal:** Build it" in state_block
        assert "**Current Phase:** BUILD" in state_block
        assert "**Active Plan:** test-plan" in state_block
        assert "**Current Task:** Task 1" in state_block
        assert "**Task Progress:** 1/3 completed" in state_block
        assert "**Phases Completed:** DEFINE, PLAN" in state_block

    @pytest.mark.asyncio
    async def test_includes_loaded_skills_in_block(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ws.save_loaded_skills(mock_agent, {"skills": [
            {"name": "tdd", "loaded_at": 1.0},
            {"name": "sdd", "loaded_at": 2.0},
        ]})

        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent["workflow_state"]
        assert "**Loaded Skills:** tdd, sdd" in state_block

    @pytest.mark.asyncio
    async def test_includes_last_checkpoint_in_block(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ws.create_checkpoint(mock_agent, "Milestone 1", phase="BUILD")

        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent["workflow_state"]
        assert "cp-001" in state_block
        assert "Milestone 1" in state_block


# ---------------------------------------------------------------------------
# LoopData unmodified when no state files exist
# ---------------------------------------------------------------------------

class TestNoStateFiles:
    @pytest.mark.asyncio
    async def test_loop_data_unmodified_when_no_state(self, mock_agent, tmp_project):
        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        assert "workflow_state" not in loop_data.extras_persistent

    @pytest.mark.asyncio
    async def test_extras_persistent_empty_when_no_state(self, mock_agent, tmp_project):
        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        assert len(loop_data.extras_persistent) == 0


# ---------------------------------------------------------------------------
# LoopData unmodified on errors
# ---------------------------------------------------------------------------

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_loop_data_unmodified_on_broken_agent(self):
        """Even with a None agent, extension must not raise."""
        ext_mod = _load_extension()
        ext = ext_mod.ReattachWorkflowState.__new__(ext_mod.ReattachWorkflowState)
        ext.agent = None

        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)
        assert "workflow_state" not in loop_data.extras_persistent

    @pytest.mark.asyncio
    async def test_loop_data_unmodified_when_no_project(self):
        """When project resolution fails, loop_data must stay clean."""
        agent = MagicMock()
        agent.context = None
        agent.data = {}

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

        ext = _make_ext(agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)
        assert "workflow_state" not in loop_data.extras_persistent

    def test_source_has_top_level_try_except(self):
        """Verify the extension source contains a top-level try/except in execute."""
        ext_path = (
            Path(__file__).parent.parent / "extensions" / "python" /
            "message_loop_prompts_after" / "_67_reattach_workflow_state.py"
        )
        source = ext_path.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == "execute":
                assert len(node.body) > 0
                assert isinstance(node.body[0], ast.Try), \
                    "execute() body must start with a try/except"
                return
        pytest.fail("execute() method not found")


# ---------------------------------------------------------------------------
# agent.data['loaded_skills'] updated from rehydrated state
# ---------------------------------------------------------------------------

class TestLoadedSkillsInjection:
    @pytest.mark.asyncio
    async def test_injects_skill_names_into_agent_data(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ws.save_loaded_skills(mock_agent, {"skills": [
            {"name": "incremental-implementation", "loaded_at": 1.0},
            {"name": "test-driven-development", "loaded_at": 2.0},
        ]})

        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        # Check that agent.data['loaded_skills'] was updated
        assert mock_agent.data["loaded_skills"] == [
            "incremental-implementation",
            "test-driven-development",
        ]

    @pytest.mark.asyncio
    async def test_does_not_inject_when_no_skills_in_state(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ws.save_active_plan(mock_agent, {"plan_name": "test"})

        original_skills = mock_agent.data.get("loaded_skills", [])
        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        # loaded_skills should remain unchanged (no skills in state)
        assert mock_agent.data["loaded_skills"] == original_skills


# ---------------------------------------------------------------------------
# Round-trip: write via helper -> read via rehydrate
# ---------------------------------------------------------------------------

class TestRoundTrip:
    @pytest.mark.asyncio
    async def test_full_roundtrip(self, mock_agent, tmp_project):
        """Write state via helper, then verify rehydrate reads it correctly."""
        ws = _load_workflow_state()

        # Write all state
        ws.save_active_plan(mock_agent, {
            "plan_name": "durable-workflow-state",
            "plan_path": "docs/plans/plan.md",
            "current_task": "Task 3",
            "tasks_total": 6,
            "tasks_completed": 2,
        })
        ws.save_active_goal(mock_agent, {
            "goal": "Persist workflow state durably",
            "source": "user message",
        })
        ws.save_current_phase(mock_agent, {
            "phase": "BUILD",
            "phases_completed": ["DEFINE", "PLAN"],
        })
        ws.save_loaded_skills(mock_agent, {"skills": [
            {"name": "incremental-implementation", "loaded_at": 1.0},
        ]})
        ws.create_checkpoint(mock_agent, "Helper complete", phase="BUILD")

        # Rehydrate
        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent["workflow_state"]
        assert "durable-workflow-state" in state_block
        assert "Persist workflow state durably" in state_block
        assert "BUILD" in state_block
        assert "incremental-implementation" in state_block
        assert "cp-001" in state_block


# ---------------------------------------------------------------------------
# Compatibility with skill_match.get_loaded_skills()
# ---------------------------------------------------------------------------

class TestSkillMatchCompat:
    @pytest.mark.asyncio
    async def test_rehydrated_skills_compatible_with_get_loaded_skills(self, mock_agent, tmp_project):
        """Verify that rehydrated loaded_skills format works with skill_match."""
        ws = _load_workflow_state()
        ws.save_loaded_skills(mock_agent, {"skills": [
            {"name": "test-driven-development", "loaded_at": 1.0},
        ]})

        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        # After rehydration, agent.data['loaded_skills'] should be a list of strings
        loaded = mock_agent.data["loaded_skills"]
        assert isinstance(loaded, list)
        assert all(isinstance(s, str) for s in loaded)
        assert "test-driven-development" in loaded


# ---------------------------------------------------------------------------
# Config disabled
# ---------------------------------------------------------------------------

class TestConfigDisabled:
    @pytest.mark.asyncio
    async def test_loop_data_unmodified_when_disabled(self, tmp_project):
        agent = _make_agent(tmp_project, config={"workflow_state_enabled": False})

        # Write some state
        ws = _load_workflow_state()
        ws.save_active_plan(agent, {"plan_name": "test"})

        ext = _make_ext(agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        assert "workflow_state" not in loop_data.extras_persistent

    @pytest.mark.asyncio
    async def test_loop_data_unmodified_when_config_false_string(self, tmp_project):
        agent = _make_agent(tmp_project, config={"workflow_state_enabled": "false"})

        ws = _load_workflow_state()
        ws.save_active_plan(agent, {"plan_name": "test"})

        ext = _make_ext(agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        assert "workflow_state" not in loop_data.extras_persistent

    @pytest.mark.asyncio
    async def test_no_skills_injected_when_disabled(self, tmp_project):
        agent = _make_agent(tmp_project, config={"workflow_state_enabled": False})

        ws = _load_workflow_state()
        ws.save_loaded_skills(agent, {"skills": [{"name": "tdd", "loaded_at": 1.0}]})

        ext = _make_ext(agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        # Skills should NOT have been injected
        assert agent.data.get("loaded_skills") == []  # initial value, not updated


# ===========================================================================
# Task 5 (Slice 4): Next-skill hints in rehydrated state
# ===========================================================================


class TestNextSkillHints:
    """Tests for next-skill hints in rehydrated state (Slice 4)."""

    @pytest.mark.asyncio
    async def test_hints_appear_when_contract_skill_loaded(self, tmp_project):
        """Rehydrated state includes next-skill hints when contract-bearing skill loaded."""
        agent = _make_agent(tmp_project)

        ws = _load_workflow_state()
        ws.save_loaded_skills(agent, {
            "skills": [{"name": "test-driven-development", "loaded_at": 1.0}]
        })

        ext = _make_ext(agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent.get("workflow_state", "")
        assert "Next Skill Hints" in state_block
        assert "debugging-and-error-recovery" in state_block

    @pytest.mark.asyncio
    async def test_hints_omit_when_no_contract_skills(self, tmp_project):
        """Rehydrated state omits hints when no contract-bearing skill loaded."""
        agent = _make_agent(tmp_project)

        ws = _load_workflow_state()
        ws.save_loaded_skills(agent, {
            "skills": [{"name": "agents-best-practices", "loaded_at": 1.0}]
        })

        ext = _make_ext(agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent.get("workflow_state", "")
        assert "Next Skill Hints" not in state_block

    @pytest.mark.asyncio
    async def test_hints_disabled_in_config(self, tmp_project):
        """Rehydrated state omits hints when skill_next_skill_hints: false."""
        agent = _make_agent(tmp_project, config={"skill_next_skill_hints": False})

        ws = _load_workflow_state()
        ws.save_loaded_skills(agent, {
            "skills": [{"name": "test-driven-development", "loaded_at": 1.0}]
        })

        ext = _make_ext(agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent.get("workflow_state", "")
        assert "Next Skill Hints" not in state_block
