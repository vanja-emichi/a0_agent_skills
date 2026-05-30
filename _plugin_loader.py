"""Shared importlib-based loader for plugin-local modules.

Plugin extensions are loaded via ``importlib.util.spec_from_file_location``,
so ``helpers.skill_match`` resolves to the *framework's* ``helpers/`` package
rather than the plugin's ``helpers/`` directory.  This module provides a
single, cacheable loader that resolves plugin-local modules by absolute path.

Usage inside an extension::

    from _plugin_loader import load_plugin_module

    _skill_match = load_plugin_module('helpers', 'skill_match.py')
    is_target_tool = _skill_match.is_target_tool
"""

from __future__ import annotations

import importlib.util
import logging
import os
import sys
from typing import Any

_log = logging.getLogger(__name__)

# Plugin root: /a0/usr/plugins/a0_agent_skills
_PLUGIN_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_plugin_root() -> str:
    """Return the absolute path to the plugin root directory.

    Shared canonical source for plugin root path, used by helpers and
    extensions that need to resolve paths relative to the plugin root.
    """
    return _PLUGIN_ROOT

# Cache loaded modules to avoid repeated file I/O and exec_module calls
_module_cache: dict[str, Any] = {}


def _resolve_path(*parts: str) -> str:
    """Resolve a path relative to the plugin root."""
    return os.path.join(_PLUGIN_ROOT, *parts)


def load_plugin_module(subdir: str, filename: str, module_name: str | None = None):
    """Load a Python module from the plugin directory by absolute path.

    Args:
        subdir: Subdirectory within the plugin (e.g. ``"helpers"``).
        filename: File name including extension (e.g. ``"skill_match.py"``).
        module_name: Optional module name for ``sys.modules``; defaults to filename stem.

    Returns:
        The loaded module object.

    Raises:
        ImportError: If the module cannot be found or loaded.
    """
    cache_key = f"{subdir}/{filename}"
    if cache_key in _module_cache:
        return _module_cache[cache_key]

    # Check if already registered in sys.modules (e.g., by test conftest.py).
    # The conftest registers helpers.simplify_ignore_shared and helpers.skill_match
    # via importlib before tests run — reuse those to preserve shared singletons.
    if module_name is None:
        module_name = os.path.splitext(filename)[0]
    sys_modules_key = f"{subdir}.{module_name}"
    if sys_modules_key in sys.modules:
        cached_mod = sys.modules[sys_modules_key]
        _module_cache[cache_key] = cached_mod
        return cached_mod

    file_path = _resolve_path(subdir, filename)

    if not os.path.isfile(file_path):
        raise ImportError(f"Plugin module not found: {file_path}")

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create module spec for {file_path}")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise ImportError(f"Failed to execute {file_path}: {exc}") from exc

    _module_cache[cache_key] = module
    _log.debug("Loaded plugin module: %s from %s", module_name, file_path)
    return module


def load_extension_module(extension_point: str, filename: str):
    """Load a module from the plugin's extensions directory.

    Args:
        extension_point: e.g. ``"tool_execute_after"``
        filename: e.g. ``"_05_skill_telemetry.py"``

    Returns:
        The loaded module object.
    """
    return load_plugin_module(
        "extensions/python", os.path.join(extension_point, filename)
    )


# ---------------------------------------------------------------------------
# Shared utility functions (DRY across extensions)
# ---------------------------------------------------------------------------


def load_module_by_path(module_name: str, file_path: str):
    """Load a Python module from an absolute file path.

    Returns the existing module from sys.modules if already loaded
    (supports test mocking via unittest.mock.patch).  Otherwise loads
    via importlib.util.spec_from_file_location and registers it.

    This is the shared version of the formerly duplicated _load_module_by_path
    found in multiple extension files.
    """
    if module_name in sys.modules:
        return sys.modules[module_name]
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


def get_plugin_config(agent) -> dict:
    """Read plugin config for a0_agent_skills, returning empty dict on failure.

    Shared implementation of the formerly duplicated _get_plugin_config
    found in multiple extension files.
    """
    try:
        from helpers import plugins as _plugins
        return _plugins.get_plugin_config("a0_agent_skills", agent=agent) or {}
    except Exception:
        return {}


def config_bool(value, default: bool = True) -> bool:
    """Convert a config value to bool, handling string representations.

    Shared implementation of the formerly duplicated str-to-bool pattern
    found in multiple extensions.  Recognizes "true", "1", "yes" (case-insensitive)
    as truthy.  Returns *default* when *value* is None.
    """
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value) if value is not None else default


# Alias: get_plugin_config already catches all exceptions, so the wrapper
# added no value.  Kept for backward compatibility with any external callers.
get_plugin_config_safe = get_plugin_config


def invalidate_module_cache() -> None:
    """Clear the module cache so subsequent loads pick up fresh code.

    Should be called by the ``pre_update`` hook (in hooks.py) before
    plugin code is replaced during an update (I2).
    """
    _module_cache.clear()
    _log.debug("Module cache invalidated")


def reconstruct_tool_info(agent, tool_name: str) -> tuple[str, dict]:
    """Reconstruct full tool name (base:method) and args from loopData.

    Returns (full_tool_name, tool_args).

    Shared implementation of the formerly duplicated _reconstruct_tool_info
    found in _10_persist_workflow_state and _05_skill_telemetry.
    """
    full_tool_name = tool_name
    tool_args: dict = {}
    try:
        if agent and hasattr(agent, "loop_data") and agent.loop_data:
            current_tool = agent.loop_data.current_tool
            if current_tool is not None:
                if current_tool.method:
                    full_tool_name = f"{tool_name}:{current_tool.method}"
                tool_args = current_tool.args or {}
    except Exception:
        pass
    return full_tool_name, tool_args
