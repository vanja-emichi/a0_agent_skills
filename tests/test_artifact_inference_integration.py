# Integration tests for the full artifact inference → state persistence → rehydration pipeline.
#
# Tests the end-to-end flow WITHOUT a real LLM or agent loop:
#   1. Simulate text_editor writes to artifact paths
#   2. Persist extension detects path match and writes state files
#   3. Rehydration reads state files back and verifies content

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Module loaders (same pattern as existing tests)
# ---------------------------------------------------------------------------

_ws_module = None
_ext_module = None


def _load_workflow_state():
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
    global _ext_module
    if _ext_module is not None:
        mod_name = "extensions.python.tool_execute_after._10_persist_workflow_state"
        sys.modules[mod_name] = _ext_module
        return _ext_module
    import importlib.util

    plugin_root = Path(__file__).parent.parent
    ext_path = (
        plugin_root / "extensions" / "python" / "tool_execute_after"
        / "_10_persist_workflow_state.py"
    )
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


def _make_agent(tmp_project):
    agent = MagicMock()
    agent.context = MagicMock()
    agent.data = {"loaded_skills": []}

    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = "test_project"
    projects_mock.get_project_folder.return_value = str(tmp_project)

    cfg = {"workflow_state_enabled": True, "artifact_inference_enabled": True}
    plugins_mock = MagicMock()
    plugins_mock.get_plugin_config.return_value = cfg

    helpers_mock = MagicMock()
    helpers_mock.projects = projects_mock
    helpers_mock.plugins = plugins_mock

    sys.modules["helpers"] = helpers_mock
    sys.modules["helpers.projects"] = projects_mock
    sys.modules["helpers.plugins"] = plugins_mock
    sys.modules["helpers.skills"] = MagicMock()

    current_tool = MagicMock()
    current_tool.method = "execute"
    current_tool.args = {}
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool

    return agent


@pytest.fixture
def mock_agent(tmp_project):
    return _make_agent(tmp_project)


