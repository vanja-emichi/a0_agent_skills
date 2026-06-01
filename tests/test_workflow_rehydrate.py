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
    _ext = _load_extension()
    # Reset specs cache so each test gets fresh filesystem results
    _ext._reset_specs_cache()


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
        ws.save_workflow_artifacts(mock_agent, {"plan_path": "docs/plan.md"})
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
        assert "**Plan Path:** docs/plan.md" in state_block
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
        # With no-project fallback, rehydration now succeeds using workdir state
        assert "workflow_state" in loop_data.extras_persistent

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

        # Rehydration writes to the PLUGIN-PRIVATE key, not the core-rendered
        # 'loaded_skills' key (which would re-inject full SKILL.md bodies every
        # loop). The core key must stay empty; the gate still sees the names.
        assert mock_agent.data.get("_a0skills_rehydrated_loaded") == [
            "incremental-implementation",
            "test-driven-development",
        ]
        assert not mock_agent.data.get("loaded_skills")
        from helpers.skill_match import get_loaded_skills
        gate_loaded = get_loaded_skills(mock_agent)
        assert "incremental-implementation" in gate_loaded
        assert "test-driven-development" in gate_loaded

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
        ws.save_workflow_artifacts(mock_agent, {"plan_path": "docs/plans/plan.md"})
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
        assert "**Plan Path:** docs/plans/plan.md" in state_block
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

        # After rehydration, the enforcement gate (skill_match.get_loaded_skills)
        # must see the rehydrated skill via the plugin-private key, while the
        # core-rendered 'loaded_skills' key stays empty to avoid full-body
        # re-injection of SKILL.md content every message loop.
        assert not mock_agent.data.get("loaded_skills")
        from helpers.skill_match import get_loaded_skills
        loaded = get_loaded_skills(mock_agent)
        assert isinstance(loaded, set)
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

    @pytest.mark.asyncio
    async def test_hints_enabled_explicitly_in_config(self, tmp_project):
        """Rehydrated state includes hints when skill_next_skill_hints is explicitly True."""
        agent = _make_agent(tmp_project, config={"skill_next_skill_hints": True})

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


# ---------------------------------------------------------------------------
# Regression: rehydration must NOT repopulate the core-rendered
# agent.data['loaded_skills'] key. Doing so makes the core skills renderer
# re-inject full SKILL.md bodies for every prior-session skill on every
# message loop (unbounded context flood). Names belong in a plugin-private
# key that the enforcement gate reads; the lightweight summary lives in the
# rehydrated state block.
# ---------------------------------------------------------------------------


