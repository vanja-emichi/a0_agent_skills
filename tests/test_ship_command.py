"""Tests for the /ship command (commands/ship.py)."""

import importlib
import os
import sys

import pytest


PLUGIN_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
COMMANDS_DIR = os.path.join(PLUGIN_DIR, "commands")


def _import_ship():
    """Import ship.py from the plugin commands directory."""
    sys.path.insert(0, COMMANDS_DIR)
    try:
        return importlib.import_module("ship")
    finally:
        if COMMANDS_DIR in sys.path:
            sys.path.remove(COMMANDS_DIR)


class TestShipRun:
    """Verify ship.run() output structure and content."""

    def test_returns_nonempty_string(self):
        ship = _import_ship()
        result = ship.run({})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_has_phase_headers(self):
        ship = _import_ship()
        result = ship.run({})
        assert "## Phase A" in result
        assert "## Phase B" in result
        assert "## Phase C" in result

    def test_handles_missing_invocation_gracefully(self):
        ship = _import_ship()
        # Empty payload — no invocation key at all
        result = ship.run({})
        assert isinstance(result, str)
        assert "staged changes or recent commits" in result

    def test_contains_call_subordinate_for_all_profiles(self):
        ship = _import_ship()
        result = ship.run({})
        for profile in ("code-reviewer", "security-auditor", "test-engineer"):
            assert profile in result, f"Missing profile reference: {profile}"


class TestShipSanitization:
    """Verify raw_arguments are sanitized (Fix 8)."""

    def test_long_input_truncated(self):
        ship = _import_ship()
        long_arg = "x" * 300
        result = ship.run({"invocation": {"raw_arguments": long_arg}})
        # Should not contain the full 300-char string
        assert "x" * 300 not in result

    def test_newlines_stripped(self):
        ship = _import_ship()
        result = ship.run({"invocation": {"raw_arguments": "line1\nline2\nline3"}})
        assert "line1\nline2" not in result
        # Newlines should be replaced with spaces
        assert "line1 line2 line3" in result

    def test_markdown_heading_stripped(self):
        """Leading # characters are stripped to prevent markdown heading injection."""
        ship = _import_ship()
        result = ship.run({"invocation": {"raw_arguments": "## InjectTest"}})
        assert "## InjectTest" not in result
        assert "InjectTest" in result

    def test_multiple_hash_prefixes_stripped(self):
        """Multiple leading # characters are all stripped."""
        ship = _import_ship()
        result = ship.run({"invocation": {"raw_arguments": "### DeepHeading"}})
        assert "### DeepHeading" not in result
        assert "DeepHeading" in result


class TestShipCustomTarget:
    """Verify custom target from raw_arguments appears in output."""

    def test_custom_target_appears_in_output(self):
        ship = _import_ship()
        result = ship.run({"invocation": {"raw_arguments": "src/main.py"}})
        assert "src/main.py" in result


class TestShipPhaseBSynthesis:
    """Verify Phase B contains expected synthesis categories and Phase C has GO/NO-GO."""

    EXPECTED_CATEGORIES = [
        "Code Quality",
        "Security",
        "Performance",
        "Accessibility",
        "Infrastructure",
        "Documentation",
    ]

    def test_phase_b_has_synthesis_categories(self):
        ship = _import_ship()
        result = ship.run({})
        for cat in self.EXPECTED_CATEGORIES:
            assert cat in result, f"Phase B missing category: {cat}"

    def test_phase_c_has_go_nogo_decision_template(self):
        ship = _import_ship()
        result = ship.run({})
        assert "GO | NO-GO" in result
        assert "Blockers" in result
        assert "Rollback plan" in result
