# Tests for artifact path-pattern auto-inference in _10_persist_workflow_state.py
#
# Covers: spec/plan/todo path detection, state persistence on artifact write,
# idempotency, phase forward-only advancement, fail-safe behavior.

from __future__ import annotations

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


def _make_agent(tmp_project, config=None):
    """Create a mock agent with project resolution and data."""
    agent = MagicMock()
    agent.context = MagicMock()
    agent.data = {"loaded_skills": []}

    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = "test_project"
    projects_mock.get_project_folder.return_value = str(tmp_project)

    cfg = config if config is not None else {
        "workflow_state_enabled": True,
        "artifact_inference_enabled": True,
    }
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
    """Create a PersistWorkflowState instance with the given agent."""
    ext_mod = _load_extension()
    ext = ext_mod.PersistWorkflowState.__new__(ext_mod.PersistWorkflowState)
    ext.agent = agent
    ext._artifact_mtimes = {}
    return ext


# ---------------------------------------------------------------------------
# Path pattern matching
# ---------------------------------------------------------------------------

class TestPathPatternMatching:
    """Test _detect_artifact_from_path returns correct artifact type and slug."""

    @pytest.mark.parametrize("path", [
        "docs/specs/user-auth-spec.md",
        "/home/user/project/docs/specs/user-auth-spec.md",
        "C:\\project\\docs\\specs\\user-auth-spec.md",
    ])
    def test_spec_pattern_with_slug(self, mock_agent, path):
        ext = _make_ext(mock_agent)
        result = ext._detect_artifact_from_path("text_editor", {
            "action": "write",
            "path": path,
        })
        assert result is not None
        assert result["artifact_type"] == "spec"
        assert result["phase"] == "DEFINE"
        assert result["slug"] == "user-auth"

    @pytest.mark.parametrize("path", [
        "SPEC.md",
        "project/SPEC.md",
    ])
    def test_spec_legacy_pattern(self, mock_agent, path):
        ext = _make_ext(mock_agent)
        result = ext._detect_artifact_from_path("text_editor", {
            "action": "write",
            "path": path,
        })
        assert result is not None
        assert result["artifact_type"] == "spec"
        assert result["slug"] is None  # No slug from SPEC.md

    @pytest.mark.parametrize("path", [
        "docs/plans/user-auth-plan.md",
        "/home/user/project/docs/plans/payment-integration-plan.md",
    ])
    def test_plan_pattern_with_slug(self, mock_agent, path):
        ext = _make_ext(mock_agent)
        result = ext._detect_artifact_from_path("text_editor", {
            "action": "write",
            "path": path,
        })
        assert result is not None
        assert result["artifact_type"] == "plan"
        assert result["phase"] == "PLAN"

    def test_plan_legacy_pattern(self, mock_agent):
        ext = _make_ext(mock_agent)
        result = ext._detect_artifact_from_path("text_editor", {
            "action": "write",
            "path": "tasks/plan.md",
        })
        assert result is not None
        assert result["artifact_type"] == "plan"
        assert result["slug"] is None

    @pytest.mark.parametrize("path", [
        "tasks/user-auth-todo.md",
        "/home/user/project/tasks/sprint-1-todo.md",
    ])
    def test_todo_pattern_with_slug(self, mock_agent, path):
        ext = _make_ext(mock_agent)
        result = ext._detect_artifact_from_path("text_editor", {
            "action": "write",
            "path": path,
        })
        assert result is not None
        assert result["artifact_type"] == "todo"
        assert result["phase"] == "PLAN"

    def test_todo_legacy_pattern(self, mock_agent):
        ext = _make_ext(mock_agent)
        result = ext._detect_artifact_from_path("text_editor", {
            "action": "write",
            "path": "tasks/todo.md",
        })
        assert result is not None
        assert result["artifact_type"] == "todo"
        assert result["slug"] is None

    @pytest.mark.parametrize("path", [
        "docs/reports/report.md",
        "README.md",
        "src/main.py",
        "docs/specs/spec.md",  # No slug part before -spec.md
        "tasks/",  # No filename
    ])
    def test_non_matching_paths_return_none(self, mock_agent, path):
        ext = _make_ext(mock_agent)
        result = ext._detect_artifact_from_path("text_editor", {
            "action": "write",
            "path": path,
        })
        assert result is None

    def test_patch_action_also_detected(self, mock_agent):
        ext = _make_ext(mock_agent)
        result = ext._detect_artifact_from_path("text_editor", {
            "action": "patch",
            "path": "docs/specs/feature-spec.md",
        })
        assert result is not None
        assert result["artifact_type"] == "spec"

    def test_read_action_ignored(self, mock_agent):
        ext = _make_ext(mock_agent)
        result = ext._detect_artifact_from_path("text_editor", {
            "action": "read",
            "path": "docs/specs/feature-spec.md",
        })
        assert result is None

    def test_non_text_editor_tool_ignored(self, mock_agent):
        ext = _make_ext(mock_agent)
        result = ext._detect_artifact_from_path("code_execution_tool", {
            "action": "write",
            "path": "docs/specs/feature-spec.md",
        })
        assert result is None


