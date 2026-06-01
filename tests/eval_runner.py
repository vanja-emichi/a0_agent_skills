#!/usr/bin/env python3
"""Enforcement Settings Eval Runner — ON vs OFF comparison.

Reads eval fixtures from tests/eval_fixtures/skill-activation-evals.json
and compares enforcement pipeline behavior with settings ON vs OFF.

For each fixture, runs the simulated prefilter with each enforcement
setting enabled and disabled, then reports whether the setting changes
the recommended skill or candidate list.

Usage:
    cd /a0/usr/plugins/a0_agent_skills
    python tests/eval_runner.py
    python tests/eval_runner.py --setting phase_governance_enabled
    python tests/eval_runner.py --fixture eval-001

Output: JSON report to stdout with ON/OFF comparison for each fixture.
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

# Enforcement settings to compare ON vs OFF
ENFORCEMENT_SETTINGS = [
    "phase_governance_enabled",
    "skill_contracts_enabled",
    "skill_next_skill_hints",
    "skill_graph_validate_on_build",
]

# Phase ordering for governance filtering
_PHASE_ORDER = {"DEFINE": 0, "PLAN": 1, "BUILD": 2, "VERIFY": 3, "REVIEW": 4, "SHIP": 5}


# ---------------------------------------------------------------------------
# Simulated skill matching (from run_enforcement_evals.py)
#
# DRIFT WARNING: These patterns approximate what helpers.skill_match.search_skills()
# returns for each skill.  The real prefilter delegates to search_skills() which
# reads SKILL.md frontmatter — these regexes are a simplification.  If the eval
# runner starts disagreeing with real enforcement behavior, update patterns here
# or, ideally, refactor to import the real prefilter.
#
# A drift guard below asserts that _SIMULATED_SKILL_PATTERNS covers all skill
# directories found under skills/ — so new skills are never silently missing.
# ---------------------------------------------------------------------------

_SIMULATED_SKILL_PATTERNS: dict[str, dict] = {
    "spec-driven-development": {
        "keywords": [r"\b(spec|specification|new (?:project|feature|module|service))"],
        "anti_keywords": [r"\b(fix|debug|error|crash|list|print|show)\b"],
    },
    "test-driven-development": {
        "keywords": [r"\b(tests?|testing|TDD)\b", r"\b(implement|write|build)\b"],
        "anti_keywords": [r"\b(show|display|print|list)\b"],
    },
    "debugging-and-error-recovery": {
        "keywords": [r"\b(failing|error|crash|debug|fix)\b", r"\bbug\b"],
        "anti_keywords": [r"\b(create|write|design|set up)\b"],
    },
    "code-review-and-quality": {
        "keywords": [r"\b(review|audit|check)\b", r"\b(pull request|PR|code quality)\b"],
        "anti_keywords": [r"\b(list|count|show|display|find)\b"],
    },
    "planning-and-task-breakdown": {
        "keywords": [r"\bbreak\b.*\btasks?\b", r"\b(plan|planning|sprint)\b"],
        "anti_keywords": [r"\b(spec|specification)\b"],
    },
    "incremental-implementation": {
        "keywords": [r"\bimplement\b", r"\bPOST\b.*\bendpoint\b"],
        "anti_keywords": [r"\b(test|review|plan|spec)\b"],
    },
    "code-simplification": {
        "keywords": [r"\bsimplif\w+\b", r"\brefactor\b.*\bclean\w*\b"],
        "anti_keywords": [r"\b(pull request|PR)\b"],
    },
    "security-and-hardening": {
        "keywords": [r"\b(security|vulnerabilit\w+|OWASP)\b", r"\baudit\b.*\b(security|flaw)\b"],
        "anti_keywords": [r"\b(pull request|PR)\b"],
    },
    "performance-optimization": {
        "keywords": [r"\boptimize\b", r"\bslow\b", r"\b(latency|throughput)\b"],
        "anti_keywords": [r"\b(build|create|design)\b.*\b(component|UI)\b"],
    },
    "shipping-and-launch": {
        "keywords": [r"\bdeploy\b", r"\bproduction\b", r"\b(launch|ship|release)\b"],
        "anti_keywords": [r"\b(debug|fix|test|review)\b"],
    },
    "ci-cd-and-automation": {
        "keywords": [r"\bCI.?CD\b", r"\bpipeline\b", r"\b(automate|continuous integration)\b"],
        "anti_keywords": [r"\b(debug|review|build)\b"],
    },
    "git-workflow-and-versioning": {
        "keywords": [r"\bbranch\b", r"\bcommit\b", r"\b(version control|merge strategy)\b"],
        "anti_keywords": [r"\b(deploy|CI.?CD)\b"],
    },
    "documentation-and-adrs": {
        "keywords": [r"\bADR\b", r"\b(document|documentation)\b"],
        "anti_keywords": [r"\b(test|implement|build)\b"],
    },
    "deprecation-and-migration": {
        "keywords": [r"\bmigrate\b", r"\b(deprecate|deprecation)\b"],
        "anti_keywords": [r"\b(build new|create new)\b"],
    },
    "source-driven-development": {
        "keywords": [r"\bcheck\b.*\bdocs?\b", r"\b(official|latest)\b.*\b(docs|API)\b"],
        "anti_keywords": [r"\b(write|create|build)\b"],
    },
    "doubt-driven-development": {
        "keywords": [r"\bstress.?test\b", r"\badversarial\b", r"\bdoubt\b"],
        "anti_keywords": [r"\b(implement|build)\b"],
    },
    "frontend-ui-engineering": {
        "keywords": [r"\b(build|create)\b.*\b(component|form|UI|page)\b", r"\b(React|CSS|frontend)\b"],
        "anti_keywords": [r"\b(optimize|performance)\b"],
    },
    "api-and-interface-design": {
        "keywords": [r"\bdesign\b.*\bAPI\b", r"\bREST\b", r"\b(endpoint|OpenAPI)\b"],
        "anti_keywords": [r"\b(implement|build|test)\b"],
    },
    "browser-testing-with-devtools": {
        "keywords": [r"\btest\b.*\bbrowser\b", r"\bend.?to.?end\b", r"\b(E2E|Selenium|Playwright)\b"],
        "anti_keywords": [r"\b(unit test|write tests?)\b"],
    },
    "context-engineering": {
        "keywords": [r"\bmanage context\b", r"\bcontext\b.*\b(codebase|window)\b", r"\blarge codebase\b"],
        "anti_keywords": [r"\b(build|implement)\b"],
    },
    "interview-me": {
        "keywords": [r"\binterview\b", r"\bwhat\b.*\bI want\b", r"\bfigure out\b.*\b(user|wants?)\b"],
        "anti_keywords": [r"\b(refine|brainstorm|ideate)\b"],
    },
    "idea-refine": {
        "keywords": [r"\brefine\b.*\bidea\b", r"\b(brainstorm|ideate)\b", r"\bvague idea\b"],
        "anti_keywords": [r"\binterview\b", r"\bwhat\b.*\bI want\b"],
    },
    "using-agent-skills": {
        "keywords": [r"\bwhich skill\b", r"\bwhat skill\b", r"\bskill should\b"],
        "anti_keywords": [r"\b(deploy|ship|implement)\b"],
    },
}


# ---------------------------------------------------------------------------
# Drift guard: assert _SIMULATED_SKILL_PATTERNS covers all skill directories
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
    """Return list of skill dirs not covered by _SIMULATED_SKILL_PATTERNS."""
    known = set(_SIMULATED_SKILL_PATTERNS.keys())
    actual = _discover_skill_dirs()
    return sorted(actual - known)


# Fail fast at import time if new skills are missing from patterns.
_missing = _validate_pattern_coverage()
if _missing:
    print(
        f"WARNING: eval_runner _SIMULATED_SKILL_PATTERNS missing skills: "
        f"{_missing}.  Add patterns or the eval will not test these skills.",
        file=sys.stderr,
    )


def _make_candidate(name: str) -> SimpleNamespace:
    return SimpleNamespace(name=name, description=f"Skill: {name}")


def _simulated_prefilter(query: str) -> list[SimpleNamespace]:
    """Simulate prefilter_match using keyword patterns."""
    matches = []
    for skill_name, patterns in _SIMULATED_SKILL_PATTERNS.items():
        keyword_hit = any(
            re.search(p, query, re.IGNORECASE) for p in patterns["keywords"]
        )
        anti_hit = any(
            re.search(p, query, re.IGNORECASE) for p in patterns["anti_keywords"]
        )
        if keyword_hit and not anti_hit:
            matches.append(_make_candidate(skill_name))
    return matches


# ---------------------------------------------------------------------------
# Enforcement simulation
# ---------------------------------------------------------------------------

# Skill-to-phase mapping from contracts
_SKILL_PHASE_MAP = {
    "interview-me": "DEFINE",
    "spec-driven-development": "DEFINE",
    "idea-refine": "DEFINE",
    "planning-and-task-breakdown": "PLAN",
    "context-engineering": "PLAN",
    "incremental-implementation": "BUILD",
    "test-driven-development": "BUILD",
    "source-driven-development": "BUILD",
    "frontend-ui-engineering": "BUILD",
    "api-and-interface-design": "BUILD",
    "doubt-driven-development": "BUILD",
    "debugging-and-error-recovery": "VERIFY",
    "browser-testing-with-devtools": "VERIFY",
    "code-review-and-quality": "REVIEW",
    "code-simplification": "REVIEW",
    "security-and-hardening": "REVIEW",
    "performance-optimization": "REVIEW",
    "shipping-and-launch": "SHIP",
    "ci-cd-and-automation": "SHIP",
    "git-workflow-and-versioning": "SHIP",
    "documentation-and-adrs": "SHIP",
    "deprecation-and-migration": "SHIP",
}

# Next-skill chain from contracts
_NEXT_SKILL_MAP = {
    "interview-me": "spec-driven-development",
    "spec-driven-development": "planning-and-task-breakdown",
    "planning-and-task-breakdown": "incremental-implementation",
    "incremental-implementation": "test-driven-development",
    "test-driven-development": "debugging-and-error-recovery",
    "debugging-and-error-recovery": "code-review-and-quality",
    "code-review-and-quality": "shipping-and-launch",
}


def _apply_phase_governance(
    candidates: list[SimpleNamespace],
    current_phase: str | None,
    enabled: bool,
) -> list[SimpleNamespace]:
    """Simulate phase governance filtering."""
    if not enabled or not current_phase:
        return candidates

    current_idx = _PHASE_ORDER.get(current_phase, 0)
    expected = [
        name for name, phase in _SKILL_PHASE_MAP.items()
        if phase == current_phase
    ]

    # Filter: prefer candidates expected in current phase
    phase_match = [c for c in candidates if c.name in expected]
    return phase_match if phase_match else candidates


def _apply_contracts(
    candidates: list[SimpleNamespace],
    enabled: bool,
) -> tuple[list[SimpleNamespace], str | None]:
    """Simulate contract-aware next-skill hint."""
    if not enabled or not candidates:
        return candidates, None

    primary = candidates[0]
    next_skill = _NEXT_SKILL_MAP.get(primary.name)
    if next_skill:
        hint = f"After {primary.name}, consider loading {next_skill}"
        return candidates, hint
    return candidates, None


def _apply_graph_validation(enabled: bool) -> list[dict]:
    """Simulate graph validation — checks skill DAG for structural issues."""
    if not enabled:
        return []

    findings: list[dict] = []

    # Check for broken refs in next-skill chain
    all_skills = set(_NEXT_SKILL_MAP.keys()) | set(_NEXT_SKILL_MAP.values())
    all_skills |= set(_SKILL_PHASE_MAP.keys())
    for skill, next_skill in _NEXT_SKILL_MAP.items():
        if next_skill not in _SKILL_PHASE_MAP:
            findings.append({
                "type": "broken_ref",
                "details": f"{skill} references non-existent next_skill: {next_skill}",
            })

    # Check for skills not in any phase
    for skill in all_skills:
        if skill not in _SKILL_PHASE_MAP:
            findings.append({
                "type": "orphan",
                "details": f"{skill} not assigned to any phase",
            })

    return findings


def _run_enforcement_pipeline(
    intent: str,
    phase: str | None,
    settings: dict[str, bool],
) -> dict:
    """Run the simulated enforcement pipeline with given settings."""
    candidates = _simulated_prefilter(intent)

    if not candidates:
        return {
            "candidates": [],
            "top_candidate": None,
            "hint": None,
            "filtered": False,
            "graph_findings": [],
        }

    # Apply phase governance
    filtered = _apply_phase_governance(
        candidates, phase, settings.get("phase_governance_enabled", False)
    )
    was_filtered = len(filtered) < len(candidates)

    # Apply contracts
    result, hint = _apply_contracts(
        filtered, settings.get("skill_contracts_enabled", False)
    )

    # Apply graph validation
    graph_findings = _apply_graph_validation(
        settings.get("skill_graph_validate_on_build", False)
    )

    return {
        "candidates": [c.name for c in result],
        "top_candidate": result[0].name if result else None,
        "hint": hint,
        "filtered": was_filtered,
        "graph_findings": graph_findings,
    }


# ---------------------------------------------------------------------------
# Eval runner
# ---------------------------------------------------------------------------

def _load_fixtures(fixture_filter: str | None = None) -> list[dict]:
    """Load eval fixtures, optionally filtering by ID."""
    if not COMBINED_FIXTURE.is_file():
        print(f"Error: fixture file not found at {COMBINED_FIXTURE}", file=sys.stderr)
        sys.exit(1)

    with open(COMBINED_FIXTURE) as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: fixture file must contain a JSON array", file=sys.stderr)
        sys.exit(1)

    if fixture_filter:
        data = [d for d in data if fixture_filter in d.get("id", "")]

    return data


def run_comparison(
    fixtures: list[dict],
    setting_name: str | None = None,
) -> dict:
    """Run ON/OFF comparison for enforcement settings.

    Args:
        fixtures: List of eval fixture dicts.
        setting_name: If set, only compare this specific setting.

    Returns:
        Dict with comparison report.
    """
    settings_to_test = [setting_name] if setting_name else ENFORCEMENT_SETTINGS
    results = {
        "summary": {
            "total_fixtures": len(fixtures),
            "settings_tested": settings_to_test,
        },
        "comparisons": [],
    }

    for fixture in fixtures:
        fid = fixture.get("id", "unknown")
        intent = fixture.get("intent", "")
        expected = fixture.get("expected_skill", "")
        category = fixture.get("category", "")
        phase = fixture.get("phase")

        fixture_result = {
            "fixture_id": fid,
            "intent": intent,
            "expected_skill": expected,
            "category": category,
            "phase": phase,
            "setting_comparisons": [],
        }

        for setting in settings_to_test:
            # Run with setting OFF
            off_settings = {s: False for s in ENFORCEMENT_SETTINGS}
            off_result = _run_enforcement_pipeline(intent, phase, off_settings)

            # Run with setting ON
            on_settings = {s: False for s in ENFORCEMENT_SETTINGS}
            on_settings[setting] = True
            on_result = _run_enforcement_pipeline(intent, phase, on_settings)

            comparison = {
                "setting": setting,
                "off": off_result,
                "on": on_result,
                "behavior_changed": (
                    on_result["top_candidate"] != off_result["top_candidate"]
                    or on_result["hint"] != off_result["hint"]
                    or on_result["filtered"] != off_result["filtered"]
                    or on_result["graph_findings"] != off_result["graph_findings"]
                ),
            }
            fixture_result["setting_comparisons"].append(comparison)

        results["comparisons"].append(fixture_result)

    # Compute summary stats
    total_comparisons = 0
    changed_count = 0
    for comp in results["comparisons"]:
        for sc in comp["setting_comparisons"]:
            total_comparisons += 1
            if sc["behavior_changed"]:
                changed_count += 1

    results["summary"]["total_comparisons"] = total_comparisons
    results["summary"]["behavioral_changes"] = changed_count
    results["summary"]["change_rate"] = (
        round(changed_count / total_comparisons, 3) if total_comparisons else 0
    )

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Enforcement Settings Eval Runner — ON vs OFF comparison"
    )
    parser.add_argument(
        "--setting",
        choices=ENFORCEMENT_SETTINGS,
        help="Only test a specific setting",
    )
    parser.add_argument(
        "--fixture",
        help="Filter fixtures by ID substring",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of fixtures to test",
    )
    args = parser.parse_args()

    fixtures = _load_fixtures(args.fixture)

    if args.limit > 0:
        fixtures = fixtures[:args.limit]

    if not fixtures:
        print("No fixtures found.", file=sys.stderr)
        sys.exit(1)

    report = run_comparison(fixtures, args.setting)

    # Output JSON report
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
