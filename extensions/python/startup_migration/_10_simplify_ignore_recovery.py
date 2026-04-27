"""_10_simplify_ignore_recovery.py -- startup_migration hook

Recovers files left with BLOCK_ placeholders from a previous crash.
Fires at framework startup before any agent exists.

If the A0 process crashed while simplify-ignore had filtered files on disk,
the in-memory cache is lost but disk manifests survive. This extension
reads those manifests and restores original file content.

Also cleans up stale .lock files left over from crashed sessions.

Note: self.agent is None at startup_migration -- do NOT access it.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parents[3])
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)

from helpers.extension import Extension
from helpers.print_style import PrintStyle

from lib import simplify_ignore_utils as _su

PLUGIN_NAME = "a0_agent_skills"


class SimplifyIgnoreRecovery(Extension):
    """Crash recovery for simplify-ignore at framework startup."""

    def execute(self, **kwargs):
        # agent is None at startup_migration -- that is expected
        try:
            recovered = _su.recover_from_manifests()
            if recovered:
                PrintStyle.hint(
                    f"[{PLUGIN_NAME}] Crash recovery: restored {len(recovered)} "
                    "file(s): " + ", ".join(recovered),
                )
        except Exception as exc:
            PrintStyle.error(f"[{PLUGIN_NAME}] startup recovery failed: {exc}")

        # Clean up stale .lock files from previous sessions
        try:
            _su.cleanup_stale_lock_files()
        except Exception as exc:
            PrintStyle.error(f"[{PLUGIN_NAME}] stale lock cleanup failed: {exc}")
