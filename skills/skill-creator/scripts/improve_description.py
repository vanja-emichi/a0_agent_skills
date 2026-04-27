#!/usr/bin/env python3
"""Generate LLM-ready context for description improvement."""

import argparse
import json
import sys
from pathlib import Path

# Import from the same scripts directory
sys.path.insert(0, str(Path(__file__).resolve().parent))
from optimization_utils import load_json, extract_frontmatter_description




def generate_context(workspace: Path) -> dict:
    """Generate improve_context.json from workspace state."""
    history = load_json(workspace / "optimization_history.json")
    skill_path = Path(history["skill_path"])
    skill_content = (skill_path / "SKILL.md").read_text(encoding="utf-8")

    # Get latest iteration results
    iterations = history.get("iterations", [])
    latest = iterations[-1] if iterations else None

    # Identify failed triggers and false triggers
    if not latest:
        all_failures = []
    else:
        all_failures = [
            ft
            for key in ("train_results", "test_results")
            for ft in latest.get(key, {}).get("failed_triggers", [])
        ]
    failed_triggers = [ft for ft in all_failures if ft.get("should_trigger") and not ft.get("triggered")]
    false_triggers = [ft for ft in all_failures if not ft.get("should_trigger") and ft.get("triggered")]

    # Build scores summary
    scores = {}
    if latest:
        for key in ("train_results", "test_results"):
            r = latest.get(key, {})
            scores[key] = {
                "pass_rate": r.get("pass_rate", 0),
                "passed": r.get("passed", 0),
                "total": r.get("total", 0),
            }

    attempt_history = iterations[-5:]

    return {
        "current_description": history.get("current_description", ""),
        "scores_summary": scores,
        "failed_triggers": failed_triggers,
        "false_triggers": false_triggers,
        "attempt_history": [
            {
                "iteration": a.get("iteration"),
                "description": a.get("description"),
                "train_pass_rate": a.get("train_results", {}).get("pass_rate"),
                "test_pass_rate": a.get("test_results", {}).get("pass_rate"),
            }
            for a in attempt_history
        ],
        "skill_content": skill_content[:5000],  # Truncate to manage context size
        "constraints": {
            "char_limit": 1024,
            "imperative_phrasing": True,
            "intent_focused": True,
            "tips": [
                "Use 'Use this skill for...' phrasing",
                "Focus on user intent, not implementation details",
                "Generalize from failures to broader categories",
                "Do not create an ever-expanding list of specific queries",
            ],
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate LLM-ready context for description improvement"
    )
    parser.add_argument(
        "workspace",
        help="Path to optimization workspace directory",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    context = generate_context(workspace)

    output_path = workspace / "improve_context.json"
    output_path.write_text(
        json.dumps(context, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Context written to {output_path}")


if __name__ == "__main__":
    main()
