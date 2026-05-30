# Shared test infrastructure for a0_agent_skills tests.
#
# Provides:
#   - _clean_sys_modules fixture: save/restore sys.modules around each test
#   - Module stubs: helpers, helpers.extension, helpers.tool, helpers.plugins, helpers.projects
#   - _make_extension factory: creates SkillTelemetry instances with mocked agent
#   - Parallel tool stubs: _Response, _Tool, _install_parallel_tool_stubs for
#     call_subordinate_parallel tests

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Shared module stubs - required before any extension import
# ---------------------------------------------------------------------------

extension_mod = MagicMock()
extension_mod.Extension = object

# Singleton for the real simplify_ignore_shared module — loaded once, reused
# across _clean_sys_modules fixture resets to preserve the shared _cache.
_shared_module = None

# Singleton for the real helpers.skill_match module — loaded once, reused
# across _clean_sys_modules fixture resets.
_skill_match_module = None

# Singleton for the real helpers.phase_governance module — loaded once,
# reused across _clean_sys_modules fixture resets.
_phase_governance_module = None

# Singleton for the real helpers.workflow_state module — loaded once,
# reused across _clean_sys_modules fixture resets.
_workflow_state_module = None

# Singleton for the real helpers.skill_contracts module — loaded once,
# reused across _clean_sys_modules fixture resets.
_skill_contracts_module = None


def _install_stubs():
    """Install minimal stubs so the extension can be imported without A0 runtime.

    Called lazily via the ``_clean_sys_modules`` autouse fixture rather than at
    module import time.  A guard flag ensures stubs are only installed once per
    session even though the fixture runs before every test.
    """
    sys.modules["helpers"] = MagicMock()
    sys.modules["helpers.extension"] = extension_mod
    sys.modules["helpers.tool"] = MagicMock()
    sys.modules["helpers.plugins"] = MagicMock()
    sys.modules["helpers.projects"] = MagicMock()
    sys.modules["helpers.skills"] = MagicMock()

    # Register real plugin helper modules so tests can import them without
    # the MagicMock.  Each is loaded once via importlib and reused across
    # _clean_sys_modules fixture resets.
    import importlib.util
    global _shared_module, _skill_match_module, _phase_governance_module, _workflow_state_module, _skill_contracts_module

    # helpers.simplify_ignore_shared
    if _shared_module is None:
        _shared_path = Path(__file__).parent.parent / "helpers" / "simplify_ignore_shared.py"
        if _shared_path.exists():
            _spec = importlib.util.spec_from_file_location(
                "helpers.simplify_ignore_shared", str(_shared_path)
            )
            _shared_module = importlib.util.module_from_spec(_spec)
            _spec.loader.exec_module(_shared_module)
    if _shared_module is not None:
        sys.modules["helpers.simplify_ignore_shared"] = _shared_module

    # helpers.skill_match
    if _skill_match_module is None:
        _sm_path = Path(__file__).parent.parent / "helpers" / "skill_match.py"
        if _sm_path.exists():
            _sm_spec = importlib.util.spec_from_file_location(
                "helpers.skill_match", str(_sm_path)
            )
            _skill_match_module = importlib.util.module_from_spec(_sm_spec)
            _sm_spec.loader.exec_module(_skill_match_module)
    if _skill_match_module is not None:
        sys.modules["helpers.skill_match"] = _skill_match_module

    # helpers.phase_governance
    if _phase_governance_module is None:
        _pg_path = Path(__file__).parent.parent / "helpers" / "phase_governance.py"
        if _pg_path.exists():
            _pg_spec = importlib.util.spec_from_file_location(
                "helpers.phase_governance", str(_pg_path)
            )
            _phase_governance_module = importlib.util.module_from_spec(_pg_spec)
            _pg_spec.loader.exec_module(_phase_governance_module)
    if _phase_governance_module is not None:
        sys.modules["helpers.phase_governance"] = _phase_governance_module

    # helpers.workflow_state
    if _workflow_state_module is None:
        _ws_path = Path(__file__).parent.parent / "helpers" / "workflow_state.py"
        if _ws_path.exists():
            _ws_spec = importlib.util.spec_from_file_location(
                "helpers.workflow_state", str(_ws_path)
            )
            _workflow_state_module = importlib.util.module_from_spec(_ws_spec)
            _ws_spec.loader.exec_module(_workflow_state_module)
    if _workflow_state_module is not None:
        sys.modules["helpers.workflow_state"] = _workflow_state_module

    # Make real modules accessible via `from helpers import X` by setting them
    # as attributes on the helpers MagicMock. Without this, `from helpers import
    # workflow_state` resolves to MagicMock().workflow_state (a sub-mock), not
    # the real module we loaded above.
    if _phase_governance_module is not None:
        sys.modules["helpers"].phase_governance = _phase_governance_module
    if _workflow_state_module is not None:
        sys.modules["helpers"].workflow_state = _workflow_state_module
    # Also ensure skill_match attribute is set for `from helpers import skill_match`
    if _skill_match_module is not None:
        sys.modules["helpers"].skill_match = _skill_match_module

    # helpers.skill_contracts
    if _skill_contracts_module is None:
        _sc_path = Path(__file__).parent.parent / "helpers" / "skill_contracts.py"
        if _sc_path.exists():
            _sc_spec = importlib.util.spec_from_file_location(
                "helpers.skill_contracts", str(_sc_path)
            )
            _skill_contracts_module = importlib.util.module_from_spec(_sc_spec)
            _sc_spec.loader.exec_module(_skill_contracts_module)
    if _skill_contracts_module is not None:
        sys.modules["helpers.skill_contracts"] = _skill_contracts_module
        sys.modules["helpers"].skill_contracts = _skill_contracts_module


