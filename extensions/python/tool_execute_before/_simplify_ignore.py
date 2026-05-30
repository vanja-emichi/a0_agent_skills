"""simplify-ignore - tool_execute_before extension

Intercepts text_editor tool invocations before write and patch
actions.  Scans the tool arguments (content, new_text, patch_text,
old_text) for BLOCK_<hash> placeholders and expands them back to the
real code from the cache before the write/patch executes.

Only activates for the text_editor tool.  All errors are caught and logged
so that a failure never breaks the agent's workflow.
"""

from __future__ import annotations

import logging

from helpers.extension import Extension

_log = logging.getLogger(__name__)

# Argument keys that may contain BLOCK_<hash> placeholders and need expansion
_EXPANDABLE_ARGS = ("content", "new_text", "patch_text", "old_text")


def _import_shared():
    """Lazy import of the shared module from the plugin root.

    Uses _plugin_loader.load_module_by_path to avoid duplicating the
    importlib bootstrap logic.
    """
    import importlib.util
    import os
    import sys

    this_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.normpath(os.path.join(this_dir, '..', '..', '..'))

    # Bootstrap _plugin_loader if not already loaded
    if '_plugin_loader' not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            '_plugin_loader', os.path.join(plugin_root, '_plugin_loader.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules['_plugin_loader'] = mod
        spec.loader.exec_module(mod)
    _loader = sys.modules['_plugin_loader']

    _shared = _loader.load_module_by_path(
        'helpers.simplify_ignore_shared',
        os.path.join(plugin_root, 'helpers', 'simplify_ignore_shared.py'),
    )
    return _shared.get_cache, _shared.expand_placeholders, _shared.BLOCK_HASH_RE


class SimplifyIgnoreBefore(Extension):
    """Expand BLOCK_<hash> placeholders in text_editor write/patch arguments."""

    async def execute(
        self,
        tool_args: "dict | None" = None,
        tool_name: "str | None" = None,
        **kwargs,
    ) -> None:
        try:
            if not tool_name or tool_name != "text_editor":
                return
            if not tool_args or not isinstance(tool_args, dict):
                return

            action = tool_args.get("action", "")
            if action not in ("write", "patch"):
                return

            get_cache, expand_placeholders, BLOCK_HASH_RE = _import_shared()
            cache = get_cache()

            # Check if cache has anything before scanning args
            if cache.size() == 0:
                return

            modified = False
            for key in _EXPANDABLE_ARGS:
                value = tool_args.get(key)
                if not value or not isinstance(value, str):
                    continue
                if "BLOCK_" not in value:
                    continue
                if not BLOCK_HASH_RE.search(value):
                    continue

                expanded = expand_placeholders(value, cache)
                if expanded != value:
                    tool_args[key] = expanded
                    modified = True

            if modified:
                _log.debug("simplify-ignore: expanded placeholders in %s", action)

        except Exception:
            # NEVER break the agent's workflow
            _log.warning("simplify-ignore before extension failed", exc_info=True)
