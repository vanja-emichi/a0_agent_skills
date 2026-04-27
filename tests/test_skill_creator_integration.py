"""Tests for skill-creator integration into agent-skills plugin."""

import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = PROJECT_ROOT / "agents"
SKILLS_DIR = PROJECT_ROOT / "skills"


class TestEvaluationAgentProfiles:
    """Task 1: skill-grader, skill-comparator, skill-analyzer agent profiles."""

    EVAL_AGENTS = ["skill-grader", "skill-comparator", "skill-analyzer"]

    @pytest.mark.parametrize("agent_name", EVAL_AGENTS)
    def test_agent_yaml_exists(self, agent_name: str):
        yaml_path = AGENTS_DIR / agent_name / "agent.yaml"
        assert yaml_path.is_file(), f"Missing: {yaml_path}"

    @pytest.mark.parametrize("agent_name", EVAL_AGENTS)
    def test_agent_yaml_has_required_fields(self, agent_name: str):
        yaml_path = AGENTS_DIR / agent_name / "agent.yaml"
        if not yaml_path.is_file():
            pytest.skip(f"{yaml_path} not yet copied")
        content = yaml_path.read_text(encoding="utf-8")
        assert "title:" in content, f"{agent_name}/agent.yaml missing title"
        assert "description:" in content, f"{agent_name}/agent.yaml missing description"
        assert "context:" in content, f"{agent_name}/agent.yaml missing context"

    @pytest.mark.parametrize("agent_name", EVAL_AGENTS)
    def test_agent_role_prompt_exists(self, agent_name: str):
        role_path = AGENTS_DIR / agent_name / "prompts" / "agent.system.main.role.md"
        assert role_path.is_file(), f"Missing: {role_path}"

    @pytest.mark.parametrize("agent_name", EVAL_AGENTS)
    def test_agent_role_prompt_not_empty(self, agent_name: str):
        role_path = AGENTS_DIR / agent_name / "prompts" / "agent.system.main.role.md"
        if not role_path.is_file():
            pytest.skip(f"{role_path} not yet copied")
        content = role_path.read_text(encoding="utf-8").strip()
        assert len(content) > 50, f"{agent_name} role.md is too short ({len(content)} chars)"

    @pytest.mark.parametrize("agent_name", EVAL_AGENTS)
    def test_agent_matches_deployed_plugin(self, agent_name: str):
        """Verify files match the deployed plugin exactly."""
        deployed_base = Path(f"/a0/usr/plugins/skill-creator/agents/{agent_name}")
        local_base = AGENTS_DIR / agent_name
        if not local_base.is_dir():
            pytest.skip(f"{local_base} not yet copied")
        for deployed_file in deployed_base.rglob("*"):
            if deployed_file.is_file():
                rel = deployed_file.relative_to(deployed_base)
                local_file = local_base / rel
                assert local_file.is_file(), f"Missing local file: {rel}"
                assert local_file.read_text() == deployed_file.read_text(), f"Content mismatch: {rel}"


class TestSkillCreatorScripts:
    """Task 2: scripts and references."""

    SCRIPTS = [
        "quick_validate.py",
        "package_skill.py",
        "aggregate_benchmark.py",
        "generate_review.py",
        "run_loop.py",
        "improve_description.py",
        "optimization_utils.py",
    ]

    @pytest.mark.parametrize("script_name", SCRIPTS)
    def test_script_exists(self, script_name: str):
        script_path = SKILLS_DIR / "skill-creator" / "scripts" / script_name
        assert script_path.is_file(), f"Missing: {script_path}"

    @pytest.mark.parametrize("script_name", SCRIPTS)
    def test_script_importable(self, script_name: str):
        script_path = SKILLS_DIR / "skill-creator" / "scripts" / script_name
        if not script_path.is_file():
            pytest.skip(f"{script_path} not yet copied")
        content = script_path.read_text(encoding="utf-8")
        assert "import" in content, f"{script_name} has no imports"
        assert "def " in content, f"{script_name} has no function definitions"

    def test_schemas_md_exists(self):
        schemas_path = SKILLS_DIR / "skill-creator" / "references" / "schemas.md"
        assert schemas_path.is_file(), f"Missing: {schemas_path}"

    def test_schemas_md_not_empty(self):
        schemas_path = SKILLS_DIR / "skill-creator" / "references" / "schemas.md"
        if not schemas_path.is_file():
            pytest.skip("schemas.md not yet copied")
        content = schemas_path.read_text(encoding="utf-8").strip()
        assert len(content) > 100, f"schemas.md is too short ({len(content)} chars)"


