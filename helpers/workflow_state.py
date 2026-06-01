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

import glob
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
# NOTE: _write_lock is process-level only — it will NOT protect against
# concurrent writes from multiple Agent Zero instances sharing the same
# state directory. For multi-instance safety, use file-level locking (fcntl).
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
    "artifact_created", "artifact_updated", "approval",
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
                    # Read state path from config, fall back to default
                    cfg = _get_plugin_config(agent)
                    state_rel = (
                        cfg.get("workflow_state_path", STATE_DIR_NAME)
                        if isinstance(cfg, dict) else STATE_DIR_NAME
                    )
                    state_dir = os.path.join(proj_folder, state_rel.replace("/", os.sep))
                    base = pathlib.Path(proj_folder).resolve()
                    candidate = pathlib.Path(state_dir).resolve()
                    try:
                        candidate.relative_to(base)
                    except ValueError:
                        return None
                    return str(candidate)
    except Exception:
        _log.warning("resolve_state_dir failed — possible path issue", exc_info=True)

    # No-project fallback: use plugin-local state under workdir
    return os.path.join("/a0/usr/workdir", ".a0_agent_skills", "state")


def resolve_visible_root(agent) -> str:
    """Return the project root if a project is selected, else /a0/usr/workdir."""
    try:
        from helpers import projects as _projects
        if agent and hasattr(agent, "context") and agent.context:
            proj_name = _projects.get_context_project_name(agent.context)
            if proj_name:
                proj_folder = _projects.get_project_folder(proj_name)
                if proj_folder:
                    return str(proj_folder)
    except Exception:
        pass
    return "/a0/usr/workdir"


# --- Artifact Path Resolution ---


def _sanitize_slug(slug: str | None) -> str | None:
    """Sanitize a feature slug to prevent path traversal.

    Strips path separators and leading dots. Returns None if the
    result is empty.
    """
    if not slug:
        return None
    slug = slug.replace(os.sep, "_").replace("/", "_").replace("\\", "_")
    slug = slug.strip(".")
    return slug if slug else None


def resolve_artifact_paths(agent, slug: str | None = None) -> dict:
    """Return canonical artifact paths for the current project or workdir.

    When *slug* is provided the paths follow the feature-scoped layout
    (docs/specs/<slug>-spec.md, docs/plans/<slug>-plan.md, …).
    When *slug* is ``None`` the function falls back to legacy paths
    (SPEC.md, tasks/plan.md, tasks/todo.md).
    """
    root = resolve_visible_root(agent)
    slug = _sanitize_slug(slug)

    if slug:
        return {
            "spec": os.path.join(root, "docs", "specs", f"{slug}-spec.md"),
            "plan": os.path.join(root, "docs", "plans", f"{slug}-plan.md"),
            "todo": os.path.join(root, "tasks", f"{slug}-todo.md"),
            "idea": os.path.join(root, "docs", "ideas", f"{slug}.md"),
            "adr": os.path.join(root, "docs", "adrs"),
            "report": os.path.join(root, "docs", "reports", slug),
        }

    # Legacy fallback (no slug)
    return {
        "spec": os.path.join(root, "SPEC.md"),
        "plan": os.path.join(root, "tasks", "plan.md"),
        "todo": os.path.join(root, "tasks", "todo.md"),
        "idea": os.path.join(root, "docs", "ideas"),
        "adr": os.path.join(root, "docs", "adrs"),
        "report": os.path.join(root, "docs", "reports"),
    }


def save_workflow_artifacts(agent, data: dict) -> str | None:
    """Persist workflow artifact tracking data to workflow_artifacts.json."""
    return _save_artifact(agent, "workflow_artifacts.json", data)


def read_workflow_artifacts(agent) -> dict | None:
    """Read workflow artifact tracking data from workflow_artifacts.json."""
    return _read_artifact(agent, "workflow_artifacts.json")


def merge_workflow_artifact(agent, key: str, value) -> str | None:
    """Merge a single key-value pair into workflow_artifacts.json.

    Reads the existing artifact dict, sets ``dict[key] = value``, and writes
    it back.  Preserves all other keys.  Returns the file path on success or
    ``None`` on failure.  Never raises.
    """
    try:
        existing = read_workflow_artifacts(agent)
        if existing is None:
            existing = {}
        existing[key] = value
        return save_workflow_artifacts(agent, existing)
    except Exception:
        _log.warning("merge_workflow_artifact failed for key=%s", key, exc_info=True)
        return None


def merge_workflow_artifacts_batch(agent, updates: dict) -> str | None:
    """Merge multiple key-value pairs into workflow_artifacts.json in one write.

    Like merge_workflow_artifact but for multiple keys at once.
    Returns the file path on success or None on failure. Never raises.
    """
    try:
        existing = read_workflow_artifacts(agent)
        if existing is None:
            existing = {}
        existing.update(updates)
        return save_workflow_artifacts(agent, existing)
    except Exception:
        _log.warning("merge_workflow_artifacts_batch failed", exc_info=True)
        return None


def discover_feature_slug(agent) -> str | None:
    """Discover the active feature slug.

    Priority:
    1. Read from ``workflow_artifacts.json`` state.
    2. Scan ``docs/specs/*-spec.md`` on the visible root filesystem.
    3. Return ``None`` if nothing found.
    """
    # 1. Check state
    stored = read_workflow_artifacts(agent)
    if stored and isinstance(stored, dict):
        slug = _sanitize_slug(stored.get("feature_slug"))
        if slug:
            return slug

    # 2. Scan filesystem
    root = resolve_visible_root(agent)
    specs_dir = os.path.join(root, "docs", "specs")
    if os.path.isdir(specs_dir):
        candidates = sorted(glob.glob(os.path.join(specs_dir, "*-spec.md")))
        if candidates:
            if len(candidates) > 1:
                _log.debug(
                    "Multiple spec candidates found; selecting last alphabetically: %s",
                    candidates[-1],
                )
            filename = os.path.basename(candidates[-1])
            slug = filename[: -len("-spec.md")]
            return _sanitize_slug(slug)

    return None


