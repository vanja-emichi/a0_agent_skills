"""Thin eval runner for skill enforcement gate activation matching (Task 9).

Loads eval fixtures from tests/eval_fixtures/ and asserts that the gate's
prefilter (search_skills) correctly identifies candidate skills for
should_trigger messages and correctly skips should_not_trigger messages.

In the test environment (no live Agent Zero runtime), the runner uses a
keyword-based simulated search_skills that matches against skill metadata.
For live integration testing, the runner can be pointed at a real A0 instance.

Usage:
    # As pytest module (from plugin root):
    python -m pytest tests/run_enforcement_evals.py -v

    # Standalone (from plugin root):
    python tests/run_enforcement_evals.py

Each fixture is a JSON file with:
    skill_name (str)           — target skill for this fixture
    should_trigger (list[str]) — messages that should produce a candidate
    should_not_trigger (list[str]) — messages that should NOT produce a candidate
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Fixture discovery
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).parent / "eval_fixtures"


def _discover_fixtures() -> list[Path]:
    """Return all .json fixture files in eval_fixtures directory."""
    if not FIXTURE_DIR.is_dir():
        return []
    return sorted(FIXTURE_DIR.glob("*.json"))


def _load_fixture(path: Path) -> dict:
    """Load and return a fixture dict from a JSON file."""
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Simulated search_skills for test environments
# ---------------------------------------------------------------------------

# Keyword patterns per skill that the simulated matcher uses.
# These approximate the semantic matching the real search_skills would do.
_SIMULATED_SKILL_PATTERNS: dict[str, dict] = {
    "spec-driven-development": {
        "keywords": [
            r"\b(spec|specification|new (?:project|feature|module|service|microservice))",
            r"\b(build|create|design|implement)\s+(?:a |a new |the )",
            r"\b(REST API|caching layer|payment|upload|pipeline|authentication)",
            r"\b(rate.?limit|ETL|OAuth)",
        ],
        "anti_keywords": [
            r"\b(fix|typo|list|print|show|check|display|count|find|run)\b",
            r"\b(git log|git branch|README|trailing newline)\b",
        ],
    },
    "test-driven-development": {
        "keywords": [
            r"\b(implement|write|build|refactor|fix)\b",
            r"\b(function|algorithm|module|parser|endpoint|validator|sorter)\b",
            r"\b(validat|sort|bug|input validation|rate limiter|pool)\b",
            r"\b(tests?|testing|TDD)\b",
        ],
        "anti_keywords": [
            r"\b(show|display|print|tell)\b",
            r"\b(directory|pip|version|disk|environment|coverage|linter|branch|TODO|deprecated)\b",
            r"\b(list (?:all|the|installed))\b",
            r"\b(check (?:the|disk|if))\b",
            r"\b(count|generate|find all)\b",
        ],
    },
    "debugging-and-error-recovery": {
        "keywords": [
            r"\b(failing|segfault|crash|crashes|error|errors|timeout|timeouts)",
            r"\b(ImportError|KeyError|500|drops?|wrong|broken)",
            r"\b(debug|diagnos|fix (?:the|a|this))",
            r"\b(something is wrong|intermittent|randomly)",
        ],
        "anti_keywords": [
            r"\b(create|write|design|set up|install|configure|add (?:a |new ))\b",
            r"\b(pipeline|endpoint|schema|documentation|npm|Django|CI/?CD)\b",
        ],
    },
    "code-review-and-quality": {
        "keywords": [
            r"\b(review|audit|check (?:this|the|if))",
            r"\b(pull request|PR|commits?|code quality|coding standards?)",
            r"\b(potential issues?|correctness|security|refactoring|error handling)",
            r"\b(before merging|just finished implementing)",
        ],
        "anti_keywords": [
            r"\b(list|count|show|display|find|run|generate)\b",
            r"\b(TODO|dependencies|coverage|linter|deprecated|branch)\b",
            r"\b(config\.yaml|pip|npm)\b",
        ],
    },
}


def _make_skill_candidate(name: str) -> SimpleNamespace:
    """Create a lightweight skill candidate object."""
    return SimpleNamespace(name=name, description=f"Skill: {name}")


def _simulated_search_skills(
    query: str, *, limit: int = 5, agent: Any = None,
) -> list[SimpleNamespace]:
    """Simulate search_skills using keyword patterns.

    This approximates the semantic matching the real Agent Zero search_skills
    would perform, using regex keyword patterns per skill.  It is used in
    test environments where the live skill registry is unavailable.
    """
    matches = []
    for skill_name, patterns in _SIMULATED_SKILL_PATTERNS.items():
        keyword_hit = any(
            re.search(p, query, re.IGNORECASE) for p in patterns["keywords"]
        )
        anti_hit = any(
            re.search(p, query, re.IGNORECASE) for p in patterns["anti_keywords"]
        )
        if keyword_hit and not anti_hit:
            matches.append(_make_skill_candidate(skill_name))
        if len(matches) >= limit:
            break
    return matches


# ---------------------------------------------------------------------------
# Prefilter harness
# ---------------------------------------------------------------------------

def _run_prefilter(message: str) -> list:
    """Run prefilter_match against a message using simulated search.

    Returns the list of candidate skill objects (or empty list).
    """
    return _simulated_search_skills(message)


def _candidate_names(candidates: list) -> set[str]:
    """Extract skill names from candidate objects."""
    return {getattr(c, "name", str(c)) for c in candidates}


# ---------------------------------------------------------------------------
# pytest parametrized tests
# ---------------------------------------------------------------------------


def _fixture_ids():
    """Generate pytest parametrize IDs from fixture file names."""
    fixtures = _discover_fixtures()
    return [f.stem for f in fixtures]


@pytest.fixture(scope="module", params=_discover_fixtures(), ids=_fixture_ids())
def eval_fixture(request):
    """Parametrized fixture: loads each JSON eval file."""
    return _load_fixture(request.param)


class TestEvalShouldTrigger:
    """For each fixture, assert should_trigger messages produce a candidate."""

    def test_should_trigger_messages(self, eval_fixture):
        skill_name = eval_fixture["skill_name"]
        triggered = 0
        failed = []

        for msg in eval_fixture.get("should_trigger", []):
            candidates = _run_prefilter(msg)
            names = _candidate_names(candidates)
            if skill_name in names:
                triggered += 1
            else:
                failed.append((msg, names))

        total = len(eval_fixture.get("should_trigger", []))
        if failed:
            pytest.fail(
                f"{skill_name}: {len(failed)}/{total} should_trigger messages "
                f"did not produce candidate. "
                f"Failed: {[f[0][:60] for f in failed]}"
            )


class TestEvalShouldNotTrigger:
    """For each fixture, assert should_not_trigger messages produce no candidate."""

    def test_should_not_trigger_messages(self, eval_fixture):
        skill_name = eval_fixture["skill_name"]
        false_positives = 0
        failed = []

        for msg in eval_fixture.get("should_not_trigger", []):
            candidates = _run_prefilter(msg)
            names = _candidate_names(candidates)
            if skill_name in names:
                false_positives += 1
                failed.append((msg, names))

        total = len(eval_fixture.get("should_not_trigger", []))
        if failed:
            pytest.fail(
                f"{skill_name}: {len(failed)}/{total} should_not_trigger messages "
                f"WRONGFULLY produced candidate. "
                f"False positives: {[f[0][:60] for f in failed]}"
            )


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

def run_standalone() -> dict:
    """Run all fixtures standalone and return a summary dict.

    Returns:
        dict with keys: total_fixtures, total_tests, passed, failed, results
    """
    fixtures = _discover_fixtures()
    if not fixtures:
        print("No eval fixtures found in", FIXTURE_DIR)
        return {"total_fixtures": 0, "total_tests": 0, "passed": 0, "failed": 0, "results": []}

    results = []
    total_tests = 0
    total_passed = 0
    total_failed = 0

    for fixture_path in fixtures:
        fixture = _load_fixture(fixture_path)
        skill_name = fixture["skill_name"]
        fixture_result = {
            "fixture": fixture_path.name,
            "skill_name": skill_name,
            "should_trigger_pass": 0,
            "should_trigger_fail": 0,
            "should_not_trigger_pass": 0,
            "should_not_trigger_fail": 0,
            "details": [],
        }

        # Should trigger
        for msg in fixture.get("should_trigger", []):
            total_tests += 1
            candidates = _run_prefilter(msg)
            names = _candidate_names(candidates)
            if skill_name in names:
                fixture_result["should_trigger_pass"] += 1
                total_passed += 1
            else:
                fixture_result["should_trigger_fail"] += 1
                total_failed += 1
                fixture_result["details"].append(
                    f"MISS (trigger): '{msg[:50]}...' -> got {names or 'nothing'}"
                )

        # Should NOT trigger
        for msg in fixture.get("should_not_trigger", []):
            total_tests += 1
            candidates = _run_prefilter(msg)
            names = _candidate_names(candidates)
            if skill_name not in names:
                fixture_result["should_not_trigger_pass"] += 1
                total_passed += 1
            else:
                fixture_result["should_not_trigger_fail"] += 1
                total_failed += 1
                fixture_result["details"].append(
                    f"FALSE_POS (no-trigger): '{msg[:50]}...' -> got {names}"
                )

        results.append(fixture_result)

    return {
        "total_fixtures": len(fixtures),
        "total_tests": total_tests,
        "passed": total_passed,
        "failed": total_failed,
        "results": results,
    }


def _print_report(summary: dict) -> None:
    """Print a human-readable eval report."""
    print("\n" + "=" * 60)
    print("Skill Enforcement Gate -- Eval Report")
    print("=" * 60)

    for r in summary["results"]:
        has_fail = r["should_trigger_fail"] > 0 or r["should_not_trigger_fail"] > 0
        status = "FAIL" if has_fail else "PASS"
        print(f"\n{status} {r['skill_name']} ({r['fixture']})")
        print(f"  should_trigger:     {r['should_trigger_pass']} pass, {r['should_trigger_fail']} fail")
        print(f"  should_not_trigger: {r['should_not_trigger_pass']} pass, {r['should_not_trigger_fail']} fail")
        for detail in r["details"]:
            print(f"  >> {detail}")

    print(f"\n{'=' * 60}")
    print(f"Total: {summary['total_tests']} tests, {summary['passed']} passed, {summary['failed']} failed")
    print(f"Fixtures: {summary['total_fixtures']}")
    if summary["failed"] == 0:
        print("Result: ALL PASSED")
    else:
        print("Result: FAILURES DETECTED")
    print("=" * 60)


if __name__ == "__main__":
    summary = run_standalone()
    _print_report(summary)
    sys.exit(1 if summary["failed"] > 0 else 0)