# ---------------------------------------------------------------------------
# Spec write triggers active_goal + DEFINE phase
# ---------------------------------------------------------------------------

class TestSpecArtifactPersistence:
    @pytest.mark.asyncio
    async def test_spec_write_saves_active_goal(self, mock_agent, tmp_project):
        # Create the spec file so mtime check works
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "user-auth-spec.md"
        spec_file.write_text("# Spec\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(spec_file),
            },
        )

        ws = _load_workflow_state()
        goal = ws.read_active_goal(mock_agent)
        assert goal is not None
        assert goal["goal"] == "user auth"
        assert goal["source"] == "artifact_inference"
        assert goal["slug"] == "user-auth"

    @pytest.mark.asyncio
    async def test_spec_write_sets_define_phase(self, mock_agent, tmp_project):
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "user-auth-spec.md"
        spec_file.write_text("# Spec\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(spec_file),
            },
        )

        ws = _load_workflow_state()
        phase = ws.read_current_phase(mock_agent)
        assert phase is not None
        assert phase["phase"] == "DEFINE"

    @pytest.mark.asyncio
    async def test_spec_write_appends_progress_events(self, mock_agent, tmp_project):
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "user-auth-spec.md"
        spec_file.write_text("# Spec\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(spec_file),
            },
        )

        ws = _load_workflow_state()
        log = ws.read_progress_log(mock_agent)
        event_types = [e["event"] for e in log]
        assert "goal_set" in event_types
        assert "artifact_created" in event_types

    @pytest.mark.asyncio
    async def test_spec_write_regenerates_handoff(self, mock_agent, tmp_project):
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "user-auth-spec.md"
        spec_file.write_text("# Spec\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(spec_file),
            },
        )

        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(mock_agent)
        assert os.path.exists(os.path.join(state_dir, "handoff.md"))


# ---------------------------------------------------------------------------
# Plan write triggers active_plan + PLAN phase
# ---------------------------------------------------------------------------

class TestPlanArtifactPersistence:
    @pytest.mark.asyncio
    async def test_plan_write_saves_active_plan(self, mock_agent, tmp_project):
        plan_dir = tmp_project / "docs" / "plans"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "user-auth-plan.md"
        plan_file.write_text("# Plan\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(plan_file),
            },
        )

        ws = _load_workflow_state()
        plan = ws.read_active_plan(mock_agent)
        assert plan is not None
        assert plan["plan_name"] == "user auth"
        assert plan["slug"] == "user-auth"

    @pytest.mark.asyncio
    async def test_plan_write_sets_plan_phase(self, mock_agent, tmp_project):
        plan_dir = tmp_project / "docs" / "plans"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "user-auth-plan.md"
        plan_file.write_text("# Plan\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(plan_file),
            },
        )

        ws = _load_workflow_state()
        phase = ws.read_current_phase(mock_agent)
        assert phase is not None
        assert phase["phase"] == "PLAN"


# ---------------------------------------------------------------------------
# Todo write updates current_task
# ---------------------------------------------------------------------------

