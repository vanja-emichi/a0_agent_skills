"""Persist Workflow State Extension — a0_agent_skills plugin.

Fires after every tool execution. Persists workflow state to .a0proj/state/
when relevant tool calls are detected:

- After skills_tool:load → saves loaded_skills.json + progress event
- After plan/goal/phase state changes (detected via tool_args) → saves state files
- After text_editor write/patch to known artifact paths → infers state from path
- After any state write → regenerates handoff.md

Configuration keys (default_config.yaml):
  workflow_state_enabled: true          # Set to false to disable all state persistence
  artifact_inference_enabled: true      # Set to false to disable path-pattern inference

Must never raise — all logic is wrapped in a top-level try/except so that a
state persistence failure cannot affect normal agent operation.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import re
import sys
import time
from typing import TYPE_CHECKING

from helpers.extension import Extension

if TYPE_CHECKING:
    from helpers.tool import Response

_log = logging.getLogger(__name__)


def _bootstrap_plugin_loader():
    if '_plugin_loader' not in sys.modules:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))
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


def _config_bool(value) -> bool:
    return _bootstrap_plugin_loader().config_bool(value)


def _reconstruct_tool_info(agent, tool_name: str) -> tuple[str, dict]:
    return _bootstrap_plugin_loader().reconstruct_tool_info(agent, tool_name)


# Tool names that trigger state persistence
_SKILL_TOOL_PREFIX = "skills_tool"
_TEXT_EDITOR_TOOL = "text_editor"
_STATE_ACTION_PATTERNS = {
    "plan_set",
    "goal_set",
    "phase_change",
}

# Keys in tool_args that indicate workflow state changes (cheap early-exit check).
_STATE_ARG_KEYS = {"plan_name", "goal", "phase", "current_task", "artifact_type"}

# Actions on text_editor that indicate file creation/update.
_WRITE_ACTIONS = {"write", "patch"}

# Phase ordering for forward-only advancement.
_PHASE_ORDER = {"DEFINE": 0, "PLAN": 1, "BUILD": 2, "VERIFY": 3, "REVIEW": 4, "SHIP": 5}

# Path patterns for artifact auto-inference.
# (?:^|[\/]) matches either start-of-string or a path separator,
# so both absolute and relative paths are handled.
SPEC_PATTERNS = [
    re.compile(r'(?:^|[\\/])docs[\\/]specs[\\/].+-spec\.md$'),
    re.compile(r'SPEC\.md$'),
]
PLAN_PATTERNS = [
    re.compile(r'(?:^|[\\/])docs[\\/]plans[\\/].+-plan\.md$'),
    re.compile(r'(?:^|[\\/])tasks[\\/]plan\.md$'),
]
TODO_PATTERNS = [
    re.compile(r'(?:^|[\\/])tasks[\\/].+-todo\.md$'),
    re.compile(r'(?:^|[\\/])tasks[\\/]todo\.md$'),
]


def _is_workflow_state_enabled(cfg: dict) -> bool:
    return _config_bool(cfg.get("workflow_state_enabled", True))


def _is_artifact_inference_enabled(cfg: dict) -> bool:
    return _config_bool(cfg.get("artifact_inference_enabled", True))


# Cap the persisted loaded-skills summary so the on-disk list cannot grow
# without bound across many skill loads over a long-lived project.
_MAX_PERSISTED_SKILLS = 50


def _get_loaded_skills_from_agent(agent) -> list[dict]:
    try:
        data = getattr(agent, "data", None)
        if isinstance(data, dict):
            now = time.time()
            ordered: list[str] = []
            seen: set[str] = set()
            # Union the core-rendered 'loaded_skills' (skills actively loaded
            # this session) with the plugin-private rehydrated names, so the
            # persisted summary survives session resume. Dedup preserves order.
            for key in ("loaded_skills", "_a0skills_rehydrated_loaded"):
                values = data.get(key)
                if isinstance(values, list):
                    for s in values:
                        name = str(s).strip()
                        if name and name not in seen:
                            seen.add(name)
                            ordered.append(name)
            if ordered:
                ordered = ordered[-_MAX_PERSISTED_SKILLS:]
                return [{"name": n, "loaded_at": now} for n in ordered]

        try:
            from helpers.skills import get_loaded_skill_entries
            entries = get_loaded_skill_entries(agent)
            now = time.time()
            return [{"name": e.get("name", ""), "loaded_at": now} for e in entries if e.get("name")]
        except Exception:
            pass
    except Exception:
        pass
    return []


def _extract_slug(filename: str, suffix: str) -> str | None:
    """Extract slug from a filename like 'user-auth-spec.md' → 'user-auth'.

    *suffix* is the trailing portion including the extension, e.g. '-spec.md'.
    Returns None if the filename does not end with the expected suffix or
    the result is empty.
    """
    try:
        # Normalize backslashes to forward slashes so os.path.basename
        # works correctly on Linux when given Windows-style paths.
        normalized = filename.replace("\\", "/")
        base = normalized.rsplit("/", 1)[-1]
        if not base.endswith(suffix):
            return None
        slug = base[: -len(suffix)]
        slug = slug.strip(".").strip()
        return slug if slug else None
    except Exception:
        return None


class PersistWorkflowState(Extension):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Track last mtime per artifact path for idempotency.
        self._artifact_mtimes: dict[str, float] = {}

    async def execute(
        self,
        tool_name: str | None = None,
        tool_args: dict | None = None,
        response: "Response | None" = None,
        **kwargs,
    ):
        try:
            # ── CHEAP early exit: skip ~95% of irrelevant tool calls ──
            if not tool_name:
                return

            # ── Reconstruct tool args BEFORE relevance check ──
            # The framework's tool_execute_after hook does NOT pass tool_args,
            # so we must recover them via _reconstruct_tool_info first.
            full_tool_name, reconstructed_args = _reconstruct_tool_info(
                self.agent, tool_name
            )
            effective_args = tool_args or reconstructed_args

            # Determine if this tool call is relevant for state persistence.
            # Use effective_args (reconstructed) instead of tool_args (which is None).
            is_relevant = False
            if tool_name.startswith(_SKILL_TOOL_PREFIX):
                is_relevant = True
            elif tool_name == _TEXT_EDITOR_TOOL:
                # text_editor is relevant when action is write or patch
                if isinstance(effective_args, dict) and effective_args.get("action") in _WRITE_ACTIONS:
                    is_relevant = True
            elif isinstance(effective_args, dict):
                action = effective_args.get("action", "")
                if action in _STATE_ACTION_PATTERNS or (_STATE_ARG_KEYS & effective_args.keys()):
                    is_relevant = True

            if not is_relevant:
                return

            # ── NOW do the expensive stuff ──
            cfg = _get_plugin_config(self.agent)
            if not _is_workflow_state_enabled(cfg):
                return

            state_changed = False

            is_skill_load = (
                (full_tool_name.startswith(_SKILL_TOOL_PREFIX) and full_tool_name.endswith(":load"))
                or (tool_name == _SKILL_TOOL_PREFIX and effective_args.get("action") == "load")
            )
            if is_skill_load:
                state_changed = self._persist_loaded_skills()
                self._resolve_and_log_dependencies(effective_args)

            action = effective_args.get("action", "")
            if action in _STATE_ACTION_PATTERNS or self._detect_state_in_args(effective_args):
                state_changed = self._persist_state_from_args(effective_args) or state_changed

            # ── Path-pattern artifact inference ──
            if _is_artifact_inference_enabled(cfg):
                artifact = self._detect_artifact_from_path(tool_name, effective_args)
                if artifact:
                    state_changed = self._persist_artifact_state(artifact) or state_changed

            if state_changed:
                self._regenerate_handoff()

            # Relay artifact events when args explicitly set the key
            self._relay_artifact_events(effective_args)

        except Exception:
            _log.debug("Persist workflow state failed", exc_info=True)

    # ── Path-pattern artifact inference ──────────────────────────────────

    def _detect_artifact_from_path(self, tool_name: str, tool_args: dict) -> dict | None:
        """Detect artifact type from the file path of a text_editor write/patch.

        Returns a dict like {"artifact_type": "spec", "phase": "DEFINE",
                             "slug": "user-auth", "path": "..."}
        or None if the path does not match any known pattern.
        """
        try:
            if tool_name != _TEXT_EDITOR_TOOL:
                return None
            action = tool_args.get("action", "")
            if action not in _WRITE_ACTIONS:
                return None

            path = tool_args.get("path", "")
            if not path or not isinstance(path, str):
                return None

            # Normalize path separators for cross-platform matching.
            normalized = path.replace(os.sep, "/")

            # Check SPEC patterns.
            for pattern in SPEC_PATTERNS:
                if pattern.search(path) or pattern.search(normalized):
                    slug = _extract_slug(path, "-spec.md")
                    return {
                        "artifact_type": "spec",
                        "phase": "DEFINE",
                        "slug": slug,
                        "path": path,
                    }

            # Check PLAN patterns.
            for pattern in PLAN_PATTERNS:
                if pattern.search(path) or pattern.search(normalized):
                    slug = _extract_slug(path, "-plan.md")
                    return {
                        "artifact_type": "plan",
                        "phase": "PLAN",
                        "slug": slug,
                        "path": path,
                    }

            # Check TODO patterns.
            for pattern in TODO_PATTERNS:
                if pattern.search(path) or pattern.search(normalized):
                    slug = _extract_slug(path, "-todo.md")
                    return {
                        "artifact_type": "todo",
                        "phase": "PLAN",
                        "slug": slug,
                        "path": path,
                    }

            return None
        except Exception:
            _log.debug("Failed to detect artifact from path", exc_info=True)
            return None

    def _persist_artifact_state(self, artifact: dict) -> bool:
        """Persist state inferred from an artifact path-pattern match.

        Handles idempotency via mtime check — writing the same file twice
        with no mtime change does not create duplicate progress events.
        Returns True if state was changed.
        """
        try:
            from helpers.workflow_state import (
                save_active_plan,
                save_active_goal,
                save_current_phase,
                read_current_phase,
                read_active_plan,
                append_progress_event,
                merge_workflow_artifact,
                merge_workflow_artifacts_batch,
            )

            artifact_type = artifact["artifact_type"]
            path = artifact.get("path", "")
            slug = artifact.get("slug")
            target_phase = artifact.get("phase", "")

            # ── Idempotency: check mtime ──
            try:
                current_mtime = os.path.getmtime(path) if os.path.exists(path) else 0.0
            except OSError:
                current_mtime = 0.0

            prev_mtime = self._artifact_mtimes.get(path, 0.0)
            if current_mtime and current_mtime == prev_mtime:
                return False  # Same file, same mtime → no duplicate event

            changed = False

            # ── SPEC artifact → active_goal + DEFINE phase ──
            if artifact_type == "spec":
                goal_text = slug.replace("-", " ") if slug else "active spec"

                # Detect goal change → new lifecycle
                from helpers.workflow_state import read_active_goal, read_active_plan
                existing = read_active_goal(self.agent) or {}
                old_slug = existing.get("slug", "")
                is_new_lifecycle = old_slug and old_slug != slug

                # Also check current phase for lifecycle context
                current_phase_data = read_current_phase(self.agent) or {}
                existing_lifecycle = current_phase_data.get("lifecycle_goal", "")
                is_same_lifecycle = existing_lifecycle and existing_lifecycle == slug

                if is_new_lifecycle:
                    # New goal → reset lifecycle
                    _log.info("Goal changed: %s → %s, resetting lifecycle", old_slug, slug)
                    # Save previous lifecycle for context (old artifacts still on disk)
                    from helpers.workflow_state import save_previous_lifecycle
                    save_previous_lifecycle(self.agent, {
                        "goal": old_slug,
                        "phase": current_phase_data.get("phase", "(unknown)"),
                        "completed_phases": current_phase_data.get("phases_completed", []),
                    })
                    save_active_plan(self.agent, {})  # clear old plan
                    append_progress_event(self.agent, {
                        "event": "lifecycle_reset",
                        "old_goal": old_slug,
                        "new_goal": slug,
                        "source": "artifact_inference",
                    })

                save_active_goal(self.agent, {
                    "goal": goal_text,
                    "source": "artifact_inference",
                    "slug": slug,
                })
                append_progress_event(self.agent, {
                    "event": "goal_set",
                    "goal": goal_text,
                    "source": "artifact_inference",
                })

                if is_new_lifecycle or (not old_slug and not existing_lifecycle):
                    # New goal or truly first spec → set DEFINE
                    from helpers.workflow_state import save_current_phase as _save_phase
                    _save_phase(self.agent, {
                        "phase": "DEFINE",
                        "phases_completed": [],
                        "lifecycle_goal": slug,
                    })
                elif not is_same_lifecycle:
                    # No lifecycle tracked but goal exists → set DEFINE for safety
                    from helpers.workflow_state import save_current_phase as _save_phase
                    _save_phase(self.agent, {
                        "phase": "DEFINE",
                        "phases_completed": [],
                        "lifecycle_goal": slug,
                    })
                else:
                    # Same lifecycle, spec update → advance only forward
                    self._advance_phase(target_phase)

                append_progress_event(self.agent, {
                    "event": "artifact_created",
                    "artifact_type": "spec",
                    "path": path,
                    "source": "artifact_inference",
                })
                merge_workflow_artifacts_batch(self.agent, {"spec_path": path, "feature_slug": slug})
                changed = True

            # ── PLAN artifact → active_plan + PLAN phase ──
            elif artifact_type == "plan":
                plan_name = slug.replace("-", " ") if slug else "active plan"
                save_active_plan(self.agent, {
                    "plan_name": plan_name,
                    "slug": slug,
                })
                append_progress_event(self.agent, {
                    "event": "plan_set",
                    "plan_name": plan_name,
                    "source": "artifact_inference",
                })
                self._advance_phase(target_phase)
                append_progress_event(self.agent, {
                    "event": "artifact_created",
                    "artifact_type": "plan",
                    "path": path,
                    "source": "artifact_inference",
                })
                merge_workflow_artifact(self.agent, "plan_path", path)
                changed = True

            # ── TODO artifact → active_plan current_task (merge, not replace) ──
            elif artifact_type == "todo":
                current_task = self._read_first_unchecked_task(path)
                existing_plan = read_active_plan(self.agent) or {}
                if slug:
                    existing_plan["slug"] = slug
                if current_task:
                    existing_plan["current_task"] = current_task
                save_active_plan(self.agent, existing_plan)
                if current_task:
                    append_progress_event(self.agent, {
                        "event": "task_started",
                        "current_task": current_task,
                        "source": "artifact_inference",
                    })
                append_progress_event(self.agent, {
                    "event": "artifact_created",
                    "artifact_type": "todo",
                    "path": path,
                    "source": "artifact_inference",
                })
                merge_workflow_artifact(self.agent, "todo_path", path)
                changed = True

            # Update mtime tracking.
            if changed:
                self._artifact_mtimes[path] = current_mtime

            return changed
        except Exception:
            _log.debug("Failed to persist artifact state", exc_info=True)
            return False

    def _advance_phase(self, target_phase: str) -> None:
        """Advance current phase to *target_phase* only if it is forward.

        Never rewinds phase.  Uses the existing save_current_phase helper.
        """
        try:
            from helpers.workflow_state import (
                save_current_phase,
                read_current_phase,
                append_progress_event,
            )

            target_rank = _PHASE_ORDER.get(target_phase)
            if target_rank is None:
                return

            current = read_current_phase(self.agent)
            current_phase = (current or {}).get("phase", "")
            current_rank = _PHASE_ORDER.get(current_phase, -1)

            if target_rank > current_rank:
                # Carry forward lifecycle_goal from current phase
                lifecycle_goal = (current or {}).get("lifecycle_goal", "")
                new_phase_data = {
                    "phase": target_phase,
                    "phases_completed": [],
                    "source": "artifact_inference",
                }
                if lifecycle_goal:
                    new_phase_data["lifecycle_goal"] = lifecycle_goal
                save_current_phase(self.agent, new_phase_data)
                append_progress_event(self.agent, {
                    "event": "phase_change",
                    "to": target_phase,
                    "from": current_phase or "(none)",
                    "source": "artifact_inference",
                })
        except Exception:
            _log.debug("Failed to advance phase", exc_info=True)

    def _read_first_unchecked_task(self, path: str) -> str | None:
        """Read the first unchecked task from a todo markdown file.

        Looks for lines starting with '- [ ]'.  Returns the task text
        or None if no unchecked task is found or the file cannot be read.
        """
        try:
            if not os.path.exists(path):
                return None
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("- [ ]"):
                        task = stripped[len("- [ ]"):].strip()
                        if task:
                            return task
            return None
        except Exception:
            return None

    # ── Existing methods (unchanged) ────────────────────────────────────

    def _persist_loaded_skills(self) -> bool:
        try:
            from helpers.workflow_state import save_loaded_skills, append_progress_event

            skills_list = _get_loaded_skills_from_agent(self.agent)
            if not skills_list:
                return False

            save_loaded_skills(self.agent, {"skills": skills_list})

            for skill in skills_list:
                append_progress_event(self.agent, {
                    "event": "skill_loaded",
                    "skill": skill["name"],
                })

            return True
        except Exception:
            _log.debug("Failed to persist loaded skills", exc_info=True)
            return False

    def _resolve_and_log_dependencies(self, args: dict) -> None:
        """Resolve skill dependencies and log telemetry.

        Does NOT directly call skills_tool — returns dependency info
        in metadata that the agent can act on.
        """
        try:
            from helpers.skill_contracts import resolve_dependencies
            from helpers.workflow_state import read_loaded_skills, append_progress_event

            skill_name = args.get("skill_name", "")
            if not skill_name:
                return

            loaded = read_loaded_skills(self.agent) or {}
            skills_map = loaded.get("skills", {})
            already_loaded = set()
            if isinstance(skills_map, dict):
                already_loaded = {
                    s["name"] for s in skills_map.values()
                    if isinstance(s, dict) and s.get("name")
                } if skills_map else set()
                # Also handle list format
            elif isinstance(skills_map, list):
                already_loaded = {
                    s["name"] for s in skills_map
                    if isinstance(s, dict) and s.get("name")
                }

            deps = resolve_dependencies(skill_name, already_loaded)
            if not deps:
                return

            _log.info(
                "Dependencies for '%s': %s (already loaded: %s)",
                skill_name, deps, list(already_loaded),
            )

            append_progress_event(self.agent, {
                "event": "dependency_resolution",
                "skill_name": skill_name,
                "resolved_deps": deps,
                "already_loaded": sorted(already_loaded),
                "skipped": [
                    d for d in deps if d in already_loaded
                ],
            })

        except Exception:
            _log.debug("Failed to resolve dependencies", exc_info=True)

    def _detect_state_in_args(self, args: dict) -> bool:
        state_keys = {"plan_name", "goal", "phase", "current_task"}
        return bool(state_keys & set(args.keys()))

    def _persist_state_from_args(self, args: dict) -> bool:
        """Persist workflow state from explicit tool args.

        Routes plan_path to workflow_artifacts.json and plan-owned keys
        (plan_name, current_task, tasks_total, tasks_completed) to active_plan.json
        per the two-store model (ADR-007).
        """
        try:
            from helpers.workflow_state import (
                save_active_plan,
                save_active_goal,
                save_current_phase,
                read_active_plan,
                append_progress_event,
                merge_workflow_artifact,
            )

            changed = False

            if "plan_name" in args or "current_task" in args:
                existing_plan = read_active_plan(self.agent) or {}
                # Merge plan-owned keys into active_plan.json (NOT plan_path)
                for k in ("plan_name", "current_task", "tasks_total", "tasks_completed"):
                    if k in args:
                        existing_plan[k] = args[k]
                save_active_plan(self.agent, existing_plan)
                # Route plan_path to its canonical owner (workflow_artifacts.json)
                if "plan_path" in args:
                    merge_workflow_artifact(self.agent, "plan_path", args["plan_path"])
                if "plan_name" in args:
                    append_progress_event(self.agent, {
                        "event": "plan_set",
                        "plan_name": args["plan_name"],
                    })
                changed = True

            if "goal" in args:
                save_active_goal(self.agent, {
                    "goal": args["goal"],
                    "source": args.get("source", "tool call"),
                })
                append_progress_event(self.agent, {
                    "event": "goal_set",
                    "goal": args["goal"],
                })
                changed = True

            if "phase" in args:
                save_current_phase(self.agent, {
                    "phase": args["phase"],
                    "phases_completed": args.get("phases_completed", []),
                })
                append_progress_event(self.agent, {
                    "event": "phase_change",
                    "to": args["phase"],
                })
                changed = True

            return changed
        except Exception:
            _log.debug("Failed to persist state from args", exc_info=True)
            return False

    def _relay_artifact_events(self, args: dict) -> None:
        """Relay artifact events when args explicitly set the key."""
        try:
            artifact_type = args.get("artifact_type")
            if not artifact_type:
                return

            from helpers.workflow_state import append_progress_event

            event_type = args.get("artifact_event")
            if event_type in ("artifact_created", "artifact_updated"):
                append_progress_event(self.agent, {
                    "event": event_type,
                    "artifact_type": artifact_type,
                    "path": args.get("path", ""),
                })
        except Exception:
            _log.debug("Failed to detect artifact changes", exc_info=True)

    def _regenerate_handoff(self) -> None:
        try:
            from helpers.workflow_state import write_handoff
            write_handoff(self.agent)
        except Exception:
            _log.debug("Failed to regenerate handoff", exc_info=True)
