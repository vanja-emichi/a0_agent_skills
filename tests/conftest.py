# Shared test fixtures for agent-skills tests.
"""Common fixtures for importing the routing extension with mocked A0 deps.

Extracted from test_clean_orchestrator.py and test_clean_orchestrator_edge_cases.py
to eliminate ~60 lines of duplication.

Plan fixtures (tmp_plan_dir, mock_agent, make_plan_tool, run_async)
centralized from test_plan_*.py to eliminate ~150 lines of duplication.
"""
from __future__ import annotations

import asyncio
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add A0 framework root to sys.path for imports like `from helpers.errors import ...`
_A0_ROOT = str(Path(__file__).resolve().parents[4])  # /a0/usr/projects/agent_skills/tests -> /a0
if _A0_ROOT not in sys.path:
    sys.path.insert(0, _A0_ROOT)

# Also ensure plugin root is importable (for `from lib.lifecycle_state import ...`)
_PLUGIN_ROOT = str(Path(__file__).resolve().parents[1])
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


REPO_ROOT = Path(__file__).resolve().parents[1]
EXT_PATH = (
    REPO_ROOT
    / "extensions"
    / "python"
    / "system_prompt"
    / "_20_agent_skills_prompt.py"
)
SKILLS_DIR = REPO_ROOT / "skills"
PROMPTS_DIR = REPO_ROOT / "prompts"
ML_DIR = REPO_ROOT / "extensions" / "python" / "message_loop_start"
COMMANDS_DIR = REPO_ROOT / "commands"

# Stale plan:* tool call patterns (renamed to lifecycle:*)
STALE_PLAN_PATTERNS = [
    "plan:init",
    "plan:status",
    "plan:archive",
    "plan:phase_start",
    "plan:phase_complete",
    "plan:log_finding",
    "plan:log_progress",
    "plan:log_error",
    "plan:extend",
    "plan:migrate",
]


@pytest.fixture()
def extension_module():
    """Import the routing extension module with mocked A0 deps."""
    saved = {}
    for mod_name in ["helpers", "helpers.extension", "helpers.print_style", "agent"]:
        saved[mod_name] = sys.modules.get(mod_name)

    class FakeExtension:
        def __init__(self, agent=None, **kwargs):
            self.agent = agent

    helpers_ext = MagicMock()
    helpers_ext.Extension = FakeExtension
    helpers_ps = MagicMock()
    helpers_ps.PrintStyle = MagicMock()

    sys.modules["helpers"] = MagicMock()
    sys.modules["helpers.extension"] = helpers_ext
    sys.modules["helpers.print_style"] = helpers_ps
    sys.modules["agent"] = MagicMock()

    spec = importlib.util.spec_from_file_location(
        "agent_skills_prompt", EXT_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    yield mod

    for mod_name, orig in saved.items():
        if orig is None:
            sys.modules.pop(mod_name, None)
        else:
            sys.modules[mod_name] = orig


@pytest.fixture()
def delegation_table(extension_module):
    """Get the compact delegation table."""
    return extension_module.get_delegation_table()


@pytest.fixture()
def extension_source():
    """Read the extension source code."""
    return EXT_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Plan test fixtures (centralized from test_plan_*.py)
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_plan_dir(tmp_path):
    """Create a plan directory under .a0proj/run/current/."""
    plan_dir = tmp_path / ".a0proj" / "run" / "current"
    plan_dir.mkdir(parents=True, exist_ok=True)
    return plan_dir


@pytest.fixture
def mock_agent(tmp_plan_dir):
    """Create a mock Agent with enough structure for Plan tool."""
    agent = MagicMock()
    agent.context = MagicMock()
    agent.context.data = {}
    agent.context.agent = agent
    agent.context.agent.config = MagicMock()
    return agent


@pytest.fixture
def make_plan_tool():
    """Factory fixture to create Plan tool instances."""
    from tools.plan import Plan
    def _make(agent, method, args):
        return Plan(
            agent=agent,
            name="plan",
            method=method,
            args=args,
            message="",
            loop_data=None,
        )
    return _make


@pytest.fixture
def run_async():
    """Run an async coroutine synchronously for testing."""
    return lambda coro: asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture
def include_plan():
    """Provide the IncludePlan extension class."""
    from extensions.python.message_loop_prompts_after._72_include_plan import IncludePlan
    return IncludePlan


@pytest.fixture
def make_loop_data():
    """Factory fixture to create LoopData-like objects for testing."""
    from unittest.mock import MagicMock
    def _make(**kwargs):
        loop_data = MagicMock()
        loop_data.extras_temporary = kwargs.pop("extras_temporary", {})
        loop_data.extras_persistent = kwargs.pop("extras_persistent", {})
        loop_data.iteration = kwargs.pop("iteration", 0)
        return loop_data
    return _make
