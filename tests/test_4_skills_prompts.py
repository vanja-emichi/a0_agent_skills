# test_4_skills_prompts.py - Phase 4: Skills & Prompts verification

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ROOT = os.path.join(os.path.dirname(__file__), "..")
SKILLS_DIR = os.path.join(ROOT, "skills")
PROMPTS_DIR = os.path.join(ROOT, "prompts")

STALE_PATTERNS = [
    "plan:init",
    "plan:status",
    "plan:archive",
    "plan:phase_start",
    "plan:phase_complete",
    "plan:log_finding",
    "plan:log_progress",
    "plan:log_error",
    "plan:extend",
    "plan:migrate",
]


def _read(path):
    return open(path).read()


def _exists(path):
    return os.path.exists(path)


class TestSkillRename:
    """planning-with-files renamed to lifecycle-runtime."""

    def test_lifecycle_runtime_dir_exists(self):
        assert _exists(os.path.join(SKILLS_DIR, "lifecycle-runtime"))

    def test_planning_with_files_dir_removed(self):
        assert not _exists(os.path.join(SKILLS_DIR, "planning-with-files"))

    def test_lifecycle_runtime_has_skill_md(self):
        assert _exists(os.path.join(SKILLS_DIR, "lifecycle-runtime", "SKILL.md"))


class TestPromptRename:
    """plan.md prompt renamed to lifecycle.md."""

    def test_lifecycle_prompt_exists(self):
        assert _exists(os.path.join(PROMPTS_DIR, "agent.system.tool.lifecycle.md"))

    def test_plan_prompt_removed(self):
        assert not _exists(os.path.join(PROMPTS_DIR, "agent.system.tool.plan.md"))

    def test_lifecycle_prompt_has_3_methods(self):
        content = _read(os.path.join(PROMPTS_DIR, "agent.system.tool.lifecycle.md"))
        assert "lifecycle:init" in content
        assert "lifecycle:status" in content
        assert "lifecycle:archive" in content

    def test_lifecycle_prompt_has_7_phases(self):
        content = _read(os.path.join(PROMPTS_DIR, "agent.system.tool.lifecycle.md"))
        assert "IDEA" in content
        assert "SHIP" in content


class TestNoStaleRefsInSkills:
    """No stale plan:* tool call references in any SKILL.md."""

    def test_no_stale_tool_calls(self):
        for skill_name in sorted(os.listdir(SKILLS_DIR)):
            skill_path = os.path.join(SKILLS_DIR, skill_name)
            if not os.path.isdir(skill_path):
                continue
            md_path = os.path.join(skill_path, "SKILL.md")
            if not os.path.exists(md_path):
                continue
            content = _read(md_path)
            for pattern in STALE_PATTERNS:
                assert pattern not in content, f"Found '{pattern}' in skills/{skill_name}/SKILL.md"


class TestNoStaleRefsInPrompts:
    """No stale plan:* references in prompts."""

    def test_no_stale_tool_calls(self):
        if not os.path.exists(PROMPTS_DIR):
            return
        for f in sorted(os.listdir(PROMPTS_DIR)):
            if not f.endswith(".md"):
                continue
            content = _read(os.path.join(PROMPTS_DIR, f))
            for pattern in STALE_PATTERNS:
                assert pattern not in content, f"Found '{pattern}' in prompts/{f}"


class TestLifecycleRuntimeSkill:
    """The lifecycle-runtime SKILL.md describes the new model."""

    def test_describes_3_methods(self):
        content = _read(os.path.join(SKILLS_DIR, "lifecycle-runtime", "SKILL.md"))
        assert "lifecycle:init" in content
        assert "lifecycle:status" in content
        assert "lifecycle:archive" in content

    def test_no_removed_methods(self):
        content = _read(os.path.join(SKILLS_DIR, "lifecycle-runtime", "SKILL.md"))
        assert "phase_start" not in content or "removed" in content.lower()
