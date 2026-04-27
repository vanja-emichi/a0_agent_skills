# extensions/python/message_loop_prompts_after/_10_lifecycle_inject.py
#
# Injects lifecycle state into EXTRAS every turn.

from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parents[3])
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)

from agent import LoopData

from lib.extension_base import LifecycleExtension


class IncludePlan(LifecycleExtension):
    """Include lifecycle state in EXTRAS on every turn."""

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        if not self.agent:
            return

        try:
            lifecycle_dir = self._resolve_lifecycle_dir()
        except Exception:
            return

        if lifecycle_dir is None:
            return

        state = self._load_lifecycle()
        if state is None:
            return

        extras_content = state.render_extras(max_suffix=12)

        if extras_content.strip():
            loop_data.extras_temporary["lifecycle_state"] = extras_content
