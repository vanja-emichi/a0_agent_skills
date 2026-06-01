"""Lifecycle hooks for the a0_agent_skills plugin.

Hook Policy Decisions
======================

Upstream (addyosmani/agent-skills) has 9 hook files. See docs/hook-alignment.md
for the full classification and policy details.

Summary: 1 PORT (done), 2 OMIT, 6 DEFER. No shipping blockers.

Technical Notes
===============

The original design used install() to write a routing promptinclude file to the
workdir, but that approach had a critical flaw — workdir promptincludes are NOT
injected when a project is active, so the routing rules were invisible during
real work.

Routing is now handled by the system_prompt extension at:
  extensions/python/system_prompt/_15_agent_skills_routing.py

That extension reads prompts/agent.skills.routing.md at runtime and appends
routing rules to the system prompt during assembly — working universally
regardless of whether a project is active.

These stubs are retained for potential future plugin lifecycle needs
(e.g., migration hooks, version upgrade notifications).
"""


import importlib.util
import os
import sys as _sys

# sys.path injection is handled by __init__.py (canonical location).
# _PLUGIN_ROOT retained for _bootstrap_plugin_loader() path resolution.
_PLUGIN_ROOT = os.path.dirname(os.path.abspath(__file__))


def _bootstrap_plugin_loader():
    if '_plugin_loader' not in _sys.modules:
        this_dir = os.path.dirname(os.path.abspath(__file__))
        plugin_root = this_dir  # hooks.py is in plugin root, no walk up needed
        spec = importlib.util.spec_from_file_location(
            '_plugin_loader', os.path.join(plugin_root, '_plugin_loader.py'))
        mod = importlib.util.module_from_spec(spec)
        _sys.modules['_plugin_loader'] = mod
        spec.loader.exec_module(mod)
    return _sys.modules['_plugin_loader']


def install() -> None:
    """Called when the plugin is installed or enabled.

    Routing injection is handled by the system_prompt extension,
    not by file writing. sys.path injection is done at module load
    time (above) so extensions can import plugin helpers.
    """
    pass


def uninstall() -> None:
    """Called when the plugin is uninstalled or disabled."""
    pass


def pre_update() -> None:
    """Called immediately before plugin code is replaced during an update.

    Should call ``invalidate_module_cache()`` from ``_plugin_loader`` so
    that subsequent imports pick up the fresh code (I2).
    """
    try:
        _loader = _bootstrap_plugin_loader()
        _loader.invalidate_module_cache()
    except Exception:
        pass
