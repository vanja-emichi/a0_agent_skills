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
import sys
from pathlib import Path

from helpers.extension import Extension


# ── lazy-load shared utils from sibling directory ────────────────────────────
def _utils():
    utils_path = Path(__file__).parent.parent / 'simplify_ignore_utils.py'
    spec = importlib.util.spec_from_file_location('simplify_ignore_utils', utils_path)
    mod = importlib.util.module_from_spec(spec)   # type: ignore[arg-type]
    spec.loader.exec_module(mod)                  # type: ignore[union-attr]
    return mod


class SimplifyIgnoreRestore(Extension):
    """
    Monologue-end hook: restore all simplify-ignore-protected files from
    the in-context backup and clear the cache.
    """

    async def execute(self, **kwargs):
        try:
            await self._run(**kwargs)
        except Exception as exc:
            print(f'[simplify-ignore-restore] unexpected error: {exc}', file=sys.stderr)

    async def _run(self, **kwargs):
        utils = _utils()
        cache: dict = self.agent.context.data.get(utils.CACHE_KEY, {})

        if not cache:
            return  # Nothing to restore

        restored = []
        failed = []

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
                    print(
                        f'[simplify-ignore-restore] {file_path} was moved/deleted. '
                        f'Recovered original to {recovered}',
                        file=sys.stderr,
                    )
                    restored.append(file_path)
                except OSError as exc:
                    print(
                        f'[simplify-ignore-restore] could not write recovered file '
                        f'{recovered}: {exc}',
                        file=sys.stderr,
                    )
                    failed.append(file_path)
                continue

            # Restore real content to original file path
            try:
                with open(file_path, 'w', encoding='utf-8') as fh:
                    fh.write(original)
                restored.append(file_path)
            except OSError as exc:
                print(
                    f'[simplify-ignore-restore] could not restore {file_path}: {exc}',
                    file=sys.stderr,
                )
                failed.append(file_path)

        # Clear the cache regardless — failed entries would need manual recovery
        self.agent.context.data.pop(utils.CACHE_KEY, None)

        if restored:
            print(
                f'[simplify-ignore-restore] restored {len(restored)} file(s): '
                + ', '.join(restored),
                file=sys.stderr,
            )
        if failed:
            print(
                f'[simplify-ignore-restore] WARNING: failed to restore {len(failed)} '
                f'file(s): ' + ', '.join(failed),
                file=sys.stderr,
            )
