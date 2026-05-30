# Tests for helpers/workflow_state.py -- sole owner of .a0proj/state/ I/O.
#
# Covers: read/write for all 7 artifact types, missing files, corrupt files,
# path traversal prevention, JSONL format, handoff markdown, read_all_state,
# checkpoint CRUD, lazy directory creation.

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Plugin helper module loader -- loads workflow_state.py via importlib
# ---------------------------------------------------------------------------

_ws_module = None


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
    assert ws_path.exists(), f"workflow_state.py not found at {ws_path}"

    spec = importlib.util.spec_from_file_location("helpers.workflow_state", str(ws_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules["helpers.workflow_state"] = mod
    _ws_module = mod
    return mod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _setup_ws_module():
    """Ensure the workflow_state module is loaded before each test."""
    _load_workflow_state()


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory."""
    proj = tmp_path / "test_project"
    proj.mkdir()
    return proj


def _make_agent(tmp_project):
    """Create a mock agent that resolves state dir to tmp_project/.a0proj/state/."""
    agent = MagicMock()
    agent.context = MagicMock()

    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = "test_project"
    projects_mock.get_project_folder.return_value = str(tmp_project)

    helpers_mock = MagicMock()
    helpers_mock.projects = projects_mock
    sys.modules["helpers"] = helpers_mock
    sys.modules["helpers.projects"] = projects_mock
    sys.modules["helpers.plugins"] = MagicMock()

    return agent


@pytest.fixture
def mock_agent(tmp_project):
    return _make_agent(tmp_project)


@pytest.fixture
def no_project_agent():
    """Mock agent where project resolution fails."""
    agent = MagicMock()
    agent.context = None

    projects_mock = MagicMock()
    projects_mock.get_context_project_name.return_value = None

    helpers_mock = MagicMock()
    helpers_mock.projects = projects_mock
    sys.modules["helpers"] = helpers_mock
    sys.modules["helpers.projects"] = projects_mock
    sys.modules["helpers.plugins"] = MagicMock()

    return agent


# ---------------------------------------------------------------------------
# resolve_state_dir
# ---------------------------------------------------------------------------

class TestResolveStateDir:
    def test_returns_path_with_valid_project(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        result = ws.resolve_state_dir(mock_agent)
        assert result is not None
        assert ".a0proj" in result
        assert "state" in result
        assert result.startswith(str(tmp_project))

    def test_returns_none_when_no_project(self, no_project_agent):
        ws = _load_workflow_state()
        assert ws.resolve_state_dir(no_project_agent) is None

    def test_returns_none_when_agent_is_none(self):
        ws = _load_workflow_state()
        assert ws.resolve_state_dir(None) is None

    def test_creates_no_directory_on_resolve(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        result = ws.resolve_state_dir(mock_agent)
        assert result is not None
        assert not os.path.exists(result)


# ---------------------------------------------------------------------------
# Active plan
# ---------------------------------------------------------------------------

class TestActivePlan:
    def test_save_and_read_roundtrip(self, mock_agent):
        ws = _load_workflow_state()
        data = {"plan_name": "test-plan", "plan_path": "docs/plan.md",
                "current_task": "Task 1", "tasks_total": 3, "tasks_completed": 0}
        path = ws.save_active_plan(mock_agent, data)
        assert path is not None
        assert os.path.exists(path)

        result = ws.read_active_plan(mock_agent)
        assert result is not None
        assert result["plan_name"] == "test-plan"
        assert result["version"] == 1
        assert "updated_at" in result

    def test_read_missing_returns_none(self, mock_agent):
        ws = _load_workflow_state()
        assert ws.read_active_plan(mock_agent) is None

    def test_read_corrupt_returns_none(self, mock_agent):
        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(mock_agent)
        os.makedirs(state_dir, exist_ok=True)
        with open(os.path.join(state_dir, "active_plan.json"), "w") as f:
            f.write("{invalid json!!!")
        assert ws.read_active_plan(mock_agent) is None

    def test_save_returns_none_when_no_project(self, no_project_agent):
        ws = _load_workflow_state()
        assert ws.save_active_plan(no_project_agent, {"plan_name": "x"}) is None

    def test_lazy_directory_creation(self, mock_agent, tmp_project):
        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(mock_agent)
        assert not os.path.exists(state_dir)
        ws.save_active_plan(mock_agent, {"plan_name": "test"})
        assert os.path.exists(state_dir)
        assert os.path.exists(os.path.join(state_dir, "active_plan.json"))


# ---------------------------------------------------------------------------
# Active goal
# ---------------------------------------------------------------------------

class TestActiveGoal:
    def test_save_and_read_roundtrip(self, mock_agent):
        ws = _load_workflow_state()
        data = {"goal": "Build durable workflow state", "source": "user message"}
        path = ws.save_active_goal(mock_agent, data)
        assert path is not None

        result = ws.read_active_goal(mock_agent)
        assert result["goal"] == "Build durable workflow state"
        assert result["version"] == 1

    def test_read_missing_returns_none(self, mock_agent):
        ws = _load_workflow_state()
        assert ws.read_active_goal(mock_agent) is None

    def test_read_corrupt_returns_none(self, mock_agent):
        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(mock_agent)
        os.makedirs(state_dir, exist_ok=True)
        with open(os.path.join(state_dir, "active_goal.json"), "w") as f:
            f.write("not json at all")
        assert ws.read_active_goal(mock_agent) is None

    def test_save_returns_none_when_no_project(self, no_project_agent):
        ws = _load_workflow_state()
        assert ws.save_active_goal(no_project_agent, {"goal": "x"}) is None


# ---------------------------------------------------------------------------
# Current phase
# ---------------------------------------------------------------------------

class TestCurrentPhase:
    def test_save_and_read_roundtrip(self, mock_agent):
        ws = _load_workflow_state()
        data = {"phase": "BUILD", "phases_completed": ["DEFINE", "PLAN"]}
        path = ws.save_current_phase(mock_agent, data)
        assert path is not None

        result = ws.read_current_phase(mock_agent)
        assert result["phase"] == "BUILD"
        assert result["phases_completed"] == ["DEFINE", "PLAN"]
        assert result["version"] == 1
        assert "entered_at" in result

    def test_entered_at_set_when_missing(self, mock_agent):
        ws = _load_workflow_state()
        ws.save_current_phase(mock_agent, {"phase": "PLAN"})
        result = ws.read_current_phase(mock_agent)
        assert "entered_at" in result

    def test_read_missing_returns_none(self, mock_agent):
        ws = _load_workflow_state()
        assert ws.read_current_phase(mock_agent) is None

    def test_read_corrupt_returns_none(self, mock_agent):
        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(mock_agent)
        os.makedirs(state_dir, exist_ok=True)
        with open(os.path.join(state_dir, "current_phase.json"), "w") as f:
            f.write("}{broken")
        assert ws.read_current_phase(mock_agent) is None


# ---------------------------------------------------------------------------
# Loaded skills
# ---------------------------------------------------------------------------

class TestLoadedSkills:
    def test_save_and_read_roundtrip(self, mock_agent):
        ws = _load_workflow_state()
        data = {"skills": [
            {"name": "incremental-implementation", "loaded_at": 1234567890.0},
            {"name": "test-driven-development", "loaded_at": 1234567891.0},
        ]}
        path = ws.save_loaded_skills(mock_agent, data)
        assert path is not None

        result = ws.read_loaded_skills(mock_agent)
        assert result["version"] == 1
        assert len(result["skills"]) == 2
        assert result["skills"][0]["name"] == "incremental-implementation"

    def test_read_missing_returns_none(self, mock_agent):
        ws = _load_workflow_state()
        assert ws.read_loaded_skills(mock_agent) is None

    def test_save_returns_none_when_no_project(self, no_project_agent):
        ws = _load_workflow_state()
        assert ws.save_loaded_skills(no_project_agent, {"skills": []}) is None

    def test_skills_compatible_with_get_loaded_skills(self, mock_agent):
        """Verify that loaded_skills.json format works with skill_match.get_loaded_skills()."""
        ws = _load_workflow_state()
        data = {"skills": [
            {"name": "incremental-implementation", "loaded_at": 1234567890.0},
            {"name": "test-driven-development", "loaded_at": 1234567891.0},
        ]}
        ws.save_loaded_skills(mock_agent, data)
        result = ws.read_loaded_skills(mock_agent)

        # skill_match.get_loaded_skills reads from agent.data['loaded_skills']
        # which expects a list of skill name strings
        skill_names = [s["name"] for s in result["skills"]]
        assert skill_names == ["incremental-implementation", "test-driven-development"]

        # Simulating what skill_match.get_loaded_skills does:
        # It reads agent.data['loaded_skills'] as a list
        # The rehydrate extension should set agent.data['loaded_skills'] = skill_names
        assert isinstance(skill_names, list)
        assert all(isinstance(s, str) for s in skill_names)


# ---------------------------------------------------------------------------
# Checkpoints
# ---------------------------------------------------------------------------

class TestCheckpoints:
    def test_save_and_read_roundtrip(self, mock_agent):
        ws = _load_workflow_state()
        data = {"checkpoints": [{
            "id": "cp-001", "label": "Test checkpoint",
            "created_at": 1234567890.0, "phase": "BUILD", "task": "Task 1",
        }]}
        path = ws.save_checkpoints(mock_agent, data)
        assert path is not None

        result = ws.read_checkpoints(mock_agent)
        assert result["version"] == 1
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["id"] == "cp-001"

    def test_read_missing_returns_none(self, mock_agent):
        ws = _load_workflow_state()
        assert ws.read_checkpoints(mock_agent) is None

    def test_read_corrupt_returns_none(self, mock_agent):
        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(mock_agent)
        os.makedirs(state_dir, exist_ok=True)
        with open(os.path.join(state_dir, "checkpoints.json"), "w") as f:
            f.write("not json")
        assert ws.read_checkpoints(mock_agent) is None


class TestCheckpointCRUD:
    def test_create_checkpoint(self, mock_agent):
        ws = _load_workflow_state()
        cp_id = ws.create_checkpoint(mock_agent, "First checkpoint",
                                     phase="BUILD", task="Task 1")
        assert cp_id == "cp-001"

        result = ws.read_checkpoints(mock_agent)
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0]["label"] == "First checkpoint"

    def test_create_multiple_checkpoints(self, mock_agent):
        ws = _load_workflow_state()
        id1 = ws.create_checkpoint(mock_agent, "First")
        id2 = ws.create_checkpoint(mock_agent, "Second")
        assert id1 == "cp-001"
        assert id2 == "cp-002"

        result = ws.read_checkpoints(mock_agent)
        assert len(result["checkpoints"]) == 2

    def test_update_checkpoint(self, mock_agent):
        ws = _load_workflow_state()
        cp_id = ws.create_checkpoint(mock_agent, "Original")
        updated = ws.update_checkpoint(mock_agent, cp_id, {"label": "Updated", "notes": "Added notes"})
        assert updated is True

        result = ws.read_checkpoints(mock_agent)
        assert result["checkpoints"][0]["label"] == "Updated"
        assert result["checkpoints"][0]["notes"] == "Added notes"

    def test_update_nonexistent_checkpoint(self, mock_agent):
        ws = _load_workflow_state()
        assert ws.update_checkpoint(mock_agent, "cp-999", {"label": "Nope"}) is False

    def test_create_returns_none_when_no_project(self, no_project_agent):
        ws = _load_workflow_state()
        assert ws.create_checkpoint(no_project_agent, "test") is None


# ---------------------------------------------------------------------------
# Progress log (JSONL)
# ---------------------------------------------------------------------------

class TestProgressLog:
    def test_append_and_read(self, mock_agent):
        ws = _load_workflow_state()
        event = {"event": "phase_change", "from": "DEFINE", "to": "PLAN"}
        path = ws.append_progress_event(mock_agent, event)
        assert path is not None

        entries = ws.read_progress_log(mock_agent)
        assert len(entries) == 1
        assert entries[0]["event"] == "phase_change"
        assert entries[0]["from"] == "DEFINE"
        assert "ts" in entries[0]

    def test_append_adds_ts_automatically(self, mock_agent):
        ws = _load_workflow_state()
        ws.append_progress_event(mock_agent, {"event": "task_started", "task": "T1"})
        entries = ws.read_progress_log(mock_agent)
        assert "ts" in entries[0]

    def test_preserves_existing_ts(self, mock_agent):
        ws = _load_workflow_state()
        ws.append_progress_event(mock_agent, {"event": "custom", "ts": 42.0})
        entries = ws.read_progress_log(mock_agent)
        assert entries[0]["ts"] == 42.0

    def test_append_is_additive(self, mock_agent):
        ws = _load_workflow_state()
        ws.append_progress_event(mock_agent, {"event": "task_started", "task": "T1"})
        ws.append_progress_event(mock_agent, {"event": "task_completed", "task": "T1"})
        entries = ws.read_progress_log(mock_agent)
        assert len(entries) == 2
        assert entries[0]["event"] == "task_started"
        assert entries[1]["event"] == "task_completed"

    def test_each_line_is_valid_json(self, mock_agent):
        ws = _load_workflow_state()
        ws.append_progress_event(mock_agent, {"event": "skill_loaded", "skill": "tdd"})
        ws.append_progress_event(mock_agent, {"event": "skill_unloaded", "skill": "tdd"})

        state_dir = ws.resolve_state_dir(mock_agent)
        log_path = os.path.join(state_dir, "progress_log.jsonl")
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if line:
                    json.loads(line)  # should not raise

    def test_read_missing_returns_empty_list(self, mock_agent):
        ws = _load_workflow_state()
        assert ws.read_progress_log(mock_agent) == []

    def test_read_skips_invalid_lines(self, mock_agent):
        ws = _load_workflow_state()
        state_dir = ws.resolve_state_dir(mock_agent)
        os.makedirs(state_dir, exist_ok=True)
        log_path = os.path.join(state_dir, "progress_log.jsonl")
        with open(log_path, "w") as f:
            f.write('{"event":"valid","ts":1.0}\n')
            f.write('not valid json\n')
            f.write('{"event":"also_valid","ts":2.0}\n')
        entries = ws.read_progress_log(mock_agent)
        assert len(entries) == 2
        assert entries[0]["event"] == "valid"
        assert entries[1]["event"] == "also_valid"

    def test_append_returns_none_when_no_project(self, no_project_agent):
        ws = _load_workflow_state()
        assert ws.append_progress_event(no_project_agent, {"event": "custom"}) is None

    def test_all_event_types(self, mock_agent):
        """Verify all spec-defined event types can be appended."""
        ws = _load_workflow_state()
        event_types = [
            "phase_change", "skill_loaded", "skill_unloaded",
            "task_started", "task_completed", "checkpoint",
            "goal_set", "plan_set", "custom",
        ]
        for et in event_types:
            result = ws.append_progress_event(mock_agent, {"event": et})
            assert result is not None, f"Failed for event type: {et}"

        entries = ws.read_progress_log(mock_agent)
        assert len(entries) == len(event_types)
        actual_events = {e["event"] for e in entries}
        assert actual_events == set(event_types)


# ---------------------------------------------------------------------------
# Handoff markdown
# ---------------------------------------------------------------------------

class TestHandoff:
    def test_write_creates_markdown(self, mock_agent):
        ws = _load_workflow_state()
        ws.save_active_plan(mock_agent, {"plan_name": "test", "plan_path": "docs/plan.md",
                                          "current_task": "Task 1"})
        ws.save_active_goal(mock_agent, {"goal": "Build it"})
        ws.save_current_phase(mock_agent, {"phase": "BUILD"})

        path = ws.write_handoff(mock_agent)
        assert path is not None
        assert os.path.exists(path)

        with open(path) as f:
            content = f.read()

        assert "# Workflow Handoff" in content
        assert "**Phase:** BUILD" in content
        assert "**Goal:** Build it" in content
        assert "**Plan:** docs/plan.md" in content
        assert "**Current Task:** Task 1" in content
        assert "**Updated:**" in content

    def test_handoff_with_skills(self, mock_agent):
        ws = _load_workflow_state()
        ws.save_loaded_skills(mock_agent, {"skills": [
            {"name": "tdd", "loaded_at": 1.0},
            {"name": "sdd", "loaded_at": 2.0},
        ]})
        path = ws.write_handoff(mock_agent)
        with open(path) as f:
            content = f.read()
        assert "**Loaded Skills:** tdd, sdd" in content

    def test_handoff_with_no_skills(self, mock_agent):
        ws = _load_workflow_state()
        path = ws.write_handoff(mock_agent)
        with open(path) as f:
            content = f.read()
        assert "**Loaded Skills:** (none)" in content

    def test_handoff_with_checkpoint(self, mock_agent):
        ws = _load_workflow_state()
        ws.create_checkpoint(mock_agent, "Milestone 1", phase="BUILD")
        path = ws.write_handoff(mock_agent)
        with open(path) as f:
            content = f.read()
        assert "**Last Checkpoint:** cp-001" in content
        assert "Milestone 1" in content

    def test_handoff_no_checkpoint(self, mock_agent):
        ws = _load_workflow_state()
        path = ws.write_handoff(mock_agent)
        with open(path) as f:
            content = f.read()
        assert "**Last Checkpoint:** (none)" in content

    def test_write_handoff_returns_none_when_no_project(self, no_project_agent):
        ws = _load_workflow_state()
        assert ws.write_handoff(no_project_agent) is None


# ---------------------------------------------------------------------------
# read_all_state
# ---------------------------------------------------------------------------

class TestReadAllState:
    def test_returns_consolidated_dict_when_files_exist(self, mock_agent):
        ws = _load_workflow_state()
        ws.save_active_plan(mock_agent, {"plan_name": "test"})
        ws.save_active_goal(mock_agent, {"goal": "Build"})
        ws.save_current_phase(mock_agent, {"phase": "BUILD"})
        ws.save_loaded_skills(mock_agent, {"skills": [{"name": "tdd"}]})
        ws.save_checkpoints(mock_agent, {"checkpoints": []})
        ws.append_progress_event(mock_agent, {"event": "custom"})

        result = ws.read_all_state(mock_agent)
        assert "active_plan" in result
        assert "active_goal" in result
        assert "current_phase" in result
        assert "loaded_skills" in result
        assert "checkpoints" in result
        assert "progress_log" in result
        assert result["active_plan"]["plan_name"] == "test"
        assert result["active_goal"]["goal"] == "Build"
        assert result["current_phase"]["phase"] == "BUILD"

    def test_returns_empty_dict_when_no_files(self, mock_agent):
        ws = _load_workflow_state()
        result = ws.read_all_state(mock_agent)
        assert result == {}

    def test_partial_state_returns_only_existing(self, mock_agent):
        ws = _load_workflow_state()
        ws.save_active_plan(mock_agent, {"plan_name": "test"})
        result = ws.read_all_state(mock_agent)
        assert "active_plan" in result
        assert "active_goal" not in result
        assert "progress_log" not in result  # no events = not included


# ---------------------------------------------------------------------------
# Path traversal prevention
# ---------------------------------------------------------------------------

class TestPathTraversal:
    def test_state_path_rejects_traversal(self):
        ws = _load_workflow_state()
        with pytest.raises(ValueError, match="[Pp]ath traversal"):
            ws._state_path("/safe/dir", "../../etc/passwd")

    def test_state_path_rejects_absolute(self):
        ws = _load_workflow_state()
        with pytest.raises(ValueError, match="[Pp]ath traversal"):
            ws._state_path("/safe/dir", "/etc/passwd")

    def test_state_path_accepts_normal_filename(self):
        ws = _load_workflow_state()
        result = ws._state_path("/safe/dir", "active_plan.json")
        assert result == os.path.join("/safe/dir", "active_plan.json")

    def test_state_path_rejects_dotdot_in_dirs(self):
        ws = _load_workflow_state()
        with pytest.raises(ValueError):
            ws._state_path("/safe/dir", "sub/../../../etc/passwd")
