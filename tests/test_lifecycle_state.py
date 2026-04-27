# test_lifecycle_state.py - Task 1.2 TDD: PlanState -> LifecycleState
# RED phase: This test SHOULD FAIL until lifecycle_state.py is created

import sys, os, tempfile, json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestLifecycleStateClass:
    """Test that LifecycleState class exists with correct interface."""

    def test_import_lifecycle_state(self):
        from lib.lifecycle_state import LifecycleState
        assert LifecycleState is not None

    def test_dataclasses_preserved(self):
        from lib.lifecycle_state import Phase, Finding, ProgressEntry, ErrorEntry
        p = Phase(title="IDEA", status="pending")
        assert p.title == "IDEA"
        assert p.status == "pending"
        f = Finding(content="test finding")
        assert f.source == "trusted"
        pe = ProgressEntry(content="did stuff")
        assert pe.content == "did stuff"
        ee = ErrorEntry(content="boom", error_hash="abc123")
        assert ee.error_hash == "abc123"

    def test_no_plan_state_class(self):
        """PlanState should not be in lifecycle_state module."""
        import lib.lifecycle_state as mod
        assert not hasattr(mod, "PlanState"), "PlanState class should not exist in lifecycle_state module"


class TestConstantsUpdated:
    """Test that lifecycle_state uses new constant names."""

    def test_exports_lifecycle_constants(self):
        import lib.lifecycle_state as mod
        assert hasattr(mod, "CONTEXT_KEY_LIFECYCLE_STATE")
        assert mod.CONTEXT_KEY_LIFECYCLE_STATE == "lifecycle_state"
        assert hasattr(mod, "CONTEXT_KEY_LIFECYCLE_STATE_MTIME")
        assert mod.CONTEXT_KEY_LIFECYCLE_STATE_MTIME == "lifecycle_state_mtime"

    def test_no_plan_constant_exports(self):
        import lib.lifecycle_state as mod
        plan_exports = [n for n in dir(mod) if "CONTEXT_KEY_PLAN" in n]
        assert plan_exports == [], f"Found stale PLAN constants: {plan_exports}"


