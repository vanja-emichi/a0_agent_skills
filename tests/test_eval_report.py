"""Eval report: reads latest eval iteration, verifies data integrity, outputs summary.

This is a structural test — no live server needed.
It reads eval-workspace/iteration-<N>/benchmark.json files from the source project.
"""

import json
import os

import pytest

# The eval workspace lives in the source project — derive path relative to this test file
# tests/ → plugin dir → plugins/ → usr/ → then into projects/a0_agent_skills
_SOURCE_PROJECT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "projects", "a0_agent_skills")
)
EVAL_WORKSPACE = os.environ.get(
    "EVAL_WORKSPACE",
    os.path.join(_SOURCE_PROJECT, "eval-workspace"),
)


def _find_best_iteration():
    """Find the highest iteration number in eval-workspace."""
    if not os.path.isdir(EVAL_WORKSPACE):
        pytest.skip(f"Eval workspace not found at {EVAL_WORKSPACE}")

    iterations = []
    for name in os.listdir(EVAL_WORKSPACE):
        if name.startswith("iteration-"):
            try:
                num = int(name.split("-")[1])
                iterations.append((num, os.path.join(EVAL_WORKSPACE, name)))
            except (ValueError, IndexError):
                continue

    if not iterations:
        pytest.skip("No eval iterations found")

    iterations.sort(reverse=True)
    return iterations[0]  # (num, path)


def _find_best_iteration():
    """Find the iteration with the most evaluated skills."""
    if not os.path.isdir(EVAL_WORKSPACE):
        pytest.skip(f"Eval workspace not found at {EVAL_WORKSPACE}")

    best_num = 0
    best_path = None
    best_count = 0

    for name in os.listdir(EVAL_WORKSPACE):
        if not name.startswith("iteration-"):
            continue
        try:
            num = int(name.split("-")[1])
        except (ValueError, IndexError):
            continue
        path = os.path.join(EVAL_WORKSPACE, name)
        count = len(_read_benchmarks(path))
        if count > best_count:
            best_count = count
            best_num = num
            best_path = path

    if best_path is None:
        pytest.skip("No eval iterations with benchmarks found")

    return best_num, best_path


def _normalize_benchmark(data):
    """Normalize benchmark.json to flat pass rates.

    Handles the agent-skills-eval format:
    {
      "run_summary": {
        "with_skill": {"pass_rate": {"mean": X}},
        "without_skill": {"pass_rate": {"mean": Y}},
        "delta": {"pass_rate": Z}
      }
    }
    """
    rs = data.get("run_summary", {})

    with_rate = rs.get("with_skill", {}).get("pass_rate", {})
    without_rate = rs.get("without_skill", {}).get("pass_rate", {})
    delta_rate = rs.get("delta", {}).get("pass_rate", 0)

    # pass_rate can be a number (0-1) or a dict with mean/stddev
    if isinstance(with_rate, dict):
        with_val = with_rate.get("mean", 0) * 100
    else:
        with_val = with_rate * 100 if with_rate <= 1 else with_rate

    if isinstance(without_rate, dict):
        without_val = without_rate.get("mean", 0) * 100
    else:
        without_val = without_rate * 100 if without_rate <= 1 else without_rate

    delta_val = delta_rate * 100 if abs(delta_rate) <= 1 else delta_rate

    return {
        "with_skill_pass_rate": round(with_val, 1),
        "without_skill_pass_rate": round(without_val, 1),
        "delta_pass_rate": round(delta_val, 1),
    }


def _read_benchmarks(iter_dir):
    """Read all benchmark.json files from an iteration directory.

    Handles two structures:
    - Full run: <iteration>/<skill-name>/benchmark.json
    - Single skill: <iteration>/benchmark.json (root level)

    Returns normalized flat pass-rate dicts.
    """
    results = []

    # Check for root-level benchmark.json (single-skill run)
    root_bench = os.path.join(iter_dir, "benchmark.json")
    if os.path.isfile(root_bench):
        with open(root_bench) as f:
            data = json.load(f)
        meta_path = os.path.join(iter_dir, "meta.json")
        if os.path.isfile(meta_path):
            with open(meta_path) as f:
                meta = json.load(f)
            skill_name = meta.get("skill", "unknown")
        else:
            skill_name = "unknown"
        results.append((skill_name, _normalize_benchmark(data)))

    # Check for skill-named subdirectories (full run)
    for entry in sorted(os.listdir(iter_dir)):
        entry_path = os.path.join(iter_dir, entry)
        if not os.path.isdir(entry_path):
            continue
        if entry.startswith("eval-") or entry == "report":
            continue
        bench_path = os.path.join(entry_path, "benchmark.json")
        if not os.path.isfile(bench_path):
            continue
        with open(bench_path) as f:
            data = json.load(f)
        results.append((entry, _normalize_benchmark(data)))

    return results


# --- Task 1: Discovery ---

