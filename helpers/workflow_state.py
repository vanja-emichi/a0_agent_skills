"""Workflow-state helper — sole owner of .a0proj/state/ I/O.

Provides read/write functions for all durable workflow state artifacts:
- active_plan.json
- active_goal.json
- current_phase.json
- loaded_skills.json
- checkpoints.json
- progress_log.jsonl
- handoff.md

Extensions must call this helper; they never touch state files directly.
All functions are fail-safe — missing/corrupt files return safe defaults.
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import pathlib
import sys
import time
import threading
from typing import Any

_log = logging.getLogger(__name__)
_write_lock = threading.Lock()


def _bootstrap_plugin_loader():
    if '_plugin_loader' not in sys.modules:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.normpath(os.path.join(this_dir, '..'))
        spec = importlib.util.spec_from_file_location(
            '_plugin_loader', os.path.join(plugin_root, '_plugin_loader.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules['_plugin_loader'] = mod
        spec.loader.exec_module(mod)
    return sys.modules['_plugin_loader']


def _get_plugin_config(agent) -> dict:
    try:
        return _bootstrap_plugin_loader().get_plugin_config(agent)
    except Exception:
        return {}


_VALID_PHASES = frozenset({"DEFINE", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP"})
_VALID_EVENT_TYPES = frozenset({
    "phase_change", "skill_loaded", "skill_unloaded",
    "task_started", "task_completed", "checkpoint",
    "goal_set", "plan_set", "gate_correction", "custom",
})

STATE_DIR_NAME = ".a0proj/state"
VERSION = 1

DEFAULT_MAX_PROGRESS_ENTRIES = 10_000

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def resolve_state_dir(agent) -> str | None:
    try:
        from helpers import projects as _projects
        if agent and hasattr(agent, "context") and agent.context:
            proj_name = _projects.get_context_project_name(agent.context)
            if proj_name:
                proj_folder = _projects.get_project_folder(proj_name)
                if proj_folder:
                    state_dir = os.path.join(proj_folder, STATE_DIR_NAME.replace("/", os.sep))
                    base = pathlib.Path(proj_folder).resolve()
                    candidate = pathlib.Path(state_dir).resolve()
                    try:
                        candidate.relative_to(base)
                    except ValueError:
                        return None
                    return str(candidate)
    except Exception:
        _log.warning("resolve_state_dir failed — possible path issue", exc_info=True)
        pass
    return None


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True, mode=0o750)


def _safe_read_json(path: str, default: Any = None) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        _log.warning("Corrupt state file %s: %s", path, exc)
        return default


def _safe_write_json(path: str, data: dict) -> None:
    if os.path.exists(path) and os.path.islink(path):
        raise ValueError(f"Refusing to write to symlink: {path}")

    dir_name = os.path.dirname(path)
    if dir_name:
        _ensure_dir(dir_name)
    with _write_lock:
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
            os.replace(tmp_path, path)
            try:
                os.chmod(path, 0o640)
            except OSError:
                pass
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


def _state_path(state_dir: str, filename: str) -> str:
    full = os.path.join(state_dir, filename)
    base = pathlib.Path(state_dir).resolve()
    candidate = pathlib.Path(full).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        raise ValueError(f"Path traversal detected: {filename}")
    return str(candidate)


def _save_artifact(agent, filename: str, data: dict) -> str | None:
    try:
        state_dir = resolve_state_dir(agent)
        if not state_dir:
            return None
        path = _state_path(state_dir, filename)
        data["version"] = VERSION
        data["updated_at"] = time.time()
        _safe_write_json(path, data)
        return path
    except Exception as exc:
        _log.warning("Failed to save %s: %s", filename, exc)
        return None


def _read_artifact(agent, filename: str) -> dict | None:
    try:
        state_dir = resolve_state_dir(agent)
        if not state_dir:
            return None
        path = _state_path(state_dir, filename)
        data = _safe_read_json(path)
        if data and isinstance(data, dict):
            stored = data.get('version', 0)
            if stored != VERSION:
                _log.warning(
                    'State file version mismatch in %s: expected %d, got %d',
                    filename, VERSION, stored,
                )
        return data
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Active plan
# ---------------------------------------------------------------------------


def save_active_plan(agent, plan_data: dict) -> str | None:
    return _save_artifact(agent, "active_plan.json", plan_data)


def read_active_plan(agent) -> dict | None:
    return _read_artifact(agent, "active_plan.json")


# ---------------------------------------------------------------------------
# Active goal
# ---------------------------------------------------------------------------


def save_active_goal(agent, goal_data: dict) -> str | None:
    return _save_artifact(agent, "active_goal.json", goal_data)


def read_active_goal(agent) -> dict | None:
    return _read_artifact(agent, "active_goal.json")


# ---------------------------------------------------------------------------
# Current phase
# ---------------------------------------------------------------------------


def save_current_phase(agent, phase_data: dict) -> str | None:
    if "entered_at" not in phase_data:
        phase_data["entered_at"] = time.time()
    return _save_artifact(agent, "current_phase.json", phase_data)


def read_current_phase(agent) -> dict | None:
    return _read_artifact(agent, "current_phase.json")


# ---------------------------------------------------------------------------
# Loaded skills
# ---------------------------------------------------------------------------

def save_loaded_skills(agent, skills_data: dict) -> str | None:
    return _save_artifact(agent, "loaded_skills.json", skills_data)


def read_loaded_skills(agent) -> dict | None:
    return _read_artifact(agent, "loaded_skills.json")


# ---------------------------------------------------------------------------
# Checkpoints
# ---------------------------------------------------------------------------

def save_checkpoints(agent, checkpoints_data: dict) -> str | None:
    return _save_artifact(agent, "checkpoints.json", checkpoints_data)


def read_checkpoints(agent) -> dict | None:
    return _read_artifact(agent, "checkpoints.json")


# ---------------------------------------------------------------------------
# Progress log (JSONL append-only)
# ---------------------------------------------------------------------------

def append_progress_event(agent, event_data: dict) -> str | None:
    try:
        state_dir = resolve_state_dir(agent)
        if not state_dir:
            return None
        path = _state_path(state_dir, "progress_log.jsonl")
        _ensure_dir(state_dir)
        if "ts" not in event_data:
            event_data["ts"] = time.time()
        line = json.dumps(event_data, separators=(",", ":")) + "\n"

        max_entries = DEFAULT_MAX_PROGRESS_ENTRIES
        try:
            cfg = _get_plugin_config(agent)
            max_entries = int(cfg.get("max_progress_entries", DEFAULT_MAX_PROGRESS_ENTRIES))
        except Exception:
            pass

        with _write_lock:
            if max_entries > 0 and os.path.exists(path):
                try:
                    line_count = 0
                    with open(path, "r", encoding="utf-8") as fh:
                        for _ in fh:
                            line_count += 1
                            if line_count > max_entries + 1:
                                break
                    if line_count >= max_entries:
                        with open(path, "r", encoding="utf-8") as fh:
                            existing = fh.readlines()
                        keep = existing[max_entries // 2:]
                        import tempfile
                        tmp_fd, tmp_path = tempfile.mkstemp(dir=state_dir)
                        try:
                            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tf:
                                tf.writelines(keep)
                            os.replace(tmp_path, path)
                        except Exception:
                            try:
                                os.unlink(tmp_path)
                            except OSError:
                                pass
                            raise
                except Exception:
                    pass

            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
        return path
    except Exception as exc:
        _log.warning("Failed to append progress event: %s", exc)
        return None


def read_progress_log(agent, tail: int = 0) -> list[dict]:
    try:
        state_dir = resolve_state_dir(agent)
        if not state_dir:
            return []
        return _read_progress_log_from_dir(state_dir, tail)
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Handoff markdown
# ---------------------------------------------------------------------------

def write_handoff(agent) -> str | None:
    try:
        state_dir = resolve_state_dir(agent)
        if not state_dir:
            return None
        path = _state_path(state_dir, "handoff.md")

        state = read_all_state(agent)
        plan = state.get("active_plan") or {}
        goal = state.get("active_goal") or {}
        phase = state.get("current_phase") or {}
        skills = state.get("loaded_skills") or {}
        checkpoints = state.get("checkpoints") or {}

        proj_name = "(unknown)"
        try:
            from helpers import projects as _projects
            if agent and hasattr(agent, "context") and agent.context:
                pn = _projects.get_context_project_name(agent.context)
                if pn:
                    proj_name = pn
        except Exception:
            pass

        skill_names = ", ".join(
            s.get("name", "?") for s in (skills.get("skills") or [])
        ) or "(none)"

        last_cp = "(none)"
        cp_list = checkpoints.get("checkpoints") or []
        if cp_list:
            last = cp_list[-1]
            last_cp = f"{last.get('id', '?')} \u2014 {last.get('label', '?')}"

        updated = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time())
        )

        md = (
            "# Workflow Handoff\n\n"
            f"**Project:** {proj_name}\n"
            f"**Phase:** {phase.get('phase', '(unknown)')}\n"
            f"**Goal:** {goal.get('goal', '(unknown)')}\n"
            f"**Plan:** {plan.get('plan_path', '(unknown)')}\n"
            f"**Current Task:** {plan.get('current_task', '(unknown)')}\n"
            f"**Loaded Skills:** {skill_names}\n"
            f"**Last Checkpoint:** {last_cp}\n"
            f"**Updated:** {updated}\n"
        )

        _ensure_dir(state_dir)
        with _write_lock:
            with open(path, "w", encoding="utf-8") as f:
                f.write(md)
        return path
    except Exception as exc:
        _log.warning("Failed to write handoff: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Consolidated read
# ---------------------------------------------------------------------------

def _read_progress_log_from_dir(state_dir: str, tail: int = 0) -> list[dict]:
    try:
        path = _state_path(state_dir, "progress_log.jsonl")
        if not os.path.exists(path):
            return []

        if tail > 0:
            return _read_tail_entries(path, tail)

        entries = []
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    entries.append(entry)
                except json.JSONDecodeError:
                    _log.warning("Invalid JSONL line %d in %s", line_num, path)
        return entries
    except Exception:
        return []


def _read_tail_entries(path: str, tail: int) -> list[dict]:
    import collections

    chunk_size = 8192
    lines: collections.deque[str] = collections.deque(maxlen=tail)

    with open(path, "r", encoding="utf-8") as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        if file_size == 0:
            return []

        pos = file_size
        leftover = ""
        while pos > 0 and len(lines) < tail:
            read_size = min(chunk_size, pos)
            pos -= read_size
            f.seek(pos)
            chunk = f.read(read_size)

            parts = chunk.split("\n")
            if leftover:
                parts[-1] += leftover
            leftover = parts[0]

            for part in reversed(parts[1:]):
                stripped = part.strip()
                if stripped:
                    lines.appendleft(stripped)

        if leftover and len(lines) < tail:
            stripped = leftover.strip()
            if stripped:
                lines.appendleft(stripped)

    entries = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return entries


def read_all_state(agent) -> dict:
    try:
        state_dir = resolve_state_dir(agent)
        if not state_dir:
            return {}

        plan = _safe_read_json(_state_path(state_dir, "active_plan.json"))
        goal = _safe_read_json(_state_path(state_dir, "active_goal.json"))
        phase = _safe_read_json(_state_path(state_dir, "current_phase.json"))
        skills = _safe_read_json(_state_path(state_dir, "loaded_skills.json"))
        checkpoints = _safe_read_json(_state_path(state_dir, "checkpoints.json"))

        progress = _read_progress_log_from_dir(state_dir)

        result = {}
        if plan is not None:
            result["active_plan"] = plan
        if goal is not None:
            result["active_goal"] = goal
        if phase is not None:
            result["current_phase"] = phase
        if skills is not None:
            result["loaded_skills"] = skills
        if checkpoints is not None:
            result["checkpoints"] = checkpoints
        if progress:
            result["progress_log"] = progress
        return result
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def create_checkpoint(agent, label: str, phase: str = "", task: str = "", notes: str = "") -> str | None:
    try:
        existing = read_checkpoints(agent) or {"checkpoints": []}
        cp_list = existing.get("checkpoints", [])

        cp_num = len(cp_list) + 1
        cp_id = f"cp-{cp_num:03d}"

        cp = {
            "id": cp_id,
            "label": label,
            "created_at": time.time(),
            "phase": phase,
            "task": task,
            "notes": notes,
        }
        cp_list.append(cp)
        existing["checkpoints"] = cp_list
        result = save_checkpoints(agent, existing)
        if result is None:
            return None
        return cp_id
    except Exception as exc:
        _log.warning("Failed to create checkpoint: %s", exc)
        return None


def update_checkpoint(agent, cp_id: str, updates: dict) -> bool:
    try:
        existing = read_checkpoints(agent) or {"checkpoints": []}
        cp_list = existing.get("checkpoints", [])

        for cp in cp_list:
            if cp.get("id") == cp_id:
                cp.update(updates)
                save_checkpoints(agent, existing)
                return True
        return False
    except Exception:
        return False
