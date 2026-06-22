#!/usr/bin/env python3
"""Check skill-to-skill cross-references for correct A0 skills_tool syntax.

Dimension 3: Cross-references.
Validates that when a skill references another skill, it uses the correct
skills_tool invocation syntax rather than Claude/Codex-style references.

Usage:
    python3 check_cross_refs.py [--plugin /path/to/plugin]

Outputs JSON with per-skill results and overall score.
"""

import json
import os
import re
import sys
from pathlib import Path


# Invalid patterns (Claude/Codex style)
INVALID_REF_PATTERNS = [
    (r'invoke\s+the\s+[`\']?(\w+[\w-]*)[`\']?\s+skill\s+using\s+(?:the\s+)?(?:skill|tool)\s+tool', "Claude skill invocation syntax"),
    (r'<skill\s+name=["\']([\w-]+)["\']', "XML skill tag syntax"),
    (r'use_skill\s*\(\s*["\']([\w-]+)', "Function-call skill syntax"),
]

# Valid A0 skills_tool patterns - check that referenced skill names exist
VALID_SKILLS_TOOL_PATTERNS = [
    r'skill_name["\']?\s*:\s*["\']([\w-]+)["\']',
    r'load.*?skill.*?["\']([\w-]+)["\']',
]


def get_known_skills(skills_dir: Path) -> set:
    """Get all skill names from the plugin directory."""
    skills = set()
    for d in skills_dir.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            if (d / "SKILL.md").exists():
                skills.add(d.name)
    return skills


def check_skill(skill_dir: Path, all_skills: set) -> dict:
    """Check a single skill for cross-reference correctness."""
    skill_name = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    
    if not skill_md.exists():
        return {
            "skill": skill_name,
            "dimension": "cross_references",
            "pass": False,
            "issues": ["SKILL.md not found"],
            "details": {}
        }
    
    content = skill_md.read_text(encoding="utf-8")
    issues = []
    refs_found = []
    
    # Check for invalid patterns
    for pattern, description in INVALID_REF_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            for match in matches:
                issues.append(f"{description}: references '{match}'")
    
    # Find all skill name mentions in prose (backticked or quoted)
    for other_skill in all_skills:
        if other_skill == skill_name:
            continue
        prose_pattern = rf'[`\'"]({re.escape(other_skill)})[`\'"]'
        prose_matches = re.findall(prose_pattern, content)
        if prose_matches:
            refs_found.append(other_skill)
    
    # Check that skills_tool references point to existing skills
    for pattern in VALID_SKILLS_TOOL_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if match not in all_skills:
                issues.append(f"skills_tool references unknown skill: '{match}'")
    
    return {
        "skill": skill_name,
        "dimension": "cross_references",
        "pass": len(issues) == 0,
        "issues": issues,
        "details": {
            "refs_to_other_skills": refs_found,
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
    
    all_skills = get_known_skills(skills_dir)
    
    results = []
    for skill_dir in sorted(skills_dir.iterdir()):
        if skill_dir.is_dir() and not skill_dir.name.startswith("."):
            if (skill_dir / "SKILL.md").exists():
                results.append(check_skill(skill_dir, all_skills))
    
    passed = sum(1 for r in results if r["pass"])
    failed = sum(1 for r in results if not r["pass"])
    score = passed / len(results) if results else 0.0
    
    output = {
        "dimension": "cross_references",
        "total_skills": len(results),
        "passed": passed,
        "failed": failed,
        "score": round(score, 4),
        "results": results,
    }
    
    print(json.dumps(output, indent=2))
    
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
