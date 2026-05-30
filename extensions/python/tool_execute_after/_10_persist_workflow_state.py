"""Persist Workflow State Extension — a0_agent_skills plugin.

Fires after every tool execution. Persists workflow state to .a0proj/state/
when relevant tool calls are detected:

- After skills_tool:load → saves loaded_skills.json + progress event
- After plan/goal/phase state changes (detected via tool_args) → saves state files
- After any state write → regenerates handoff.md

Configuration keys (default_config.yaml):
  workflow_state_enabled: true   # Set to false to disable all state persistence

Must never raise — all logic is wrapped in a top-level try/except so that a
state persistence failure cannot affect normal agent operation.
"""

from __future__ import annotations

import importlib.util
import logging
import os
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
_STATE_ACTION_PATTERNS = {
    "plan_set",
    "goal_set",
    "phase_change",
}


def _is_workflow_state_enabled(cfg: dict) -> bool:
    return _config_bool(cfg.get("workflow_state_enabled", True))


def _get_loaded_skills_from_agent(agent) -> list[dict]:
    try:
        data = getattr(agent, "data", None)
        if isinstance(data, dict):
            loaded = data.get("loaded_skills")
            if isinstance(loaded, list):
                now = time.time()
                return [{"name": str(s), "loaded_at": now} for s in loaded if str(s).strip()]

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


class PersistWorkflowState(Extension):

    async def execute(
        self,
        tool_name: str | None = None,
        tool_args: dict | None = None,
        response: "Response | None" = None,
        **kwargs,
    ):
        try:
            cfg = _get_plugin_config(self.agent)
            if not _is_workflow_state_enabled(cfg):
                return

            if not tool_name:
                return

            full_tool_name, reconstructed_args = _reconstruct_tool_info(
                self.agent, tool_name
            )
            effective_args = tool_args or reconstructed_args

            state_changed = False

            if full_tool_name.startswith(_SKILL_TOOL_PREFIX) and full_tool_name.endswith(":load"):
                state_changed = self._persist_loaded_skills()

            action = effective_args.get("action", "")
            if action in _STATE_ACTION_PATTERNS or self._detect_state_in_args(effective_args):
                state_changed = self._persist_state_from_args(effective_args) or state_changed

            if state_changed:
                self._regenerate_handoff()

        except Exception:
            _log.debug("Persist workflow state failed", exc_info=True)

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

    def _detect_state_in_args(self, args: dict) -> bool:
        state_keys = {"plan_name", "goal", "phase", "current_task"}
        return bool(state_keys & set(args.keys()))

    def _persist_state_from_args(self, args: dict) -> bool:
        try:
            from helpers.workflow_state import (
                save_active_plan,
                save_active_goal,
                save_current_phase,
                append_progress_event,
            )

            changed = False

            if "plan_name" in args or "current_task" in args:
                save_active_plan(self.agent, {
                    k: args[k] for k in ("plan_name", "plan_path", "current_task",
                                         "tasks_total", "tasks_completed")
                    if k in args
                })
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

    def _regenerate_handoff(self) -> None:
        try:
            from helpers.workflow_state import write_handoff
            write_handoff(self.agent)
        except Exception:
            _log.debug("Failed to regenerate handoff", exc_info=True)
