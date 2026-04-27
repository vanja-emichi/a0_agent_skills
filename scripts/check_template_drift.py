#!/usr/bin/env python3
# scripts/check_template_drift.py — Analytics template drift checker (T6)
#
# Validates that analytics templates match expected structure.
# Exits 0 when templates match, non-zero with diff on drift.
# Runnable in CI.

import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
ANALYTICS_DIR = PLUGIN_ROOT / "templates" / "analytics"

# Expected template structure
EXPECTED = {
    "state.md": {
        "required_lines": [
            "# Plan: {{slug}}",
            "## Goal",
            "{{goal}}",
            "## Phases",
            "{{phases}}",
        ],
    },
    "findings.md": {
        "required_section": "# Findings",
    },
    "progress.md": {
        "required_section": "# Progress",
    },
}


def check_template(name: str, spec: dict) -> list[str]:
    """Check a single template against its spec. Returns list of issues."""
    issues = []
    path = ANALYTICS_DIR / name

    if not path.exists():
        issues.append(f"MISSING: {name} not found in templates/analytics/")
        return issues

    content = path.read_text(encoding="utf-8")

    if "required_lines" in spec:
        for line in spec["required_lines"]:
            if line not in content:
                issues.append(f"DRIFT: {name} missing expected line: '{line}'")

    if "required_section" in spec:
        section = spec["required_section"]
        if section not in content:
            issues.append(f"DRIFT: {name} missing section: '{section}'")

    return issues


def main() -> int:
    """Run drift check. Returns 0 on pass, 1 on drift."""
    all_issues = []

    for name, spec in EXPECTED.items():
        issues = check_template(name, spec)
        all_issues.extend(issues)

    if all_issues:
        print("Template drift detected:", file=sys.stderr)
        for issue in all_issues:
            print(f"  {issue}", file=sys.stderr)
        return 1

    print("Analytics templates OK — no drift detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
