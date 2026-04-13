"""
_10_simplify_ignore_after.py  —  tool_execute_after hook

Fires after any tool runs.
When the tool is `text_editor:patch` or `text_editor:write`, and the target
file is tracked in the simplify-ignore cache, this hook:

  1. Reads the current on-disk content (which may contain BLOCK_<hash>
     placeholders because the agent wrote/patched a filtered view).
  2. Expands all placeholders back to real block content — merging the
     agent's edits with the protected blocks.
  3. Saves the merged content as the new 'original' backup in context
     (so the real file, with model changes applied, is always preserved).
  4. Re-filters the file on disk so placeholders remain hidden from the
     agent in subsequent reads.

NOTE: A0 core (agent.py) does NOT pass tool_args to tool_execute_after.
We derive the file path from self.agent.loop_data.current_tool.args instead.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

from helpers.extension import Extension
from helpers.print_style import PrintStyle


# importlib is used because A0 extensions cannot rely on sys.path
# containing the plugin directory — derive path from __file__ instead.
# Shared utilities now live in <plugin_root>/lib/ for cleaner separation.
_utils_mod = None

def _utils():
    global _utils_mod
    if _utils_mod is None:
        utils_path = Path(__file__).resolve().parents[3] / 'lib' / 'simplify_ignore_utils.py'
        spec = importlib.util.spec_from_file_location('simplify_ignore_utils', utils_path)
        mod = importlib.util.module_from_spec(spec)   # type: ignore[arg-type]
        spec.loader.exec_module(mod)                  # type: ignore[union-attr]
        _utils_mod = mod
    return _utils_mod


# Tools that may modify a file's content
_WRITE_TOOLS = {'text_editor:patch', 'text_editor:write'}


class SimplifyIgnoreAfter(Extension):
    """
    Post-tool hook: expand placeholders then re-filter after the agent edits
    a file that contains simplify-ignore blocks.
    """

    async def execute(self, **kwargs):
        try:
            await self._run(**kwargs)
        except Exception as exc:
            PrintStyle.error(f'[simplify-ignore-after] unexpected error: {exc}')

    async def _run(self, **kwargs):
        tool_name: str = kwargs.get('tool_name', '')

        # Only act on write-class tools
        if tool_name not in _WRITE_TOOLS:
            return

        # A0 core does not pass tool_args to tool_execute_after.
        # Derive the file path from the still-active current_tool reference
        # (current_tool is cleared in the finally block AFTER this hook runs).
        file_path: str = ''
        try:
            current_tool = self.agent.loop_data.current_tool
            if current_tool and current_tool.args:
                file_path = current_tool.args.get('path', '')
        except (AttributeError, TypeError):
            pass

        if not file_path:
            return

        # Normalise to absolute path
        file_path = str(Path(file_path).resolve())

        utils = _utils()
        cache: dict = self.agent.context.data.get(utils.CACHE_KEY, {})

        # Only act on files we are tracking
        if file_path not in cache:
            return

        entry = cache[file_path]
        blocks: dict = entry.get('blocks', {})

        # If no blocks are tracked, nothing to expand
        if not blocks:
            return

        # ── 1. Read what the agent wrote (may contain placeholders) ──────────
        try:
            on_disk = Path(file_path).read_text(encoding='utf-8', errors='replace')
        except OSError as exc:
            PrintStyle.error(f'[simplify-ignore-after] could not read {file_path}: {exc}')
            return

        # ── 2. Expand placeholders → merged real content ──────────────────────
        expanded = utils.expand_content(on_disk, blocks, file_path)

        # ── 3. Write expanded content to disk ─────────────────────────────────
        try:
            with open(file_path, 'w', encoding='utf-8') as fh:
                fh.write(expanded)
        except OSError as exc:
            PrintStyle.error(f'[simplify-ignore-after] could not write expanded file: {exc}')
            return

        # ── 4. Update the 'original' backup with the merged content ───────────
        #       (model's edits are now baked in alongside the real block code)
        entry['original'] = expanded

        # ── 5. Re-filter in-place so placeholders stay hidden ─────────────────
        filtered, new_blocks, had_blocks = utils.filter_content(expanded, file_path)

        if had_blocks:
            # Update block metadata (hashes are content-stable but keep fresh)
            entry['blocks'] = new_blocks
            try:
                with open(file_path, 'w', encoding='utf-8') as fh:
                    fh.write(filtered)
            except OSError as exc:
                PrintStyle.error(f'[simplify-ignore-after] could not write re-filtered file: {exc}')
        else:
            # All blocks were deleted by the model — clear tracking for this file
            # (no blocks left to protect; file stays as-is with expanded content)
            cache.pop(file_path, None)
