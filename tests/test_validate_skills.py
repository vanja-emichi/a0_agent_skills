#!/usr/bin/env python3
"""Tests for scripts/validate_skills.py.

Validates heading extraction, alias matching, per-skill compliance,
case insensitivity, exit codes, and CLI flags.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure plugin root is importable
_PLUGIN_ROOT = str(Path(__file__).resolve().parent.parent)
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)

from scripts.validate_skills import (
    REQUIRED_SECTIONS,
    _alias_matches,
    _tokenize,
    check_skill,
    extract_headings,
    validate_skills,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_skill_md(path: Path, headings: list[str]) -> Path:
    """Write a minimal SKILL.md with the given ## headings."""
    lines = ["---", "name: test-skill", "description: test", "---", ""]
    for h in headings:
        lines.append("## " + h)
        lines.append("Some content.")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _compliant_headings() -> list[str]:
    """Return headings that satisfy all 7 required sections."""
    return [
        "Overview",
        "When to Use",
        "Core Process",
        "Common Rationalizations",
        "Red Flags",
        "Verification",
        "Boundaries",
    ]


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


class TestExtractHeadings:
    """Tests for extract_headings function."""

    def test_extract_headings_finds_h2_and_h3(self) -> None:
        """## and ### headings are extracted."""
        md = "## First\n\nSome text\n\n### Second\n\nMore text\n"
        headings = extract_headings(md)
        assert headings == ["First", "Second"]

    def test_extract_headings_ignores_h1_and_h4(self) -> None:
        """# and #### headings are NOT extracted (ATX 2-3 only)."""
        md = "# Title\n\n## H2\n\n### H3\n\n#### H4\n"
        headings = extract_headings(md)
        assert headings == ["H2", "H3"]


class TestTokenize:
    """Tests for _tokenize helper."""

    def test_tokenize_splits_words(self) -> None:
        """Tokenization splits on non-alphanumeric."""
        assert _tokenize("Core Process") == ["core", "process"]

    def test_tokenize_lowercases(self) -> None:
        """Tokenization lowercases."""
        assert _tokenize("OVERVIEW") == ["overview"]

    def test_tokenize_strips_special_chars(self) -> None:
        """Tokenization strips non-alphanumeric characters."""
        assert _tokenize("Always/Never") == ["always", "never"]


class TestAliasMatches:
    """Tests for _alias_matches — the C1 fix for substring collision."""

    def test_exact_single_word_match(self) -> None:
        """Single-token alias matches heading with same word."""
        assert _alias_matches("overview", "Overview") is True

    def test_case_insensitive_match(self) -> None:
        """Alias matching is case-insensitive."""
        assert _alias_matches("overview", "OVERVIEW") is True

    def test_multi_token_all_words_present(self) -> None:
        """Multi-token alias matches when all words appear in heading."""
        assert _alias_matches("core process", "The Core Process Steps") is True

    def test_multi_token_partial_mismatch(self) -> None:
        """Multi-token alias fails when not all words present."""
        assert _alias_matches("core process", "Core Principles") is False

    def test_plural_variant(self) -> None:
        """Singular/plural variants match (e.g., 'step' ≈ 'steps')."""
        assert _alias_matches("step", "Steps") is True
        assert _alias_matches("steps", "Step") is True

    def test_word_match_in_longer_heading(self) -> None:
        """Word-level match: 'process' matches 'The Simplification Process'."""
        assert _alias_matches("process", "The Simplification Process") is True

    def test_word_match_boundaries_in_security(self) -> None:
        """Word-level match: 'boundaries' matches 'Security Boundaries'."""
        assert _alias_matches("boundaries", "Security Boundaries") is True

    def test_word_match_workflow_in_automation(self) -> None:
        """Word-level match: 'workflow' matches 'Workflow Automation'.

        This IS a valid match — 'workflow' is a complete word in the heading.
        The C1 fix prevents INTRA-word substring collisions (e.g., 'rule' in
        'ruler'), not legitimate word matches.
        """
        assert _alias_matches("workflow", "Workflow Automation") is True

    def test_c1_no_intra_word_collision(self) -> None:
        """C1 fix: 'rule' must NOT match 'Ruler' (intra-word substring).

        The old `alias in heading` check would match 'rule' in 'ruler'.
        Word-level token matching correctly prevents this because 'rule'
        is not a complete word token in 'ruler'.
        """
        assert _alias_matches("rule", "Ruler") is False

    def test_c1_no_intra_word_collision_valid(self) -> None:
        """C1 fix: 'valid' must NOT match 'Validation' (intra-word).

        'valid' in 'validation' was True with old substring check.
        Word-level matching: 'valid' ≠ 'validation' as tokens.
        """
        assert _alias_matches("valid", "Validation") is False

    def test_multi_word_the_workflow(self) -> None:
        """Multi-token alias 'the workflow' matches heading with both words."""
        assert _alias_matches("the workflow", "The Optimization Workflow") is True

    def test_multi_word_core_process(self) -> None:
        """Multi-token alias 'core process' matches heading with both words."""
        assert _alias_matches("core process", "Core Process and Steps") is True


