#!/usr/bin/env python3
"""Optimization orchestrator — manages iteration loop for skill description optimization."""

import argparse
import json
import sys
from pathlib import Path

# Ensure sibling modules are importable
sys.path.insert(0, str(Path(__file__).resolve().parent))
from optimization_utils import split_evals, load_json, extract_frontmatter_description


def save_json(path: Path, data: dict) -> None:
    """Save JSON file with pretty printing."""
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _normalize_eval_list(data) -> list[dict]:
    """Normalize eval data to a list, handling both list and dict with 'evals' key."""
    if isinstance(data, list):
        return data
    return data.get("evals", []) if isinstance(data, dict) else []


def _summarize_results(results: list[dict]) -> dict:
    """Compute pass rate and collect failed triggers from result entries."""
    passed = sum(1 for r in results if r["should_trigger"] == r["triggered"])
    total = len(results)
    pass_rate = passed / total if total > 0 else 0.0
    failed_triggers = [
        {"query": r["query"], "should_trigger": r["should_trigger"], "triggered": r["triggered"]}
        for r in results if r["should_trigger"] != r["triggered"]
    ]
    return {
        "pass_rate": round(pass_rate, 4),
        "passed": passed,
        "total": total,
        "failed_triggers": failed_triggers,
    }

def cmd_init(args: argparse.Namespace) -> None:
    """Initialize workspace with train/test split and history."""
    skill_path = Path(args.skill_path).resolve()
    evals_path = Path(args.evals_path).resolve()
    workspace = Path(args.workspace).resolve() if args.workspace else None

    if workspace is None:
        workspace = skill_path.parent / "optimization_workspace"

    workspace.mkdir(parents=True, exist_ok=True)

    # Read evals
    evals = _normalize_eval_list(load_json(evals_path))

    # Split using optimization_utils
    train, test = split_evals(evals)
    # Save splits as plain lists
    save_json(workspace / "train_evals.json", train)
    save_json(workspace / "test_evals.json", test)

    # Extract description from SKILL.md
    description = extract_frontmatter_description(skill_path)

    # Create optimization history
    history = {
        "skill_path": str(skill_path),
        "original_description": description,
        "current_description": description,
        "iterations": [],
        "max_iterations": 5,
    }
    save_json(workspace / "optimization_history.json", history)

    print(f"Workspace initialized at {workspace}")
    print(f"  Train evals: {len(train)}")
    print(f"  Test evals: {len(test)}")
    print(f"  Original description: {description[:80]}...")


def _compute_results(result_items: list[dict], train_queries: set, test_queries: set) -> tuple[dict, dict]:
    """Separate results into train/test and compute pass rates."""
    train_results = []
    test_results = []

    for r in result_items:
        query = r.get("query", "")
        should_trigger = r.get("should_trigger", False)
        triggered = r.get("triggered", False)
        entry = {
            "query": query,
            "should_trigger": should_trigger,
            "triggered": triggered,
        }
        if query in test_queries:
            test_results.append(entry)
        else:
            train_results.append(entry)

    return _summarize_results(train_results), _summarize_results(test_results)


def cmd_record_results(args: argparse.Namespace) -> None:
    """Record evaluation results from stdin JSON."""
    workspace = Path(args.workspace).resolve()
    history = load_json(workspace / "optimization_history.json")

    # Read train/test query sets for splitting
    train_data = load_json(workspace / "train_evals.json")
    test_data = load_json(workspace / "test_evals.json")
    train_queries = {e["query"] for e in _normalize_eval_list(train_data)}
    test_queries = {e["query"] for e in _normalize_eval_list(test_data)}

    # Read stdin
    stdin_raw = sys.stdin.read(10 * 1024 * 1024)  # 10MB cap
    stdin_data = json.loads(stdin_raw)
    iteration_num = stdin_data["iteration"]
    description = stdin_data.get("description", history.get("current_description", ""))
    results = stdin_data.get("results", [])

    # Compute train/test results
    train_results, test_results = _compute_results(results, train_queries, test_queries)

    # Determine status
    overall_pass = (
        train_results["pass_rate"] == 1.0 and test_results["pass_rate"] == 1.0
    )
    status = "passed" if overall_pass else "needs_improvement"

    # Build iteration entry
    iteration_entry = {
        "iteration": iteration_num,
        "description": description,
        "train_results": train_results,
        "test_results": test_results,
        "status": status,
    }

    # Update or append iteration
    match_idx = next(
        (i for i, it in enumerate(history["iterations"]) if it["iteration"] == iteration_num),
        None,
    )
    if match_idx is not None:
        history["iterations"][match_idx] = iteration_entry
    else:
        history["iterations"].append(iteration_entry)

    # Update current description
    history["current_description"] = description

    save_json(workspace / "optimization_history.json", history)
    print(f"Recorded iteration {iteration_num}: status={status}")
    print(f"  Train: {train_results['passed']}/{train_results['total']} ({train_results['pass_rate']:.1%})")
    print(f"  Test:  {test_results['passed']}/{test_results['total']} ({test_results['pass_rate']:.1%})")


