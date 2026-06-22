#!/usr/bin/env python3
"""Scan all skills for A0-native content depth patterns.

rev-002 Part 1: Automated content scanner.
Checks each skill for presence of A0-native patterns and structural elements.

Usage:
    python3 check_content_depth.py [--plugin /path/to/plugin]

Outputs JSON with per-skill results and overall score.
"""

import json
import re
import sys
from pathlib import Path


# Frontend skills where browser tool is relevant
FRONTEND_SKILLS = {
    "frontend-ui-engineering",
    "browser-testing-with-devtools",
    "performance-optimization",
}


def check_skill(skill_dir: Path) -> dict:
    """Check a single skill for content depth patterns."""
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    
    if not skill_md.exists():
        return {
            "skill": skill_name,
            "score": 0,
            "max_score": 8,
            "checks": {},
            "issues": ["SKILL.md not found"],
        }
    
    content = skill_md.read_text(encoding="utf-8")
    content_lower = content.lower()
    is_frontend = skill_name in FRONTEND_SKILLS
    
    checks = {}
    issues = []
    
    # 1. parallel_tool_mentioned
    checks["parallel_tool_mentioned"] = 1 if re.search(r'(?:\bparallel\b.{0,200}(?:tool|execut|run|concurrent|fan.out|batch|simultaneous))|(?:parallel.{0,50}tool)', content_lower, re.DOTALL) else 0
    if not checks["parallel_tool_mentioned"]:
        issues.append("No `parallel` tool reference found")
    
    # 2. call_subordinate_mentioned
    checks["call_subordinate_mentioned"] = 1 if "call_subordinate" in content_lower else 0
    if not checks["call_subordinate_mentioned"]:
        issues.append("No `call_subordinate` reference found")
    
    # 3. browser_tool_mentioned (frontend skills only)
    if is_frontend:
        checks["browser_tool_mentioned"] = 1 if re.search(r'\bbrowser\b.*(?:tool|action|content|screenshot)', content_lower) else 0
        if not checks["browser_tool_mentioned"]:
            issues.append("Frontend skill missing `browser` tool reference")
    else:
        # Non-frontend skills get a pass on this check
        checks["browser_tool_mentioned"] = 1  # N/A - auto-pass
    
    # 4. skills_tool_load_syntax
    checks["skills_tool_load_syntax"] = 1 if re.search(r'skills_tool.*(?:action|load|skill_name)', content_lower) else 0
    if not checks["skills_tool_load_syntax"]:
        issues.append("No `skills_tool` load syntax example found")
    
    # 5. project_context_aware
    checks["project_context_aware"] = 1 if re.search(r'\.a0proj|project.*(path|dir|context)|active project', content_lower) else 0
    if not checks["project_context_aware"]:
        issues.append("No project context awareness")
    
    # 6. has_related_section
    checks["has_related_section"] = 1 if re.search(r'\*\*Related:\*\*', content) else 0
    if not checks["has_related_section"]:
        issues.append("Missing **Related:** section")
    
    # 7. has_files_section
    checks["has_files_section"] = 1 if re.search(r'^## Files', content, re.MULTILINE) else 0
    if not checks["has_files_section"]:
        issues.append("Missing ## Files section")
    
    # 8. has_native_triggers (check for A0-specific trigger patterns)
    frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
    if frontmatter_match:
        triggers_text = frontmatter_match.group(1)
        has_triggers = "triggers:" in triggers_text
        trigger_count = len(re.findall(r'-\s+["\']', triggers_text))
        checks["has_native_triggers"] = 1 if (has_triggers and trigger_count >= 3) else 0
        if not checks["has_native_triggers"]:
            issues.append(f"Triggers: has={has_triggers}, count={trigger_count} (need >= 3)")
    else:
        checks["has_native_triggers"] = 0
        issues.append("No frontmatter found")
    
    score = sum(checks.values())
    
    return {
        "skill": skill_name,
        "score": score,
        "max_score": 8,
        "checks": checks,
        "issues": issues,
        "is_frontend": is_frontend,
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
    
    total_score = sum(r["score"] for r in results)
    max_possible = sum(r["max_score"] for r in results)
    avg_score = total_score / len(results) if results else 0.0
    
    # Find weakest skills
    sorted_results = sorted(results, key=lambda x: x["score"])
    weakest = [r for r in sorted_results if r["score"] < 6]
    
    output = {
        "revision": "rev-002",
        "dimension": "content_depth_automated",
        "total_skills": len(results),
        "total_score": total_score,
        "max_possible": max_possible,
        "average_score": round(avg_score, 2),
        "weakest_skills": [f"{r['skill']} ({r['score']}/8)" for r in weakest],
        "results": results,
    }
    
    print(json.dumps(output, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
