#!/usr/bin/env python3
"""Parity report: compare the a0_agent_skills plugin tree to the upstream snapshot.

Outputs a categorized report showing:
- Shared files (identical or changed)
- Plugin-only files (A0-native additions)
- Upstream-only files (not yet ported or intentionally omitted)

Usage:
    python scripts/parity_report.py [--upstream PATH] [--plugin PATH] [--json]

Defaults:
    --upstream  /a0/usr/projects/a0_agent_skills/comparison/official_agent_skills
    --plugin    /a0/usr/plugins/a0_agent_skills
"""

import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

# Noise directories to skip
NOISE_DIRS = {
    "__pycache__", ".pytest_cache", ".git", ".coverage",
    "node_modules", ".npm", "venv", ".venv",
}

NOISE_FILES = {
    ".coverage", ".DS_Store", "Thumbs.db",
}

# Category classifiers — order matters, first match wins
CATEGORY_RULES = [
    ("skills", lambda r: r.startswith("skills/")),
    ("agents", lambda r: r.startswith("agents/")),
    ("commands", lambda r: r.startswith("commands/")),
    ("extensions", lambda r: r.startswith("extensions/")),
    ("tools", lambda r: r.startswith("tools/")),
    ("tests", lambda r: r.startswith("tests/")),
    ("docs", lambda r: r.startswith("docs/")),
    ("hooks", lambda r: r.startswith("hooks/") or r == "hooks.py"),
    ("references", lambda r: r.startswith("references/")),
    ("scripts", lambda r: r.startswith("scripts/")),
    ("prompts", lambda r: r.startswith("prompts/")),
    ("claude", lambda r: r.startswith(".claude/")),
    ("gemini", lambda r: r.startswith(".gemini/")),
    ("claude-plugin", lambda r: r.startswith(".claude-plugin/")),
    ("github", lambda r: r.startswith(".github/")),
    ("manifest", lambda r: r in {"plugin.yaml", "default_config.yaml", "LICENSE"}),
    ("readme", lambda r: r == "README.md"),
    ("repo-docs", lambda r: r in {"AGENTS.md", "CLAUDE.md", "CONTRIBUTING.md", ".gitignore"}),
    ("other", lambda _: True),
]


def file_hash(path: str) -> str:
    """Return SHA-256 hex digest of file contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files(root: str) -> dict[str, str]:
    """Walk a directory and return {relative_path: sha256_hash}."""
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune noise dirs in-place
        dirnames[:] = [
            d for d in dirnames
            if d not in NOISE_DIRS and not d.startswith(".toggle")
        ]
        for fname in filenames:
            if fname in NOISE_FILES:
                continue
            if fname.endswith(".pyc"):
                continue
            full = os.path.join(dirpath, fname)
            rel = os.path.relpath(full, root)
            try:
                files[rel] = file_hash(full)
            except (OSError, PermissionError):
                files[rel] = "<unreadable>"
    return files


def classify(rel: str) -> str:
    """Return the category for a relative path."""
    for cat, matches in CATEGORY_RULES:
        if matches(rel):
            return cat
    return "other"


def build_report(plugin_root: str, upstream_root: str) -> dict:
    """Build the full parity report."""
    plugin_files = collect_files(plugin_root)
    upstream_files = collect_files(upstream_root)

    plugin_set = set(plugin_files.keys())
    upstream_set = set(upstream_files.keys())

    shared = plugin_set & upstream_set
    plugin_only = plugin_set - upstream_set
    upstream_only = upstream_set - plugin_set

    # Classify shared into identical and changed
    shared_identical = sorted(
        r for r in shared if plugin_files[r] == upstream_files[r]
    )
    shared_changed = sorted(
        r for r in shared if plugin_files[r] != upstream_files[r]
    )

    # Group by category
    report = {
        "plugin_root": plugin_root,
        "upstream_root": upstream_root,
        "summary": {
            "plugin_files": len(plugin_files),
            "upstream_files": len(upstream_files),
            "shared_total": len(shared),
            "shared_identical": len(shared_identical),
            "shared_changed": len(shared_changed),
            "plugin_only": len(plugin_only),
            "upstream_only": len(upstream_only),
        },
        "by_category": {},
        "shared_changed": shared_changed,
        "shared_identical": shared_identical,
        "plugin_only": sorted(plugin_only),
        "upstream_only": sorted(upstream_only),
    }

    # Build per-category breakdown
    cats = defaultdict(lambda: {
        "shared_identical": [],
        "shared_changed": [],
        "plugin_only": [],
        "upstream_only": [],
    })

    for r in shared_identical:
        cats[classify(r)]["shared_identical"].append(r)
    for r in shared_changed:
        cats[classify(r)]["shared_changed"].append(r)
    for r in plugin_only:
        cats[classify(r)]["plugin_only"].append(r)
    for r in upstream_only:
        cats[classify(r)]["upstream_only"].append(r)

    # Sort each list inside each category
    for cat in cats:
        for key in cats[cat]:
            cats[cat][key] = sorted(cats[cat][key])

    report["by_category"] = dict(sorted(cats.items()))

    return report


def format_text_report(report: dict) -> str:
    """Format the report as human-readable text."""
    lines = []
    s = report["summary"]

    lines.append("# Parity Report: a0_agent_skills plugin vs upstream")
    lines.append("")
    lines.append(f"Plugin:   {report['plugin_root']}")
    lines.append(f"Upstream: {report['upstream_root']}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|---|---:|")
    lines.append(f"| Plugin files | {s['plugin_files']} |")
    lines.append(f"| Upstream files | {s['upstream_files']} |")
    lines.append(f"| Shared (total) | {s['shared_total']} |")
    lines.append(f"| Shared identical | {s['shared_identical']} |")
    lines.append(f"| Shared changed | {s['shared_changed']} |")
    lines.append(f"| Plugin only | {s['plugin_only']} |")
    lines.append(f"| Upstream only | {s['upstream_only']} |")
    lines.append("")

    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | Shared identical | Shared changed | Plugin only | Upstream only |")
    lines.append("|---|---:|---:|---:|---:|")
    for cat, items in report["by_category"].items():
        si = len(items["shared_identical"])
        sc = len(items["shared_changed"])
        po = len(items["plugin_only"])
        uo = len(items["upstream_only"])
        lines.append(f"| {cat} | {si} | {sc} | {po} | {uo} |")
    lines.append("")

    lines.append("## Shared Changed Files")
    lines.append("")
    for f in report["shared_changed"]:
        lines.append(f"- `{f}`")
    lines.append("")

    lines.append("## Plugin-Only Files (A0-native)")
    lines.append("")
    for f in report["plugin_only"]:
        lines.append(f"- `{f}`")
    lines.append("")

    lines.append("## Upstream-Only Files (not in plugin)")
    lines.append("")
    for f in report["upstream_only"]:
        lines.append(f"- `{f}`")
    lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Parity report: plugin vs upstream snapshot"
    )
    parser.add_argument(
        "--plugin", default="/a0/usr/plugins/a0_agent_skills",
        help="Path to the plugin root"
    )
    parser.add_argument(
        "--upstream",
        default="/a0/usr/projects/a0_agent_skills/comparison/official_agent_skills",
        help="Path to the upstream snapshot"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output as JSON instead of text"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="Write output to file instead of stdout"
    )
    args = parser.parse_args()

    report = build_report(args.plugin, args.upstream)

    if args.json:
        output = json.dumps(report, indent=2)
    else:
        output = format_text_report(report)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