def cmd_iteration_status(args: argparse.Namespace) -> None:
    """Print current iteration status."""
    workspace = Path(args.workspace).resolve()
    history = load_json(workspace / "optimization_history.json")

    iterations = history.get("iterations", [])
    if not iterations:
        print("No iterations recorded yet.")
        return

    latest = iterations[-1]
    print(f"Iteration: {latest['iteration']}")
    print(f"Description: {latest.get('description', 'N/A')[:80]}")

    tr = latest.get("train_results", {})
    te = latest.get("test_results", {})
    print(f"Train pass rate: {tr.get('passed', 0)}/{tr.get('total', 0)} ({tr.get('pass_rate', 0):.1%})")
    print(f"Test pass rate:  {te.get('passed', 0)}/{te.get('total', 0)} ({te.get('pass_rate', 0):.1%})")
    print(f"Status: {latest.get('status', 'unknown')}")

    # Failed triggers
    all_failed = [
        ft
        for key in ("train_results", "test_results")
        for ft in latest.get(key, {}).get("failed_triggers", [])
    ]
    if all_failed:
        print(f"Failed triggers ({len(all_failed)}):")
        for ft in all_failed:
            print(f"  - [{ft.get('query', '?')}] should_trigger={ft.get('should_trigger')}, triggered={ft.get('triggered')}")


def cmd_select_best(args: argparse.Namespace) -> None:
    """Select best description across iterations by test score."""
    workspace = Path(args.workspace).resolve()
    history = load_json(workspace / "optimization_history.json")

    iterations = history.get("iterations", [])
    if not iterations:
        print("No iterations recorded.")
        return

    best = None
    best_score = -1.0
    for it in iterations:
        # Prefer test score, fall back to train score
        score = it.get("test_results", {}).get("pass_rate")
        if score is None:
            score = it.get("train_results", {}).get("pass_rate", 0.0)
        if score > best_score:
            best_score = score
            best = it

    if best:
        print(f"Best iteration: {best['iteration']}")
        print(f"Description: {best.get('description', 'N/A')}")
        print(f"Test score:  {best.get('test_results', {}).get('pass_rate', 0.0):.1%}")
        print(f"Train score: {best.get('train_results', {}).get('pass_rate', 0.0):.1%}")


def cmd_report(args: argparse.Namespace) -> None:
    """Generate optimization_report.md."""
    workspace = Path(args.workspace).resolve()
    history = load_json(workspace / "optimization_history.json")

    lines = []
    lines.append("# Optimization Report")
    lines.append("")
    lines.append(f"**Skill**: {history.get('skill_path', 'N/A')}")
    lines.append(f"**Original description**: {history.get('original_description', 'N/A')}")
    lines.append(f"**Current description**: {history.get('current_description', 'N/A')}")
    lines.append("")

    iterations = history.get("iterations", [])
    if iterations:
        lines.append("| Iteration | Description | Train Score | Test Score | Status |")
        lines.append("|-----------|-------------|-------------|------------|--------|")
        for it in iterations:
            desc = it.get("description", "N/A")[:40]
            train_score = f"{it.get('train_results', {}).get('pass_rate', 0.0):.1%}"
            test_score = f"{it.get('test_results', {}).get('pass_rate', 0.0):.1%}"
            status = it.get("status", "unknown")
            lines.append(f"| {it['iteration']} | {desc} | {train_score} | {test_score} | {status} |")
        lines.append("")
    else:
        lines.append("No iterations recorded.")
        lines.append("")

    report_path = workspace / "optimization_report.md"
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report written to {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Optimization orchestrator")
    subparsers = parser.add_subparsers(dest="command")

    # init
    init_parser = subparsers.add_parser("init", help="Initialize workspace")
    init_parser.add_argument("skill_path", help="Path to skill directory")
    init_parser.add_argument("evals_path", help="Path to evals.json")
    init_parser.add_argument("--workspace", help="Workspace directory")
    init_parser.set_defaults(func=cmd_init)

    # record-results
    record_parser = subparsers.add_parser("record-results", help="Record eval results")
    record_parser.add_argument("workspace", help="Workspace directory")
    record_parser.set_defaults(func=cmd_record_results)

    # iteration-status
    status_parser = subparsers.add_parser("iteration-status", help="Show current status")
    status_parser.add_argument("workspace", help="Workspace directory")
    status_parser.set_defaults(func=cmd_iteration_status)

    # select-best
    best_parser = subparsers.add_parser("select-best", help="Select best description")
    best_parser.add_argument("workspace", help="Workspace directory")
    best_parser.set_defaults(func=cmd_select_best)

    # report
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("workspace", help="Workspace directory")
    report_parser.set_defaults(func=cmd_report)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
