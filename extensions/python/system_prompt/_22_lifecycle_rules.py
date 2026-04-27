# extensions/python/system_prompt/_22_lifecycle_rules.py
#
# Injects a planning-discipline rule into the system prompt when a lifecycle exists.
# Only appends when plan state is detected at .a0proj/run/current/.
# Keeps system prompt lean when no lifecycle is active.

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parents[3])
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)

from helpers.print_style import PrintStyle

from lib.extension_base import LifecycleExtension

PLANNING_RULE = (
    "## Planning Discipline\n"
    "When an active lifecycle exists at `.a0proj/run/current/`, you MUST follow its phases in order. "
    "Use `lifecycle:status` before starting a phase and `lifecycle:status` when done. "
    "Write findings to findings.md directly. "
    "See `/lifecycle-status` for current state."
)


class PlanningRules(LifecycleExtension):
    """Injects planning discipline rules into the system prompt when a lifecycle is active."""

    async def execute(self, system_prompt: list[str] | None = None, **kwargs):
        if system_prompt is None:
            system_prompt = []
        try:
            await self._run(system_prompt=system_prompt, **kwargs)
        except Exception as exc:
            PrintStyle.error(f"[planning-rules] system_prompt injection error: {exc}")

    async def _run(self, system_prompt: list[str] | None = None, **kwargs):
        if not self.agent:
            return

        if system_prompt is None:
            system_prompt = []

        state = self._load_lifecycle()
        if state is None:
            return  # No active lifecycle - keep system prompt lean

        # Inject planning discipline rule
        system_prompt.append(PLANNING_RULE)
