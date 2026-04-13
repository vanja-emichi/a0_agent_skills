#!/usr/bin/env python3
"""Validate Agent Zero plugin structure.

Usage (run from repo root):
    python3 scripts/validate.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed

Each check prints:
    PASS <message> [path]
    FAIL [reason] [path]

Checks performed:
    1. plugin.yaml           — exists + has: name, title, version, description
    2. skills/*/SKILL.md     — exists + YAML frontmatter has: name, description
    3. agents/*/agent.yaml   — exists + has: title, description, context
    4. agents/*/prompts/agent.system.main.specifics.md — exists
    5. commands/*.command.yaml — has: name, description, type, template_path + paired .txt
    6. extensions/**/*.py    — valid Python syntax (all .py files, not just _NN_ pattern)
    7. references/*.md       — non-empty

Skips: .a0proj/ (all targeted checks use explicit subdirectories)
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

Result = tuple[bool, str]  # (ok, message)


def _pass(msg: str) -> Result:
    return (True, f"PASS {msg}")


def _fail(reason: str, path: str = "") -> Result:
    parts = ["FAIL", reason]
    if path:
        parts.append(str(path))
    return (False, " ".join(parts))


# ---------------------------------------------------------------------------
# Check 1 — plugin.yaml
# ---------------------------------------------------------------------------

REQUIRED_PLUGIN_FIELDS = ["name", "title", "version", "description"]


def check_plugin_yaml(root: Path) -> list[Result]:
    """Verify plugin.yaml exists and contains all required fields."""
    p = root / "plugin.yaml"
    if not p.exists():
        return [_fail("plugin.yaml not found", str(p))]

    try:
        data = yaml.safe_load(p.read_text()) or {}
    except yaml.YAMLError as exc:
        return [_fail(f"plugin.yaml YAML parse error: {exc}", str(p))]

    if not isinstance(data, dict):
        return [_fail("plugin.yaml is not a YAML mapping", str(p))]

    missing = [f for f in REQUIRED_PLUGIN_FIELDS if not data.get(f)]
    if missing:
        return [_fail(f"missing required fields: {', '.join(missing)}", str(p))]

    return [_pass(f"plugin.yaml has all required fields [{p}]")]


# ---------------------------------------------------------------------------
# Frontmatter helper
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> dict | None:
    """Return parsed YAML frontmatter dict or None if absent or malformed.

    Expects the file to start with '---' on its own line, followed by YAML
    content, closed by another '---' line.
    """
    # Known limitation: a YAML multiline description value containing '---'
    # on its own line will prematurely terminate frontmatter parsing.
    # In practice, SKILL.md descriptions are single-line, so this is safe.
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    # Find closing ---
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break
    if end_idx is None:
        return None
    fm_text = "\n".join(lines[1:end_idx])
    try:
        data = yaml.safe_load(fm_text)
        return data if isinstance(data, dict) else None
    except yaml.YAMLError:
        return None


# ---------------------------------------------------------------------------
# Check 2 — skills/*/SKILL.md
# ---------------------------------------------------------------------------

REQUIRED_SKILL_FM_FIELDS = ["name", "description"]


def check_skills(root: Path) -> list[Result]:
    """Verify each skill directory contains SKILL.md with valid frontmatter."""
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return []

    results: list[Result] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            results.append(_fail("SKILL.md missing", str(skill_dir)))
            continue
        fm = _parse_frontmatter(skill_md.read_text())
        if fm is None:
            results.append(_fail("SKILL.md has no valid YAML frontmatter", str(skill_md)))
            continue
        missing = [f for f in REQUIRED_SKILL_FM_FIELDS if not fm.get(f)]
        if missing:
            results.append(_fail(
                f"frontmatter missing: {', '.join(missing)}", str(skill_md)
            ))
        else:
            results.append(_pass(f"skills/{skill_dir.name}/SKILL.md [{skill_md}]"))

    return results


# ---------------------------------------------------------------------------
# Check 3 — agents/*/agent.yaml
# ---------------------------------------------------------------------------

REQUIRED_AGENT_YAML_FIELDS = ["title", "description", "context"]


def check_agents_yaml(root: Path) -> list[Result]:
    """Verify each agent directory has agent.yaml with required fields."""
    agents_dir = root / "agents"
    if not agents_dir.exists():
        return []

    results: list[Result] = []
    for agent_dir in sorted(agents_dir.iterdir()):
        if not agent_dir.is_dir():
            continue
        agent_yaml = agent_dir / "agent.yaml"
        if not agent_yaml.exists():
            results.append(_fail("agent.yaml missing", str(agent_dir)))
            continue
        try:
            data = yaml.safe_load(agent_yaml.read_text()) or {}
        except yaml.YAMLError as exc:
            results.append(_fail(f"agent.yaml YAML parse error: {exc}", str(agent_yaml)))
            continue
        if not isinstance(data, dict):
            results.append(_fail("agent.yaml is not a YAML mapping", str(agent_yaml)))
            continue
        missing = [f for f in REQUIRED_AGENT_YAML_FIELDS if not data.get(f)]
        if missing:
            results.append(_fail(
                f"missing fields: {', '.join(missing)}", str(agent_yaml)
            ))
        else:
            results.append(_pass(
                f"agents/{agent_dir.name}/agent.yaml [{agent_yaml}]"
            ))

    return results


# ---------------------------------------------------------------------------
# Check 4 — agents/*/prompts/agent.system.main.specifics.md
# ---------------------------------------------------------------------------

SPECIFICS_FILENAME = "agent.system.main.specifics.md"


def check_agent_specifics(root: Path) -> list[Result]:
    """Verify each agent has the specifics prompt file."""
    agents_dir = root / "agents"
    if not agents_dir.exists():
        return []

    results: list[Result] = []
    for agent_dir in sorted(agents_dir.iterdir()):
        if not agent_dir.is_dir():
            continue
        specifics = agent_dir / "prompts" / SPECIFICS_FILENAME
        if specifics.exists():
            results.append(_pass(
                f"agents/{agent_dir.name}/prompts/{SPECIFICS_FILENAME} [{specifics}]"
            ))
        else:
            results.append(_fail(
                f"{SPECIFICS_FILENAME} missing",
                str(agent_dir / "prompts")
            ))

    return results


# ---------------------------------------------------------------------------
# Check 5 — commands/*.command.yaml
# ---------------------------------------------------------------------------

REQUIRED_COMMAND_FIELDS = ["name", "description", "type", "template_path"]


def check_commands(root: Path) -> list[Result]:
    """Verify each command YAML has required fields and paired template file."""
    commands_dir = root / "commands"
    if not commands_dir.exists():
        return []

    results: list[Result] = []
    commands_dir_resolved = commands_dir.resolve()
    for cmd_file in sorted(commands_dir.glob("*.command.yaml")):
        try:
            data = yaml.safe_load(cmd_file.read_text()) or {}
        except yaml.YAMLError as exc:
            results.append(_fail(f"YAML parse error: {exc}", str(cmd_file)))
            continue
        if not isinstance(data, dict):
            results.append(_fail("not a YAML mapping", str(cmd_file)))
            continue
        missing = [f for f in REQUIRED_COMMAND_FIELDS if not data.get(f)]
        if missing:
            results.append(_fail(
                f"missing fields: {', '.join(missing)}", str(cmd_file)
            ))
            continue
        # Resolve template path and verify it stays inside commands/
        template_path = (commands_dir / data["template_path"]).resolve()
        try:
            template_path.relative_to(commands_dir_resolved)
        except ValueError:
            results.append(_fail(
                f"template_path escapes commands dir: {data['template_path']}",
                str(cmd_file),
            ))
            continue
        if not template_path.exists():
            results.append(_fail(
                f"template_path not found: {data['template_path']}", str(cmd_file)
            ))
        else:
            results.append(_pass(f"commands/{cmd_file.name} [{cmd_file}]"))

    return results


# ---------------------------------------------------------------------------
# Check 6 — extensions/**/*.py syntax
# ---------------------------------------------------------------------------

def check_extensions(root: Path) -> list[Result]:
    """Verify ALL .py extension files have valid Python syntax.

    This includes utility modules like simplify_ignore_utils.py — a syntax
    error there would silently kill all hooks that import it.
    """
    ext_dir = root / "extensions"
    if not ext_dir.exists():
        return []

    results: list[Result] = []
    for py_file in sorted(ext_dir.rglob("*.py")):
        source = py_file.read_text(encoding="utf-8", errors="replace")
        try:
            ast.parse(source, filename=str(py_file))
            rel = py_file.relative_to(ext_dir)
            results.append(_pass(f"extensions/{rel} [{py_file}]"))
        except SyntaxError as exc:
            results.append(_fail(f"syntax error: {exc}", str(py_file)))

    return results


# ---------------------------------------------------------------------------
# Check 7 — references/*.md non-empty
# ---------------------------------------------------------------------------

def check_references(root: Path) -> list[Result]:
    """Verify all reference Markdown files are non-empty."""
    ref_dir = root / "references"
    if not ref_dir.exists():
        return []

    results: list[Result] = []
    for md_file in sorted(ref_dir.glob("*.md")):
        content = md_file.read_text().strip()
        if content:
            results.append(_pass(f"references/{md_file.name} [{md_file}]"))
        else:
            results.append(_fail("file is empty", str(md_file)))

    return results


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------

CHECKS = [
    ("Check 1: plugin.yaml",                            check_plugin_yaml),
    ("Check 2: skills/*/SKILL.md",                      check_skills),
    ("Check 3: agents/*/agent.yaml",                    check_agents_yaml),
    ("Check 4: agents/*/prompts/specifics.md",          check_agent_specifics),
    ("Check 5: commands/*.command.yaml",                check_commands),
    ("Check 6: extensions/**/*.py syntax",              check_extensions),
    ("Check 7: references/*.md non-empty",              check_references),
]


def main(root: Path | None = None) -> int:
    if root is None:
        # Default: repo root is two levels above this script (scripts/validate.py)
        root = Path(__file__).resolve().parent.parent

    total_pass = 0
    total_fail = 0

    for label, fn in CHECKS:
        print(f"\n{label}")
        print("-" * len(label))
        results = fn(root)
        if not results:
            print("  (no items found)")
        for ok, msg in results:
            print(f"  {msg}")
            if ok:
                total_pass += 1
            else:
                total_fail += 1

    print(f"\n{'=' * 50}")
    print(f"{total_pass} checks passed, {total_fail} failed")

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
