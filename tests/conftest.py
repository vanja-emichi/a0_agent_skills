# Shared test infrastructure for a0_agent_skills telemetry tests.
#
# Provides:
#   - _clean_sys_modules fixture: save/restore sys.modules around each test
#   - Module stubs: helpers, helpers.extension, helpers.tool, helpers.plugins, helpers.projects
#   - _make_extension factory: creates SkillTelemetry instances with mocked agent

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Shared module stubs - required before any extension import
# ---------------------------------------------------------------------------

extension_mod = MagicMock()
extension_mod.Extension = object


def _install_stubs():
    """Install minimal stubs so the extension can be imported without A0 runtime."""
    sys.modules["helpers"] = MagicMock()
    sys.modules["helpers.extension"] = extension_mod
    sys.modules["helpers.tool"] = MagicMock()
    sys.modules["helpers.plugins"] = MagicMock()
    sys.modules["helpers.projects"] = MagicMock()


# Install stubs at conftest load time so imports in test modules work
_install_stubs()


@pytest.fixture(autouse=True)
def _clean_sys_modules():
    """Save and restore sys.modules to avoid cross-test contamination."""
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
