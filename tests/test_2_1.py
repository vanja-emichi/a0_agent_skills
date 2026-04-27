# test_2_1.py - Task 2.1 TDD: PlanExtension shadowing fix + Tasks 2.2-2.8 rename verification

import sys, os, py_compile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


EXPECTED_EXTENSIONS = [
    "extensions/python/system_prompt/_22_lifecycle_rules.py",
    "extensions/python/monologue_start/_30_lifecycle_resume.py",
    "extensions/python/monologue_end/_30_lifecycle_verifier.py",
    "extensions/python/message_loop_prompts_after/_10_lifecycle_inject.py",
    "extensions/python/tool_execute_before/_31_lifecycle_gate.py",
    "extensions/python/tool_execute_before/_30_no_lifecycle_gate.py",
    "extensions/python/tool_execute_after/_30_lifecycle_auto_progress.py",
]

# Old filenames that should NOT exist
OLD_EXTENSIONS = [
    "extensions/python/system_prompt/_22_planning_rules.py",
    "extensions/python/monologue_start/_30_plan_resume.py",
    "extensions/python/monologue_end/_30_phase_verifier.py",
    "extensions/python/message_loop_prompts_after/_72_include_plan.py",
    "extensions/python/tool_execute_before/_31_response_gate.py",
    "extensions/python/tool_execute_before/_30_no_plan_gate.py",
    "extensions/python/tool_execute_after/_30_plan_auto_progress.py",
]


class TestNoShadowing:
    """Verify no module-level PlanExtension alias in any extension."""

    def test_no_plan_extension_alias(self):
        base = os.path.join(os.path.dirname(__file__), "..", "extensions", "python")
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                content = open(path).read()
                assert "PlanExtension = " not in content, f"Found PlanExtension alias in {path}"

    def test_lifecycle_extension_used(self):
        """Extensions that need base class should use _EB.LifecycleExtension."""
        base = os.path.join(os.path.dirname(__file__), "..", "extensions", "python")
        found = []
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                content = open(path).read()
                if "LifecycleExtension" in content:
                    found.append(os.path.relpath(path, base))
        assert len(found) >= 7, f"Expected 7+ extensions using LifecycleExtension, found {len(found)}: {found}"

    def test_no_stale_plan_refs(self):
        """Extensions should not reference old plan names."""
        base = os.path.join(os.path.dirname(__file__), "..", "extensions", "python")
        stale_patterns = [
            "_load_plan(", "_resolve_plan_dir",
            "plan_strike_blocked", "plan_nudges", "plan_gate_warnings",
            "plan_actions_since_finding", "plan_resume_shown",
            "no-plan-gate", "plan-resume", "plan:phase_complete",
        ]
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                content = open(path).read()
                for pattern in stale_patterns:
                    assert pattern not in content, f"Found stale '{pattern}' in {path}"

    def test_no_debug_prints(self):
        """No PLAN-DEBUG print statements in extensions."""
        base = os.path.join(os.path.dirname(__file__), "..", "extensions", "python")
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d != "__pycache__"]
            for f in files:
                if not f.endswith(".py"):
                    continue
                path = os.path.join(root, f)
                content = open(path).read()
                assert "[PLAN-DEBUG" not in content, f"Found debug print in {path}"

    def test_all_extensions_compile(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        for f in EXPECTED_EXTENSIONS:
            py_compile.compile(os.path.join(base, f), doraise=True)

    def test_old_filenames_removed(self):
        """Old extension filenames should not exist."""
        base = os.path.join(os.path.dirname(__file__), "..")
        for old in OLD_EXTENSIONS:
            path = os.path.join(base, old)
            assert not os.path.exists(path), f"Old file still exists: {old}"

    def test_new_filenames_exist(self):
        """New extension filenames should exist."""
        base = os.path.join(os.path.dirname(__file__), "..")
        for new in EXPECTED_EXTENSIONS:
            path = os.path.join(base, new)
            assert os.path.exists(path), f"New file missing: {new}"


class TestStrikeTrackerExtension:
    """Task 2.9: Strike tracker extension exists and compiles."""

    STRIKE_TRACKER = "extensions/python/_functions/agent/Agent/handle_exception/end/_55_lifecycle_strike_tracker.py"

    def test_strike_tracker_file_exists(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        path = os.path.join(base, self.STRIKE_TRACKER)
        assert os.path.exists(path), f"Strike tracker not found at {path}"

    def test_strike_tracker_compiles(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        py_compile.compile(os.path.join(base, self.STRIKE_TRACKER), doraise=True)

    def test_strike_tracker_has_lifecycle_extension(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        content = open(os.path.join(base, self.STRIKE_TRACKER)).read()
        assert "LifecycleExtension" in content, "Strike tracker should use LifecycleExtension"
        assert "LifecycleStrikeTracker" in content, "Should define LifecycleStrikeTracker class"

    def test_strike_tracker_records_strikes(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        content = open(os.path.join(base, self.STRIKE_TRACKER)).read()
        assert "tracker.record" in content, "Should record strikes"
        assert "tracker.persist" in content, "Should persist strikes"
        assert "lifecycle_strike_blocked" in content, "Should set blocked flag"

    def test_strike_tracker_uses_strike_tracker_lib(self):
        base = os.path.join(os.path.dirname(__file__), "..")
        content = open(os.path.join(base, self.STRIKE_TRACKER)).read()
        assert ("from lib.strike_tracker import StrikeTracker" in content or "get_strike_tracker_module" in content), "Should import StrikeTracker directly or via import_utils"
        assert "StrikeTracker" in content, "Should use StrikeTracker class"
