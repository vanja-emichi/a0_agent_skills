#!/usr/bin/env python3
"""Check all SKILL.md files for non-native Agent Zero tool references.

Dimension 2: Tool name nativity.
Scans for Claude/Codex-specific tool names that should have been adapted to A0 native tools.

Usage:
    python3 check_tool_names.py [--plugin /path/to/plugin]

Outputs JSON with per-skill results and overall score.
"""

import json
import os
import re
import sys
from pathlib import Path


# Non-native tool patterns from Claude Code, Codex, etc.
NON_NATIVE_PATTERNS = [
    (r'\bstr_replace_editor\b', "Claude Code tool name"),
    (r'\bTodoWrite\b', "Claude Code tool name"),
    (r'\btodo_write\b', "Claude Code tool name"),
    (r'<function_calls>', "Claude function call syntax"),
    (r'<antaplause>', "Claude artifact syntax"),
    (r'\bBash>\b', "Codex tool syntax"),
    (r'\bRead>\b', "Codex tool syntax"),
    (r'\bWrite>\b', "Codex tool syntax"),
    (r'\bEdit>\b', "Codex tool syntax"),
    (r'\bmcp__\w+', "MCP tool prefix reference"),
    (r'\bcomputer\b_tool\b', "Non-A0 computer use tool"),
    (r'\btodo_write\b', "Claude todo tool"),
]

# Native A0 tool names (whitelist — these are fine)
NATIVE_TOOLS = {
    'code_execution_tool', 'text_editor', 'skills_tool', 'browser',
    'document_query', 'call_subordinate', 'response', 'search_engine',
    'scheduler', 'wait', 'input', 'notify_user', 'parallel',
    'a2a_chat', 'behaviour_adjustment', 'vision_load', 'vision_analyze'
}


def check_skill(skill_dir: Path) -> dict:
    """Check a single skill directory for non-native tool references."""
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    
    if not skill_md.exists():
        return {
            "skill": skill_name,
            "dimension": "tool_name_nativity",
            "pass": False,
            "issues": ["SKILL.md not found"],
            "details": {}
        }
    
    content = skill_md.read_text(encoding="utf-8")
    issues = []
    
    for pattern, description in NON_NATIVE_PATTERNS:
        matches = re.findall(pattern, content)
        if matches:
            issues.append(f"{description}: found '{matches[0]}' ({len(matches)} occurrences)")
    
    # Also check any support .md files in the skill directory
    for support_file in skill_dir.rglob("*.md"):
        if support_file.name == "SKILL.md":
            continue
        support_content = support_file.read_text(encoding="utf-8", errors="ignore")
        rel_path = support_file.relative_to(skill_dir)
        for pattern, description in NON_NATIVE_PATTERNS:
            matches = re.findall(pattern, support_content)
            if matches:
                issues.append(f"{description} in {rel_path}: found '{matches[0]}' ({len(matches)} occurrences)")
    
    return {
        "skill": skill_name,
        "dimension": "tool_name_nativity",
        "pass": len(issues) == 0,
        "issues": issues,
        "details": {
            "files_checked": 1 + len(list(skill_dir.rglob("*.md"))) - 1,
        }
    }


def main():
    plugin_path = Path("/a0/usr/plugins/a0_agent_skills")
    if len(sys.argv) > 2 and sys.argv[1] == "--plugin":
        plugin_path = Path(sys.argv[2])
    
    skills_dir = plugin_path / "skills"
    if not skills_dir.exists():
        print(json.dumps({"error": f"Skills directory not found: {skills_dir}"}, indent=2))
        sys.exit(1)
    
    results = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.is_dir() and not skill_dir.name.startswith("."):
            results.append(check_skill(skill_dir))
    
    passed = sum(1 for r in results if r["pass"])
    failed = sum(1 for r in results if not r["pass"])
    score = passed / len(results) if results else 0.0
    
    output = {
        "dimension": "tool_name_nativity",
        "total_skills": len(results),
        "passed": passed,
        "failed": failed,
        "score": round(score, 4),
        "results": results,
    }
    
    print(json.dumps(output, indent=2))
    
    # Exit code: 0 = all pass, 1 = some failures
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
