"""_10_simplify_ignore_chain_end.py — process_chain_end hook

Final safeguard: ensure simplify-ignore files are restored after the entire
processing chain completes. If monologue_end missed any tracked files
(e.g., due to an exception), this hook catches them.

Fires at the absolute end of the processing chain — after monologue_end.
Belt-and-suspenders approach for file integrity.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_plugin_root = str(_Path(__file__).resolve().parents[3])
if _plugin_root not in _sys.path:
    _sys.path.insert(0, _plugin_root)
from pathlib import Path

from helpers.extension import Extension
from helpers.print_style import PrintStyle

from lib import simplify_ignore_utils as _su

PLUGIN_NAME = "a0_agent_skills"


class SimplifyIgnoreChainEnd(Extension):
    """Final restore safety net at process_chain_end."""

    async def execute(self, **kwargs):
        if not self.agent:
            return
        try:
            cache: dict = self.agent.context.data.get(_su.CACHE_KEY, {})
            if not cache:
                return

            # Some files weren't restored by monologue_end
            PrintStyle.warning(
                f"[{PLUGIN_NAME}] {len(cache)} file(s) still tracked "
                "after monologue_end — restoring now"
            )

            restored = []
            for file_path, entry in list(cache.items()):
                original = entry.get("original", "")
                if original:
                    try:
                        Path(file_path).write_text(original, encoding="utf-8")
                        _su.clear_manifest(file_path)
                        restored.append(file_path)
                    except Exception as exc:
                        PrintStyle.error(
                            f"[{PLUGIN_NAME}] chain_end restore failed "
                            f"for {file_path}: {exc}"
                        )

            # Clear all cache entries that were successfully restored
            for file_path in restored:
                cache.pop(file_path, None)

            if restored:
                PrintStyle.hint(
                    f"[{PLUGIN_NAME}] chain_end recovered {len(restored)} "
                    "file(s): " + ", ".join(restored)
                )
        except Exception as exc:
            PrintStyle.error(f"[{PLUGIN_NAME}] chain_end error: {exc}")