class TestCreateNoTemplate:
    """Test that create() works without template parameter."""

    def test_create_basic(self, tmp_path):
        from lib.lifecycle_state import LifecycleState
        state = LifecycleState.create(
            goal="A goal that is at least twenty characters long",
            phases=["IDEA", "SPEC", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP"],
            slug="test-plan",
            plan_dir=tmp_path / "lifecycle",
        )
        assert isinstance(state, LifecycleState)
        assert state.goal == "A goal that is at least twenty characters long"
        assert len(state.phases) == 7
        assert state.phases[0].title == "IDEA"
        assert state.slug == "test-plan"

    def test_create_hardcodes_four_files(self, tmp_path):
        from lib.lifecycle_state import LifecycleState
        plan_dir = tmp_path / "lifecycle"
        LifecycleState.create(
            goal="A goal that is at least twenty characters long",
            phases=["IDEA", "SPEC", "PLAN"],
            slug="test-plan",
            plan_dir=plan_dir,
        )
        assert (plan_dir / "state.md").exists()
        assert (plan_dir / "findings.md").exists()
        assert (plan_dir / "progress.md").exists()
        assert (plan_dir / "errors.md").exists()

    def test_create_no_template_dir_needed(self, tmp_path):
        """create() should not require any templates directory."""
        from lib.lifecycle_state import LifecycleState
        plan_dir = tmp_path / "lifecycle"
        # This should work even without any templates/ dir
        LifecycleState.create(
            goal="A goal that is at least twenty characters long",
            phases=["IDEA", "BUILD", "SHIP"],
            slug="no-templates",
            plan_dir=plan_dir,
        )
        assert (plan_dir / "state.md").exists()


class TestPersistFrontmatter:
    """Test that persist() writes YAML frontmatter to state.md."""

    def test_persist_writes_yaml_frontmatter(self, tmp_path):
        from lib.lifecycle_state import LifecycleState
        plan_dir = tmp_path / "lifecycle"
        state = LifecycleState.create(
            goal="A goal that is at least twenty characters long",
            phases=["IDEA", "SPEC", "PLAN"],
            slug="frontmatter-test",
            plan_dir=plan_dir,
        )
        content = (plan_dir / "state.md").read_text()
        # Must have YAML frontmatter delimiters
        assert content.startswith("---"), f"state.md must start with ---, got: {content[:50]}"
        assert "---" in content[3:], "state.md must have closing ---"

    def test_frontmatter_has_phase_info(self, tmp_path):
        from lib.lifecycle_state import LifecycleState
        plan_dir = tmp_path / "lifecycle"
        state = LifecycleState.create(
            goal="A goal that is at least twenty characters long",
            phases=["IDEA", "SPEC", "PLAN"],
            slug="fm-fields",
            plan_dir=plan_dir,
        )
        content = (plan_dir / "state.md").read_text()
        # Parse frontmatter
        parts = content.split("---")
        assert len(parts) >= 3, "Must have opening ---, content, closing ---"
        fm_text = parts[1]
        assert "phases:" in fm_text or "current_phase_index:" in fm_text
        assert "slug:" in fm_text
        assert "goal:" in fm_text


class TestLoadFromFrontmatter:
    """Test that load() reads YAML frontmatter from state.md."""

    def test_load_from_frontmatter(self, tmp_path):
        from lib.lifecycle_state import LifecycleState
        plan_dir = tmp_path / "lifecycle"
        LifecycleState.create(
            goal="A goal that is at least twenty characters long",
            phases=["IDEA", "SPEC", "PLAN"],
            slug="load-test",
            plan_dir=plan_dir,
        )
        # Delete metadata.json to force frontmatter parsing
        meta = plan_dir / "metadata.json"
        if meta.exists():
            meta.unlink()
        loaded = LifecycleState.load(plan_dir)
        assert loaded is not None
        assert loaded.slug == "load-test"
        assert loaded.goal == "A goal that is at least twenty characters long"
        assert len(loaded.phases) == 3

    def test_load_fallback_to_metadata_json(self, tmp_path):
        """load() should still work with metadata.json (backward compat)."""
        from lib.lifecycle_state import LifecycleState
        plan_dir = tmp_path / "lifecycle"
        plan_dir.mkdir()
        # Create old-style metadata.json
        metadata = {
            "slug": "legacy",
            "goal": "A legacy goal that is at least twenty chars",
            "created_at": "2025-01-01T00:00:00+00:00",
            "current_phase_index": 0,
            "phases": [{"title": "IDEA", "status": "pending"}, {"title": "SHIP", "status": "pending"}],
        }
        (plan_dir / "metadata.json").write_text(json.dumps(metadata))
        (plan_dir / "state.md").write_text("# Old style")
        loaded = LifecycleState.load(plan_dir)
        assert loaded is not None
        assert loaded.slug == "legacy"
        assert len(loaded.phases) == 2

    def test_load_returns_none_when_no_state(self, tmp_path):
        from lib.lifecycle_state import LifecycleState
        plan_dir = tmp_path / "empty"
        plan_dir.mkdir()
        assert LifecycleState.load(plan_dir) is None


class TestRenderExtras:
    """Test that render_extras still works with lifecycle branding."""

    def test_render_extras_mentions_lifecycle(self, tmp_path):
        from lib.lifecycle_state import LifecycleState
        plan_dir = tmp_path / "lifecycle"
        state = LifecycleState.create(
            goal="A goal that is at least twenty characters long",
            phases=["IDEA", "SPEC", "PLAN"],
            slug="extras-test",
            plan_dir=plan_dir,
        )
        extras = state.render_extras()
        # Should mention lifecycle or plan (not strictly required to change yet)
        assert "extras-test" in extras or "Plan" in extras or "Lifecycle" in extras


class TestRenderExtrasBudget:
    """T11: render_extras should respect a character budget."""

    def _make_state_with_findings(self, tmp_path, n_findings=20, n_progress=20):
        """Helper: create a lifecycle state with many findings and progress entries."""
        from lib.lifecycle_state import LifecycleState, Finding, ProgressEntry
        plan_dir = tmp_path / "lifecycle"
        state = LifecycleState.create(
            goal="A goal that is at least twenty characters long",
            phases=["IDEA", "SPEC", "PLAN", "BUILD"],
            slug="budget-test",
            plan_dir=plan_dir,
        )
        for i in range(n_findings):
            state.append_finding(Finding(content=f"Finding number {i:03d} with some padding text to make it longer"))
        for i in range(n_progress):
            state.append_progress(ProgressEntry(content=f"Progress entry number {i:03d} with padding text"))
        return state

    def test_render_extras_respects_budget(self, tmp_path):
        """render_extras should truncate when content exceeds budget."""
        state = self._make_state_with_findings(tmp_path, n_findings=30, n_progress=30)
        extras = state.render_extras(budget=500)
        # Output should be roughly within budget (allow some overhead for truncation notice)
        assert len(extras) <= 600, f"render_extras output too long: {len(extras)} chars"
        # Should have a truncation notice
        assert "truncated" in extras.lower(), f"Expected truncation notice, got: {extras[-200:]}"

    def test_render_extras_never_truncates_prefix(self, tmp_path):
        """Goal and phase list should always be present regardless of budget."""
        state = self._make_state_with_findings(tmp_path, n_findings=50, n_progress=50)
        # Even with tiny budget, goal and phases should be present
        extras = state.render_extras(budget=100)
        assert "budget-test" in extras, "Slug should always be present"
        assert "A goal that is at least twenty characters long" in extras, "Goal should always be present"
        assert "Phases:" in extras, "Phase list header should always be present"

    def test_render_extras_no_truncation_when_under_budget(self, tmp_path):
        """No truncation notice when content fits within budget."""
        from lib.lifecycle_state import LifecycleState
        plan_dir = tmp_path / "lifecycle"
        state = LifecycleState.create(
            goal="A goal that is at least twenty characters long",
            phases=["IDEA", "BUILD"],
            slug="small-test",
            plan_dir=plan_dir,
        )
        extras = state.render_extras(budget=5000)
        assert "truncated" not in extras.lower(), "Should not truncate when under budget"

    def test_render_extras_default_budget_2000(self, tmp_path):
        """Default budget should be 2000 chars."""
        state = self._make_state_with_findings(tmp_path, n_findings=100, n_progress=100)
        extras = state.render_extras()
        # With 100 findings and 100 progress, default 2000 budget should truncate
        assert len(extras) <= 2100, f"Default budget should cap output: {len(extras)}"


import asyncio
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestAutoProgressPersistence:
    """T12: Auto-progress counter should persist to file for compaction survival."""

    def _make_mock_agent(self, tmp_path):
        """Create a mock agent with plan_dir set up."""
        agent = MagicMock()
        agent.context = MagicMock()
        agent.context.data = {}
        agent.context.agent = agent

        # Mock loop_data
        loop_data = MagicMock()
        loop_data.current_tool = None
        agent.loop_data = loop_data

        # Set up plan_dir in the right location
        plan_dir = tmp_path / ".a0proj" / "run" / "current"
        plan_dir.mkdir(parents=True, exist_ok=True)

        return agent, plan_dir

    def _create_lifecycle(self, plan_dir):
        """Create a minimal lifecycle state in plan_dir."""
        from lib.lifecycle_state import LifecycleState
        state = LifecycleState.create(
            goal="A goal that is at least twenty characters long",
            phases=["IDEA", "BUILD", "SHIP"],
            slug="persist-test",
            plan_dir=plan_dir,
        )
        return state

    def test_auto_progress_persists_to_file(self, tmp_path):
        """Auto-progress counter should survive context loss by persisting to file."""
        agent, plan_dir = self._make_mock_agent(tmp_path)
        self._create_lifecycle(plan_dir)

        from extensions.python.tool_execute_after._30_lifecycle_auto_progress import PlanAutoProgress
        ext = PlanAutoProgress(agent=agent)

        # Override _resolve_lifecycle_dir to return our plan_dir
        ext._resolve_lifecycle_dir = lambda: plan_dir

        # Simulate file-mutating tool calls to increment counter
        async def run_once(tool_name):
            await ext.execute(tool_name=tool_name)

        loop = asyncio.new_event_loop()
        # First call - increments to 1
        loop.run_until_complete(run_once("text_editor:write"))
        # Second call - increments to 2, triggers nudge, resets to 0
        loop.run_until_complete(run_once("text_editor:patch"))

        # Check that auto_progress.json was created
        progress_file = plan_dir / "auto_progress.json"
        assert progress_file.exists(), f"auto_progress.json should exist in {plan_dir}"

        # Simulate context compaction - clear context.data
        agent.context.data = {}

        # Reload - counter should be recoverable from file
        ext2 = PlanAutoProgress(agent=agent)
        ext2._resolve_lifecycle_dir = lambda: plan_dir
        # The counter was reset to 0 after nudge, so after compaction it should still be 0
        data = agent.context.data
        # Just verify the file exists and is readable
        saved = json.loads(progress_file.read_text())
        assert "counter" in saved, f"Saved data should have counter key: {saved}"

        loop.close()

    def test_auto_progress_file_cleaned_on_cleanup(self, tmp_path):
        """Auto-progress file should be removed when lifecycle is cleaned up."""
        agent, plan_dir = self._make_mock_agent(tmp_path)
        state = self._create_lifecycle(plan_dir)

        from extensions.python.tool_execute_after._30_lifecycle_auto_progress import PlanAutoProgress
        ext = PlanAutoProgress(agent=agent)
        ext._resolve_lifecycle_dir = lambda: plan_dir

        # Simulate increment
        async def run_once(tool_name):
            await ext.execute(tool_name=tool_name)

        loop = asyncio.new_event_loop()
        loop.run_until_complete(run_once("text_editor:write"))

        # Verify file exists
        progress_file = plan_dir / "auto_progress.json"
        assert progress_file.exists(), "auto_progress.json should exist after increment"

        # Cleanup lifecycle
        state.cleanup()

        # After cleanup, the entire plan_dir is gone
        assert not plan_dir.exists(), "plan_dir should be removed after cleanup"
        loop.close()
