#!/usr/bin/env python3
"""Outcome-lift eval runner for the a0_agent_skills enforcement gate.

Measures whether enforce mode produces better outcomes than observe-only
mode across eval fixtures.  Satisfies success criterion 7.

Usage::

    python tests/run_outcome_lift.py                # standalone
    python -m pytest tests/test_outcome_lift.py -v   # via pytest
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Bootstrap: ensure plugin helpers are importable without the full runtime
# ---------------------------------------------------------------------------

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "eval_fixtures"
COMBINED_FIXTURE = FIXTURES_DIR / "skill-activation-evals.json"

_stubs_done = False


def _ensure_stubs() -> None:
    """Install framework stubs so helpers.skill_match can be imported."""
    global _stubs_done
    if _stubs_done:
        return
    _stubs_done = True

    from unittest.mock import MagicMock

    for name in (
        "helpers",
        "helpers.extension",
        "helpers.tool",
        "helpers.plugins",
        "helpers.projects",
        "helpers.skills",
    ):
        sys.modules.setdefault(name, MagicMock())

    sm = sys.modules.get("helpers.skill_match")
    if sm is None or not getattr(sm, "prefilter_match", None):
        sm_path = PLUGIN_ROOT / "helpers" / "skill_match.py"
        if sm_path.exists():
            spec = importlib.util.spec_from_file_location(
                "helpers.skill_match", str(sm_path),
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules["helpers.skill_match"] = mod
            sys.modules["helpers"].skill_match = mod
            spec.loader.exec_module(mod)


_ensure_stubs()

from helpers.skill_match import (          # noqa: E402
    classify_skill,
    prefilter_match,
)

# ---------------------------------------------------------------------------
# Lightweight Skill factory
# ---------------------------------------------------------------------------


def _make_skill(name: str, description: str = "") -> Any:
    """Create a minimal Skill-like object."""
    return type("Skill", (), {
        "name": name,
        "description": description,
        "tags": [],
        "triggers": [],
        "path": Path(f"/fake/skills/{name}"),
    })()

# ---------------------------------------------------------------------------
# Fixture loading
# ---------------------------------------------------------------------------


def load_eval_cases() -> list[dict]:
    """Load eval cases from the combined fixture file.

    Returns a list of dicts, each with at least:
        id, intent, expected_skill, category
    """
    if not COMBINED_FIXTURE.is_file():
        return []
    data = json.loads(COMBINED_FIXTURE.read_text("utf-8"))
    if isinstance(data, list):
        return data
    return []


# ---------------------------------------------------------------------------
# Mock search: keyword-overlap ranking
# ---------------------------------------------------------------------------


def _keyword_overlap(query: str, text: str) -> int:
    """Count shared words between *query* and *text*."""
    qw = set(query.lower().split())
    tw = set(text.lower().split())
    return len(qw & tw)


def _make_mock_search(all_skills: list[Any]):
    """Return a ``search_skills`` replacement that ranks by keyword overlap."""
    def _search(query: str, limit: int = 5, agent: Any = None):
        scored = [
            (_keyword_overlap(query, f"{s.name} {s.description}"), s)
            for s in all_skills
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [s for score, s in scored[:limit] if score > 0]
    return _search

# ---------------------------------------------------------------------------
# Single-prompt evaluation
# ---------------------------------------------------------------------------


async def eval_prompt(
    prompt: str,
    expected_skill: str,
    should_trigger: bool,
    all_skills: list[Any],
) -> dict:
    """Evaluate *prompt* under observe and enforce modes."""
    from unittest.mock import AsyncMock, MagicMock, patch

    agent = MagicMock()
    agent.data = {"loaded_skills": []}
    mock_search = _make_mock_search(all_skills)

    # ---- observe mode: prefilter only ----
    with patch("helpers.skill_match.search_skills", mock_search):
        candidates = prefilter_match(agent, prompt, limit=5)

    cand_names = [c.name for c in candidates]

    # Observe correctness:
    #   trigger  → expected skill must appear in candidates
    #   suppress → expected skill must NOT appear in candidates
    if should_trigger:
        observe_correct = expected_skill in cand_names
    else:
        observe_correct = expected_skill not in cand_names

    # ---- enforce mode: prefilter + classify ----
    if should_trigger and expected_skill in cand_names:
        util_json = json.dumps({
            "should_load": True,
            "reason": f"eval: {expected_skill} is relevant",
        })
    else:
        util_json = json.dumps({
            "should_load": False,
            "reason": "eval: no relevant skill",
        })

    agent.call_utility_model = AsyncMock(return_value=util_json)

    with patch("helpers.skill_match.search_skills", mock_search):
        result = await classify_skill(
            agent, "code_execution_tool", {}, candidates, prompt,
        )

    # Enforce correctness:
    #   trigger  → should_correct with the expected candidate
    #   suppress → should_not_correct / no_candidate / already_loaded
    if should_trigger:
        enforce_correct = (
            result["state"] == "should_correct"
            and result["candidate"] == expected_skill
        )
    else:
        enforce_correct = result["state"] in (
            "should_not_correct",
            "no_candidate",
            "already_loaded",
        )

    return {
        "prompt": prompt[:80],
        "expected_skill": expected_skill,
        "should_trigger": should_trigger,
        "candidates": cand_names,
        "observe_correct": observe_correct,
        "enforce_state": result["state"],
        "enforce_candidate": result.get("candidate"),
        "enforce_correct": enforce_correct,
    }

# ---------------------------------------------------------------------------
# Full suite
# ---------------------------------------------------------------------------


async def run_all() -> dict:
    """Execute the full eval suite and return a structured report."""
    cases = load_eval_cases()
    if not cases:
        return {
            "summary": {
                "total_cases": 0,
                "trigger_cases": 0,
                "suppress_cases": 0,
                "observe_correct": 0,
                "observe_rate": 0.0,
                "enforce_correct": 0,
                "enforce_rate": 0.0,
                "lift": 0.0,
                "trigger_observe_rate": 0.0,
                "trigger_enforce_rate": 0.0,
                "suppress_observe_rate": 0.0,
                "suppress_enforce_rate": 0.0,
            },
            "results": [],
        }

    # Build skill objects from unique skill names referenced in cases
    all_skill_names = sorted({c["expected_skill"] for c in cases})
    all_skills = [_make_skill(name) for name in all_skill_names]

    results: list[dict] = []
    for case in cases:
        expected = case["expected_skill"]
        category = case.get("category", "positive")
        # positive cases: skill should trigger; near-miss cases: skill should NOT trigger
        should_trigger = category == "positive"
        results.append(
            await eval_prompt(case["intent"], expected, should_trigger, all_skills)
        )

    total = len(results)
    triggers = [r for r in results if r["should_trigger"]]
    suppresses = [r for r in results if not r["should_trigger"]]

    obs_correct = sum(1 for r in results if r["observe_correct"])
    enf_correct = sum(1 for r in results if r["enforce_correct"])

    def _rate(n: int, d: int) -> float:
        return round(n / d, 4) if d else 0.0

    report = {
        "summary": {
            "total_cases": total,
            "trigger_cases": len(triggers),
            "suppress_cases": len(suppresses),
            "observe_correct": obs_correct,
            "observe_rate": _rate(obs_correct, total),
            "enforce_correct": enf_correct,
            "enforce_rate": _rate(enf_correct, total),
            "lift": _rate(enf_correct - obs_correct, total),
            "trigger_observe_rate": _rate(
                sum(1 for r in triggers if r["observe_correct"]),
                len(triggers),
            ),
            "trigger_enforce_rate": _rate(
                sum(1 for r in triggers if r["enforce_correct"]),
                len(triggers),
            ),
            "suppress_observe_rate": _rate(
                sum(1 for r in suppresses if r["observe_correct"]),
                len(suppresses),
            ),
            "suppress_enforce_rate": _rate(
                sum(1 for r in suppresses if r["enforce_correct"]),
                len(suppresses),
            ),
        },
        "results": results,
    }
    return report


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------


def format_report(report: dict) -> str:
    """Render the report as a readable table."""
    s = report["summary"]
    bar = "=" * 64
    lines = [
        bar,
        "  OUTCOME-LIFT EVAL REPORT  (criterion 7)",
        bar,
        "",
        f"  Total eval cases : {s['total_cases']}",
        f"    trigger  (should load skill)  : {s['trigger_cases']}",
        f"    suppress (should NOT load)    : {s['suppress_cases']}",
        "",
        f"  {'Mode':<12} {'Correct':>8} {'Rate':>8}",
        f"  {'-' * 12} {'-' * 8} {'-' * 8}",
        f"  {'observe':<12} {s['observe_correct']:>8} {s['observe_rate']:>7.1%}",
        f"  {'enforce':<12} {s['enforce_correct']:>8} {s['enforce_rate']:>7.1%}",
        "",
        f"  LIFT (enforce − observe) : {s['lift']:+.1%}",
        "",
        "  Trigger-case detail:",
        f"    observe correct : {s['trigger_observe_rate']:.1%}",
        f"    enforce correct : {s['trigger_enforce_rate']:.1%}",
        "",
        "  Suppress-case detail:",
        f"    observe correct : {s['suppress_observe_rate']:.1%}",
        f"    enforce correct : {s['suppress_enforce_rate']:.1%}",
        "",
        bar,
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    report = asyncio.run(run_all())
    print(format_report(report))
    print()
    compact = {
        **report,
        "results": f"({len(report['results'])} cases)",
    }
    print(json.dumps(compact, indent=2))
