#!/usr/bin/env python3
"""Pytest wrapper for the outcome-lift eval runner.

Asserts that enforce mode produces equal or better match rates
than observe-only mode across all eval fixtures.

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_outcome_lift.py -v
"""

from __future__ import annotations

import asyncio

import pytest

from tests.run_outcome_lift import run_all


class TestOutcomeLift:
    """Assert enforcement gate improves or maintains outcomes."""

    @pytest.fixture(scope="class")
    def report(self):
        """Run the full eval suite once for all tests in this class."""
        return asyncio.run(run_all())

    def test_runner_executes_all_fixtures(self, report):
        """At least one eval case must be present."""
        assert report["summary"]["total_cases"] > 0

    def test_enforce_rate_gte_observe_rate(self, report):
        """Enforce mode match rate must be >= observe mode rate."""
        s = report["summary"]
        assert s["enforce_rate"] >= s["observe_rate"], (
            f"enforce_rate ({s['enforce_rate']:.1%}) < "
            f"observe_rate ({s['observe_rate']:.1%})"
        )

    def test_suppress_enforce_perfect(self, report):
        """Enforce mode must correctly reject all suppress cases."""
        s = report["summary"]
        assert s["suppress_enforce_rate"] == 1.0, (
            f"suppress enforce rate {s['suppress_enforce_rate']:.1%} < 100%")

    def test_enforce_correct_count(self, report):
        """Enforce mode should produce at least some correct results."""
        s = report["summary"]
        assert s["enforce_correct"] > 0

    def test_lift_non_negative(self, report):
        """Outcome lift (enforce − observe) must be >= 0."""
        s = report["summary"]
        assert s["lift"] >= 0, f"lift is negative: {s['lift']}"
