# test_lifecycle_tool.py - Task 1.3 TDD: Plan -> Lifecycle tool
# RED phase: This test SHOULD FAIL until tools/lifecycle.py is created

import sys, os, json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Block agent.py import to prevent langchain.embeddings.base failure (deprecated in langchain 0.3.x)
# Chain: helpers.tool -> agent -> models -> langchain.embeddings.base (broken)
import types as _types
_am = _types.ModuleType("agent")
_am.Agent = type("Agent", (), {})
_am.LoopData = type("LoopData", (), {})
_am.LoopData.__module__ = "agent"
_am.Agent.__module__ = "agent"
sys.modules["agent"] = _am

# Minimal mocks for Tool base class and Response
class MockResponse:
    def __init__(self, message="", break_loop=False):
        self.message = message
        self.break_loop = break_loop


def make_mock_agent(tmp_path):
    """Create a mock agent with context and project resolution."""
    agent = MagicMock()
    agent.context = MagicMock()
    agent.context.data = {}
    # Mock project resolution to use tmp_path
    agent.context.chat_id = "test"
    return agent


def make_mock_tool(agent, method, args=None):
    """Create a Lifecycle instance with mocked agent."""
    from tools.lifecycle import Lifecycle
    tool = Lifecycle.__new__(Lifecycle)
    tool.method = method
    tool.args = args or {}
    tool.agent = agent
    return tool


class TestLifecycleClass:
    """Test that Lifecycle class exists with correct interface."""

    def test_import_lifecycle(self):
        from tools.lifecycle import Lifecycle
        assert Lifecycle is not None

    def test_no_plan_class(self):
        import tools.lifecycle as mod
        assert not hasattr(mod, "Plan"), "Plan class should not exist"

    def test_only_three_valid_methods(self):
        import tools.lifecycle as mod
        expected = {"init", "status", "archive"}
        assert set(mod.VALID_METHODS) == expected

    def test_removed_methods_not_present(self):
        import tools.lifecycle as mod
        Lifecycle = mod.Lifecycle
        removed = ["phase_start", "phase_complete", "extend",
                   "log_finding", "log_progress", "log_error", "migrate"]
        for method_name in removed:
            assert not hasattr(Lifecycle, f"_{method_name}"),                 f"Removed method _{method_name} should not exist"


