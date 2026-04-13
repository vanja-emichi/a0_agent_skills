"""
_10_simplify_ignore_restore.py  —  monologue_end hook

Fires when the agent's monologue (turn) ends.

Restores ALL files tracked by the simplify-ignore cache to their real
content (the 'original' backup, which always reflects the model's latest
edits merged with protected block code).

The file on disk during the session always holds BLOCK_<hash> placeholders.
This hook is what makes the real code reappear after the session ends,
mapping directly to the `Stop` event handler in simplify-ignore.sh.

Post-restore the cache entry is cleared so a fresh read next turn starts
from scratch (re-filtering if the file still contains markers).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from helpers.extension import Extension
from helpers.print_style import PrintStyle


# importlib is used because A0 extensions cannot rely on sys.path
# containing the plugin directory — derive path from __file__ instead.
_utils_mod = None


def _utils():
    global _utils_mod
    if _utils_mod is None:
        utils_path = Path(__file__).parent.parent / 'simplify_ignore_utils.py'
        spec = importlib.util.spec_from_file_location('simplify_ignore_utils', utils_path)
        mod = importlib.util.module_from_spec(spec)   # type: ignore[arg-type]
        spec.loader.exec_module(mod)                  # type: ignore[union-attr]
        _utils_mod = mod
    return _utils_mod


class SimplifyIgnoreRestore(Extension):
    """
    Monologue-end hook: restore all simplify-ignore-protected files from
    the in-context backup and clear the cache.
    """

    async def execute(self, **kwargs):
        try:
            await self._run(**kwargs)
        except Exception as exc:
            PrintStyle.error(f'[simplify-ignore-restore] unexpected error: {exc}')

    async def _run(self, **kwargs):
        utils = _utils()
        cache: dict = self.agent.context.data.get(utils.CACHE_KEY, {})

        if not cache:
            return  # Nothing to restore

        restored: list[str] = []
        failed: list[str] = []

        for file_path, entry in list(cache.items()):
            original: str = entry.get('original', '')
            if not original:
                continue

            target = Path(file_path)

            if not target.exists():
                # File was moved/deleted — save recovered copy next to expected location
                recovered = Path(str(file_path) + '.recovered')
                try:
                    recovered.parent.mkdir(parents=True, exist_ok=True)
                    recovered.write_text(original, encoding='utf-8')
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
                continue

            # Restore real content to original file path
            try:
                with open(file_path, 'w', encoding='utf-8') as fh:
                    fh.write(original)
                restored.append(file_path)
            except OSError as exc:
                PrintStyle.error(
                    f'[simplify-ignore-restore] could not restore {file_path}: {exc}',
                )
                failed.append(file_path)

        # Only clear cache entries that were successfully restored.
        # Failed entries remain in cache so they can be retried next turn.
        for file_path in restored:
            cache.pop(file_path, None)

        if restored:
            PrintStyle.hint(
                f'[simplify-ignore-restore] restored {len(restored)} file(s): '
                + ', '.join(restored),
            )
        if failed:
            PrintStyle.error(
                f'[simplify-ignore-restore] WARNING: failed to restore {len(failed)} '
                f'file(s): ' + ', '.join(failed),
            )
            PrintStyle.error(
                '[simplify-ignore-restore] These entries remain in cache for retry. '
                'To recover manually, inspect agent context under key '
                f'"{utils.CACHE_KEY}" and write the "original" value back to each file.',
            )