class TestDiscovery:
    """Verify we can find and read eval iterations."""

    def test_finds_latest_iteration(self):
        num, path = _find_best_iteration()
        assert num > 0, "Iteration number should be positive"
        assert os.path.isdir(path), f"Iteration path {path} should exist"
        print(f"\nLatest iteration: {num} at {path}")

    def test_latest_iteration_has_benchmarks(self):
        num, path = _find_best_iteration()
        benchmarks = _read_benchmarks(path)
        assert len(benchmarks) > 0, "Latest iteration should have at least one benchmark"
        print(f"\nFound {len(benchmarks)} benchmarks in iteration {num}")


# --- Task 2: Data integrity ---

class TestDataIntegrity:
    """Verify benchmark.json structure and calculations."""

    REQUIRED_KEYS = ["with_skill_pass_rate", "without_skill_pass_rate", "delta_pass_rate"]

    def test_benchmarks_have_required_keys(self):
        _, path = _find_best_iteration()
        for skill_name, data in _read_benchmarks(path):
            for key in self.REQUIRED_KEYS:
                assert key in data, f"{skill_name} missing key: {key}"

    def test_pass_rates_are_percentages(self):
        _, path = _find_best_iteration()
        for skill_name, data in _read_benchmarks(path):
            for key in ["with_skill_pass_rate", "without_skill_pass_rate"]:
                val = data[key]
                assert 0 <= val <= 100, (
                    f"{skill_name}.{key} = {val}, expected 0-100"
                )

    def test_deltas_are_correct(self):
        _, path = _find_best_iteration()
        for skill_name, data in _read_benchmarks(path):
            expected_delta = round(
                data["with_skill_pass_rate"] - data["without_skill_pass_rate"],
                1,
            )
            actual_delta = data["delta_pass_rate"]
            assert abs(actual_delta - expected_delta) < 0.2, (
                f"{skill_name}: expected delta {expected_delta}, got {actual_delta}"
            )


# --- Task 3: Summary generation ---

class TestSummaryReport:
    """Generate and verify a markdown summary table."""

    def test_generates_summary_table(self):
        num, path = _find_best_iteration()
        benchmarks = _read_benchmarks(path)

        # Build table
        lines = []
        lines.append(f"\n## Eval Report — Iteration {num}")
        lines.append("")
        lines.append("| Skill | With | Without | Delta | Verdict |")
        lines.append("|---|---|---|---|---|")

        positive = 0
        zero = 0
        negative = 0
        total_delta = 0.0

        for skill_name, data in sorted(benchmarks, key=lambda x: -x[1]["delta_pass_rate"]):
            with_p = data["with_skill_pass_rate"]
            without_p = data["without_skill_pass_rate"]
            delta = data["delta_pass_rate"]
            total_delta += delta

            if delta > 0:
                verdict = "✅"
                positive += 1
            elif delta < 0:
                verdict = "❌"
                negative += 1
            else:
                verdict = "⚠️"
                zero += 1

            lines.append(
                f"| {skill_name} | {with_p:.1f}% | {without_p:.1f}% | "
                f"{delta:+.1f}pp | {verdict} |"
            )

        avg_delta = total_delta / len(benchmarks) if benchmarks else 0
        lines.append("")
        lines.append(f"**Skills: {len(benchmarks)} | "
                     f"Positive: {positive} | Zero: {zero} | "
                     f"Negative: {negative} | Avg delta: {avg_delta:+.1f}pp**")

        report = "\n".join(lines)
        print(report)

        # Verify the report is valid
        assert len(benchmarks) > 0
        assert "| Skill |" in report
        assert len(lines) > 5  # header + at least a few rows


# --- Task 4: Quality assertions ---

class TestQualityThresholds:
    """Verify quality thresholds across all evaluated skills."""

    def test_majority_of_skills_have_positive_lift(self):
        _, path = _find_best_iteration()
        benchmarks = _read_benchmarks(path)
        assert len(benchmarks) >= 5, f"Need >=5 skills for meaningful report, found {len(benchmarks)}"
        positive = sum(1 for _, d in benchmarks if d["delta_pass_rate"] > 0)
        ratio = positive / len(benchmarks)
        print(f"\nPositive lift: {positive}/{len(benchmarks)} ({ratio:.0%})")
        assert ratio >= 0.75, (
            f"Expected >=75% skills with positive lift, got {ratio:.0%}"
        )

    def test_average_delta_is_positive(self):
        _, path = _find_best_iteration()
        benchmarks = _read_benchmarks(path)
        assert len(benchmarks) >= 5, f"Need >=5 skills for meaningful report, found {len(benchmarks)}"
        avg = sum(d["delta_pass_rate"] for _, d in benchmarks) / len(benchmarks)
        print(f"\nAverage delta: {avg:+.1f}pp")
        assert avg > 0, f"Expected positive average delta, got {avg:+.1f}pp"

    def test_no_skill_has_extreme_negative_lift(self):
        """No skill should have delta below -20pp."""
        _, path = _find_best_iteration()
        for skill_name, data in _read_benchmarks(path):
            delta = data["delta_pass_rate"]
            assert delta > -20, (
                f"{skill_name} has extreme negative lift: {delta:+.1f}pp"
            )
