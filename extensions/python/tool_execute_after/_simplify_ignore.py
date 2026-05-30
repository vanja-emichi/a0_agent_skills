"""simplify-ignore - tool_execute_after extension

Intercepts text_editor tool responses after a read action.  Scans the
response for simplify-ignore-start/simplify-ignore-end markers, replaces
protected blocks with BLOCK_<hash> placeholders in the response (not on
disk), and caches the real block content keyed by hash.

Only activates for the text_editor tool.  All errors are caught and logged
so that a failure never breaks the agent's workflow.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from helpers.extension import Extension

if TYPE_CHECKING:
    from helpers.tool import Response

_log = logging.getLogger(__name__)


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
    return _shared.get_cache, _shared.replace_blocks


class SimplifyIgnoreAfter(Extension):
    """Replace simplify-ignore blocks in text_editor read responses."""

    async def execute(
        self,
        response: "Response | None" = None,
        tool_name: "str | None" = None,
        **kwargs,
    ) -> None:
        try:
            if not tool_name or tool_name != "text_editor":
                return
            if response is None:
                return

            message = getattr(response, "message", None)
            if not message or not isinstance(message, str):
                return

            # Quick check: if no simplify-ignore markers, skip entirely
            if "simplify-ignore-start" not in message:
                return

            get_cache, replace_blocks = _import_shared()
            cache = get_cache()

            new_message = replace_blocks(message, cache)
            if new_message != message:
                response.message = new_message

        except Exception:
            # NEVER break the agent's workflow
            _log.warning("simplify-ignore after extension failed", exc_info=True)
