"""a0_agent_skills plugin."""

import os
import sys as _sys

__version__ = "0.4.0"

# ── sys.path injection for plugin-local helpers ──────────────────────
# The plugin root contains _plugin_loader.py which extensions import.
# The framework mounts only /usr, so the plugin root is not on sys.path.
# We inject it here so that `from _plugin_loader import ...` works.
_PLUGIN_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PLUGIN_ROOT not in _sys.path:
    _sys.path.insert(0, _PLUGIN_ROOT)

# Also inject helpers/ for bare imports like `from helpers.extension import ...`
_PLUGIN_HELPERS = os.path.join(_PLUGIN_ROOT, "helpers")
if _PLUGIN_HELPERS not in _sys.path:
    _sys.path.insert(0, _PLUGIN_HELPERS)
