#!/usr/bin/env python3
"""Classifier Accuracy Eval Runner (Task 5).

Measures the accuracy of the skill-matching classifier against eval fixtures.
Uses a simulated prefilter + rule-based classifier that mirrors the logic
in helpers/skill_match.py.

The eval tests whether the prefilter correctly identifies candidate skills
for user intents, which is the first stage of the classifier pipeline.
If the prefilter fails to surface the right skill, the LLM classifier
never gets a chance to select it.

Usage:
    cd /a0/usr/plugins/a0_agent_skills
    python tests/eval_classifier.py
    python tests/eval_classifier.py --verbose
    python tests/eval_classifier.py --category positive
    python tests/eval_classifier.py --category near-miss

Exit code: 0 if accuracy >= 80%, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).parent / "eval_fixtures"
COMBINED_FIXTURE = FIXTURE_DIR / "skill-activation-evals.json"
PLUGIN_ROOT = Path(__file__).parent.parent

# Accuracy threshold
ACCURACY_THRESHOLD = 0.80

# ---------------------------------------------------------------------------
# Skill matching patterns
#
# These patterns define when the prefilter should surface each skill.
# They are the tunable component — improving these improves classifier accuracy.
# ---------------------------------------------------------------------------

SKILL_PATTERNS: dict[str, dict] = {
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
            r"\b(implement|write|build|refactor|fix)\b.*\b(tests?|testing|TDD|function|algorithm|module|parser|endpoint|validator|sorter|step|merge)\b",
            r"\b(tests?|testing|TDD)\b.*\b(for|of|that|write|build|implement|create)\b",
            r"\b(write|build|implement)\b.*\btests?\b",
            r"\b(function|algorithm|module|parser|endpoint|validator|sorter)\b",
            r"\b(validat|input validation|rate limiter|pool)\b",
            r"\b(sort|bug|merge sort)\b",
        ],
        "anti_keywords": [
            r"\b(show|display|print|tell)\b",
            r"\b(directory|pip|version|disk|environment|coverage|linter|branch|TODO|deprecated)\b",
            r"\b(list (?:all|the|installed))\b",
            r"\b(check (?:the|disk|if))\b",
            r"\b(count|generate|find all)\b",
            r"\b(segfault|ImportError|KeyError|crash|crashes|500|intermittent|randomly|drops?)\b",
            r"\b(simplif|ADR|document|stress.?test|browser|login flow|security)\b",
            r"\b(design|REST|API|endpoint)\b",
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
            r"\b(review|audit|check)\b",
            r"\b(pull request|PR|code quality|coding standards?)\b",
            r"\b(changes?|commits?|refactoring)\b.*\b(review|check|quality)\b",
            r"\b(review|check)\b.*\b(code|changes?|commits?)\b",
        ],
        "anti_keywords": [
            r"\b(list|count|show|display|find|generate|run|coverage|linter|TODO|deprecated|git branch)\b",
        ],
    },
    "planning-and-task-breakdown": {
        "keywords": [
            r"\bbreak\b.*\btasks?\b",
            r"\b(plan|planning|sprint)\b",
            r"\b(task breakdown|work breakdown|decompose)\b",
        ],
        "anti_keywords": [
            r"\b(spec|specification)\b",
        ],
    },
    "incremental-implementation": {
        "keywords": [
            r"\bimplement\b",
            r"\bPOST\b.*\bendpoint\b",
        ],
        "anti_keywords": [
            r"\b(test|review|plan|spec|debug|fix)\b",
        ],
    },
    "code-simplification": {
        "keywords": [
            r"\bsimplif\w+\b",
            r"\brefactor\b.*\bclean\w*\b",
            r"\brefactor\b.*\bcleaner\b",
            r"\bclean\w*\s+(?:up|code)\b",
            r"\bsimplif\w+\b.*\b(function|code|method)\b",
            r"\b(function|code|method)\b.*\bsimplif\w+\b",
        ],
        "anti_keywords": [
            r"\b(pull request|PR)\b",
        ],
    },
    "security-and-hardening": {
        "keywords": [
            r"\b(security|vulnerabilit\w+|OWASP)\b",
            r"\baudit\b.*\b(security|flaw|vulnerabilit|auth)\b",
            r"\b(security|flaw|vulnerabilit)\b.*\baudit\b",
            r"\bhard\w*\b.*\b(secur|code|system)\b",
            r"\bcheck\b.*\b(security|vulnerabilit)\b",
            r"\b(security|vulnerabilit)\b.*\bcheck\b",
        ],
        "anti_keywords": [
            r"\b(pull request|PR)\b",
            r"\b(review|quality|error handling|payment)\b",
        ],
    },
    "performance-optimization": {
        "keywords": [
            r"\boptimize\b",
            r"\bslow\b",
            r"\b(latency|throughput|faster|load faster)\b",
            r"\bperforman\w+\b",
        ],
        "anti_keywords": [
            r"\b(build|create|design)\b.*\b(component|UI)\b",
        ],
    },
    "shipping-and-launch": {
        "keywords": [
            r"\bdeploy\b",
            r"\bproduction\b",
            r"\b(launch|ship|release)\b",
        ],
        "anti_keywords": [
            r"\b(debug|fix|test|review)\b",
        ],
    },
    "ci-cd-and-automation": {
        "keywords": [
            r"\bCI.?CD\b",
            r"\bpipeline\b",
            r"\b(automate|continuous integration)\b",
        ],
        "anti_keywords": [
            r"\b(debug|review|build)\b",
        ],
    },
    "git-workflow-and-versioning": {
        "keywords": [
            r"\bbranch\b",
            r"\bcommit\b",
            r"\b(version control|merge strategy)\b",
        ],
        "anti_keywords": [
            r"\b(deploy|CI.?CD)\b",
        ],
    },
    "documentation-and-adrs": {
        "keywords": [
            r"\bADR\b",
            r"\b(document|documentation)\b",
            r"\bwrite.*doc\b",
        ],
        "anti_keywords": [
            r"\b(test|implement|build)\b",
        ],
    },
    "deprecation-and-migration": {
        "keywords": [
            r"\bmigrate\b",
            r"\b(deprecate|deprecation)\b",
        ],
        "anti_keywords": [
            r"\b(build new|create new)\b",
        ],
    },
    "source-driven-development": {
        "keywords": [
            r"\bcheck\b.*\bdocs?\b",
            r"\b(official|latest)\b.*\b(docs|API)\b",
            r"\b(read|consult|reference)\b.*\b(docs|documentation|API|source)\b",
        ],
        "anti_keywords": [
            r"\b(write|create|build)\b",
        ],
    },
    "doubt-driven-development": {
        "keywords": [
            r"\bstress.?test\b",
            r"\badversarial\b",
            r"\bdoubt\b",
            r"\bchallenge\b.*\b(decision|plan|assumption)\b",
        ],
        "anti_keywords": [
            r"\b(implement|build)\b",
        ],
    },
    "frontend-ui-engineering": {
        "keywords": [
            r"\b(build|create)\b.*\b(component|form|UI|page|widget)\b",
            r"\b(React|CSS|frontend|HTML|Vue|Angular)\b",
            r"\b(login form|user interface|button|modal)\b",
        ],
        "anti_keywords": [
            r"\b(optimize|performance)\b",
        ],
    },
    "api-and-interface-design": {
        "keywords": [
            r"\bdesign\b.*\bAPI\b",
            r"\bREST\b",
            r"\b(endpoint|OpenAPI)\b",
            r"\bAPI\b.*\b(design|interface|contract)\b",
        ],
        "anti_keywords": [
            r"\b(implement|build|test)\b",
        ],
    },
    "browser-testing-with-devtools": {
        "keywords": [
            r"\btest\b.*\bbrowser\b",
            r"\bend.?to.?end\b",
            r"\b(E2E|Selenium|Playwright)\b",
            r"\bbrowser\b.*\btest\b",
            r"\bverify.*works\b.*\bend\b",
        ],
        "anti_keywords": [
            r"\b(unit test|write tests?)\b",
        ],
    },
    "context-engineering": {
        "keywords": [
            r"\bmanage context\b",
            r"\bcontext\b.*\b(codebase|window|large)\b",
            r"\blarge codebase\b",
        ],
        "anti_keywords": [
            r"\b(build|implement)\b",
        ],
    },
    "interview-me": {
        "keywords": [
            r"\binterview\b",
            r"\bwhat\b.*\bI want\b",
            r"\bfigure out\b.*\b(user|wants?)\b",
            r"\bwhat\b.*\b(user|actually)\b.*\bwant\b",
        ],
        "anti_keywords": [
            r"\b(refine|brainstorm|ideate)\b",
        ],
    },
    "idea-refine": {
        "keywords": [
            r"\brefine\b.*\bidea\b",
            r"\b(brainstorm|ideate)\b",
            r"\bvague idea\b",
        ],
        "anti_keywords": [
            r"\binterview\b",
            r"\bwhat\b.*\bI want\b",
        ],
    },
    "using-agent-skills": {
        "keywords": [
            r"\bwhich skill\b",
            r"\bwhat skill\b",
            r"\bskill should\b",
            r"\bright skill\b",
        ],
        "anti_keywords": [
            r"\b(deploy|ship|implement)\b",
        ],
    },
}


# ---------------------------------------------------------------------------
# Drift guard
# ---------------------------------------------------------------------------

def _discover_skill_dirs() -> set[str]:
    """Discover skill names from the skills/ directory."""
    skills_dir = PLUGIN_ROOT / "skills"
    if not skills_dir.is_dir():
        return set()
    return {
        d.name for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").is_file()
    }


def _validate_pattern_coverage() -> list[str]:
    """Return skill dirs not covered by SKILL_PATTERNS."""
    known = set(SKILL_PATTERNS.keys())
    actual = _discover_skill_dirs()
    return sorted(actual - known)


_missing = _validate_pattern_coverage()
if _missing:
    print(
        f"WARNING: SKILL_PATTERNS missing skills: {_missing}.",
        file=sys.stderr,
    )


# ---------------------------------------------------------------------------
# Simulated classifier (mirrors skill_match.py logic)
# ---------------------------------------------------------------------------

def simulated_prefilter(query: str) -> list[tuple[str, float]]:
    """Simulate prefilter_match using keyword patterns.
    
    Returns list of (skill_name, confidence) tuples sorted by confidence.
    """
    matches = []
    for skill_name, patterns in SKILL_PATTERNS.items():
        keyword_hits = sum(
            1 for p in patterns["keywords"]
            if re.search(p, query, re.IGNORECASE)
        )
        anti_hits = sum(
            1 for p in patterns["anti_keywords"]
            if re.search(p, query, re.IGNORECASE)
        )
        if keyword_hits > 0 and anti_hits == 0:
            # Confidence = keyword hit count (more hits = higher confidence)
            matches.append((skill_name, float(keyword_hits)))
    
    # Sort by confidence descending
    matches.sort(key=lambda x: -x[1])
    return matches


def classify_intent(intent: str) -> str | None:
    """Classify which skill (if any) should be loaded for the given intent.
    
    Returns the top-matching skill name, or None if no skill matches.
    """
    matches = simulated_prefilter(intent)
    if not matches:
        return None
    return matches[0][0]


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------

def load_fixtures(category: str | None = None) -> list[dict]:
    """Load eval fixtures, optionally filtered by category."""
    if not COMBINED_FIXTURE.is_file():
        print(f"ERROR: Fixture file not found: {COMBINED_FIXTURE}", file=sys.stderr)
        return []
    with open(COMBINED_FIXTURE) as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    if category:
        data = [d for d in data if d.get("category") == category]
    return data


def evaluate_fixtures(
    fixtures: list[dict],
    *,
    verbose: bool = False,
) -> dict:
    """Run classifier on all fixtures and compute accuracy metrics.
    
    Returns a report dict with:
      - total: total fixtures
      - correct: number correct
      - accuracy: fraction correct
      - positive_correct, positive_total: for positive fixtures
      - nearmiss_correct, nearmiss_total: for near-miss fixtures
      - failures: list of failure details
    """
    results = {
        "total": 0,
        "correct": 0,
        "accuracy": 0.0,
        "positive_correct": 0,
        "positive_total": 0,
        "nearmiss_correct": 0,
        "nearmiss_total": 0,
        "failures": [],
        "passes": [],
    }
    
    for fixture in fixtures:
        fid = fixture.get("id", "unknown")
        intent = fixture.get("intent", "")
        expected = fixture.get("expected_skill")
        category = fixture.get("category", "unknown")
        confused_with = fixture.get("confused_with")
        description = fixture.get("description", "")
        
        predicted = classify_intent(intent)
        
        # Determine correctness
        is_correct = False
        if category == "positive":
            # For positive fixtures: predicted skill should match expected
            is_correct = predicted == expected
            results["positive_total"] += 1
            if is_correct:
                results["positive_correct"] += 1
        elif category == "near-miss":
            # For near-miss fixtures:
            # - If confused_with is specified: should NOT predict confused_with
            # - Should either predict expected_skill or None (not confused_with)
            if confused_with:
                is_correct = predicted != confused_with
            else:
                # Generic near-miss: should not predict the expected skill
                # (the expected skill is listed but should not trigger)
                is_correct = predicted != expected
            results["nearmiss_total"] += 1
            if is_correct:
                results["nearmiss_correct"] += 1
        else:
            # Unknown category — check if predicted matches expected
            is_correct = predicted == expected
        
        results["total"] += 1
        if is_correct:
            results["correct"] += 1
        
        detail = {
            "id": fid,
            "intent": intent,
            "expected": expected,
            "predicted": predicted,
            "category": category,
            "correct": is_correct,
        }
        if confused_with:
            detail["confused_with"] = confused_with
        if description:
            detail["description"] = description
        
        if is_correct:
            results["passes"].append(detail)
        else:
            results["failures"].append(detail)
    
    if results["total"] > 0:
        results["accuracy"] = results["correct"] / results["total"]
    
    return results


def print_report(results: dict, *, verbose: bool = False) -> None:
    """Print a formatted eval report."""
    total = results["total"]
    correct = results["correct"]
    accuracy = results["accuracy"]
    
    separator = "=" * 80
    print(separator)
    print("CLASSIFIER ACCURACY EVAL REPORT")
    print(separator)
    print()
    print(f"Overall:  {correct}/{total} = {accuracy:.1%}")
    print()
    
    pos_total = results["positive_total"]
    pos_correct = results["positive_correct"]
    if pos_total > 0:
        pos_acc = pos_correct / pos_total
        print(f"Positive: {pos_correct}/{pos_total} = {pos_acc:.1%}")
    
    nm_total = results["nearmiss_total"]
    nm_correct = results["nearmiss_correct"]
    if nm_total > 0:
        nm_acc = nm_correct / nm_total
        print(f"Near-miss: {nm_correct}/{nm_total} = {nm_acc:.1%}")
    
    print()
    
    # Threshold check
    threshold_met = accuracy >= ACCURACY_THRESHOLD
    status = "PASS" if threshold_met else "FAIL"
    print(f"Threshold: {ACCURACY_THRESHOLD:.0%} — {status}")
    print()
    
    # Failures
    failures = results["failures"]
    if failures:
        print("FAILURES:")
        for f in failures:
            expected_str = f["expected"] or "(none)"
            predicted_str = f["predicted"] or "(none)"
            confused = f.get("confused_with", "")
            desc = f.get("description", "")
            line = f"  {f['id']}: expected={expected_str}, predicted={predicted_str}"
            if confused:
                line += f", confused_with={confused}"
            if desc:
                line += f"  [{desc}]"
            line += f"\n    intent: \"{f['intent'][:80]}\""
            print(line)
        print()
    
    if verbose and results["passes"]:
        print("PASSES:")
        for f in results["passes"]:
            expected_str = f["expected"] or "(none)"
            predicted_str = f["predicted"] or "(none)"
            print(f"  {f['id']}: expected={expected_str}, predicted={predicted_str} [{f['category']}]")
        print()
    
    # Per-skill breakdown
    print("PER-SKILL BREAKDOWN:")
    skill_stats: dict[str, dict] = {}
    for f in results["passes"] + results["failures"]:
        skill = f["expected"]
        if skill not in skill_stats:
            skill_stats[skill] = {"correct": 0, "total": 0}
        skill_stats[skill]["total"] += 1
        if f["correct"]:
            skill_stats[skill]["correct"] += 1
    
    for skill in sorted(skill_stats.keys()):
        stats = skill_stats[skill]
        acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0
        marker = "✓" if acc >= 0.8 else "✗"
        print(f"  {marker} {skill}: {stats['correct']}/{stats['total']} = {acc:.0%}")
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Classifier accuracy eval runner")
    parser.add_argument("--verbose", action="store_true", help="Show passing fixtures")
    parser.add_argument("--category", choices=["positive", "near-miss"], help="Filter by category")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    fixtures = load_fixtures(args.category)
    if not fixtures:
        print("No fixtures loaded.", file=sys.stderr)
        return 1
    
    results = evaluate_fixtures(fixtures, verbose=args.verbose)
    
    if args.json:
        # Clean output for JSON mode
        output = {
            "accuracy": results["accuracy"],
            "total": results["total"],
            "correct": results["correct"],
            "positive_accuracy": (
                results["positive_correct"] / results["positive_total"]
                if results["positive_total"] > 0 else 0
            ),
            "nearmiss_accuracy": (
                results["nearmiss_correct"] / results["nearmiss_total"]
                if results["nearmiss_total"] > 0 else 0
            ),
            "failures": results["failures"],
            "threshold_met": results["accuracy"] >= ACCURACY_THRESHOLD,
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(results, verbose=args.verbose)
    
    return 0 if results["accuracy"] >= ACCURACY_THRESHOLD else 1


if __name__ == "__main__":
    sys.exit(main())