def _make_ext(agent):
    ext_mod = _load_extension()
    ext = ext_mod.PersistWorkflowState.__new__(ext_mod.PersistWorkflowState)
    ext.agent = agent
    ext._artifact_mtimes = {}
    return ext


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestSpecInferencePipeline:
    """Spec artifact → goal + DEFINE phase → rehydration."""

    def test_spec_write_creates_goal_and_define_phase(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ext = _make_ext(mock_agent)

        # Create spec file on disk (mtime check needs a real file)
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "user-auth-spec.md"
        spec_file.write_text("# User Auth Spec\n")

        # Detect artifact from path
        artifact = ext._detect_artifact_from_path("text_editor", {
            "action": "write",
            "path": str(spec_file),
        })
        assert artifact is not None
        assert artifact["artifact_type"] == "spec"
        assert artifact["phase"] == "DEFINE"
        assert artifact["slug"] == "user-auth"

        # Persist state
        changed = ext._persist_artifact_state(artifact)
        assert changed is True

        # Verify active_goal.json created
        goal = ws.read_active_goal(mock_agent)
        assert goal is not None
        assert goal["goal"] == "user auth"
        assert goal["source"] == "artifact_inference"

        # Verify current_phase.json set to DEFINE
        phase = ws.read_current_phase(mock_agent)
        assert phase is not None
        assert phase["phase"] == "DEFINE"

        # Verify progress_log.jsonl has events
        log = ws.read_progress_log(mock_agent)
        event_types = [e["event"] for e in log]
        assert "goal_set" in event_types
        assert "artifact_created" in event_types

        # Rehydrate via read_all_state
        state = ws.read_all_state(mock_agent)
        assert state["active_goal"]["goal"] == "user auth"
        assert state["current_phase"]["phase"] == "DEFINE"


class TestPlanInferencePipeline:
    """Plan artifact → active_plan + PLAN phase advancement → rehydration."""

    def test_plan_write_creates_plan_and_advances_phase(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ext = _make_ext(mock_agent)

        # Pre-set DEFINE phase (simulating prior spec write)
        ws.save_current_phase(mock_agent, {"phase": "DEFINE", "phases_completed": []})

        # Create plan file on disk
        plan_dir = tmp_project / "docs" / "plans"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "user-auth-plan.md"
        plan_file.write_text("# User Auth Plan\n")

        artifact = ext._detect_artifact_from_path("text_editor", {
            "action": "write",
            "path": str(plan_file),
        })
        assert artifact["artifact_type"] == "plan"
        assert artifact["slug"] == "user-auth"

        changed = ext._persist_artifact_state(artifact)
        assert changed is True

        # Verify active_plan.json
        plan = ws.read_active_plan(mock_agent)
        assert plan["plan_name"] == "user auth"
        assert plan["slug"] == "user-auth"

        # Verify phase advanced DEFINE → PLAN
        phase = ws.read_current_phase(mock_agent)
        assert phase["phase"] == "PLAN"

        # Rehydrate
        state = ws.read_all_state(mock_agent)
        assert state["active_plan"]["plan_name"] == "user auth"
        assert state["current_phase"]["phase"] == "PLAN"


class TestTodoInferencePipeline:
    """Todo artifact → current_task extraction → rehydration."""

    def test_todo_write_extracts_current_task(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ext = _make_ext(mock_agent)

        ws.save_current_phase(mock_agent, {"phase": "PLAN", "phases_completed": ["DEFINE"]})

        # Create todo file with unchecked tasks
        tasks_dir = tmp_project / "tasks"
        tasks_dir.mkdir(parents=True)
        todo_file = tasks_dir / "user-auth-todo.md"
        todo_file.write_text(
            "# Tasks\n\n"
            "- [ ] Task 1: Set up models\n"
            "- [ ] Task 2: Write tests\n"
            "- [x] Task 0: Already done\n"
        )

        artifact = ext._detect_artifact_from_path("text_editor", {
            "action": "write",
            "path": str(todo_file),
        })
        assert artifact["artifact_type"] == "todo"

        ext._persist_artifact_state(artifact)

        # Verify current_task extracted from first unchecked line
        plan = ws.read_active_plan(mock_agent)
        assert plan["current_task"] == "Task 1: Set up models"
        assert plan["slug"] == "user-auth"

        # Verify progress log has task_started event
        log = ws.read_progress_log(mock_agent)
        task_events = [e for e in log if e["event"] == "task_started"]
        assert len(task_events) == 1
        assert task_events[0]["current_task"] == "Task 1: Set up models"

        # Rehydrate
        state = ws.read_all_state(mock_agent)
        assert state["active_plan"]["current_task"] == "Task 1: Set up models"


class TestFullPipelineRehydration:
    """Sequential spec → plan → todo with rehydration after each step."""

    def test_sequential_artifact_writes_build_complete_state(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ext = _make_ext(mock_agent)

        # --- SPEC ---
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "payment-spec.md"
        spec_file.write_text("# Payment Spec\n")
        artifact = ext._detect_artifact_from_path("text_editor", {
            "action": "write", "path": str(spec_file),
        })
        ext._persist_artifact_state(artifact)

        # --- PLAN ---
        plan_dir = tmp_project / "docs" / "plans"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "payment-plan.md"
        plan_file.write_text("# Payment Plan\n")
        artifact = ext._detect_artifact_from_path("text_editor", {
            "action": "write", "path": str(plan_file),
        })
        ext._persist_artifact_state(artifact)

        # --- TODO ---
        tasks_dir = tmp_project / "tasks"
        tasks_dir.mkdir(parents=True)
        todo_file = tasks_dir / "payment-todo.md"
        todo_file.write_text("- [ ] Implement stripe webhook\n- [ ] Add retry logic\n")
        artifact = ext._detect_artifact_from_path("text_editor", {
            "action": "write", "path": str(todo_file),
        })
        ext._persist_artifact_state(artifact)

        # --- Full rehydration ---
        state = ws.read_all_state(mock_agent)
        assert state["active_goal"]["goal"] == "payment"
        assert state["current_phase"]["phase"] == "PLAN"

        # Todo write MERGES into active_plan; plan_name survives.
        plan = state["active_plan"]
        assert plan["slug"] == "payment"
        assert plan["current_task"] == "Implement stripe webhook"
        assert plan["plan_name"] == "payment"  # preserved by merge (not erased)

        # Verify progress log contains all expected events
        log = state.get("progress_log", [])
        event_types = [e["event"] for e in log]
        assert "goal_set" in event_types
        assert "plan_set" in event_types
        assert "task_started" in event_types
        assert event_types.count("artifact_created") == 3


class TestWorkflowArtifactPathsIntegration:
    """Verify that spec→plan→todo sequence writes all paths to workflow_artifacts.json."""

    def test_spec_plan_todo_all_paths_survive(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        ext = _make_ext(mock_agent)

        # --- SPEC ---
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "payment-spec.md"
        spec_file.write_text("# Payment Spec\n")
        artifact = ext._detect_artifact_from_path("text_editor", {
            "action": "write", "path": str(spec_file),
        })
        ext._persist_artifact_state(artifact)

        # After spec: workflow_artifacts.json has spec_path and feature_slug
        artifacts = ws.read_workflow_artifacts(mock_agent)
        assert artifacts is not None
        assert artifacts["spec_path"] == str(spec_file)
        assert artifacts["feature_slug"] == "payment"

        # --- PLAN ---
        plan_dir = tmp_project / "docs" / "plans"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "payment-plan.md"
        plan_file.write_text("# Payment Plan\n")
        artifact = ext._detect_artifact_from_path("text_editor", {
            "action": "write", "path": str(plan_file),
        })
        ext._persist_artifact_state(artifact)

        # After plan: plan_path added, spec_path and feature_slug still there
        artifacts = ws.read_workflow_artifacts(mock_agent)
        assert artifacts is not None
        assert artifacts["spec_path"] == str(spec_file)
        assert artifacts["feature_slug"] == "payment"
        assert artifacts["plan_path"] == str(plan_file)

        # --- TODO ---
        tasks_dir = tmp_project / "tasks"
        tasks_dir.mkdir(parents=True)
        todo_file = tasks_dir / "payment-todo.md"
        todo_file.write_text("- [ ] Implement stripe webhook\n- [ ] Add retry logic\n")
        artifact = ext._detect_artifact_from_path("text_editor", {
            "action": "write", "path": str(todo_file),
        })
        ext._persist_artifact_state(artifact)

        # After todo: all paths + feature_slug survive
        artifacts = ws.read_workflow_artifacts(mock_agent)
        assert artifacts is not None
        assert artifacts["spec_path"] == str(spec_file)
        assert artifacts["feature_slug"] == "payment"
        assert artifacts["plan_path"] == str(plan_file)
        assert artifacts["todo_path"] == str(todo_file)
