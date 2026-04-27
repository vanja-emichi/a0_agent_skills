"""
_10_simplify_ignore_before.py  --  tool_execute_before hook

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

Concurrency: acquires a non-blocking file lock before filtering to prevent
corruption when multiple agent contexts share the same project.
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
            PrintStyle.error(f'[simplify-ignore-before] unexpected error: {exc}')

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
        basename = Path(file_path).name
        if basename.startswith('simplify-ignore') or basename.startswith('SIMPLIFY-IGNORE'):
            return

        # Skip non-existent files (let the real tool surface the error)
        if not Path(file_path).is_file():
            return

        # -- Context cache ---------------------------------------------------
        cache: dict = self.agent.context.data.setdefault(_su.CACHE_KEY, {})

        # If already filtered, do nothing -- the placeholder file is on disk
        if file_path in cache:
            return

        # -- Quick pre-check: skip files with no markers ---------------------
        try:
            raw = Path(file_path).read_text(encoding='utf-8', errors='replace')
        except OSError:
            return

        if 'simplify-ignore-start' not in raw:
            return

        # -- Acquire file lock (fail-open) -----------------------------------
        lock_fd = _su._acquire_lock(file_path, timeout=5.0)
        if lock_fd is None:
            # Could not acquire lock -- skip filtering (fail-open, safe)
            PrintStyle.hint(
                f'[simplify-ignore-before] could not acquire lock for {file_path}, skipping filtering',
            )
            return

        # -- Filter ----------------------------------------------------------
        filtered, blocks, had_blocks = _su.filter_content(raw, file_path)

        if not had_blocks:
            # No complete blocks found (e.g. only unclosed markers)
            _su._release_lock(lock_fd)
            return

        # Persist the backup and block metadata in context
        cache[file_path] = {
            'original': raw,   # real content -- updated after each model edit
            'blocks':   blocks,
            'lock_fd':  lock_fd,  # held until restore
        }

        _su.write_manifest(file_path, raw, blocks)

        # Write filtered version to disk (preserves inode via open+write)
        try:
            with open(file_path, 'w', encoding='utf-8') as fh:
                fh.write(filtered)
        except OSError as exc:
            PrintStyle.error(f'[simplify-ignore-before] could not write filtered file: {exc}')
            # Rollback context entry, manifest, and lock so nothing is half-done
            cache.pop(file_path, None)
            _su.clear_manifest(file_path)
            _su._release_lock(lock_fd)
