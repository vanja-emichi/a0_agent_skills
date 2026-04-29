# extensions/python/tool_execute_before/_31_lifecycle_gate.py — tool_execute_before hook
#
# Fires before the `response` tool executes.
# Enforces phase-in-progress check:
#
#   - If any phase has status `in_progress`, gate the response.
#   - force=true overrides this check (passes with warning).
#   - Config key: planning.gates.response (default: nudge)
#
# Modes per gate: off / nudge / block

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parents[3])
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)
from pathlib import Path

from helpers.print_style import PrintStyle
from helpers import plugins, projects
from helpers.errors import RepairableException

from lib.extension_base import LifecycleExtension
from lib import lifecycle_state as _lifecycle_state_mod

# Module-level alias for test mocking compatibility
def _get_lifecycle_state():
    return _lifecycle_state_mod

PLUGIN_NAME = "a0_agent_skills"


class ResponseGate(LifecycleExtension):
    """Gate that warns or blocks the `response` tool when phases are
    in-progress."""

    # Override _resolve_lifecycle_dir to use module-level imports (test-mockable)
    def _resolve_lifecycle_dir(self) -> Path | None:
        project_name = projects.get_context_project_name(self.agent.context)
        if project_name:
            project_folder = projects.get_project_folder(project_name)
            return Path(project_folder, ".a0proj", "run", "current")
        LifecycleState = _get_lifecycle_state().LifecycleState
        return LifecycleState._get_fallback_dir()

    # Override _load_lifecycle to use module-level _get_lifecycle_state (test-mockable)
    def _load_lifecycle(self):
        lifecycle_dir = self._resolve_lifecycle_dir()
        if lifecycle_dir is None:
            return None
        LifecycleState = _get_lifecycle_state().LifecycleState
        return LifecycleState.load(plan_dir=lifecycle_dir, context=self.agent.context)

    async def execute(self, **kwargs):
        try:
            await self._run(**kwargs)
        except RepairableException:
            raise  # Re-raise — this is how block mode aborts the tool call
        except Exception as exc:
            PrintStyle.error(f"[response-gate] unexpected error: {exc}")

    async def _run(self, **kwargs):
        tool_name = kwargs.get("tool_name", "")

        # Only gate the response tool
        if tool_name != "response":
            return

        tool_args = kwargs.get("tool_args", {}) or {}

        # Read config mode
        config = plugins.get_plugin_config(PLUGIN_NAME, agent=self.agent) or {}
        gates = config.get("planning", {}).get("gates", {})
        response_mode = gates.get("response", "nudge")

        force = str(tool_args.get("force", "")).lower() == "true"

        # ------------------------------------------------------------------
        # Phase-in-progress enforcement
        # ------------------------------------------------------------------
        state = self._load_lifecycle()

        # No lifecycle: pass through
        if state is None:
            return

        # Check if any phase is in_progress
        has_in_progress = any(
            phase.status == "in_progress" for phase in state.phases
        )
        if not has_in_progress:
            return  # All phases settled — pass through

        # Phase is in progress — check force override
        if force:
            self.agent.context.data.setdefault(
                "lifecycle_gate_warnings", []
            ).append(
                "Response sent with phase still in progress. "
                "Consider calling lifecycle:status."
            )
            return

        # Apply response_mode
        if response_mode == "off":
            return  # Silent pass-through

        if response_mode == "nudge":
            msg = (
                "[response-gate] Phase in progress. "
                "Consider calling lifecycle:status before responding."
            )
            PrintStyle.warning(msg)
            self.agent.context.data.setdefault(
                "lifecycle_gate_warnings", []
            ).append(msg)
            return  # Let the tool execute

        if response_mode == "block":
            raise RepairableException(
                "Phase in progress. Call lifecycle:status before responding, "
                "or add force=true."
            )