class TestSkillCreatorAgentProfile:
    """Task 3: skill-creator specialist agent profile."""

    def test_agent_yaml_exists(self):
        yaml_path = AGENTS_DIR / "skill-creator" / "agent.yaml"
        assert yaml_path.is_file(), f"Missing: {yaml_path}"

    def test_agent_yaml_has_required_fields(self):
        yaml_path = AGENTS_DIR / "skill-creator" / "agent.yaml"
        if not yaml_path.is_file():
            pytest.skip("skill-creator agent.yaml not yet created")
        content = yaml_path.read_text(encoding="utf-8")
        assert "title:" in content
        assert "description:" in content
        assert "context:" in content

    def test_specifics_md_exists(self):
        specifics_path = AGENTS_DIR / "skill-creator" / "prompts" / "agent.system.main.specifics.md"
        assert specifics_path.is_file(), f"Missing: {specifics_path}"

    def test_specifics_loads_skill(self):
        specifics_path = AGENTS_DIR / "skill-creator" / "prompts" / "agent.system.main.specifics.md"
        if not specifics_path.is_file():
            pytest.skip("specifics.md not yet created")
        content = specifics_path.read_text(encoding="utf-8")
        assert "skills_tool:load" in content, "specifics.md must instruct to load skill"
        assert "skill-creator" in content, "specifics.md must reference skill-creator"


class TestSkillCreatorSKILL:
    """Task 4: SKILL.md scheduler-first rewrite."""

    def test_skill_md_exists(self):
        skill_path = SKILLS_DIR / "skill-creator" / "SKILL.md"
        assert skill_path.is_file(), f"Missing: {skill_path}"

    def test_skill_md_has_frontmatter(self):
        skill_path = SKILLS_DIR / "skill-creator" / "SKILL.md"
        if not skill_path.is_file():
            pytest.skip("SKILL.md not yet created")
        content = skill_path.read_text(encoding="utf-8")
        assert content.startswith("---"), "SKILL.md must start with YAML frontmatter"
        assert "name:" in content.split("---")[1], "Frontmatter must have name field"
        assert "description:" in content.split("---")[1], "Frontmatter must have description field"

    def test_skill_md_under_500_lines(self):
        skill_path = SKILLS_DIR / "skill-creator" / "SKILL.md"
        if not skill_path.is_file():
            pytest.skip("SKILL.md not yet created")
        lines = skill_path.read_text(encoding="utf-8").splitlines()
        assert len(lines) <= 500, f"SKILL.md has {len(lines)} lines, max is 500"

    def test_skill_md_has_scheduler_pattern(self):
        skill_path = SKILLS_DIR / "skill-creator" / "SKILL.md"
        if not skill_path.is_file():
            pytest.skip("SKILL.md not yet created")
        content = skill_path.read_text(encoding="utf-8")
        assert "scheduler" in content.lower(), "SKILL.md must reference scheduler tasks"
        assert "create_adhoc_task" in content, "SKILL.md must use scheduler:create_adhoc_task"
        assert "dedicated_context" in content, "SKILL.md must use dedicated_context: true"

    def test_skill_md_has_all_features(self):
        skill_path = SKILLS_DIR / "skill-creator" / "SKILL.md"
        if not skill_path.is_file():
            pytest.skip("SKILL.md not yet created")
        content = skill_path.read_text(encoding="utf-8")
        assert "Feature 1" in content or "## Create" in content
        assert "Feature 2" in content or "## Edit" in content
        assert "Feature 3" in content or "## Test" in content
        assert "Feature 4" in content or "## Grade" in content
        assert "Feature 5" in content or "## Benchmark" in content
        assert "Feature 6" in content or "## Optimize" in content