class TestInitMethod:
    """Test _init hardcodes 7 phases, no phases/template param."""

    def test_init_creates_lifecycle(self, tmp_path):
        from tools.lifecycle import Lifecycle
        agent = make_mock_agent(tmp_path)
        # Mock _resolve_lifecycle_dir to use tmp_path
        Lifecycle._resolve_lifecycle_dir = lambda self: tmp_path / "lifecycle"
        tool = make_mock_tool(agent, "init", {
            "goal": "A goal that is at least twenty characters long",
            "slug": "test-lifecycle",
        })
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(tool._init())
        assert result.message is not None
        # Check state was cached
        from lib.constants import CONTEXT_KEY_LIFECYCLE_STATE
        assert CONTEXT_KEY_LIFECYCLE_STATE in agent.context.data

    def test_init_hardcodes_seven_phases(self, tmp_path):
        from tools.lifecycle import Lifecycle
        agent = make_mock_agent(tmp_path)
        Lifecycle._resolve_lifecycle_dir = lambda self: tmp_path / "lifecycle"
        tool = make_mock_tool(agent, "init", {
            "goal": "A goal that is at least twenty characters long",
            "slug": "seven-phases",
        })
        import asyncio
        asyncio.get_event_loop().run_until_complete(tool._init())
        state = agent.context.data["lifecycle_state"]
        expected_phases = ["IDEA", "SPEC", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP"]
        assert len(state.phases) == 7
        actual_titles = [p.title for p in state.phases]
        assert actual_titles == expected_phases

    def test_init_no_phases_param(self, tmp_path):
        """_init should ignore any phases param - always hardcodes 7."""
        from tools.lifecycle import Lifecycle
        agent = make_mock_agent(tmp_path)
        Lifecycle._resolve_lifecycle_dir = lambda self: tmp_path / "lifecycle2"
        tool = make_mock_tool(agent, "init", {
            "goal": "A goal that is at least twenty characters long",
            "slug": "ignore-phases",
            "phases": ["only", "two"],  # should be ignored
        })
        import asyncio
        asyncio.get_event_loop().run_until_complete(tool._init())
        state = agent.context.data["lifecycle_state"]
        assert len(state.phases) == 7  # hardcoded, not 2


class TestStatusMethod:
    """Test _status shows lifecycle state."""

    def test_status_no_lifecycle(self, tmp_path):
        from tools.lifecycle import Lifecycle
        agent = make_mock_agent(tmp_path)
        Lifecycle._resolve_lifecycle_dir = lambda self: tmp_path / "empty"
        tool = make_mock_tool(agent, "status", {})
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(tool._status())
        assert "No active lifecycle" in result.message or "No active" in result.message

    def test_status_with_lifecycle(self, tmp_path):
        from tools.lifecycle import Lifecycle
        agent = make_mock_agent(tmp_path)
        lc_dir = tmp_path / "lifecycle"
        Lifecycle._resolve_lifecycle_dir = lambda self: lc_dir
        # Create a lifecycle first
        tool_init = make_mock_tool(agent, "init", {
            "goal": "A goal that is at least twenty characters long",
            "slug": "status-test",
        })
        import asyncio
        asyncio.get_event_loop().run_until_complete(tool_init._init())
        # Now check status
        tool_status = make_mock_tool(agent, "status", {})
        result = asyncio.get_event_loop().run_until_complete(tool_status._status())
        assert "status-test" in result.message or "Goal" in result.message


class TestArchiveMethod:
    """Test _archive archives lifecycle."""

    def test_archive_completed(self, tmp_path):
        from tools.lifecycle import Lifecycle
        agent = make_mock_agent(tmp_path)
        project_root = tmp_path / "project"
        project_root.mkdir()
        lc_dir = project_root / ".a0proj" / "run" / "current"
        Lifecycle._resolve_lifecycle_dir = lambda self: lc_dir
        Lifecycle._resolve_project_root = lambda self: project_root
        # Init
        tool_init = make_mock_tool(agent, "init", {
            "goal": "A goal that is at least twenty characters long",
            "slug": "archive-test",
        })
        import asyncio
        asyncio.get_event_loop().run_until_complete(tool_init._init())
        # Archive
        tool_archive = make_mock_tool(agent, "archive", {
            "promote_adrs": True,
        })
        result = asyncio.get_event_loop().run_until_complete(tool_archive._archive())
        assert "archived" in result.message.lower() or "complete" in result.message.lower()


class TestExecuteDispatch:
    """Test execute() dispatches to correct method."""

    def test_execute_dispatches_init(self, tmp_path):
        from tools.lifecycle import Lifecycle
        agent = make_mock_agent(tmp_path)
        Lifecycle._resolve_lifecycle_dir = lambda self: tmp_path / "lifecycle"
        tool = make_mock_tool(agent, "init", {
            "goal": "A goal that is at least twenty characters long",
            "slug": "dispatch-test",
        })
        import asyncio
        result = asyncio.get_event_loop().run_until_complete(tool.execute())
        assert result is not None

    def test_execute_rejects_unknown_method(self, tmp_path):
        from tools.lifecycle import Lifecycle
        agent = make_mock_agent(tmp_path)
        tool = make_mock_tool(agent, "unknown_method", {})
        import asyncio
        try:
            asyncio.get_event_loop().run_until_complete(tool.execute())
            assert False, "Should have raised"
        except Exception as e:
            assert "Unknown" in str(e) or "unknown" in str(e).lower()


class TestToolRegistrationGuard:
    """Regression guard: Lifecycle MUST inherit from Tool for A0 discovery.

    v0.3.0 post-launch bug: lifecycle.py had class Lifecycle: (plain class)
    instead of class Lifecycle(Tool):. A0 tool discovery uses
    issubclass(cls, Tool) in modules.load_classes_from_folder, which
    silently skips plain classes. This test prevents recurrence.
    """

    def test_lifecycle_inherits_from_tool_base(self):
        """Lifecycle class must inherit from Agent Zero Tool base class."""
        from helpers.tool import Tool
        from tools.lifecycle import Lifecycle

        assert issubclass(Lifecycle, Tool), (
            "Lifecycle must inherit from Tool for A0 registration. "
            "Without this, load_classes_from_folder/load_classes_from_file "
            "silently skips it. Ref: v0.3.0 post-launch bug."
        )

    def test_lifecycle_has_execute_method(self):
        """Lifecycle must implement the execute method required by Tool."""
        from helpers.tool import Tool
        from tools.lifecycle import Lifecycle

        instance = Lifecycle.__new__(Lifecycle)
        assert hasattr(instance, "execute"), (
            "Lifecycle must have execute method for A0 tool dispatch."
        )
        assert callable(getattr(instance, "execute")), (
            "Lifecycle.execute must be callable."
        )

    def test_lifecycle_has_tool_init_signature(self):
        """Lifecycle must accept Tool.__init__ signature: (agent, name, method, args, message, loop_data)."""
        from unittest.mock import MagicMock
        from tools.lifecycle import Lifecycle

        agent = MagicMock()
        tool = Lifecycle(
            agent=agent,
            name="lifecycle",
            method="status",
            args={},
            message="",
            loop_data=None,
        )
        assert tool.agent is agent
        assert tool.name == "lifecycle"
        assert tool.method == "status"
        assert tool.args == {}

class TestEmitSpec:
    """Test emit_spec support in _archive method."""

    def _setup_lifecycle(self, tmp_path):
        """Helper: init a lifecycle, complete all phases, return (agent, project_root, lc_dir)."""
        from tools.lifecycle import Lifecycle
        import asyncio

        agent = make_mock_agent(tmp_path)
        project_root = tmp_path / "project"
        project_root.mkdir()
        lc_dir = project_root / ".a0proj" / "run" / "current"

        Lifecycle._resolve_lifecycle_dir = lambda self: lc_dir
        Lifecycle._resolve_project_root = lambda self: project_root

        # Init
        tool_init = make_mock_tool(agent, "init", {
            "goal": "A goal that is at least twenty characters long",
            "slug": "emit-spec-test",
        })
        asyncio.get_event_loop().run_until_complete(tool_init._init())

        # Complete all phases
        state = agent.context.data["lifecycle_state"]
        for phase in state.phases:
            phase.status = "completed"
        state.persist()

        return agent, project_root, lc_dir

    def test_emit_spec_creates_spec_md(self, tmp_path):
        """lifecycle:archive emit_spec=true creates SPEC.md at project root."""
        import asyncio
        from tools.lifecycle import Lifecycle

        agent, project_root, lc_dir = self._setup_lifecycle(tmp_path)

        # Write some findings
        findings_path = lc_dir / "findings.md"
        findings_path.parent.mkdir(parents=True, exist_ok=True)
        findings_path.write_text("Finding one is here\nFinding two is here", encoding="utf-8")

        # Archive with emit_spec=true
        tool_archive = make_mock_tool(agent, "archive", {
            "emit_spec": True,
            "promote_adrs": False,
        })
        result = asyncio.get_event_loop().run_until_complete(tool_archive._archive())

        spec_path = project_root / "SPEC.md"
        assert spec_path.exists(), "SPEC.md should be created at project root"
        content = spec_path.read_text(encoding="utf-8")
        assert "A goal that is at least twenty characters long" in content
        assert "Completed Phases" in content
        assert "7/7 phases completed" in content
        assert "Finding one is here" in content
        assert "SPEC.md written" in result.message

    def test_emit_spec_false_no_file(self, tmp_path):
        """lifecycle:archive emit_spec=false does NOT create SPEC.md."""
        import asyncio
        from tools.lifecycle import Lifecycle

        agent, project_root, lc_dir = self._setup_lifecycle(tmp_path)

        # Archive with emit_spec=false
        tool_archive = make_mock_tool(agent, "archive", {
            "emit_spec": False,
            "promote_adrs": False,
        })
        result = asyncio.get_event_loop().run_until_complete(tool_archive._archive())

        spec_path = project_root / "SPEC.md"
        assert not spec_path.exists(), "SPEC.md should NOT be created when emit_spec=false"

    def test_emit_spec_default_no_file(self, tmp_path):
        """lifecycle:archive without emit_spec does NOT create SPEC.md."""
        import asyncio
        from tools.lifecycle import Lifecycle

        agent, project_root, lc_dir = self._setup_lifecycle(tmp_path)

        # Archive without emit_spec
        tool_archive = make_mock_tool(agent, "archive", {
            "promote_adrs": False,
        })
        result = asyncio.get_event_loop().run_until_complete(tool_archive._archive())

        spec_path = project_root / "SPEC.md"
        assert not spec_path.exists(), "SPEC.md should NOT be created by default"