class TestTodoArtifactPersistence:
    @pytest.mark.asyncio
    async def test_todo_write_saves_current_task(self, mock_agent, tmp_project):
        tasks_dir = tmp_project / "tasks"
        tasks_dir.mkdir(parents=True)
        todo_file = tasks_dir / "user-auth-todo.md"
        todo_file.write_text("# Todo\n- [ ] Implement login\n- [x] Setup project\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(todo_file),
            },
        )

        ws = _load_workflow_state()
        plan = ws.read_active_plan(mock_agent)
        assert plan is not None
        assert plan.get("current_task") == "Implement login"

    @pytest.mark.asyncio
    async def test_todo_write_with_no_unchecked_tasks(self, mock_agent, tmp_project):
        tasks_dir = tmp_project / "tasks"
        tasks_dir.mkdir(parents=True)
        todo_file = tasks_dir / "user-auth-todo.md"
        todo_file.write_text("# Todo\n- [x] Done\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(todo_file),
            },
        )

        ws = _load_workflow_state()
        plan = ws.read_active_plan(mock_agent)
        assert plan is not None
        # current_task may not be present if no unchecked task
        assert plan.get("current_task") is None


# ---------------------------------------------------------------------------
# Path A merge: plan_name survives TODO write
# ---------------------------------------------------------------------------

class TestTodoMergePreservesPlanName:
    """Path A: after spec→plan→todo, active_plan.json must contain BOTH
    plan_name AND current_task (TODO handler merges, not replaces)."""

    @pytest.mark.asyncio
    async def test_plan_name_survives_todo_write(self, mock_agent, tmp_project):
        ws = _load_workflow_state()

        # Pre-set PLAN phase (simulating prior spec write)
        ws.save_current_phase(mock_agent, {"phase": "PLAN", "phases_completed": ["DEFINE"]})

        # --- PLAN write → sets plan_name ---
        plan_dir = tmp_project / "docs" / "plans"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "payment-plan.md"
        plan_file.write_text("# Payment Plan\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(plan_file)},
        )

        plan = ws.read_active_plan(mock_agent)
        assert plan is not None
        assert plan["plan_name"] == "payment"
        assert plan["slug"] == "payment"

        # --- TODO write → must preserve plan_name ---
        tasks_dir = tmp_project / "tasks"
        tasks_dir.mkdir(parents=True)
        todo_file = tasks_dir / "payment-todo.md"
        todo_file.write_text("- [ ] Implement webhook\n- [ ] Add retry logic\n")

        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(todo_file)},
        )

        plan = ws.read_active_plan(mock_agent)
        assert plan is not None
        assert plan["plan_name"] == "payment"  # preserved by merge
        assert plan["current_task"] == "Implement webhook"
        assert plan["slug"] == "payment"


# ---------------------------------------------------------------------------
# Idempotency — same file written twice = no duplicate events
# ---------------------------------------------------------------------------

class TestIdempotency:
    @pytest.mark.asyncio
    async def test_same_mtime_no_duplicate_events(self, mock_agent, tmp_project):
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "feature-spec.md"
        spec_file.write_text("# Spec\n")

        ext = _make_ext(mock_agent)

        # First write
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(spec_file),
            },
        )

        ws = _load_workflow_state()
        log_after_first = ws.read_progress_log(mock_agent)
        first_count = len([e for e in log_after_first if e.get("event") == "goal_set"])

        # Second write with same mtime (file unchanged)
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(spec_file),
            },
        )

        log_after_second = ws.read_progress_log(mock_agent)
        second_count = len([e for e in log_after_second if e.get("event") == "goal_set"])

        assert first_count == second_count  # No duplicate

    @pytest.mark.asyncio
    async def test_different_mtime_creates_new_event(self, mock_agent, tmp_project):
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "feature-spec.md"
        spec_file.write_text("# Spec v1\n")

        ext = _make_ext(mock_agent)

        # First write
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(spec_file),
            },
        )

        # Modify file (change mtime)
        time.sleep(0.05)
        spec_file.write_text("# Spec v2\n")

        # Second write with different mtime
        await ext.execute(
            tool_name="text_editor",
            tool_args={
                "action": "write",
                "path": str(spec_file),
            },
        )

        ws = _load_workflow_state()
        log = ws.read_progress_log(mock_agent)
        goal_events = [e for e in log if e.get("event") == "goal_set"]
        assert len(goal_events) == 2  # New event created


