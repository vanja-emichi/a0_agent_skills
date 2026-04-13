"""
_10_simplify_ignore_before.py  —  tool_execute_before hook

Fires before any tool runs.
When the tool is `text_editor:read`, inspect the target file for
`simplify-ignore-start/end` blocks and, if found:
  1. Read the real file content.
  2. Back it up in agent context (not on disk).
  3. Replace each protected block with a `BLOCK_<hash>` placeholder in-place
     so the agent reads the filtered version, never the real code.

Skips files already filtered (backup present in context).
Skips files whose name starts with `simplify-ignore` or `SIMPLIFY-IGNORE`
(to avoid hiding the hook source itself).
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

from helpers.extension import Extension


# ── lazy-load shared utils from sibling directory ────────────────────────────
def _utils():
    utils_path = Path(__file__).parent.parent / 'simplify_ignore_utils.py'
    spec = importlib.util.spec_from_file_location('simplify_ignore_utils', utils_path)
    mod = importlib.util.module_from_spec(spec)   # type: ignore[arg-type]
    spec.loader.exec_module(mod)                  # type: ignore[union-attr]
    return mod


class SimplifyIgnoreBefore(Extension):
    """
    Pre-tool hook: replace simplify-ignore blocks with BLOCK_<hash> placeholders
    before the agent reads a file.
    """

    async def execute(self, **kwargs):
        try:
            await self._run(**kwargs)
        except Exception as exc:
            # Extension failures must never break the tool call.
            import sys
            print(f'[simplify-ignore-before] unexpected error: {exc}', file=sys.stderr)

    async def _run(self, **kwargs):
        tool_name: str = kwargs.get('tool_name', '')
        tool_args: dict = kwargs.get('tool_args', {}) or {}

        # Only act on text_editor:read
        if tool_name != 'text_editor:read':
            return

        file_path: str = tool_args.get('path', '')
        if not file_path:
            return

        # Normalise to absolute path
        file_path = str(Path(file_path).resolve())

        # Skip hook source files themselves
        basename = os.path.basename(file_path)
        if basename.startswith('simplify-ignore') or basename.startswith('SIMPLIFY-IGNORE'):
            return

        # Skip non-existent files (let the real tool surface the error)
        if not os.path.isfile(file_path):
            return

        # ── Context cache ────────────────────────────────────────────────────
        utils = _utils()
        cache: dict = self.agent.context.data.setdefault(utils.CACHE_KEY, {})

        # If already filtered, do nothing — the placeholder file is on disk
        if file_path in cache:
            return

        # ── Quick pre-check: skip files with no markers ──────────────────────
        try:
            raw = Path(file_path).read_text(encoding='utf-8', errors='replace')
        except OSError:
            return

        if 'simplify-ignore-start' not in raw:
            return

        # ── Filter ──────────────────────────────────────────────────────────
        filtered, blocks, had_blocks = utils.filter_content(raw, file_path)

        if not had_blocks:
            # No complete blocks found (e.g. only unclosed markers)
            return

        # Persist the backup and block metadata in context
        cache[file_path] = {
            'original': raw,   # real content — updated after each model edit
            'blocks':   blocks,
        }

        # Write filtered version to disk (preserves inode via open+write)
        try:
            with open(file_path, 'w', encoding='utf-8') as fh:
                fh.write(filtered)
        except OSError as exc:
            import sys
            print(f'[simplify-ignore-before] could not write filtered file: {exc}',
                  file=sys.stderr)
            # Rollback context entry so nothing is half-done
            cache.pop(file_path, None)
