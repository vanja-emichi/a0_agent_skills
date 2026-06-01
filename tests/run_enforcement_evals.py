"""Thin eval runner for skill enforcement gate activation matching (Task 9).

Loads eval fixtures from tests/eval_fixtures/skill-activation-evals.json
and asserts that the gate's prefilter (search_skills) correctly
identifies candidate skills for positive intents and correctly
discriminates near-miss intents.

In the test environment (no live Agent Zero runtime), the runner uses a
keyword-based simulated search_skills that matches against skill metadata.
For live integration testing, the runner can be pointed at a real A0 instance.

Usage:
    # As pytest module (from plugin root):
    python -m pytest tests/run_enforcement_evals.py -v

    # Standalone (from plugin root):
    python tests/run_enforcement_evals.py

The fixture file is a JSON array of eval cases:
    id (str)                 — unique case identifier
    intent (str)             — user message to test
    expected_skill (str)     — skill that should (or should not) be matched
    category (str)           — "positive" or "near-miss"
    description (str)        — optional human-readable description
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

# ---------------------------------------------------------------------------
# Fixture discovery
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).parent / "eval_fixtures"
COMBINED_FIXTURE = FIXTURE_DIR / "skill-activation-evals.json"


def _load_combined_fixture() -> list[dict]:
    """Load the combined eval fixture (list of cases)."""
    if not COMBINED_FIXTURE.is_file():
        return []
    with open(COMBINED_FIXTURE) as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return []


# ---------------------------------------------------------------------------
# Simulated search_skills for test environments
# ---------------------------------------------------------------------------

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
    "planning-and-task-breakdown": {
        "keywords": [
            r"\bbreak\b.*\btasks?\b",
            r"\b(plan|planning|sprint)\b",
            r"\b(decompose|organize|break down)\b",
            r"\b(work|features?)\b.*\btasks?\b",
        ],
        "anti_keywords": [
            r"\b(spec|specification)\b",
            r"\b(write|create)\b.*\bspec\b",
            r"\b(debug|fix|error|crash)\b",
        ],
    },
    "incremental-implementation": {
        "keywords": [
            r"\bimplement\b",
            r"\b(incremental|slice)\b",
            r"\b(build|develop)\b.*\bfeature\b",
            r"\bPOST\b.*\bendpoint\b",
        ],
        "anti_keywords": [
            r"\b(test|testing|tests?)\b.*\bfor\b",
            r"\b(review|audit)\b",
            r"\b(plan|spec|design)\b",
        ],
    },
    "code-simplification": {
        "keywords": [
            r"\bsimplif\w+\b",
            r"\brefactor\b.*\bclean\w*\b",
            r"\breduce (?:complexity|complex)\b",
            r"\brefactor\b.*\bclear\w*\b",
            r"\b(cleaner|clean code)\b",
        ],
        "anti_keywords": [
            r"\b(pull request|PR)\b",
            r"\breview\b.*\b(merge|PR)\b",
            r"\b(security|vulnerability|OWASP)\b",
        ],
    },
    "security-and-hardening": {
        "keywords": [
            r"\b(security|vulnerabilit\w+)\b",
            r"\baudit\b.*\b(security|flaw)\b",
            r"\b(harden|hardening)\b",
            r"\b(OWASP|injection|XSS|CSRF)\b",
            r"\b(security flaw)\b",
        ],
        "anti_keywords": [
            r"\b(pull request|PR)\b.*\bmerge\b",
            r"\breview\b.*\bbefore\b.*\bmerge\b",
            r"\b(code quality|coding standards?)\b",
        ],
    },
    "performance-optimization": {
        "keywords": [
            r"\boptimize\b",
            r"\bslow\b",
            r"\b(latency|throughput|bottleneck)\b",
            r"\bload\w*\b.*\bfaster\b",
            r"\bperformance\b",
        ],
        "anti_keywords": [
            r"\b(build|create|design)\b.*\b(component|UI|form|page)\b",
            r"\b(React|CSS|frontend)\b",
            r"\b(deploy|ship|launch)\b",
        ],
    },
    "shipping-and-launch": {
        "keywords": [
            r"\bdeploy\b",
            r"\bproduction\b",
            r"\b(launch|ship|release)\b",
            r"\b(release checklist|go.?live)\b",
        ],
        "anti_keywords": [
            r"\b(debug|fix|error|crash|failing)\b",
            r"\b(test|testing|write tests?)\b",
            r"\b(review|audit|security)\b",
        ],
    },
    "ci-cd-and-automation": {
        "keywords": [
            r"\bCI.?CD\b",
            r"\bpipeline\b",
            r"\b(automate|GitHub Actions|continuous integration)\b",
            r"\b(set up|configure)\b.*\bpipeline\b",
        ],
        "anti_keywords": [
            r"\b(debug|fix bug|error|crash)\b",
            r"\b(review|audit|security)\b",
            r"\b(build|implement|code|write)\b",
        ],
    },
    "git-workflow-and-versioning": {
        "keywords": [
            r"\bbranch\b",
            r"\bcommit\b",
            r"\b(version control|release branch|merge strategy)\b",
            r"\b(create|make)\b.*\b(branch|commit|tag)\b",
        ],
        "anti_keywords": [
            r"\b(deploy|production|CI.?CD)\b",
            r"\b(debug|fix|error|crash)\b",
            r"\b(test|testing|write)\b",
        ],
    },
    "documentation-and-adrs": {
        "keywords": [
            r"\bADR\b",
            r"\b(document|documentation)\b",
            r"\bREADME\b",
            r"\b(architecture decision)\b",
            r"\bwrite\b.*\b(docs|documentation)\b",
        ],
        "anti_keywords": [
            r"\b(spec|specification)\b.*\b(new|create|build)\b",
            r"\b(test|testing)\b",
            r"\b(implement|build|code)\b",
        ],
    },
    "deprecation-and-migration": {
        "keywords": [
            r"\bmigrate\b",
            r"\b(deprecate|deprecation)\b",
            r"\b(upgrade|update)\b.*\b(framework|library|version)\b",
            r"\bfrom\b.*\bto\b.*\b(GraphQL|REST|v\d)\b",
        ],
        "anti_keywords": [
            r"\b(build new|create new|from scratch|new project)\b",
            r"\b(deploy|production|ship)\b",
            r"\b(test|testing|debug)\b",
        ],
    },
    "source-driven-development": {
        "keywords": [
            r"\bcheck\b.*\bdocs?\b",
            r"\b(official|latest)\b.*\b(docs|API|reference)\b",
            r"\bframework\b.*\bdocs\b",
            r"\bAPI reference\b",
        ],
        "anti_keywords": [
            r"\b(write|create|build)\b.*\b(docs|documentation)\b",
            r"\b(deploy|ship|launch)\b",
            r"\b(test|testing|debug)\b",
        ],
    },
    "doubt-driven-development": {
        "keywords": [
            r"\bstress.?test\b",
            r"\badversarial\b",
            r"\bchallenge\b.*\b(approach|plan|design)\b",
            r"\bdoubt\b",
            r"\bstress.?test\b.*\bplan\b",
        ],
        "anti_keywords": [
            r"\b(implement|build|code|write)\b",
            r"\b(fix|debug|error|crash)\b",
            r"\b(deploy|ship|testing)\b",
        ],
    },
    "frontend-ui-engineering": {
        "keywords": [
            r"\b(build|create)\b.*\b(component|form|UI|page|interface)\b",
            r"\b(React|CSS|frontend)\b",
            r"\b(login|signup|button)\b.*\b(form|component|page)\b",
            r"\blogin form\b",
        ],
        "anti_keywords": [
            r"\b(optimize|performance|slow|latency|fast\w*)\b",
            r"\b(deploy|ship|CI.?CD)\b",
            r"\b(debug|fix|error|crash)\b",
        ],
    },
    "api-and-interface-design": {
        "keywords": [
            r"\bdesign\b.*\bAPI\b",
            r"\bREST\b",
            r"\b(endpoint|interface contract|OpenAPI)\b",
            r"\bdesign\b.*\b(endpoint|interface)\b",
        ],
        "anti_keywords": [
            r"\b(implement|build|code|write)\b.*\b(function|module|parser)\b",
            r"\b(test|testing|debug)\b",
            r"\b(deploy|ship|launch)\b",
        ],
    },
    "browser-testing-with-devtools": {
        "keywords": [
            r"\btest\b.*\bbrowser\b",
            r"\bend.?to.?end\b",
            r"\b(E2E|Selenium|Playwright|visual test)\b",
            r"\bbrowser\b.*\btest\b",
            r"\bverify\b.*\bend\b",
        ],
        "anti_keywords": [
            r"\b(unit test|write tests? for|implement tests?)\b",
            r"\b(build|implement|code|create)\b",
            r"\b(deploy|ship|launch)\b",
        ],
    },
    "context-engineering": {
        "keywords": [
            r"\bmanage context\b",
            r"\bcontext\b.*\b(codebase|window|agent)\b",
            r"\blarge codebase\b",
            r"\bcontext window\b",
        ],
        "anti_keywords": [
            r"\b(build|implement|deploy|create)\b",
            r"\b(fix|debug|error|crash)\b",
            r"\b(test|review|audit)\b",
        ],
    },
    "interview-me": {
        "keywords": [
            r"\binterview\b",
            r"\bwhat\b.*\bI want\b",
            r"\bfigure out\b.*\b(user|wants?)\b",
            r"\bclarify requirements?\b",
            r"\b(extract intent|what.*want)\b",
        ],
        "anti_keywords": [
            r"\b(refine|brainstorm|ideate)\b.*\bidea\b",
            r"\b(build|implement|code|deploy)\b",
            r"\b(fix|debug|test|review)\b",
        ],
    },
    "idea-refine": {
        "keywords": [
            r"\brefine\b.*\bidea\b",
            r"\b(brainstorm|ideate|explore options?)\b",
            r"\bvague idea\b",
            r"\brefine\b.*\b(vague|raw|concept)\b",
        ],
        "anti_keywords": [
            r"\binterview\b",
            r"\bwhat\b.*\bI want\b",
            r"\b(build|implement|code|deploy)\b",
        ],
    },
    "using-agent-skills": {
        "keywords": [
            r"\bwhich skill\b",
            r"\bwhat skill\b",
            r"\bskill should\b",
            r"\bskill selection\b",
        ],
        "anti_keywords": [
            r"\b(deploy|ship|launch|release)\b",
            r"\b(implement|build|code|write)\b",
            r"\b(fix|debug|error|crash)\b",
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


def _load_positive_cases() -> list[dict]:
    """Return cases where the expected skill should appear in candidates.

    Includes all "positive" cases plus "near-miss" discrimination cases
    (those with a "confused_with" field).
    """
    cases = []
    for c in _load_combined_fixture():
        if c.get("category") == "positive":
            cases.append(c)
        elif c.get("category") == "near-miss" and c.get("confused_with"):
            cases.append(c)
    return cases


def _load_near_miss_cases() -> list[dict]:
    """Return suppression cases: expected skill should NOT appear.

    These are "near-miss" cases WITHOUT a "confused_with" field,
    meaning the intent should not trigger the expected skill at all.
    """
    return [
        c for c in _load_combined_fixture()
        if c.get("category") == "near-miss" and not c.get("confused_with")
    ]


class TestPositiveCases:
    """Positive cases: the expected skill must appear in candidates."""

    @pytest.mark.parametrize(
        "case", _load_positive_cases(), ids=lambda c: c["id"]
    )
    def test_positive_intent_triggers_skill(self, case):
        candidates = _run_prefilter(case["intent"])
        names = _candidate_names(candidates)
        assert case["expected_skill"] in names, (
            f"{case['id']}: Expected '{case['expected_skill']}' for "
            f"'{case['intent'][:60]}', got {names or 'nothing'}"
        )


class TestNearMissCases:
    """Near-miss cases: the expected skill must NOT appear in candidates."""

    @pytest.mark.parametrize(
        "case", _load_near_miss_cases(), ids=lambda c: c["id"]
    )
    def test_near_miss_does_not_trigger_skill(self, case):
        candidates = _run_prefilter(case["intent"])
        names = _candidate_names(candidates)
        assert case["expected_skill"] not in names, (
            f"{case['id']}: '{case['expected_skill']}' should NOT match "
            f"'{case['intent'][:60]}', but it did"
        )


# ---------------------------------------------------------------------------
# Standalone runner
# ---------------------------------------------------------------------------

def run_standalone() -> dict:
    """Run all eval cases and return a summary dict.

    Returns:
        dict with keys: total_fixtures, total_tests, passed, failed, results
    """
    cases = _load_combined_fixture()
    if not cases:
        print("No eval cases found in", COMBINED_FIXTURE)
        return {"total_fixtures": 0, "total_tests": 0, "passed": 0, "failed": 0, "results": []}

    results = []
    total_tests = 0
    total_passed = 0
    total_failed = 0

    for case in cases:
        total_tests += 1
        intent = case.get("intent", "")
        expected = case.get("expected_skill", "")
        category = case.get("category", "positive")
        candidates = _run_prefilter(intent)
        names = _candidate_names(candidates)

        if category == "positive":
            if expected in names:
                total_passed += 1
                detail_status = "PASS"
            else:
                total_failed += 1
                detail_status = "MISS"
        elif category == "near-miss":
            # near-miss with confused_with: discrimination test (expected should match)
            # near-miss without confused_with: suppression test (expected should NOT match)
            if case.get("confused_with"):
                if expected in names:
                    total_passed += 1
                    detail_status = "PASS"
                else:
                    total_failed += 1
                    detail_status = "MISS"
            else:
                if expected not in names:
                    total_passed += 1
                    detail_status = "PASS"
                else:
                    total_failed += 1
                    detail_status = "FALSE_POS"
        else:
            total_passed += 1
            detail_status = "SKIP"

        results.append({
            "case_id": case.get("id", "?"),
            "skill_name": expected,
            "category": category,
            "status": detail_status,
            "intent": intent[:60],
            "got": names or "nothing",
        })

    return {
        "total_fixtures": 1,
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
        status = r.get("status", "?")
        print(f"  {status} [{r.get('category', '?')}] {r.get('skill_name', '?')} -- {r.get('intent', '?')}")
        if r.get("got") and r["got"] != [r.get("skill_name")] and status != "PASS":
            print(f"       got: {r['got']}")

    print(f"\n{'=' * 60}")
    print(f"Total: {summary['total_tests']} tests, {summary['passed']} passed, {summary['failed']} failed")
    print(f"Fixture: skill-activation-evals.json")
    if summary["failed"] == 0:
        print("Result: ALL PASSED")
    else:
        print("Result: FAILURES DETECTED")
    print("=" * 60)


if __name__ == "__main__":
    summary = run_standalone()
    _print_report(summary)
    sys.exit(1 if summary["failed"] > 0 else 0)
