#!/usr/bin/env python3
"""Generate formatted markdown review from benchmark.json.

Usage:
    python generate_review.py <workspace_path>

Reads benchmark.json from the workspace directory and outputs
a formatted markdown review to stdout.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from optimization_utils import load_json


def _safe_avg(values: list[float]) -> float:
    """Return average of values, or 0 if empty."""
    return sum(values) / len(values) if values else 0


def fmt_pct(value: float) -> str:
    """Format a float as a percentage string."""
    if value is None:
        return "N/A"
    return f"{value * 100:.0f}%"

def fmt_num(value) -> str:
    """Format a number with reasonable precision."""
    if value is None:
        return "N/A"
    if isinstance(value, float):
        if value >= 100:
            return f"{value:.0f}"
        return f"{value:.1f}"
    return str(value)


def generate_review(benchmark: dict) -> str:
    """Generate markdown review from benchmark data."""
    lines = []
    metadata = benchmark.get("metadata", {})
    runs = benchmark.get("runs", [])

    # Header
    skill_name = metadata.get("skill_name", "unknown")
    timestamp = metadata.get("timestamp", "N/A")
    lines.append(f"# Benchmark Review: {skill_name}")
    lines.append(f"Date: {timestamp}")
    lines.append("")

    if not runs:
        lines.append("No runs found in benchmark.")
        return "\n".join(lines)

    # --- Summary table: aggregate by configuration ---
    config_stats = defaultdict(lambda: {"pass_rates": [], "times": [], "tokens": []})
    for run in runs:
        config = run.get("configuration", "unknown")
        result = run.get("result", {})
        if result.get("pass_rate") is not None:
            config_stats[config]["pass_rates"].append(result["pass_rate"])
        if result.get("time_seconds") is not None:
            config_stats[config]["times"].append(result["time_seconds"])
        if result.get("tokens") is not None:
            config_stats[config]["tokens"].append(result["tokens"])

    lines.append("## Summary")
    lines.append("| Configuration | Avg Pass Rate | Avg Time (s) | Avg Tokens |")
    lines.append("|---|---|---|---|")
    for config in sorted(config_stats.keys()):
        stats = config_stats[config]
        avg_pr = _safe_avg(stats["pass_rates"])
        avg_time = _safe_avg(stats["times"])
        avg_tokens = _safe_avg(stats["tokens"])
        lines.append(
            f"| {config} | {fmt_pct(avg_pr)} | {fmt_num(avg_time)} | {fmt_num(avg_tokens)} |"
        )
    lines.append("")

    # --- Per-Eval Results table ---
    lines.append("## Per-Eval Results")
    lines.append("| Eval | Name | Config | Pass Rate | Passed/Total |")
    lines.append("|---|---|---|---|---|")
    for run in runs:
        eval_id = run.get("eval_id", "?")
        eval_name = run.get("eval_name", "")
        config = run.get("configuration", "unknown")
        result = run.get("result", {})
        pass_rate = result.get("pass_rate", 0)
        passed = result.get("passed", 0)
        total = result.get("total", 0)
        lines.append(
            f"| {eval_id} | {eval_name} | {config} | {fmt_pct(pass_rate)} "
            f"| {passed}/{total} |"
        )
    lines.append("")

    # Deduplicated notes preserving first-seen order
    seen_notes = set()
    all_notes = []
    for run in runs:
        for note in run.get("notes", []):
            if note and note not in seen_notes:
                seen_notes.add(note)
                all_notes.append(note)
    if all_notes:
        lines.append("## Notes")
        for note in all_notes:
            lines.append(f"- {note}")
        lines.append("")

    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <workspace_path>", file=sys.stderr)
        sys.exit(1)

    workspace = Path(sys.argv[1])
    benchmark_path = workspace / "benchmark.json"

    benchmark = load_json(str(benchmark_path))
    if benchmark is None:
        print(
            f"Error: Could not load benchmark.json from {benchmark_path}",
            file=sys.stderr,
        )
        sys.exit(1)

    review = generate_review(benchmark)
    print(review)
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate markdown review from benchmark data")
    parser.add_argument("workspace", help="Path to workspace/iteration-N directory")
    parser.add_argument("--output", "-o", help="Output file path (default: stdout)")
    args = parser.parse_args()
    workspace = Path(args.workspace)
    output_file = Path(args.output) if args.output else None
    sys.exit(main(workspace, output_file))