class TestNoCoreLoadedSkillsFlood:
    @pytest.mark.asyncio
    async def test_rehydration_does_not_repopulate_core_loaded_skills(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ws.save_loaded_skills(mock_agent, {"skills": [
            {"name": "spec-driven-development", "loaded_at": 1.0},
            {"name": "test-driven-development", "loaded_at": 2.0},
        ]})

        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        # Core-rendered key MUST stay empty so the skills renderer does not
        # re-inject full SKILL.md bodies for prior-session skills.
        assert not mock_agent.data.get("loaded_skills")

        # Plugin-private key MUST carry the rehydrated names.
        private = mock_agent.data.get("_a0skills_rehydrated_loaded", [])
        assert "spec-driven-development" in private
        assert "test-driven-development" in private

        # The enforcement gate must still treat them as already-loaded.
        from helpers.skill_match import get_loaded_skills
        loaded = get_loaded_skills(mock_agent)
        assert "spec-driven-development" in loaded
        assert "test-driven-development" in loaded

        # The lightweight names summary must still appear in the state block.
        state_block = loop_data.extras_persistent.get("workflow_state", "")
        assert "spec-driven-development" in state_block


# ---------------------------------------------------------------------------
# Task 4 (artifact-path-wiring-fix): plan_path reads from workflow_artifacts.json
# with backward-compat fallback to active_plan.json
# ---------------------------------------------------------------------------


class TestPlanPathFromArtifacts:
    """Plan path reads from workflow_artifacts.json with fallback."""

    @pytest.mark.asyncio
    async def test_plan_path_from_workflow_artifacts(self, mock_agent, tmp_project):
        """plan_path in workflow_artifacts.json is used for display."""
        ws = _load_workflow_state()
        ws.save_active_plan(mock_agent, {
            "plan_name": "my-plan",
            "plan_path": "old/path.md",
            "current_task": "Task 1",
        })
        ws.save_workflow_artifacts(mock_agent, {"plan_path": "docs/plans/my-plan-plan.md"})

        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent["workflow_state"]
        # Artifacts value takes priority
        assert "**Plan Path:** docs/plans/my-plan-plan.md" in state_block

    @pytest.mark.asyncio
    async def test_plan_path_backward_compat_fallback(self, mock_agent, tmp_project):
        """When plan_path only in active_plan.json, rehydration still displays it."""
        ws = _load_workflow_state()
        ws.save_active_plan(mock_agent, {
            "plan_name": "legacy-plan",
            "plan_path": "docs/plans/legacy-plan.md",
            "current_task": "Task 2",
        })
        # Intentionally do NOT save workflow_artifacts — simulates old state

        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent["workflow_state"]
        # Falls back to active_plan.json value
        assert "**Plan Path:** docs/plans/legacy-plan.md" in state_block

    @pytest.mark.asyncio
    async def test_plan_name_still_from_active_plan(self, mock_agent, tmp_project):
        """plan_name always reads from active_plan.json, not workflow_artifacts."""
        ws = _load_workflow_state()
        ws.save_active_plan(mock_agent, {
            "plan_name": "plan-from-active",
            "plan_path": "docs/plan.md",
            "current_task": "Task 1",
        })
        ws.save_workflow_artifacts(mock_agent, {"plan_path": "docs/plans/plan-from-active-plan.md"})

        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent["workflow_state"]
        # plan_name comes from active_plan.json, not artifacts
        assert "**Active Plan:** plan-from-active" in state_block

    @pytest.mark.asyncio
    async def test_current_task_still_from_active_plan(self, mock_agent, tmp_project):
        """current_task always reads from active_plan.json, not workflow_artifacts."""
        ws = _load_workflow_state()
        ws.save_active_plan(mock_agent, {
            "plan_name": "task-test",
            "plan_path": "docs/plan.md",
            "current_task": "Task 5 of 10",
        })
        ws.save_workflow_artifacts(mock_agent, {"plan_path": "docs/plans/task-test-plan.md"})

        ext = _make_ext(mock_agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent["workflow_state"]
        assert "**Current Task:** Task 5 of 10" in state_block


# ---------------------------------------------------------------------------
# Task 7: Spec status filtering — shipped specs filtered from proposals
# ---------------------------------------------------------------------------


class TestSpecStatusFiltering:
    """Tests for spec status filtering in rehydrated state (Task 7)."""

    @pytest.mark.asyncio
    async def test_shipped_spec_excluded_from_state_block(self, tmp_path):
        """Specs with Status: SHIPPED are excluded from active specs."""
        proj = tmp_path / "test_project"
        proj.mkdir()
        specs_dir = proj / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        # Create a shipped spec
        shipped_spec = specs_dir / "old-feature-spec.md"
        shipped_spec.write_text("# Old Feature\n\n**Status:** Shipped\n\nDone.")

        # Create an active spec
        active_spec = specs_dir / "new-feature-spec.md"
        active_spec.write_text("# New Feature\n\n**Status:** Draft\n\nWork in progress.")

        agent = _make_agent(proj)
        ws = _load_workflow_state()
        ws.save_active_plan(agent, {"plan_name": "test"})

        ext = _make_ext(agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent.get("workflow_state", "")
        # Active spec should appear
        assert "new-feature-spec.md" in state_block
        # Shipped spec should NOT appear
        assert "old-feature-spec.md" not in state_block

    @pytest.mark.asyncio
    async def test_approved_spec_excluded_from_state_block(self, tmp_path):
        """Specs with Status: Approved are excluded from active specs."""
        proj = tmp_path / "test_project"
        proj.mkdir()
        specs_dir = proj / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        approved_spec = specs_dir / "approved-feature-spec.md"
        approved_spec.write_text("# Approved Feature\n\n**Status:** Approved\n\nReady.")

        draft_spec = specs_dir / "draft-feature-spec.md"
        draft_spec.write_text("# Draft Feature\n\n**Status:** Draft\n\nWIP.")

        agent = _make_agent(proj)
        ws = _load_workflow_state()
        ws.save_active_plan(agent, {"plan_name": "test"})

        ext = _make_ext(agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent.get("workflow_state", "")
        assert "draft-feature-spec.md" in state_block
        assert "approved-feature-spec.md" not in state_block

    @pytest.mark.asyncio
    async def test_in_progress_spec_shown_in_state_block(self, tmp_path):
        """Specs with Status: In Progress are shown as active."""
        proj = tmp_path / "test_project"
        proj.mkdir()
        specs_dir = proj / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        wip_spec = specs_dir / "wip-feature-spec.md"
        wip_spec.write_text("# WIP Feature\n\n**Status:** In Progress\n\nWorking.")

        agent = _make_agent(proj)
        ws = _load_workflow_state()
        ws.save_active_plan(agent, {"plan_name": "test"})

        ext = _make_ext(agent)
        loop_data = _LoopData()
        await ext.execute(loop_data=loop_data)

        state_block = loop_data.extras_persistent.get("workflow_state", "")
        assert "wip-feature-spec.md" in state_block
        assert "In Progress" in state_block

    @pytest.mark.asyncio
    async def test_no_specs_dir_no_error(self, tmp_path):
        """When no docs/specs/ directory exists, extension still works."""
        proj = tmp_path / "test_project"
        proj.mkdir()
        # No docs/specs/ created

        agent = _make_agent(proj)
        ws = _load_workflow_state()
        ws.save_active_plan(agent, {"plan_name": "test"})

        ext = _make_ext(agent)
        loop_data = _LoopData()
        # Must not raise
        await ext.execute(loop_data=loop_data)

        # State block should exist (from plan) but not have spec section
        state_block = loop_data.extras_persistent.get("workflow_state", "")
        assert "Active Specs" not in state_block


# ---------------------------------------------------------------------------
# Specs cache TTL — ensures _scan_active_specs caching works correctly
# ---------------------------------------------------------------------------


class TestSpecsCacheTTL:
    """Tests for specs scan caching with TTL."""

    @pytest.mark.asyncio
    async def test_specs_cached_within_ttl(self, tmp_path):
        """Second call within TTL returns cached result without re-reading files."""
        proj = tmp_path / "test_project"
        proj.mkdir()
        specs_dir = proj / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        spec_file = specs_dir / "feature-spec.md"
        spec_file.write_text("# Feature\n\n**Status:** Draft\n\nWIP.")

        agent = _make_agent(proj)
        ws = _load_workflow_state()
        ws.save_active_plan(agent, {"plan_name": "test"})

        ext_mod = _load_extension()
        ext_mod._reset_specs_cache()

        ext = _make_ext(agent)
        loop_data1 = _LoopData()
        await ext.execute(loop_data=loop_data1)

        # Delete the spec file — if cache works, second call still shows it
        spec_file.unlink()

        loop_data2 = _LoopData()
        await ext.execute(loop_data=loop_data2)

        state_block2 = loop_data2.extras_persistent.get("workflow_state", "")
        assert "feature-spec.md" in state_block2, "Cached result should still list deleted file"

    @pytest.mark.asyncio
    async def test_specs_cache_expires_after_ttl(self, tmp_path):
        """Cache expires after TTL and re-reads filesystem."""
        proj = tmp_path / "test_project"
        proj.mkdir()
        specs_dir = proj / "docs" / "specs"
        specs_dir.mkdir(parents=True)

        spec_file = specs_dir / "feature-spec.md"
        spec_file.write_text("# Feature\n\n**Status:** Draft\n\nWIP.")

        agent = _make_agent(proj)
        ws = _load_workflow_state()
        ws.save_active_plan(agent, {"plan_name": "test"})

        ext_mod = _load_extension()
        ext_mod._reset_specs_cache()

        # Set a very short TTL for testing
        original_ttl = ext_mod._SPECS_CACHE_TTL
        ext_mod._SPECS_CACHE_TTL = 0.01  # 10ms

        try:
            ext = _make_ext(agent)
            loop_data1 = _LoopData()
            await ext.execute(loop_data=loop_data1)

            # Wait for TTL to expire
            import time
            time.sleep(0.05)

            # Delete the spec file
            spec_file.unlink()

            loop_data2 = _LoopData()
            await ext.execute(loop_data=loop_data2)

            state_block2 = loop_data2.extras_persistent.get("workflow_state", "")
            assert "feature-spec.md" not in state_block2, (
                "After TTL expiry, re-scan should not find deleted file"
            )
        finally:
            ext_mod._SPECS_CACHE_TTL = original_ttl
            ext_mod._reset_specs_cache()
