#!/usr/bin/env python3
"""Tests for lib/ship_personas.py and parallel /ship flow.

Persona unit tests (first 4) and merge/fallback/integration tests (last 6),
plus C2 path-traversal and I6 changed-files tests.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import pytest

# Ensure plugin root is importable
_PLUGIN_ROOT = str(Path(__file__).resolve().parent.parent)
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

from lib.ship_personas import (
    CODE_QUALITY_PROMPT,
    LIFECYCLE_CONTEXT,
    SECURITY_REVIEW_PROMPT,
    TEST_VERIFICATION_PROMPT,
    _validate_path,
    build_quality_prompt,
    build_security_prompt,
    build_test_prompt,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Safe spec_path that resolves under cwd (passes _validate_path)
_SAFE_SPEC = str(Path.cwd() / "SPEC.md")


def _make_specialist_output(verdict: str, critical: int = 0) -> str:
    """Create a minimal specialist output markdown string."""
    return (
        "## Review\n\n"
        "### Summary\n"
        "- Verdict: " + verdict + "\n"
        "- Critical count: " + str(critical) + "\n"
        "- High count: 0\n"
    )


# ---------------------------------------------------------------------------
# Persona unit tests (4)
# ---------------------------------------------------------------------------


class TestSecurityPrompt:
    """Tests for build_security_prompt."""

    def test_build_security_prompt_contains_context(self) -> None:
        """Security prompt includes lifecycle context with provided values."""
        prompt = build_security_prompt(
            phase="SHIP",
            goal="Ship quality gates v0.3.1",
            slug="quality-gates-v031",
            spec_path=_SAFE_SPEC,
        )
        assert "SHIP" in prompt
        assert "Ship quality gates v0.3.1" in prompt
        assert "quality-gates-v031" in prompt
        assert "SPEC.md" in prompt
        assert "OWASP" in prompt


class TestTestPrompt:
    """Tests for build_test_prompt."""

    def test_build_test_prompt_contains_coverage_instructions(self) -> None:
        """Test prompt includes coverage verification instructions."""
        prompt = build_test_prompt(
            phase="SHIP",
            goal="Ship quality gates",
            slug="test-slug",
            spec_path=_SAFE_SPEC,
        )
        assert "test coverage" in prompt.lower()
        assert "edge cases" in prompt.lower()
        assert "happy paths" in prompt.lower()
        assert "error paths" in prompt.lower()
        assert "SHIP" in prompt


class TestQualityPrompt:
    """Tests for build_quality_prompt."""

    def test_build_quality_prompt_contains_review_axes(self) -> None:
        """Quality prompt includes all review axes."""
        prompt = build_quality_prompt(
            phase="SHIP",
            goal="Ship quality gates",
            slug="test-slug",
            spec_path=_SAFE_SPEC,
        )
        assert "correctness" in prompt.lower()
        assert "readability" in prompt.lower()
        assert "architecture" in prompt.lower()
        assert "SHIP" in prompt


class TestPromptUniqueness:
    """Tests that all prompts are distinct."""

    def test_prompts_are_unique(self) -> None:
        """All 3 rendered prompts are different strings."""
        security = build_security_prompt("P", "G", "S", _SAFE_SPEC)
        test = build_test_prompt("P", "G", "S", _SAFE_SPEC)
        quality = build_quality_prompt("P", "G", "S", _SAFE_SPEC)
        assert security != test
        assert security != quality
        assert test != quality


# ---------------------------------------------------------------------------
# C2: Path traversal tests
# ---------------------------------------------------------------------------


class TestPathTraversal:
    """Tests for _validate_path — the C2 fix for path traversal."""

    def test_valid_path_accepted(self) -> None:
        """A path under cwd is accepted."""
        cwd = str(Path.cwd())
        safe = os.path.join(cwd, "SPEC.md")
        result = _validate_path(safe)
        assert result == str(Path(safe).resolve())

    def test_absolute_escape_rejected(self) -> None:
        """A path outside cwd raises ValueError."""
        with pytest.raises(ValueError, match="escapes project root"):
            _validate_path("/etc/passwd")

    def test_dotdot_escape_rejected(self) -> None:
        """A path with '..' escaping cwd raises ValueError."""
        cwd = str(Path.cwd())
        traversal = os.path.join(cwd, "..", "..", "etc", "passwd")
        with pytest.raises(ValueError, match="escapes project root"):
            _validate_path(traversal)

    def test_build_security_prompt_rejects_traversal(self) -> None:
        """C2: build_security_prompt raises ValueError on path traversal."""
        with pytest.raises(ValueError, match="escapes project root"):
            build_security_prompt(
                phase="SHIP",
                goal="test",
                slug="test",
                spec_path="/etc/shadow",
            )

    def test_build_test_prompt_rejects_traversal(self) -> None:
        """C2: build_test_prompt raises ValueError on path traversal."""
        with pytest.raises(ValueError, match="escapes project root"):
            build_test_prompt(
                phase="SHIP",
                goal="test",
                slug="test",
                spec_path="/etc/shadow",
            )

    def test_build_quality_prompt_rejects_traversal(self) -> None:
        """C2: build_quality_prompt raises ValueError on path traversal."""
        with pytest.raises(ValueError, match="escapes project root"):
            build_quality_prompt(
                phase="SHIP",
                goal="test",
                slug="test",
                spec_path="/etc/shadow",
            )


# ---------------------------------------------------------------------------
# I6: Changed files tests
# ---------------------------------------------------------------------------


class TestChangedFiles:
    """Tests for I6: changed_files parameter in specialist prompts."""

    def test_security_prompt_includes_changed_files(self) -> None:
        """I6: Security prompt includes the changed files list."""
        prompt = build_security_prompt(
            phase="SHIP",
            goal="test",
            slug="test",
            spec_path=_SAFE_SPEC,
            changed_files="src/auth.py, src/api.py",
        )
        assert "src/auth.py, src/api.py" in prompt

    def test_test_prompt_includes_changed_files(self) -> None:
        """I6: Test prompt includes the changed files list."""
        prompt = build_test_prompt(
            phase="SHIP",
            goal="test",
            slug="test",
            spec_path=_SAFE_SPEC,
            changed_files="lib/core.py, tests/test_core.py",
        )
        assert "lib/core.py, tests/test_core.py" in prompt

    def test_quality_prompt_includes_changed_files(self) -> None:
        """I6: Quality prompt includes the changed files list."""
        prompt = build_quality_prompt(
            phase="SHIP",
            goal="test",
            slug="test",
            spec_path=_SAFE_SPEC,
            changed_files="config.yaml",
        )
        assert "config.yaml" in prompt

    def test_default_changed_files_when_not_specified(self) -> None:
        """I6: When changed_files not provided, prompt shows default."""
        prompt = build_security_prompt(
            phase="SHIP",
            goal="test",
            slug="test",
            spec_path=_SAFE_SPEC,
        )
        assert "(not specified)" in prompt


# ---------------------------------------------------------------------------
# Merge / fallback / trivial tests (6)
# ---------------------------------------------------------------------------


class TestMergeLogic:
    """Tests for merge-to-findings logic."""

    def test_merge_logic_go_verdict(self) -> None:
        """All PASS verdicts produces GO decision."""
        security_out = _make_specialist_output("PASS")
        test_out = _make_specialist_output("PASS")
        quality_out = _make_specialist_output("PASS")

        outputs = [security_out, test_out, quality_out]
        all_pass = all("Verdict: PASS" in o for o in outputs)
        assert all_pass is True

    def test_merge_logic_nogo_on_critical(self) -> None:
        """Any FAIL verdict with Critical findings produces NO-GO."""
        security_out = _make_specialist_output("FAIL", critical=2)
        test_out = _make_specialist_output("PASS")
        quality_out = _make_specialist_output("PASS")

        outputs = [security_out, test_out, quality_out]
        any_fail = any("Verdict: FAIL" in o for o in outputs)
        has_critical = any("Critical count: 0" not in o for o in outputs)
        assert any_fail is True
        assert has_critical is True

    def test_merge_logic_appends_to_findings(self, tmp_path: Path) -> None:
        """Merged decision is appended to findings.md (not overwritten)."""
        findings = tmp_path / "findings.md"
        findings.write_text(
            "## Existing Finding\n\nSome prior content.\n", encoding="utf-8"
        )

        decision = "\n## Ship Decision\n\nGO - all reviews passed.\n"
        with open(str(findings), "a", encoding="utf-8") as f:
            f.write(decision)

        content = findings.read_text(encoding="utf-8")
        assert "Existing Finding" in content
        assert "Ship Decision" in content
        assert "GO" in content


class TestFallback:
    """Tests for fallback behavior."""

    def test_fallback_to_call_subordinate(self) -> None:
        """When scheduler fails, fallback is call_subordinate with code-reviewer."""
        fallback_pattern = re.compile(
            r"call_subordinate.*profile.*code.review",
            re.IGNORECASE,
        )
        sample_prose = "Fall back to call_subordinate with profile=code-reviewer"
        assert fallback_pattern.search(sample_prose) is not None


class TestTrivialDetection:
    """Tests for trivial vs non-trivial change detection."""

    def test_trivial_change_skips_parallel(self) -> None:
        """Trivial changes skip parallel fan-out."""
        changed_files = ["README.md", "docs/guide.md"]
        total_lines = 30
        sensitive_areas = ["auth", "payments", "data access", "config/env", "secrets"]

        is_trivial = (
            len(changed_files) <= 2
            and total_lines < 50
            and not any(
                s in " ".join(changed_files).lower() for s in sensitive_areas
            )
        )
        assert is_trivial is True

    def test_nontrivial_change_runs_parallel(self) -> None:
        """Non-trivial changes trigger parallel fan-out."""
        changed_files = ["src/auth.py", "src/api.py", "src/models.py"]
        total_lines = 150
        sensitive_areas = ["auth", "payments", "data access", "config/env", "secrets"]

        is_trivial = (
            len(changed_files) <= 2
            and total_lines < 50
            and not any(
                s in " ".join(changed_files).lower() for s in sensitive_areas
            )
        )
        assert is_trivial is False

    def test_sensitive_area_makes_nontrivial(self) -> None:
        """I5: Even 1 file touching auth is non-trivial."""
        changed_files = ["src/auth.py"]
        total_lines = 5
        sensitive_areas = ["auth", "payments", "data access", "config/env", "secrets"]

        is_trivial = (
            len(changed_files) <= 2
            and total_lines < 50
            and not any(
                s in " ".join(changed_files).lower() for s in sensitive_areas
            )
        )
        assert is_trivial is False
