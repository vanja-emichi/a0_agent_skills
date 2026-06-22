#!/usr/bin/env python3
"""Agent Zero runtime-alignment audit for a0_agent_skills.

This rev-005 harness intentionally avoids giving credit for mere content expansion.
It checks whether the plugin's docs, tests, and skill content align with real Agent
Zero runtime contracts: project metadata, exact tool schemas, subordinate boundaries,
installed-plugin paths, test harness integrity, and eval-runner truthfulness.

Usage:
    python3 check_a0_runtime_alignment.py --plugin /a0/usr/plugins/a0_agent_skills
    python3 check_a0_runtime_alignment.py --plugin /path/to/checkpoint/subject/a0_agent_skills --json-out run.json

Exit code is 0 only when all gate checks pass.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

KNOWN_TOOLS = {
    "a2a_chat", "behaviour_adjustment", "browser", "call_subordinate",
    "code_execution_tool", "document_query", "input", "notify_user",
    "parallel", "response", "scheduler", "search_engine", "skills_tool",
    "text_editor", "wait", "vision_load",
}

FORBIDDEN_PATTERNS = {
    "memory_save": "nonexistent Agent Zero tool",
    "memory_load": "nonexistent Agent Zero tool",
    "str_replace_editor": "Claude/Codex editor tool reference",
    "TodoWrite": "Claude-specific todo tool reference",
    "Bash>": "Claude transcript/tool notation",
    "Edit>": "Claude transcript/tool notation",
    "Write>": "Claude transcript/tool notation",
    "Read>": "Claude transcript/tool notation",
    ".claude/": "Claude-specific path reference",
}

A0_EVAL_TERMS = [
    "skills_tool", "call_subordinate", "parallel", ".a0proj", "AGENTS.md",
    "active project", "project context", "browser tool", "scheduler task",
    "chat.json", "loaded_skills", "text_editor", "code_execution_tool",
]


def add(results: list[dict[str, Any]], check_id: str, passed: bool, message: str,
        severity: str = "gate", evidence: dict[str, Any] | None = None) -> None:
    results.append({
        "id": check_id,
        "passed": bool(passed),
        "severity": severity,
        "message": message,
        "evidence": evidence or {},
    })


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def list_command_names(commands_dir: Path) -> set[str]:
    names: set[str] = set()
    for path in sorted(commands_dir.glob("*.command.yaml")):
        text = read(path)
        m = re.search(r"^name:\s*['\"]?([^'\"\n#]+)", text, re.M)
        if m:
            names.add(m.group(1).strip())
    return names


def parse_plugin_command_names(test_file: Path) -> set[str] | None:
    if not test_file.exists():
        return None
    try:
        tree = ast.parse(read(test_file), filename=str(test_file))
    except SyntaxError:
        return None
    found: set[str] | None = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PLUGIN_COMMAND_NAMES":
                    try:
                        value = ast.literal_eval(node.value)
                    except Exception:
                        return None
                    if isinstance(value, list):
                        found = {str(x) for x in value}
    return found


def extract_json_fences(text: str) -> list[str]:
    return re.findall(r"```json\s*(.*?)\s*```", text, flags=re.S | re.I)


def analyze_skill(skill_dir: Path) -> dict[str, Any]:
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    content = read(skill_md)
    lower = content.lower()
    issues: list[str] = []
    warnings: list[str] = []

    if not content:
        issues.append("missing SKILL.md")
        return {"skill": skill_name, "passed": False, "issues": issues, "warnings": warnings}

    forbidden_hits = []
    for pattern, reason in FORBIDDEN_PATTERNS.items():
        if pattern.lower() in lower:
            forbidden_hits.append({"pattern": pattern, "reason": reason})
    if forbidden_hits:
        issues.append("forbidden/non-A0 references present")

    tool_names = sorted(set(re.findall(r"[\"']tool_name[\"']\s*:\s*[\"']([^\"']+)[\"']", content)))
    unknown_tools = [name for name in tool_names if name not in KNOWN_TOOLS]
    if unknown_tools:
        issues.append("unknown tool_name values: " + ", ".join(unknown_tools))

    # Project context must be more than a generic word. It should connect active project,
    # AGENTS.md, and .a0proj/project metadata when the skill is about project work.
    has_project_context = "project context" in lower or "### project context" in lower
    project_terms = {
        "active_project": bool(re.search(r"active project|project directory|project dir", lower)),
        "agents_md": "agents.md" in lower,
        "a0proj": ".a0proj" in lower,
    }
    project_context_pass = has_project_context and all(project_terms.values())
    if not project_context_pass:
        warnings.append("project context contract incomplete")

    # If a skill tells agents to use subordinates, it must also say the main agent owns integration/decision authority.
    mentions_subordinate = "call_subordinate" in lower or "subordinate" in lower
    subordinate_boundary_pass = True
    if mentions_subordinate:
        subordinate_boundary_pass = bool(re.search(r"main agent.{0,160}(owns|integrat|synthes|decid|final|authority)", lower, re.S))
        if not subordinate_boundary_pass:
            warnings.append("mentions subordinates without clear main-agent ownership boundary")

    json_fences = extract_json_fences(content)
    json_errors = []
    tool_json_examples = 0
    for idx, block in enumerate(json_fences, start=1):
        if "tool_name" not in block and "tool_args" not in block:
            continue
        tool_json_examples += 1
        try:
            parsed = json.loads(block)
        except Exception as exc:
            json_errors.append({"fence": idx, "error": str(exc)})
            continue
        names = []
        if isinstance(parsed, dict):
            if "tool_name" in parsed:
                names.append(parsed.get("tool_name"))
            if parsed.get("tool_name") == "parallel":
                for call in parsed.get("tool_args", {}).get("tool_calls", []):
                    if isinstance(call, dict):
                        names.append(call.get("tool_name"))
        for name in names:
            if name and name not in KNOWN_TOOLS:
                json_errors.append({"fence": idx, "error": f"unknown tool_name {name!r}"})
    if json_errors:
        issues.append("invalid JSON/tool examples")

    eval_path = skill_dir / "evals" / "evals.json"
    eval_text = read(eval_path)
    eval_exists = bool(eval_text)
    eval_a0_specific = eval_exists and any(term.lower() in eval_text.lower() for term in A0_EVAL_TERMS)
    if not eval_exists:
        issues.append("missing evals/evals.json")
    elif not eval_a0_specific:
        warnings.append("evals lack detectable A0-runtime-specific assertions")

    passed = not issues
    return {
        "skill": skill_name,
        "passed": passed,
        "issues": issues,
        "warnings": warnings,
        "forbidden_hits": forbidden_hits,
        "tool_names": tool_names,
        "unknown_tools": unknown_tools,
        "project_terms": project_terms,
        "project_context_pass": project_context_pass,
        "subordinate_boundary_pass": subordinate_boundary_pass,
        "tool_json_examples": tool_json_examples,
        "json_errors": json_errors,
        "eval_exists": eval_exists,
        "eval_a0_specific": eval_a0_specific,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plugin", default="/a0/usr/plugins/a0_agent_skills")
    ap.add_argument("--json-out")
    args = ap.parse_args()

    plugin = Path(args.plugin).resolve()
    results: list[dict[str, Any]] = []

    add(results, "plugin.exists", plugin.exists(), f"plugin path: {plugin}")
    skills_dir = plugin / "skills"
    commands_dir = plugin / "commands"
    agents_dir = plugin / "agents"

    skill_files = sorted(skills_dir.glob("*/SKILL.md")) if skills_dir.exists() else []
    command_names = list_command_names(commands_dir) if commands_dir.exists() else set()
    profile_names = {p.name for p in agents_dir.iterdir() if p.is_dir()} if agents_dir.exists() else set()

    add(results, "inventory.skills_24", len(skill_files) == 24,
        f"expected 24 skills, found {len(skill_files)}", evidence={"skills": [p.parent.name for p in skill_files]})
    add(results, "inventory.commands_8", len(command_names) == 8,
        f"expected 8 commands, found {len(command_names)}", evidence={"commands": sorted(command_names)})
    add(results, "inventory.profiles_3", len(profile_names) == 3,
        f"expected 3 profiles, found {len(profile_names)}", evidence={"profiles": sorted(profile_names)})

    plugin_agents = read(plugin / "AGENTS.md")
    stale_23 = bool(re.search(r"providing\s+23\s+production-grade", plugin_agents, re.I))
    add(results, "docs.skill_count_not_stale", not stale_23,
        "root plugin AGENTS.md must not claim 23 skills when inventory has 24")

    env_docs = "/opt/venv-a0/bin/python" in plugin_agents and "/opt/venv/bin/python" in plugin_agents
    add(results, "docs.python_envs_documented", env_docs,
        "plugin docs should document both A0 runtime and plugin test Python environments")

    eval_claim = "/a0/usr/projects/a0_agent_skills/eval/" in plugin_agents or "agent-skills-eval" in plugin_agents
    eval_path = Path("/a0/usr/projects/a0_agent_skills/eval")
    eval_claim_truthful = (not eval_claim) or eval_path.exists()
    add(results, "docs.eval_framework_claim_truthful", eval_claim_truthful,
        "docs must not claim a cloned eval framework path unless it exists",
        evidence={"claimed": eval_claim, "path": str(eval_path), "exists": eval_path.exists()})

    e2e_command_file = plugin / "tests" / "e2e" / "test_e2e_command_execution.py"
    listed = parse_plugin_command_names(e2e_command_file)
    if listed is None:
        add(results, "e2e.command_discovery_parseable", False, "could not parse PLUGIN_COMMAND_NAMES")
    else:
        missing = sorted(command_names - listed)
        extra = sorted(listed - command_names)
        add(results, "e2e.command_discovery_covers_all_commands", not missing and not extra,
            "e2e command discovery list should match installed command manifests",
            evidence={"manifest_commands": sorted(command_names), "e2e_listed": sorted(listed), "missing": missing, "extra": extra})

    ext_behavior = plugin / "tests" / "e2e" / "test_e2e_extension_behavior.py"
    ext_text = read(ext_behavior)
    has_task_uuid_bug = "wait_for_task(task_uuid)" in ext_text and "task_uuid = task[\"uuid\"]" not in ext_text.split("wait_for_task(task_uuid)", 1)[0]
    add(results, "e2e.no_obvious_task_uuid_bug", not has_task_uuid_bug,
        "e2e extension behavior test should not use task_uuid before assignment")

    # Syntax check e2e files with ast, not execution.
    syntax_errors = []
    for path in sorted((plugin / "tests" / "e2e").glob("test_*.py")):
        try:
            ast.parse(read(path), filename=str(path))
        except SyntaxError as exc:
            syntax_errors.append({"file": str(path), "error": str(exc)})
    add(results, "e2e.python_syntax", not syntax_errors,
        "all e2e test files should parse as Python", evidence={"syntax_errors": syntax_errors})

    skill_results = [analyze_skill(p.parent) for p in skill_files]
    failing_skills = [r for r in skill_results if not r["passed"]]
    skills_with_warnings = [r for r in skill_results if r["warnings"]]
    add(results, "skills.no_invalid_tool_or_forbidden_refs", not failing_skills,
        "skills should not contain nonexistent tools, Claude artifacts, invalid tool JSON, or missing evals",
        evidence={"failing": failing_skills})
    add(results, "skills.runtime_context_warnings", not skills_with_warnings,
        "skills should fully encode project context, subordinate boundaries, and A0-specific evals",
        severity="advisory",
        evidence={"warning_count": len(skills_with_warnings), "warnings": skills_with_warnings})

    failed_gates = [r for r in results if r["severity"] == "gate" and not r["passed"]]
    failed_advisory = [r for r in results if r["severity"] != "gate" and not r["passed"]]
    output = {
        "revision": "rev-005",
        "harness": "a0_runtime_alignment_static_v1",
        "plugin": str(plugin),
        "summary": {
            "gate_passed": len(failed_gates) == 0,
            "gate_failures": len(failed_gates),
            "advisory_failures": len(failed_advisory),
            "checks_total": len(results),
            "skills_checked": len(skill_results),
        },
        "checks": results,
        "skill_results": skill_results,
    }

    text = json.dumps(output, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if len(failed_gates) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