# Guard flag: stubs are installed lazily via pytest_configure (which runs
# before collection) rather than at bare module import time.
_stubs_installed: bool = False


def pytest_configure(config):
    """Install stubs once before test collection begins.

    This is the proper lazy alternative to calling ``_install_stubs()`` at
    module import time — ``pytest_configure`` runs after conftest is loaded
    but before test modules are collected, so top-level imports in test
    files still find the stubs they need.
    """
    global _stubs_installed
    if not _stubs_installed:
        _install_stubs()
        _stubs_installed = True


@pytest.fixture(autouse=True)
def _clean_sys_modules():
    """Save and restore sys.modules to avoid cross-test contamination.

    Re-installs stubs after each test to ensure a clean slate, but skips
    the expensive importlib loading after the first call.
    """
    # Reset enforcer helpers cache so test mocks aren't bypassed
    try:
        from extensions.python.tool_execute_before._10_skill_enforcer import (
            _reset_helpers_cache,
        )
        _reset_helpers_cache()
    except Exception:
        pass

    original = dict(sys.modules)
    _install_stubs()
    yield
    for key in list(sys.modules.keys()):
        if key not in original:
            del sys.modules[key]
    sys.modules.update(original)


# ---------------------------------------------------------------------------
# Shared path setup
# ---------------------------------------------------------------------------

PLUGIN_ROOT = Path(__file__).parent.parent

# Ensure plugin root is on sys.path for extension imports
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))


# ---------------------------------------------------------------------------
# Shared factory: _make_extension
# ---------------------------------------------------------------------------

def _make_extension(
    telemetry_enabled: bool | str = True,
    log_path: str | None = None,
    method: str = "load",
    skill_name: str = "test-skill",
    config: dict | None = None,
):
    # Return a (SkillTelemetry, plugins_mock, agent) tuple with mocked agent context.
    #
    # Args:
    #   telemetry_enabled: Value for telemetry_enabled in plugin config.
    #       Accepts bool or str to test type-coercion. Ignored when config is provided.
    #   log_path: Override telemetry_log_path. Ignored when config is provided.
    #   method: The method name on loop_data.current_tool.
    #   skill_name: The skill_name in current_tool.args.
    #   config: If provided, used as full plugin config dict. Pass {} for no-config tests.
    from extensions.python.tool_execute_after._05_skill_telemetry import SkillTelemetry

    ext = SkillTelemetry.__new__(SkillTelemetry)

    if config is not None:
        cfg = config
    else:
        cfg = {
            "telemetry_enabled": telemetry_enabled,
            "telemetry_log_path": log_path or ".a0proj/skill_activations.jsonl",
        }
    plugins_mock = MagicMock()
    plugins_mock.get_plugin_config.return_value = cfg

    agent = MagicMock()
    agent.context = MagicMock()
    current_tool = MagicMock()
    current_tool.method = method
    current_tool.args = {"skill_name": skill_name}
    agent.loop_data = MagicMock()
    agent.loop_data.current_tool = current_tool
    ext.agent = agent

    return ext, plugins_mock, agent


# ---------------------------------------------------------------------------
# Shared parallel tool stubs (call_subordinate_parallel tests)
# ---------------------------------------------------------------------------


@dataclass
class _Response:
    message: str
    break_loop: bool
    additional: dict[str, Any] | None = None


class _Tool:
    """Minimal Tool base class replicating helpers.tool.Tool."""

    def __init__(
        self, agent, name: str, method, args: dict, message: str, loop_data, **kwargs
    ):
        self.agent = agent
        self.name = name
        self.method = method
        self.args = args
        self.loop_data = loop_data
        self.message = message
        self.progress: str = ""

    async def set_progress(self, content: str | None):
        self.progress = content or ""


def _install_parallel_tool_stubs():
    """Install stubs for call_subordinate_parallel tool imports."""
    # helpers.tool — provide real classes
    tool_mod = sys.modules.get("helpers.tool") or MagicMock()
    tool_mod.Tool = _Tool
    tool_mod.Response = _Response
    sys.modules["helpers.tool"] = tool_mod

    # Agent module mock with proper attributes
    agent_mod = MagicMock()
    agent_mod.Agent = MagicMock
    agent_mod.AgentConfig = MagicMock

    # AgentContext — callable that accepts **kwargs
    agent_mod.AgentContext = MagicMock(return_value=MagicMock())

    # AgentContextType — needs real .TASK attribute
    class _StubContextType:
        USER = "user"
        TASK = "task"
        BACKGROUND = "background"
    agent_mod.AgentContextType = _StubContextType

    # UserMessage — simple dataclass-like callable
    def _stub_user_message(message="", attachments=None, **kw):
        um = MagicMock()
        um.message = message
        um.attachments = attachments or []
        return um
    agent_mod.UserMessage = _stub_user_message

    sys.modules["agent"] = agent_mod

    # Initialize module mock
    init_mod = MagicMock()
    init_mod.initialize_agent = MagicMock()
    sys.modules["initialize"] = init_mod

    # Persist chat mock
    persist_mod = MagicMock()
    persist_mod.save_tmp_chat = MagicMock()
    sys.modules["helpers.persist_chat"] = persist_mod