_VALID_ARTIFACT_TYPES = frozenset({"spec", "plan", "todo", "idea", "intent", "review", "report"})


def mark_artifact_approved(agent, artifact_type: str) -> str | None:
    """Mark an artifact as approved in workflow_artifacts.json.

    Records approval with timestamp and emits an 'approval' progress event.
    Returns the path to workflow_artifacts.json on success, None on failure.
    """
    if artifact_type not in _VALID_ARTIFACT_TYPES:
        _log.warning(
            "Unknown artifact type in mark_artifact_approved: %s (expected one of %s)",
            artifact_type, sorted(_VALID_ARTIFACT_TYPES),
        )
    try:
        existing = read_workflow_artifacts(agent)
        if existing is None:
            existing = {}

        for key in ("approved", "approved_at"):
            if key not in existing or not isinstance(existing[key], dict):
                existing[key] = {}

        existing["approved"][artifact_type] = True
        existing["approved_at"][artifact_type] = time.time()

        result = save_workflow_artifacts(agent, existing)

        append_progress_event(agent, {
            "event": "approval",
            "artifact_type": artifact_type,
            "approved": True,
        })

        return result
    except Exception as exc:
        _log.warning("Failed to mark artifact approved: %s", exc)
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
# Previous lifecycle (archived goal history)
# ---------------------------------------------------------------------------


def save_previous_lifecycle(agent, lifecycle_data: dict) -> str | None:
    if "archived_at" not in lifecycle_data:
        lifecycle_data["archived_at"] = time.time()
    # Append to a list of previous lifecycles
    existing = read_previous_lifecycle(agent)
    if isinstance(existing, list):
        existing.append(lifecycle_data)
    else:
        existing = [lifecycle_data]
    # Keep only last 5 lifecycles to prevent unbounded growth
    existing = existing[-5:]
    return _save_artifact(agent, "previous_lifecycle.json", existing)


def read_previous_lifecycle(agent) -> list | None:
    data = _read_artifact(agent, "previous_lifecycle.json")
    if data is None:
        return []
    return data if isinstance(data, list) else [data]


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
        event_type = event_data.get("event")
        if event_type and event_type not in _VALID_EVENT_TYPES:
            _log.warning("Unknown event type: %s", event_type)
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
                    import tempfile
                    # Single-pass: read all lines and count simultaneously
                    existing = []
                    with open(path, "r", encoding="utf-8") as fh:
                        for raw_line in fh:
                            existing.append(raw_line)
                    if len(existing) >= max_entries:
                        keep = existing[max_entries // 2:]
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

        # Build artifact section from workflow_artifacts.json
        artifacts = read_workflow_artifacts(agent) or {}
        artifact_lines = []
        if artifacts:
            # Map stored keys (with _path suffix) to display names
            artifact_key_map = {
                "idea": "idea", "intent": "intent",
                "spec_path": "spec", "plan_path": "plan", "todo_path": "todo",
            }
            for key, display_name in artifact_key_map.items():
                path_val = artifacts.get(key)
                if path_val:
                    approval = ""
                    approved_dict = artifacts.get("approved") or {}
                    if approved_dict.get(key):
                        approval = " (approved)"
                    artifact_lines.append(f"- {display_name}: {path_val}{approval}")

        md = (
            "# Workflow Handoff\n\n"
            f"**Project:** {proj_name}\n"
            f"**Phase:** {phase.get('phase', '(unknown)')}\n"
            f"**Goal:** {goal.get('goal', '(unknown)')}\n"
            f"**Plan:** {artifacts.get('plan_path') or plan.get('plan_path', '(unknown)')}\n"
            f"**Current Task:** {plan.get('current_task', '(unknown)')}\n"
            f"**Loaded Skills:** {skill_names}\n"
            f"**Last Checkpoint:** {last_cp}\n"
            f"**Updated:** {updated}\n"
        )

        if artifact_lines:
            md += "\n## Active Artifacts\n\n" + "\n".join(artifact_lines) + "\n"

        # Previous lifecycle section
        prev = state.get("previous_lifecycle") or []
        if prev:
            md += "\n## Previous Lifecycles\n\n"
            for p in prev[-3:]:  # Show last 3
                goal = p.get("goal", "?")
                phase = p.get("phase", "?")
                md += f"- **{goal}** (completed at {phase})\n"
            md += "\n"

        _ensure_dir(state_dir)
        # Check for symlink on the raw (unresolved) path before _state_path resolves it
        raw_handoff = os.path.join(state_dir, "handoff.md")
        if os.path.exists(raw_handoff) and os.path.islink(raw_handoff):
            _log.warning("Refusing to write to symlink: %s", raw_handoff)
            return None
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

        # Read workflow artifact tracking
        artifacts = read_workflow_artifacts(agent)

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
        prev_lifecycle = _safe_read_json(_state_path(state_dir, "previous_lifecycle.json"))
        if prev_lifecycle is not None:
            result["previous_lifecycle"] = prev_lifecycle
        if progress:
            result["progress_log"] = progress
        if artifacts is not None:
            result["workflow_artifacts"] = artifacts
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
