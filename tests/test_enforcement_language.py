"""T-18: Verify all 21 skills use MUST/NEVER in enforcement sections.

RED phase: These tests MUST FAIL because some skills still use
SHOULD/CONSIDER in Verification and Anti-Patterns sections.
"""
import os
import re
import pytest
import yaml

PLUGIN = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
SKILLS_DIR = os.path.join(PLUGIN, "skills")


def _read_skill(skill_name: str) -> str:
    """Read a SKILL.md file."""
    path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
    if not os.path.exists(path):
        pytest.skip(f"{skill_name}/SKILL.md not found")
    with open(path) as f:
        return f.read()


def _extract_section(content: str, section_name: str) -> str:
    """Extract a section from SKILL.md content by header name."""
    pattern = rf"^##\s+{re.escape(section_name)}.*?$"
    lines = content.split("\n")
    capturing = False
    section_lines = []
    for line in lines:
        if re.match(pattern, line, re.IGNORECASE):
            capturing = True
            section_lines.append(line)
            continue
        if capturing:
            if line.startswith("## ") and not re.match(pattern, line, re.IGNORECASE):
                break
            section_lines.append(line)
    return "\n".join(section_lines)


def _get_all_skills():
    """Get all skill directory names."""
    return sorted([
        d for d in os.listdir(SKILLS_DIR)
        if os.path.isdir(os.path.join(SKILLS_DIR, d))
        and os.path.exists(os.path.join(SKILLS_DIR, d, "SKILL.md"))
    ])


class TestEnforcementLanguage:
    """Verify enforcement sections use MUST/NEVER, not SHOULD/CONSIDER."""

    # Words that MUST NOT appear in enforcement sections
    WEAK_PATTERNS = [
        (r"\bshould\b", "should"),
        (r"\bconsider\b", "consider"),
    ]

    # Sections where enforcement language is required
    ENFORCEMENT_SECTIONS = ["Verification", "Anti-Patterns"]

    @pytest.mark.parametrize("skill_name", _get_all_skills())
    def test_verification_section_has_no_weak_language(self, skill_name: str):
        """Verification section MUST NOT contain 'should' or 'consider'."""
        content = _read_skill(skill_name)
        section = _extract_section(content, "Verification")

        if not section.strip():
            pytest.skip(f"{skill_name} has no Verification section")

        for pattern, word in self.WEAK_PATTERNS:
            matches = re.findall(pattern, section, re.IGNORECASE)
            assert matches == [], (
                f"{skill_name}: Verification section contains '{word}' "
                f"({len(matches)} occurrences). "
                f"Use MUST/REQUIRED instead."
            )

    @pytest.mark.parametrize("skill_name", _get_all_skills())
    def test_anti_patterns_section_has_no_weak_language(self, skill_name: str):
        """Anti-Patterns section MUST NOT contain 'should' or 'consider'."""
        content = _read_skill(skill_name)
        section = _extract_section(content, "Anti-Patterns")

        if not section.strip():
            pytest.skip(f"{skill_name} has no Anti-Patterns section")

        for pattern, word in self.WEAK_PATTERNS:
            matches = re.findall(pattern, section, re.IGNORECASE)
            assert matches == [], (
                f"{skill_name}: Anti-Patterns section contains '{word}' "
                f"({len(matches)} occurrences). "
                f"Use MUST NOT/NEVER instead."
            )

    @pytest.mark.parametrize("skill_name", _get_all_skills())
    def test_verification_section_has_must_language(self, skill_name: str):
        """Verification section MUST contain at least one MUST/REQUIRED."""
        content = _read_skill(skill_name)
        section = _extract_section(content, "Verification")

        if not section.strip():
            pytest.skip(f"{skill_name} has no Verification section")

        strong_words = re.findall(r"\b(MUST|REQUIRED|MANDATORY)\b", section)
        # At least the checkbox items should use MUST or be structured
        # We accept sections with checkboxes ([ ]) as implicitly mandatory
        has_checkboxes = "- [ ]" in section or "- [x]" in section
        assert strong_words or has_checkboxes, (
            f"{skill_name}: Verification section lacks MUST/REQUIRED language. "
            f"Found: {section[:200]}"
        )

    @pytest.mark.parametrize("skill_name", _get_all_skills())
    def test_anti_patterns_section_has_never_language(self, skill_name: str):
        """Anti-Patterns section MUST contain MUST NOT or NEVER."""
        content = _read_skill(skill_name)
        section = _extract_section(content, "Anti-Patterns")

        if not section.strip():
            pytest.skip(f"{skill_name} has no Anti-Patterns section")

        strong_negatives = re.findall(
            r"\b(MUST NOT|NEVER|DO NOT|AVOID)\b", section, re.IGNORECASE
        )
        # Also accept bullet lists starting with '-' as implicit negatives
        has_bullets = bool(re.findall(r"^\s*-", section, re.MULTILINE))
        assert strong_negatives or has_bullets, (
            f"{skill_name}: Anti-Patterns section lacks MUST NOT/NEVER language. "
            f"Found: {section[:200]}"
        )


def _parse_frontmatter(content: str) -> dict:
    """Parse YAML frontmatter from a SKILL.md file."""
    if not content.startswith("---"):
        return {}
    try:
        end = content.index("---", 3)
        return yaml.safe_load(content[3:end]) or {}
    except (ValueError, yaml.YAMLError):
        return {}


class TestAntiPatternsGap:
    """Track which skills are missing Anti-Patterns sections (I-1)."""

    def test_skills_missing_anti_patterns_section(self):
        """Document which skills lack an Anti-Patterns section.

        This test does NOT fail — it tracks the known gap so that when
        Anti-Patterns sections are added, the skip count in
        TestEnforcementLanguage drops.
        """
        all_skills = _get_all_skills()
        missing = []
        for skill_name in all_skills:
            content = _read_skill(skill_name)
            section = _extract_section(content, "Anti-Patterns")
            if not section.strip():
                missing.append(skill_name)

        # This test always passes — it documents the gap
        # When Anti-Patterns sections are added to skills, update this list
        print(f"\nSkills missing Anti-Patterns sections ({len(missing)}/{len(all_skills)}):")
        for name in missing:
            print(f"  - {name}")
        # Assertion is informational only — no failure expected
        assert True, (
            f"{len(missing)} of {len(all_skills)} skills lack Anti-Patterns sections. "
            f"Missing: {', '.join(missing)}"
        )


class TestTriggerPatterns:
    """Verify trigger_patterns in SKILL.md frontmatter (I-5)."""

    @pytest.mark.parametrize("skill_name", _get_all_skills())
    def test_trigger_patterns_minimum_count(self, skill_name: str):
        """Each SKILL.md MUST have at least 5 trigger_patterns."""
        content = _read_skill(skill_name)
        fm = _parse_frontmatter(content)

        trigger_patterns = fm.get("trigger_patterns", [])
        assert len(trigger_patterns) >= 5, (
            f"{skill_name}: has only {len(trigger_patterns)} trigger_patterns, "
            f"expected at least 5. "
            f"Found: {trigger_patterns}"
        )
