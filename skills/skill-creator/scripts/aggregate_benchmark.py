#!/usr/bin/env python3
"""Aggregate grading results from iteration workspace into benchmark.json.

Usage:
    python aggregate_benchmark.py <workspace_path>

Reads iteration-*/eval-*/grading.json files from the workspace,
along with optional metrics.json and timing.json from configuration subdirs,
and aggregates them into a single benchmark.json at the workspace root.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
from optimization_utils import load_json


def _parse_suffix(name: str, default: int = 0) -> int:
    """Parse numeric suffix from a directory name like 'iteration-1' or 'eval-3'."""
    parts = name.split("-")
    if len(parts) >= 2:
        try:
            return int(parts[1])
        except ValueError:
            pass
    return default


def discover_config_dirs(eval_dir: Path) -> list[tuple[str, Path]]:
    """Discover configuration subdirectories inside an eval directory.
    
    Looks for directories like 'with-skill', 'without-skill', etc.
    Returns list of (config_name, path) tuples.
    """
    configs = []
    for item in sorted(eval_dir.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
            # Convert directory name to configuration identifier
            config_name = item.name.replace("-", "_")
            configs.append((config_name, item))
    return configs


def extract_run_data(
    grading: dict,
    eval_id: int,
    eval_name: str,
    configuration: str,
    run_number: int,
    config_dir: Path | None = None,
) -> dict:
    """Extract a single run entry from grading data + optional metrics/timing."""
    summary = grading.get("summary", {})
    exec_metrics = grading.get("execution_metrics", {})
    timing_data = grading.get("timing", {})

    # Base result from grading.json
    result = {
        "pass_rate": summary.get("pass_rate", 0.0),
        "passed": summary.get("passed", 0),
        "failed": summary.get("failed", 0),
        "total": summary.get("total", 0),
        "time_seconds": timing_data.get("total_duration_seconds", 0.0),
        "tokens": 0,
        "tool_calls": exec_metrics.get("total_tool_calls", 0),
        "errors": exec_metrics.get("errors_encountered", 0),
    }

    # Augment from metrics.json if available in config dir
    if config_dir is not None:
        metrics_path = config_dir / "outputs" / "metrics.json"
        metrics = load_json(str(metrics_path))
        if metrics:
            result["tool_calls"] = metrics.get("total_tool_calls", result["tool_calls"])
            result["errors"] = metrics.get("errors_encountered", result["errors"])

        # Augment from timing.json
        timing_path = config_dir / "outputs" / "timing.json"
        timing = load_json(str(timing_path))
        if timing:
            result["tokens"] = timing.get("total_tokens", 0)
            if timing.get("total_duration_seconds"):
                result["time_seconds"] = timing["total_duration_seconds"]

    # Extract expectations
    expectations = [
        {
            "text": exp.get("text", ""),
            "passed": exp.get("passed", False),
            "evidence": exp.get("evidence", ""),
        }
        for exp in grading.get("expectations", [])
    ]

    # Extract notes from grading data
    notes = []
    user_notes = grading.get("user_notes_summary", {})
    for key in ("uncertainties", "needs_review", "workarounds"):
        notes.extend(user_notes.get(key, []))

    # Also capture eval_feedback suggestions as notes
    eval_feedback = grading.get("eval_feedback", {})
    suggestions = eval_feedback.get("suggestions", [])
    for s in suggestions:
        if isinstance(s, dict) and s.get("reason"):
            notes.append(s["reason"])
        elif isinstance(s, str):
            notes.append(s)
    overall = eval_feedback.get("overall")
    if overall:
        notes.append(overall)

    return {
        "eval_id": eval_id,
        "eval_name": eval_name,
        "configuration": configuration,
        "run_number": run_number,
        "result": result,
        "expectations": expectations,
        "notes": notes,
    }


def load_eval_names(workspace: Path) -> dict[int, str]:
    """Load eval names from evals.json if available."""
    evals_data = load_json(str(workspace / "evals.json"))
    if not evals_data:
        return {}
    names = {}
    for ev in evals_data.get("evals", []):
        eid = ev.get("id")
        name = ev.get("name", ev.get("prompt", "")[:50])
        if eid is not None:
            names[eid] = name
    return names


def discover_runs(workspace: Path) -> list[dict]:
    """Discover and aggregate all grading runs from the workspace."""
    runs = []
    eval_names = load_eval_names(workspace)

    # Find all iteration directories
    iteration_dirs = sorted(
        workspace.glob("iteration-*"),
        key=lambda p: _parse_suffix(p.name, 0),
    )

    for iter_dir in iteration_dirs:
        iter_num = _parse_suffix(iter_dir.name, 1)

        # Find all eval directories within iteration
        eval_dirs = sorted(
            iter_dir.glob("eval-*"),
            key=lambda p: _parse_suffix(p.name, 0),
        )

        for eval_dir in eval_dirs:
            eval_id = _parse_suffix(eval_dir.name, 0)
            eval_name = eval_names.get(eval_id, f"eval-{eval_id}")

            # Strategy 1: grading.json directly in eval dir (flat structure)
            grading_path = eval_dir / "grading.json"
            grading = load_json(str(grading_path))
            if grading:
                runs.append(
                    extract_run_data(
                        grading=grading,
                        eval_id=eval_id,
                        eval_name=eval_name,
                        configuration="with_skill",
                        run_number=iter_num,
                        config_dir=eval_dir,
                    )
                )
                continue

            # Strategy 2: config subdirs contain grading.json
            config_dirs = discover_config_dirs(eval_dir)
            for config_name, config_path in config_dirs:
                grading_path = config_path / "grading.json"
                grading = load_json(str(grading_path))
                if grading:
                    runs.append(
                        extract_run_data(
                            grading=grading,
                            eval_id=eval_id,
                            eval_name=eval_name,
                            configuration=config_name,
                            run_number=iter_num,
                            config_dir=config_path,
                        )
                    )

    return runs


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate grading results into benchmark.json"
    )
    parser.add_argument(
        "workspace_path",
        help="Path to the benchmark workspace directory",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace_path)
    if not workspace.is_dir():
        print(f"Error: {workspace} is not a directory", file=sys.stderr)
        return 1

    # Load skill metadata from evals.json if available
    evals_data = load_json(str(workspace / "evals.json"))
    skill_name = ""
    skill_path = ""
    if evals_data:
        skill_name = evals_data.get("skill_name", "")
        skill_path = evals_data.get("skill_path", "")

    # Fallback: derive skill_path from workspace location (up two levels)
    if not skill_path:
        skill_path = str(workspace.resolve().parent.parent)

    # Discover all runs
    runs = discover_runs(workspace)

    if not runs:
        print(f"Warning: No grading results found in {workspace}", file=sys.stderr)

    # Collect unique eval IDs that were run
    evals_run = sorted(set(r["eval_id"] for r in runs))

    # Build benchmark.json
    benchmark = {
        "metadata": {
            "skill_name": skill_name,
            "skill_path": skill_path,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evals_run": evals_run,
            "runs_per_configuration": (
                max(Counter(
                    (r["eval_id"], r["configuration"]) for r in runs
                ).values()) if runs else 0
            ),
        },
        "runs": runs,
    }

    # Write benchmark.json
    output_path = workspace / "benchmark.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(benchmark, f, indent=2, ensure_ascii=False)
    print(f"Aggregated {len(runs)} runs into {output_path}")
    print(f"Evals: {evals_run}")
    configs = sorted(set(r["configuration"] for r in runs))
    print(f"Configurations: {configs}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
