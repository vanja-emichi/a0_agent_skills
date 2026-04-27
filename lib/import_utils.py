# lib/import_utils.py - Shared importlib loaders for a0_agent_skills
#
# Extensions cannot rely on sys.path containing the plugin directory.
# This module provides singleton loaders for lib modules used across extensions.
#
# Caching uses sys.modules (not module globals) so that all extensions
# share the same module objects regardless of how import_utils itself
# was loaded.

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_cached(mod_name: str, mod_path: Path):
    """Load a module via importlib, caching in sys.modules for singleton access.

    MUST register in sys.modules BEFORE exec_module for @dataclass to work
    (avoids NoneType.__dict__ error).
    """
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, mod_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# Resolve plugin root relative to this file (lib/import_utils.py -> plugin root)
_PLUGIN_ROOT = Path(__file__).resolve().parent.parent


def get_lifecycle_state_module():
    """Load and cache the lib.lifecycle_state module singleton.

    Returns the module containing LifecycleState, Phase, Finding, etc.
    """
    return _load_cached(
        "a0_agent_skills_lifecycle_state",
        _PLUGIN_ROOT / "lib" / "lifecycle_state.py",
    )


def get_strike_tracker_module():
    """Load and cache the lib.strike_tracker module singleton.

    Returns the module containing StrikeTracker.
    """
    return _load_cached(
        "a0_agent_skills_strike_tracker",
        _PLUGIN_ROOT / "lib" / "strike_tracker.py",
    )


def get_simplify_ignore_utils_module():
    """Load and cache the lib.simplify_ignore_utils module singleton.

    Returns the module containing filter_content, expand_content, etc.
    """
    return _load_cached(
        "a0_agent_skills_simplify_ignore_utils",
        _PLUGIN_ROOT / "lib" / "simplify_ignore_utils.py",
    )


def get_extension_base_module():
    """Load and cache the lib.extension_base module singleton.

    Returns the module containing LifecycleExtension base class.
    """
    return _load_cached(
        "a0_agent_skills_extension_base",
        _PLUGIN_ROOT / "lib" / "extension_base.py",
    )
