# test_4_skills_prompts.py - Phase 4: Skills & Prompts verification

import os

from .conftest import SKILLS_DIR, PROMPTS_DIR, STALE_PLAN_PATTERNS


def _read(path):
    return path.read_text()


class TestSkillRename:
    """lifecycle-runtime merged into using-agent-skills."""

    def test_lifecycle_runtime_dir_removed(self):
        assert not (SKILLS_DIR / "lifecycle-runtime").is_dir()

    def test_planning_with_files_dir_removed(self):
        assert not (SKILLS_DIR / "planning-with-files").is_dir()

    def test_using_agent_skills_has_lifecycle_content(self):
        content = _read(SKILLS_DIR / "using-agent-skills" / "SKILL.md")
        assert "Manus Principles" in content
        assert "5-Question Reboot Test" in content


class TestPromptRename:
    """plan.md prompt renamed to lifecycle.md."""

    def test_lifecycle_prompt_exists(self):
        assert (PROMPTS_DIR / "agent.system.tool.lifecycle.md").is_file()

    def test_plan_prompt_removed(self):
        assert not (PROMPTS_DIR / "agent.system.tool.plan.md").is_file()

    def test_lifecycle_prompt_has_3_methods(self):
        content = _read(PROMPTS_DIR / "agent.system.tool.lifecycle.md")
        assert "lifecycle:init" in content
        assert "lifecycle:status" in content
        assert "lifecycle:archive" in content

    def test_lifecycle_prompt_has_7_phases(self):
        content = _read(PROMPTS_DIR / "agent.system.tool.lifecycle.md")
        assert "IDEA" in content
        assert "SHIP" in content


class TestNoStaleRefsInSkills:
    """No stale plan:* tool call references in any SKILL.md."""

    def test_no_stale_tool_calls(self):
        for skill_name in sorted(os.listdir(SKILLS_DIR)):
            skill_path = SKILLS_DIR / skill_name
            if not skill_path.is_dir():
                continue
            md_path = skill_path / "SKILL.md"
            if not md_path.is_file():
                continue
            content = _read(md_path)
            for pattern in STALE_PLAN_PATTERNS:
                assert pattern not in content, f"Found '{pattern}' in skills/{skill_name}/SKILL.md"


class TestNoStaleRefsInPrompts:
    """No stale plan:* references in prompts."""

    def test_no_stale_tool_calls(self):
        if not PROMPTS_DIR.is_dir():
            return
        for f in sorted(os.listdir(PROMPTS_DIR)):
            if not f.endswith(".md"):
                continue
            content = _read(PROMPTS_DIR / f)
            for pattern in STALE_PLAN_PATTERNS:
                assert pattern not in content, f"Found '{pattern}' in prompts/{f}"


class TestLifecycleRuntimeSkill:
    """The merged lifecycle content in using-agent-skills describes the new model."""

    def test_describes_3_methods(self):
        content = _read(SKILLS_DIR / "using-agent-skills" / "SKILL.md")
        assert "lifecycle:init" in content
        assert "lifecycle:status" in content
        assert "lifecycle:archive" in content

    def test_no_removed_methods(self):
        content = _read(SKILLS_DIR / "using-agent-skills" / "SKILL.md")
        assert "phase_start" not in content or "removed" in content.lower()