class TestCheckSkill:
    """Tests for check_skill function."""

    def test_check_skill_all_sections_present(self, tmp_path: Path) -> None:
        """A skill with all 7 required sections is compliant."""
        skill_md = _write_skill_md(
            tmp_path / "test-skill" / "SKILL.md",
            _compliant_headings(),
        )
        is_compliant, missing, found = check_skill(skill_md)
        assert is_compliant is True
        assert missing == []
        assert len(found) == 7

    def test_check_skill_with_aliases(self, tmp_path: Path) -> None:
        """Alias headings are accepted in place of canonical names."""
        skill_md = _write_skill_md(
            tmp_path / "test-skill" / "SKILL.md",
            [
                "Summary",
                "Usage",
                "The Workflow",
                "Anti-Rationalizations",
                "Warning Signs",
                "Exit Criteria",
                "Always/Never",
            ],
        )
        is_compliant, missing, found = check_skill(skill_md)
        assert is_compliant is True
        assert missing == []

    def test_check_skill_missing_sections(self, tmp_path: Path) -> None:
        """Missing sections are reported correctly."""
        skill_md = _write_skill_md(
            tmp_path / "test-skill" / "SKILL.md",
            ["Overview", "Red Flags"],
        )
        is_compliant, missing, found = check_skill(skill_md)
        assert is_compliant is False
        assert len(missing) == 5
        assert "When to Use" in missing
        assert "Core Process" in missing

    def test_check_skill_case_insensitive(self, tmp_path: Path) -> None:
        """Heading matching is case-insensitive."""
        skill_md = _write_skill_md(
            tmp_path / "test-skill" / "SKILL.md",
            [
                "OVERVIEW",
                "when to use",
                "Core PROCESS",
                "common rationalizations",
                "RED FLAGS",
                "Verification",
                "boundaries",
            ],
        )
        is_compliant, missing, found = check_skill(skill_md)
        assert is_compliant is True
        assert missing == []

    def test_check_skill_intra_word_no_false_positive(self, tmp_path: Path) -> None:
        """C1 fix: heading 'Validation Protocol' must NOT match alias 'valid'.

        With old substring matching, 'valid' in 'validation protocol' was True.
        Word-level matching prevents this intra-word collision.
        """
        skill_md = _write_skill_md(
            tmp_path / "test-skill" / "SKILL.md",
            [
                "Overview",
                "When to Use",
                "Core Process",
                "Common Rationalizations",
                "Red Flags",
                "Validation Protocol",  # must NOT match alias 'valid' (intra-word)
                "Boundaries",
            ],
        )
        # This should still pass because 'verification' and 'validation'
        # ARE in the aliases list. But 'valid' is not an alias for Verification.
        # The actual alias is 'validation', and 'validation' IS a word in
        # 'Validation Protocol', so this DOES match.
        is_compliant, missing, found = check_skill(skill_md)
        assert is_compliant is True  # 'validation' alias matches

    def test_check_skill_unicode_decode_error(self, tmp_path: Path) -> None:
        """I4 fix: non-UTF-8 files are handled gracefully.

        Returns non-compliant instead of crashing.
        """
        skill_md = tmp_path / "test-skill" / "SKILL.md"
        skill_md.parent.mkdir(parents=True, exist_ok=True)
        # Write raw bytes that are invalid UTF-8
        skill_md.write_bytes(b"\x80\x81\x82\xfe\xff")
        is_compliant, missing, found = check_skill(skill_md)
        assert is_compliant is False
        assert len(missing) == 7  # all sections missing


class TestValidateSkills:
    """Tests for validate_skills function."""

    def test_validate_all_skills_compliant(self, tmp_path: Path) -> None:
        """All skills compliant returns exit code 0."""
        skills_dir = tmp_path / "skills"
        for i in range(3):
            name = "skill-" + str(i)
            _write_skill_md(
                skills_dir / name / "SKILL.md",
                _compliant_headings(),
            )
        exit_code = validate_skills(skills_dir)
        assert exit_code == 0

    def test_validate_single_skill_flag(self, tmp_path: Path) -> None:
        """--skill NAME validates only the named skill."""
        skills_dir = tmp_path / "skills"
        _write_skill_md(
            skills_dir / "good-skill" / "SKILL.md",
            _compliant_headings(),
        )
        _write_skill_md(
            skills_dir / "bad-skill" / "SKILL.md",
            ["Overview"],
        )
        exit_code = validate_skills(skills_dir, skill_name="good-skill")
        assert exit_code == 0


class TestExitCodes:
    """Tests for exit codes."""

    def test_exit_code_0_on_compliance(self, tmp_path: Path) -> None:
        """Exit code 0 when all skills pass."""
        skills_dir = tmp_path / "skills"
        _write_skill_md(
            skills_dir / "my-skill" / "SKILL.md",
            _compliant_headings(),
        )
        exit_code = validate_skills(skills_dir)
        assert exit_code == 0

    def test_exit_code_1_on_gap(self, tmp_path: Path) -> None:
        """Exit code 1 when any skill has gaps."""
        skills_dir = tmp_path / "skills"
        _write_skill_md(
            skills_dir / "gap-skill" / "SKILL.md",
            ["Overview"],
        )
        exit_code = validate_skills(skills_dir)
        assert exit_code == 1
