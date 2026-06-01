"""Skill Activation Eval Suite.

Measures whether skill_match correctly maps user intents to the right skills.
Loads fixture data from eval_fixtures/skill-activation-evals.json.

Uses a local skill-search function that reads SKILL.md frontmatter directly,
bypassing the framework's helpers.skills (which is mocked in test environments).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

FIXTURE_PATH = Path(__file__).parent / "eval_fixtures" / "skill-activation-evals.json"
SKILLS_DIR = Path(__file__).parent.parent / "skills"


# ---------------------------------------------------------------------------
# Fixture loader
# ---------------------------------------------------------------------------


def load_eval_fixtures() -> List[Dict[str, Any]]:
    with open(FIXTURE_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Local skill search (reads SKILL.md frontmatter directly)
# ---------------------------------------------------------------------------


def _parse_yaml_frontmatter(text: str) -> Dict[str, Any]:
    """Parse the YAML frontmatter from a SKILL.md file."""
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return {}
    raw = match.group(1)
    result: Dict[str, Any] = {}
    current_key = None
    current_list: list | None = None
    current_block: str | None = None  # for >- multiline strings

    for line in raw.split("\n"):
        stripped = line.strip()

        # Continuation of a block scalar (>-)
        if current_block is not None:
            if line.startswith("  ") and stripped:
                result[current_block] = result.get(current_block, "") + " " + stripped
                continue
            else:
                current_block = None

        # List item
        if line.startswith("  - ") and current_key:
            if current_key not in result or not isinstance(result[current_key], list):
                result[current_key] = []
            result[current_key].append(stripped[2:].strip())
            continue

        # Key: value
        m = re.match(r"^(\w[\w-]*):\s*(.*)", stripped)
        if m:
            key, value = m.group(1), m.group(2).strip()
            current_key = key
            if value == "" or value == ">-" or value == "|-" or value == "|" or value == ">":
                if value in (">-", "|-", "|", ">"):
                    current_block = key
                    result[key] = ""
                else:
                    result[key] = ""
            else:
                result[key] = value
    return result


def _load_skill_registry() -> Dict[str, Dict[str, Any]]:
    """Load all SKILL.md frontmatter from the skills directory."""
    registry = {}
    if not SKILLS_DIR.is_dir():
        return registry
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        text = skill_md.read_text(encoding="utf-8")
        meta = _parse_yaml_frontmatter(text)
        name = meta.get("name", skill_dir.name)
        registry[name] = {
            "name": name,
            "description": meta.get("description", ""),
            "tags": meta.get("tags", []),
            "trigger_patterns": meta.get("trigger_patterns", []),
        }
    return registry


def _local_search_skills(query: str, *, limit: int = 10) -> List[Dict[str, Any]]:
    """Search skills by matching query against frontmatter fields.

    Mimics the framework's search_skills() but reads SKILL.md files directly.
    Returns a list of dicts with 'name' key, sorted by relevance score.
    """
    registry = _load_skill_registry()
    query_lower = query.lower()
    query_words = set(re.findall(r"\w+", query_lower))
    scored: List[tuple[float, Dict[str, Any]]] = []

    for name, skill in registry.items():
        score = 0.0

        # Exact trigger_pattern match (highest signal)
        for pattern in skill["trigger_patterns"]:
            pattern_lower = pattern.lower()
            if pattern_lower == query_lower:
                score += 10.0
            elif pattern_lower in query_lower or query_lower in pattern_lower:
                score += 5.0
            else:
                # Word overlap with trigger pattern
                pattern_words = set(re.findall(r"\w+", pattern_lower))
                overlap = query_words & pattern_words
                if overlap:
                    score += 1.0 * len(overlap) / max(len(pattern_words), 1)

        # Description matching
        desc_lower = skill["description"].lower()
        for word in query_words:
            if word in desc_lower:
                score += 0.5

        # Tag matching
        for tag in skill["tags"]:
            tag_lower = tag.lower()
            if tag_lower in query_lower or any(w in tag_lower for w in query_words):
                score += 0.3

        if score > 0:
            scored.append((score, skill))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:limit]]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def skill_match():
    """Provide the local skill search module-like interface."""
    return type("SkillMatch", (), {"search_skills": staticmethod(_local_search_skills)})()


@pytest.fixture(scope="module")
def eval_cases():
    return load_eval_fixtures()


@pytest.fixture(scope="module")
def skill_registry():
    return _load_skill_registry()


# ---------------------------------------------------------------------------
# Helper: categorize cases
# ---------------------------------------------------------------------------


def _trigger_cases() -> List[Dict[str, Any]]:
    """Cases where the expected skill SHOULD appear in candidates.

    Includes all positive cases plus near-miss discrimination cases
    (those with a confused_with field). Only includes cases with a
    'phase' field (original combined-format cases designed for
    SKILL.md frontmatter matching).
    """
    cases = []
    for c in load_eval_fixtures():
        if not c.get("phase"):
            continue
        if c.get("category") == "positive":
            cases.append(c)
        elif c.get("category") == "near-miss" and c.get("confused_with"):
            cases.append(c)
    return cases


def _suppression_cases() -> List[Dict[str, Any]]:
    """Cases where the expected skill should NOT appear in candidates.

    These are near-miss cases WITHOUT a confused_with field.
    Only includes cases with a 'phase' field (original combined-format
    cases designed for SKILL.md frontmatter matching).
    """
    return [
        c for c in load_eval_fixtures()
        if c.get("phase") and c.get("category") == "near-miss" and not c.get("confused_with")
    ]


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------


class TestPrefilterAccuracy:
    """Level 1: Does skill_match return the correct skill as a candidate?"""

    @pytest.mark.parametrize("case", _trigger_cases(), ids=lambda c: c["id"])
    def test_skill_returned_as_candidate(self, case, skill_match):
        """The expected skill must appear in search results for the intent."""
        results = skill_match.search_skills(case["intent"])
        skill_names = [r["name"] for r in results]
        assert case["expected_skill"] in skill_names, (
            f"{case['id']}: Expected '{case['expected_skill']}' in results "
            f"for intent '{case['intent']}', got {skill_names}"
        )


class TestSuppressionAccuracy:
    """Level 1b: Does skill_match correctly exclude skills for near-miss intents?"""

    @pytest.mark.parametrize("case", _suppression_cases(), ids=lambda c: c["id"])
    def test_skill_not_returned_for_suppression(self, case, skill_match):
        """The expected skill must NOT appear in search results for suppression intents."""
        results = skill_match.search_skills(case["intent"])
        skill_names = [r["name"] for r in results]
        assert case["expected_skill"] not in skill_names, (
            f"{case['id']}: '{case['expected_skill']}' should NOT be in results "
            f"for intent '{case['intent']}', but it was"
        )


class TestNearMissDiscrimination:
    """Level 2: Does the system rank the correct skill higher for ambiguous intents?"""

    @pytest.mark.parametrize(
        "case",
        [c for c in load_eval_fixtures() if c.get("confused_with")],
        ids=lambda c: c["id"]
    )
    def test_correct_skill_ranked_higher(self, case, skill_match):
        """Expected skill should rank at or above the confused_with skill."""
        results = skill_match.search_skills(case["intent"])
        skill_names = [r["name"] for r in results]
        expected_idx = skill_names.index(case["expected_skill"]) if case["expected_skill"] in skill_names else 999
        confused_idx = skill_names.index(case["confused_with"]) if case["confused_with"] in skill_names else 999
        assert expected_idx <= confused_idx, (
            f"{case['id']}: '{case['expected_skill']}' (idx {expected_idx}) "
            f"should rank at or above '{case['confused_with']}' (idx {confused_idx}) "
            f"for intent '{case['intent']}'"
        )


class TestCoverageReport:
    """Meta-test: verify all 23 skills are covered by at least one eval case."""

    ALL_SKILLS = [
        "api-and-interface-design", "browser-testing-with-devtools",
        "ci-cd-and-automation", "code-review-and-quality",
        "code-simplification", "context-engineering",
        "debugging-and-error-recovery", "deprecation-and-migration",
        "documentation-and-adrs", "doubt-driven-development",
        "frontend-ui-engineering", "git-workflow-and-versioning",
        "idea-refine", "incremental-implementation",
        "interview-me", "performance-optimization",
        "planning-and-task-breakdown", "security-and-hardening",
        "shipping-and-launch", "source-driven-development",
        "spec-driven-development", "test-driven-development",
        "using-agent-skills",
    ]

    def test_all_skills_have_eval_cases(self):
        cases = load_eval_fixtures()
        covered_skills = {c["expected_skill"] for c in cases}
        missing = set(self.ALL_SKILLS) - covered_skills
        assert not missing, f"Skills without eval cases: {missing}"

    def test_minimum_eval_case_count(self):
        cases = load_eval_fixtures()
        assert len(cases) >= 30, f"Expected ≥30 eval cases, got {len(cases)}"

    def test_at_least_one_near_miss_per_confusable_pair(self):
        cases = load_eval_fixtures()
        near_miss = [c for c in cases if c.get("confused_with")]
        assert len(near_miss) >= 5, f"Expected ≥5 near-miss cases, got {len(near_miss)}"

    def test_all_fixture_skills_exist_in_registry(self, skill_registry):
        """Every skill referenced in fixtures must exist in the skills directory."""
        cases = load_eval_fixtures()
        all_referenced = set()
        for c in cases:
            all_referenced.add(c["expected_skill"])
            if c.get("confused_with"):
                all_referenced.add(c["confused_with"])
        missing = all_referenced - set(skill_registry.keys())
        assert not missing, f"Skills in fixtures but not in registry: {missing}"