# ---------------------------------------------------------------------------
# Phase forward-only advancement
# ---------------------------------------------------------------------------

class TestPhaseAdvancement:
    @pytest.mark.asyncio
    async def test_phase_only_advances_forward(self, mock_agent, tmp_project):
        # First: write a spec → DEFINE
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "feature-spec.md"
        spec_file.write_text("# Spec\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(spec_file)},
        )

        ws = _load_workflow_state()
        phase = ws.read_current_phase(mock_agent)
        assert phase["phase"] == "DEFINE"

        # Second: write a plan → PLAN (forward)
        plan_dir = tmp_project / "docs" / "plans"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "feature-plan.md"
        plan_file.write_text("# Plan\n")

        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(plan_file)},
        )

        phase = ws.read_current_phase(mock_agent)
        assert phase["phase"] == "PLAN"

        # Third: write another spec → should NOT rewind to DEFINE
        time.sleep(0.05)
        spec_file.write_text("# Spec v2\n")
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(spec_file)},
        )

        phase = ws.read_current_phase(mock_agent)
        assert phase["phase"] == "PLAN"  # Still PLAN, did not rewind

    @pytest.mark.asyncio
    async def test_advance_to_plan_includes_define_in_completed(self, mock_agent, tmp_project):
        """Bug #2: advancing phase should populate phases_completed correctly.

        When advancing from DEFINE to PLAN via plan artifact write,
        phases_completed should include DEFINE (not be empty).
        """
        ws = _load_workflow_state()

        # Write a spec → DEFINE
        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "feature-spec.md"
        spec_file.write_text("# Spec\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(spec_file)},
        )

        phase = ws.read_current_phase(mock_agent)
        assert phase["phase"] == "DEFINE"

        # Write a plan → PLAN (forward advance)
        plan_dir = tmp_project / "docs" / "plans"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "feature-plan.md"
        plan_file.write_text("# Plan\n")

        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(plan_file)},
        )

        phase = ws.read_current_phase(mock_agent)
        assert phase["phase"] == "PLAN"
        # Bug #2 fix: phases_completed should include DEFINE
        assert "DEFINE" in phase.get("phases_completed", []), \
            f"Expected DEFINE in phases_completed, got {phase.get('phases_completed')}"


# ---------------------------------------------------------------------------
# Config disabled behavior
# ---------------------------------------------------------------------------

class TestConfigDisabled:
    @pytest.mark.asyncio
    async def test_artifact_inference_disabled(self, tmp_project):
        agent = _make_agent(tmp_project, config={
            "workflow_state_enabled": True,
            "artifact_inference_enabled": False,
        })

        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "feature-spec.md"
        spec_file.write_text("# Spec\n")

        ext = _make_ext(agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(spec_file)},
        )

        ws = _load_workflow_state()
        goal = ws.read_active_goal(agent)
        assert goal is None  # No state written

    @pytest.mark.asyncio
    async def test_workflow_state_disabled_skips_all(self, tmp_project):
        agent = _make_agent(tmp_project, config={
            "workflow_state_enabled": False,
            "artifact_inference_enabled": True,
        })

        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "feature-spec.md"
        spec_file.write_text("# Spec\n")

        ext = _make_ext(agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(spec_file)},
        )

        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(agent)
        # State dir should not exist or have no state files
        assert not os.path.exists(os.path.join(state_dir, "active_goal.json"))


# ---------------------------------------------------------------------------
# Fail-safe — never break the agent loop
# ---------------------------------------------------------------------------

