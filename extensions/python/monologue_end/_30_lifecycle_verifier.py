# extensions/python/monologue_end/_30_lifecycle_verifier.py
#
# Nudge at monologue end when phases remain pending or in_progress.
# Does NOT block - just adds a nudge to the history.
# Respects planning.mode setting (off -> no-op).

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parents[3])
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)
from pathlib import Path

from helpers import plugins
from helpers.print_style import PrintStyle

from lib.extension_base import LifecycleExtension

PLUGIN_NAME = "a0_agent_skills"


def _get_planning_mode() -> str:
    """Read planning mode from plugin settings."""
    try:
        config = plugins.get_plugin_config(PLUGIN_NAME)
        if config and "planning" in config:
            return config["planning"].get("mode", "auto")
    except Exception:
        pass
    return "auto"


class PhaseVerifier(LifecycleExtension):
    """Monologue-end nudge when plan has pending or in-progress phases."""

    async def execute(self, **kwargs):
        try:
            await self._run(**kwargs)
        except Exception as exc:
            PrintStyle.error(f"[phase-verifier] unexpected error: {exc}")

    async def _run(self, **kwargs):
        if not self.agent:
            return

        # Respect planning.mode setting
        mode = _get_planning_mode()
        if mode == "off":
            return

        state = self._load_lifecycle()
        if state is None:
            return

        # Count pending/in_progress phases
        pending_phases = [
            p for p in state.phases
            if p.status in ("pending", "in_progress")
        ]

        if not pending_phases:
            return  # All phases complete - no nudge needed

        # Find current phase info
        current_idx = state.current_phase_index
        current_phase = None
        if 0 <= current_idx < len(state.phases):
            current_phase = state.phases[current_idx]

        # Build nudge message
        n_parts = []
        if current_phase:
            n_parts.append(
                f"Current phase '{current_phase.title}' is {current_phase.status}."
            )
        n_parts.append(
            f"{len(pending_phases)} phase(s) remain. "
            f"Continue with `lifecycle:status` or advance the next phase."
        )
        nudge = " ".join(n_parts)

        # Add as history warning (non-blocking nudge)
        PrintStyle.hint(f"[phase-verifier] {nudge}")

        # Also set in context.data for downstream consumers
        ctx_data = self.agent.context.data
        if "lifecycle_nudges" not in ctx_data:
            ctx_data["lifecycle_nudges"] = []
        ctx_data["lifecycle_nudges"].append(nudge)
