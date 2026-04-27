# lib/extension_base.py - LifecycleExtension base class
#
# Eliminates importlib boilerplate and lifecycle-dir resolution duplication
# across the lifecycle-aware extensions.
#
# Usage:
#   from lib.extension_base import LifecycleExtension
#   class MyExt(LifecycleExtension):
#       async def execute(self, **kwargs):
#           state = self._load_lifecycle()
#           if state is None:
#               return

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from helpers.extension import Extension

# Module-level cache for lifecycle_state module (shared across all instances).
_lifecycle_state_mod = None


def _get_lifecycle_state():
    """Load lifecycle_state module via shared import_utils helper.

    Cached at module level after first call.
    """
    global _lifecycle_state_mod
    if _lifecycle_state_mod is not None:
        return _lifecycle_state_mod
    mod_name = "a0_agent_skills_import_utils"
    if mod_name not in sys.modules:
        mod_path = Path(__file__).resolve().parent / "import_utils.py"
        spec = importlib.util.spec_from_file_location(mod_name, mod_path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = mod
        spec.loader.exec_module(mod)
    _lifecycle_state_mod = sys.modules[mod_name].get_lifecycle_state_module()
    return _lifecycle_state_mod


class LifecycleExtension(Extension):
    """Base class for extensions that interact with lifecycle state.

    Provides:
    - _resolve_lifecycle_dir() - resolves .a0proj/run/current/ path
    - _load_lifecycle() - loads LifecycleState or returns None

    Subclasses inherit from this instead of Extension directly.
    """

    def _resolve_lifecycle_dir(self) -> Path | None:
        """Resolve the lifecycle directory from project context."""
        from helpers import projects
        try:
            project_name = projects.get_context_project_name(self.agent.context)
        except Exception:
            return None
        if project_name:
            project_folder = projects.get_project_folder(project_name)
            return Path(project_folder, ".a0proj", "run", "current")
        LifecycleState = _get_lifecycle_state().LifecycleState
        return LifecycleState._get_fallback_dir()

    def _load_lifecycle(self):
        """Load lifecycle state. Returns None if no active lifecycle exists."""
        plan_dir = self._resolve_lifecycle_dir()
        if plan_dir is None:
            return None
        LifecycleState = _get_lifecycle_state().LifecycleState
        return LifecycleState.load(plan_dir=plan_dir, context=self.agent.context)
