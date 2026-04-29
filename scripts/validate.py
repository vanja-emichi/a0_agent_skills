#!/usr/bin/env python3
"""Validate Agent Zero plugin structure for a0_agent_skills v0.3.1.

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
    4. agents/*/prompts/      — specifics.md or role.md exists
    5. commands/*.command.yaml — has: name, description, type, template_path + paired .txt
    6. extensions/**/*.py    — valid Python syntax
    7. references/*.md       — non-empty
    8. tools/lifecycle.py    — exists + has init, status, archive methods
    9. lib/ modules          — lifecycle_state.py
   10. lifecycle prompt      — agent.system.tool.lifecycle.md exists
   11. lifecycle extensions  — 7 _lifecycle_*.py files exist
   12. lifecycle-runtime skill — SKILL.md with expected sections
   13. plugin.yaml v0.3.0    — version + lifecycle settings
   14. lifecycle-status cmd  — command exists with valid yaml
      16. stale plan:* audit    — no stale v0.2.x references in source
   17. v0.2.1 lib files      — import_utils.py, constants.py
"""
from __future__ import annotations

import ast
import re
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
    suffix = f" {path}" if path else ""
    return (False, f"FAIL {reason}{suffix}")


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
    """Return parsed YAML frontmatter dict or None if absent or malformed."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    end_idx = next(
        (i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
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
# Check 4 — agents/*/prompts/ files
# ---------------------------------------------------------------------------

SPECIFICS_FILENAME = "agent.system.main.specifics.md"
ROLE_FILENAME = "agent.system.main.role.md"


def check_agent_specifics(root: Path) -> list[Result]:
    """Verify each agent has a specifics or role prompt file."""
    agents_dir = root / "agents"
    if not agents_dir.exists():
        return []

    results: list[Result] = []
    for agent_dir in sorted(agents_dir.iterdir()):
        if not agent_dir.is_dir():
            continue
        specifics = agent_dir / "prompts" / SPECIFICS_FILENAME
        role = agent_dir / "prompts" / ROLE_FILENAME
        if specifics.exists():
            results.append(_pass(
                f"agents/{agent_dir.name}/prompts/{SPECIFICS_FILENAME} [{specifics}]"
            ))
        elif role.exists():
            results.append(_pass(
                f"agents/{agent_dir.name}/prompts/{ROLE_FILENAME} [{role}]"
            ))
        else:
            results.append(_fail(
                f"{SPECIFICS_FILENAME} or {ROLE_FILENAME} missing",
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
    """Verify ALL .py extension files have valid Python syntax."""
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
# Check 8 — tools/lifecycle.py (v0.3.0 lifecycle runtime)
# ---------------------------------------------------------------------------

EXPECTED_LIFECYCLE_METHODS = ["init", "status", "archive"]


def check_lifecycle_tool(root: Path) -> list[Result]:
    """Verify tools/lifecycle.py exists and contains the 3 expected methods."""
    lifecycle_py = root / "tools" / "lifecycle.py"
    if not lifecycle_py.exists():
        return [_fail("tools/lifecycle.py not found", str(lifecycle_py))]

    results: list[Result] = []
    source = lifecycle_py.read_text(encoding="utf-8", errors="replace")

    for method in EXPECTED_LIFECYCLE_METHODS:
        if f'"{method}"' in source or f"_{method}" in source:
            continue
        results.append(_fail(
            f"tools/lifecycle.py missing method '{method}'", str(lifecycle_py)
        ))

    if not results:
        results.append(_pass(f"tools/lifecycle.py has all 3 methods (init, status, archive) [{lifecycle_py}]"))

    return results


# ---------------------------------------------------------------------------
# Check 9 — lib/ modules (v0.3.0)
# ---------------------------------------------------------------------------

EXPECTED_LIB_FILES = ["lifecycle_state.py"]


def check_lib(root: Path) -> list[Result]:
    """Verify lib/ modules exist for lifecycle runtime."""
    lib_dir = root / "lib"
    if not lib_dir.exists():
        return [_fail("lib/ directory not found", str(lib_dir))]

    results: list[Result] = []
    for lib_file in EXPECTED_LIB_FILES:
        f = lib_dir / lib_file
        if f.exists():
            try:
                ast.parse(f.read_text(encoding="utf-8", errors="replace"), filename=str(f))
                results.append(_pass(f"lib/{lib_file} [{f}]"))
            except SyntaxError as exc:
                results.append(_fail(f"syntax error: {exc}", str(f)))
        else:
            results.append(_fail(f"lib/{lib_file} not found", str(f)))

    return results


# ---------------------------------------------------------------------------
# Check 10 — prompts/agent.system.tool.lifecycle.md (v0.3.0)
# ---------------------------------------------------------------------------

def check_lifecycle_prompt(root: Path) -> list[Result]:
    """Verify the lifecycle tool prompt fragment exists."""
    prompt_dir = root / "prompts"
    if not prompt_dir.exists():
        return [_fail("prompts/ directory not found", str(prompt_dir))]

    # Accept either lifecycle.md or plan.md (backward compat)
    lifecycle_prompt = prompt_dir / "agent.system.tool.lifecycle.md"
    plan_prompt = prompt_dir / "agent.system.tool.plan.md"

    if lifecycle_prompt.exists():
        content = lifecycle_prompt.read_text(encoding="utf-8").strip()
        if not content:
            return [_fail("agent.system.tool.lifecycle.md is empty", str(lifecycle_prompt))]
        return [_pass(f"prompts/agent.system.tool.lifecycle.md [{lifecycle_prompt}]")]
    elif plan_prompt.exists():
        return [_fail("Using legacy agent.system.tool.plan.md — should be renamed to lifecycle.md", str(plan_prompt))]
    else:
        return [_fail("agent.system.tool.lifecycle.md not found", str(prompt_dir))]


# ---------------------------------------------------------------------------
# Check 11 — lifecycle-related extension files (v0.3.0)
# ---------------------------------------------------------------------------

EXPECTED_LIFECYCLE_EXTENSIONS = [
    "extensions/python/message_loop_prompts_after/_10_lifecycle_inject.py",
    "extensions/python/tool_execute_before/_30_no_lifecycle_gate.py",
    "extensions/python/tool_execute_before/_31_lifecycle_gate.py",
    "extensions/python/tool_execute_after/_30_lifecycle_auto_progress.py",
    "extensions/python/monologue_start/_30_lifecycle_resume.py",
    "extensions/python/monologue_end/_30_lifecycle_verifier.py",
    "extensions/python/system_prompt/_22_lifecycle_rules.py",
]


def check_lifecycle_extensions(root: Path) -> list[Result]:
    """Verify lifecycle-related extension files exist."""
    results: list[Result] = []
    for ext_path in EXPECTED_LIFECYCLE_EXTENSIONS:
        f = root / ext_path
        if f.exists():
            try:
                ast.parse(f.read_text(encoding="utf-8", errors="replace"), filename=str(f))
                results.append(_pass(f"{ext_path} [{f}]"))
            except SyntaxError as exc:
                results.append(_fail(f"syntax error: {exc}", str(f)))
        else:
            results.append(_fail(f"{ext_path} not found", str(f)))

    return results


# ---------------------------------------------------------------------------
# Check 12 — skills/lifecycle-runtime/SKILL.md
# ---------------------------------------------------------------------------

def check_lifecycle_skill(root: Path) -> list[Result]:
    """Verify the lifecycle-runtime skill exists with valid frontmatter."""
    skill_md = root / "skills" / "lifecycle-runtime" / "SKILL.md"
    if not skill_md.exists():
        return [_fail("skills/lifecycle-runtime/SKILL.md not found", str(skill_md))]

    fm = _parse_frontmatter(skill_md.read_text())
    if fm is None:
        return [_fail("SKILL.md has no valid YAML frontmatter", str(skill_md))]

    missing = [f for f in REQUIRED_SKILL_FM_FIELDS if not fm.get(f)]
    if missing:
        return [_fail(
            f"frontmatter missing: {', '.join(missing)}", str(skill_md)
        )]

    content = skill_md.read_text(encoding="utf-8")
    expected_sections = ["Manus Principles", "5-Question Reboot", "Untrusted"]
    found = [s for s in expected_sections if s in content]
    if len(found) < len(expected_sections):
        missing_sections = [s for s in expected_sections if s not in content]
        return [_fail(
            f"missing sections: {', '.join(missing_sections)}", str(skill_md)
        )]

    return [_pass(f"skills/lifecycle-runtime/SKILL.md [{skill_md}]")]


# ---------------------------------------------------------------------------
# Check 13 — plugin.yaml v0.3.0 settings
# ---------------------------------------------------------------------------

def check_plugin_settings(root: Path) -> list[Result]:
    """Verify plugin.yaml has correct v0.3.0 settings."""
    p = root / "plugin.yaml"
    if not p.exists():
        return [_fail("plugin.yaml not found", str(p))]

    try:
        data = yaml.safe_load(p.read_text()) or {}
    except yaml.YAMLError:
        return [_fail("plugin.yaml YAML parse error", str(p))]

    if not isinstance(data, dict):
        return [_fail("plugin.yaml is not a YAML mapping", str(p))]

    results: list[Result] = []

    # Check version is 0.3.0
    version = data.get("version", "")
    if version == "0.3.1":
        results.append(_pass("plugin.yaml version is 0.3.1"))
    else:
        results.append(_fail(f"plugin.yaml version is '{version}', expected '0.3.1'"))

    # Check settings_sections has lifecycle
    settings_sections = data.get("settings_sections", [])
    if isinstance(settings_sections, list):
        has_lifecycle = "lifecycle" in settings_sections
    elif isinstance(settings_sections, dict):
        has_lifecycle = "lifecycle" in settings_sections
    else:
        has_lifecycle = False

    if has_lifecycle:
        results.append(_pass("plugin.yaml has lifecycle settings section"))
    else:
        results.append(_fail("plugin.yaml missing lifecycle settings section"))

    # Check per_project_config
    if data.get("per_project_config"):
        results.append(_pass("plugin.yaml has per_project_config: true"))
    else:
        results.append(_fail("plugin.yaml missing per_project_config: true"))

    return results


# ---------------------------------------------------------------------------
# Check 14 — commands/lifecycle-status (v0.3.0)
# ---------------------------------------------------------------------------

def check_lifecycle_status_command(root: Path) -> list[Result]:
    """Verify /lifecycle-status slash command exists."""
    cmd_dir = root / "commands"
    if not cmd_dir.exists():
        return []

    cmd_yaml = cmd_dir / "lifecycle-status.command.yaml"
    if not cmd_yaml.exists():
        return [_fail("lifecycle-status.command.yaml not found", str(cmd_dir))]

    results: list[Result] = []
    try:
        data = yaml.safe_load(cmd_yaml.read_text()) or {}
    except yaml.YAMLError as exc:
        return [_fail(f"YAML parse error: {exc}", str(cmd_yaml))]

    if not isinstance(data, dict):
        return [_fail("not a YAML mapping", str(cmd_yaml))]

    missing = [f for f in REQUIRED_COMMAND_FIELDS if not data.get(f)]
    if missing:
        results.append(_fail(
            f"missing fields: {', '.join(missing)}", str(cmd_yaml)
        ))
    else:
        results.append(_pass(f"commands/lifecycle-status.command.yaml [{cmd_yaml}]"))

    return results


# ---------------------------------------------------------------------------
# Check 16 — stale plan:* reference audit (v0.3.0)
# ---------------------------------------------------------------------------

STALE_PATTERNS = [
    r'plan:(init|status|archive|complete|phase_start|phase_complete|log_finding|log_progress|log_error|extend)',
]


def check_stale_refs(root: Path) -> list[Result]:
    """Verify no stale plan:* tool references remain in source."""
    stale = []
    skip_dirs = {"__pycache__", ".git", "tests", ".pytest_cache"}
    for ext in ["*.py", "*.yaml", "*.txt"]:
        for f in root.rglob(ext):
            if any(d in str(f) for d in skip_dirs):
                continue
            try:
                content = f.read_text()
                for pattern in STALE_PATTERNS:
                    for m in re.findall(pattern, content):
                        stale.append(f"{f.relative_to(root)}: plan:{m}")
            except Exception:
                pass

    if stale:
        return [_fail(f"{len(stale)} stale plan:* references found", "\n  ".join(stale[:10]))]
    return [_pass("no stale plan:* references in source")]


# ---------------------------------------------------------------------------
# Check 17 — v0.2.1 lib files still present
# ---------------------------------------------------------------------------

def check_v021_files(root: Path) -> list[Result]:
    """Verify v0.2.1+ lib files still exist."""
    results = []
    for path in [
        root / "lib" / "import_utils.py",
        root / "lib" / "constants.py",
    ]:
        if path.exists():
            results.append(_pass(f"exists [{path.relative_to(root)}]"))
        else:
            results.append(_fail(f"missing [{path.relative_to(root)}]"))
    return results



# ---------------------------------------------------------------------------
# Check 18 — ghost method references in SKILL.md (v0.3.1)
# ---------------------------------------------------------------------------

def check_no_ghost_references(root: Path) -> list[Result]:
    """Verify SKILL.md files don't contain ghost method references."""
    skills_dir = root / "skills"
    if not skills_dir.exists():
        return []

    issues: list[Result] = []
    pattern = re.compile(r"#\s*(\w+)\s+removed")

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        content = skill_md.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(content.splitlines(), 1):
            if pattern.search(line):
                issues.append(_fail(
                    f"Ghost reference in {skill_dir.name}/SKILL.md:{i}: {line.strip()}"
                ))

    if not issues:
        issues.append(_pass("no ghost method references in SKILL.md files"))
    return issues

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
    # v0.3.0 lifecycle runtime checks
    ("Check 8: tools/lifecycle.py",                     check_lifecycle_tool),
    ("Check 9: lib/ modules",                           check_lib),
    ("Check 10: lifecycle tool prompt",                 check_lifecycle_prompt),
    ("Check 11: lifecycle extensions",                  check_lifecycle_extensions),
    ("Check 12: lifecycle-runtime skill",               check_lifecycle_skill),
    ("Check 13: plugin.yaml v0.3.1 settings",           check_plugin_settings),
    ("Check 14: lifecycle-status command",              check_lifecycle_status_command),
    ("Check 16: stale plan:* audit",                    check_stale_refs),
    ("Check 17: v0.2.1 lib files",                      check_v021_files),
    ("Check 18: ghost method references",                check_no_ghost_references),
]


def main(root: Path | None = None) -> int:
    if root is None:
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
