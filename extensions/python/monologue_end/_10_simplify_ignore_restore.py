
"""
_10_simplify_ignore_restore.py  --  monologue_end hook

Fires when the agent's monologue (turn) ends.

Restores ALL files tracked by the simplify-ignore cache to their real
content (the "original" backup, which always reflects the model's latest
edits merged with protected block code).

The file on disk during the session always holds BLOCK_<hash> placeholders.
This hook is what makes the real code reappear after the session ends,
mapping directly to the `Stop` event handler in simplify-ignore.sh.

Post-restore the cache entry is cleared so a fresh read next turn starts
from scratch (re-filtering if the file still contains markers).

Also releases any held file locks during cleanup.
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


class SimplifyIgnoreRestore(Extension):
    """
    Monologue-end hook: restore all simplify-ignore-protected files from
    the in-context backup, clear the cache, and release file locks.
    """

    async def execute(self, **kwargs):
        try:
            await self._run(**kwargs)
        except Exception as exc:
            PrintStyle.error(f'[simplify-ignore-restore] unexpected error: {exc}')

    async def _run(self, **kwargs):
        cache: dict = self.agent.context.data.get(_su.CACHE_KEY, {})

        if not cache:
            return  # Nothing to restore

        restored: list[str] = []
        failed: list[str] = []

        for file_path, entry in list(cache.items()):
            original: str = entry.get("original", "")
            lock_fd = entry.get("lock_fd")

            if not original:
                # Still release the lock even if no content to restore
                _su._release_lock(lock_fd)
                continue

            target = Path(file_path)

            if not target.exists():
                # File was moved/deleted -- save recovered copy next to expected location
                recovered = Path(str(file_path) + ".recovered")
                try:
                    recovered.parent.mkdir(parents=True, exist_ok=True)
                    recovered.write_text(original, encoding="utf-8")
                    PrintStyle.hint(
                        f'[simplify-ignore-restore] {file_path} was moved/deleted. '
                        f'Recovered original to {recovered}',
                    )
                    restored.append(file_path)
                except OSError as exc:
                    PrintStyle.error(
                        f'[simplify-ignore-restore] could not write recovered file '
                        f'{recovered}: {exc}',
                    )
                    failed.append(file_path)
                finally:
                    _su._release_lock(lock_fd)
                continue

            # Restore real content to original file path
            try:
                with open(file_path, "w", encoding="utf-8") as fh:
                    fh.write(original)
                restored.append(file_path)
            except OSError as exc:
                PrintStyle.error(
                    f'[simplify-ignore-restore] could not restore {file_path}: {exc}',
                )
                failed.append(file_path)
            finally:
                _su._release_lock(lock_fd)

        # Only clear cache entries that were successfully restored.
        # Failed entries remain in cache so they can be retried next turn.
        for file_path in restored:
            cache.pop(file_path, None)
            # Clear disk manifest -- original is safely back on disk
            _su.clear_manifest(file_path)

        if restored:
            PrintStyle.hint(
                f'[simplify-ignore-restore] restored {len(restored)} file(s): '
                + ", ".join(restored),
            )
        if failed:
            PrintStyle.error(
                f'[simplify-ignore-restore] WARNING: failed to restore {len(failed)} '
                f'file(s): ' + ", ".join(failed),
            )
            PrintStyle.error(
                '[simplify-ignore-restore] These entries remain in cache for retry. '
                'To recover manually, inspect agent context under key '
                f'"{_su.CACHE_KEY}" and write the "original" value back to each file.',
            )