class TestFailSafe:
    @pytest.mark.asyncio
    async def test_corrupt_path_does_not_raise(self, mock_agent):
        ext = _make_ext(mock_agent)
        # Should not raise
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": None},
        )

    @pytest.mark.asyncio
    async def test_missing_args_does_not_raise(self, mock_agent):
        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={},
        )

    @pytest.mark.asyncio
    async def test_nonexistent_path_does_not_raise(self, mock_agent):
        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": "/nonexistent/path/spec.md"},
        )

    @pytest.mark.asyncio
    async def test_non_dict_args_does_not_raise(self, mock_agent):
        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args="not a dict",
        )

    @pytest.mark.asyncio
    async def test_no_args_at_all_does_not_raise(self, mock_agent):
        ext = _make_ext(mock_agent)
        await ext.execute(tool_name="text_editor")


# ---------------------------------------------------------------------------
# Slug extraction edge cases
# ---------------------------------------------------------------------------

class TestSlugExtraction:
    def test_extract_slug_standard(self):
        ext_mod = _load_extension()
        assert ext_mod._extract_slug("user-auth-spec.md", "-spec.md") == "user-auth"

    def test_extract_slug_multi_part(self):
        ext_mod = _load_extension()
        assert ext_mod._extract_slug("my-cool-feature-spec.md", "-spec.md") == "my-cool-feature"

    def test_extract_slug_with_path(self):
        ext_mod = _load_extension()
        assert ext_mod._extract_slug("/a0/docs/specs/payment-spec.md", "-spec.md") == "payment"

    def test_extract_slug_no_match(self):
        ext_mod = _load_extension()
        assert ext_mod._extract_slug("SPEC.md", "-spec.md") is None

    def test_extract_slug_plan(self):
        ext_mod = _load_extension()
        assert ext_mod._extract_slug("user-auth-plan.md", "-plan.md") == "user-auth"

    def test_extract_slug_todo(self):
        ext_mod = _load_extension()
        assert ext_mod._extract_slug("sprint-1-todo.md", "-todo.md") == "sprint-1"


# ---------------------------------------------------------------------------
# Workflow artifact path wiring (merge_workflow_artifact)
# ---------------------------------------------------------------------------

class TestWorkflowArtifactPathWiring:
    """Verify that _persist_artifact_state writes artifact paths to
    workflow_artifacts.json via merge_workflow_artifact."""

    @pytest.mark.asyncio
    async def test_spec_write_sets_spec_path_and_feature_slug(self, mock_agent, tmp_project):
        ws = _load_workflow_state()

        spec_dir = tmp_project / "docs" / "specs"
        spec_dir.mkdir(parents=True)
        spec_file = spec_dir / "user-auth-spec.md"
        spec_file.write_text("# Spec\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(spec_file)},
        )

        artifacts = ws.read_workflow_artifacts(mock_agent)
        assert artifacts is not None
        assert artifacts["spec_path"] == str(spec_file)
        assert artifacts["feature_slug"] == "user-auth"

    @pytest.mark.asyncio
    async def test_plan_write_sets_plan_path(self, mock_agent, tmp_project):
        ws = _load_workflow_state()

        plan_dir = tmp_project / "docs" / "plans"
        plan_dir.mkdir(parents=True)
        plan_file = plan_dir / "user-auth-plan.md"
        plan_file.write_text("# Plan\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(plan_file)},
        )

        artifacts = ws.read_workflow_artifacts(mock_agent)
        assert artifacts is not None
        assert artifacts["plan_path"] == str(plan_file)

    @pytest.mark.asyncio
    async def test_todo_write_sets_todo_path(self, mock_agent, tmp_project):
        ws = _load_workflow_state()

        tasks_dir = tmp_project / "tasks"
        tasks_dir.mkdir(parents=True)
        todo_file = tasks_dir / "user-auth-todo.md"
        todo_file.write_text("- [ ] Task 1\n")

        ext = _make_ext(mock_agent)
        await ext.execute(
            tool_name="text_editor",
            tool_args={"action": "write", "path": str(todo_file)},
        )

        artifacts = ws.read_workflow_artifacts(mock_agent)
        assert artifacts is not None
        assert artifacts["todo_path"] == str(todo_file)
