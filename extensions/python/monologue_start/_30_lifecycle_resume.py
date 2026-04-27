# extensions/python/monologue_start/_30_lifecycle_resume.py
#
# One-shot resume notice at the start of a conversation.
# Fires on iteration 0 when a lifecycle exists and is recent.
# Tracks one-shot via context.data['lifecycle_resume_shown'] flag.

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parents[3])
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)
import time
from pathlib import Path

from agent import LoopData
from helpers import plugins
from helpers.print_style import PrintStyle

from lib.extension_base import LifecycleExtension

PLUGIN_NAME = "a0_agent_skills"
RESUME_FLAG_KEY = "lifecycle_resume_shown"
DEFAULT_MAX_AGE_DAYS = 7


def _get_max_age_days() -> float:
    """Read max age days from plugin settings, with fallback default."""
    try:
        config = plugins.get_plugin_config(PLUGIN_NAME)
        if config and "planning" in config:
            return float(config["planning"].get("resume_max_age_days", DEFAULT_MAX_AGE_DAYS))
    except Exception:
        pass
    return DEFAULT_MAX_AGE_DAYS


class PlanResume(LifecycleExtension):
    """One-shot resume notice at conversation start when a lifecycle is active."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            await self._run(loop_data=loop_data, **kwargs)
        except Exception as exc:
            PrintStyle.error(f"[lifecycle-resume] unexpected error: {exc}")

    async def _run(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        # Only fire on iteration 0
        if getattr(loop_data, "iteration", -1) != 0:
            return

        # One-shot: check flag in context.data
        ctx_data = self.agent.context.data
        if ctx_data.get(RESUME_FLAG_KEY):
            return

        # Load lifecycle
        lifecycle_dir = self._resolve_lifecycle_dir()
        if lifecycle_dir is None:
            return

        state = self._load_lifecycle()
        if state is None:
            return

        # Check recency — plan metadata must be modified within N days
        metadata_path = lifecycle_dir / "state.md"
        if metadata_path.exists():
            max_age_days = _get_max_age_days()
            mtime = metadata_path.stat().st_mtime
            age_days = (time.time() - mtime) / 86400.0
            if age_days > max_age_days:
                return  # Lifecycle too old to resume

        # Build resume notice
        current_idx = state.current_phase_index
        total_phases = len(state.phases)
        if state.phases and 0 <= current_idx < total_phases:
            current_phase = state.phases[current_idx]
            phase_info = f"Phase {current_idx + 1} of {total_phases} ({current_phase.title}, {current_phase.status})"
        else:
            phase_info = f"{total_phases} phases total"

        # Compute age hint
        if metadata_path.exists():
            mtime = metadata_path.stat().st_mtime
            age_secs = time.time() - mtime
            if age_secs < 60:
                age_hint = "just now"
            elif age_secs < 3600:
                age_hint = f"{int(age_secs / 60)}m ago"
            elif age_secs < 86400:
                age_hint = f"{int(age_secs / 3600)}h ago"
            else:
                age_hint = f"{int(age_secs / 86400)}d ago"
        else:
            age_hint = "unknown"

        notice = (
            f"📋 Active lifecycle detected — {phase_info}. "
            f"Goal: {state.goal}. "
            f"Last update: {age_hint}. "
            f"Call `lifecycle:status` for details."
        )

        # Inject into extras_temporary
        loop_data.extras_temporary["lifecycle_resume"] = notice

        # Set one-shot flag
        ctx_data[RESUME_FLAG_KEY] = True
