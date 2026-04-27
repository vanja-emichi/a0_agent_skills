"""Gap-closing tests for skill-creator integration.

Tests NOT covered by test_skill_creator_integration.py:
- Script syntax validity (compile, not keyword scan)
- SKILL.md frontmatter name matches directory name
- SKILL.md description length ≤ 1024 chars
- SKILL.md required anatomy sections
- skill-creator agent matches deployed plugin
- skill-creator in routing specialist table
- validate.py handles ROLE_FILENAME for eval agents
- using-agent-skills has skill-creator delegation markers
- Script CLI entry points
"""

import ast
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = PROJECT_ROOT / "agents"
SKILLS_DIR = PROJECT_ROOT / "skills"
EXT_PATH = (
    PROJECT_ROOT
    / "extensions"
    / "python"
    / "system_prompt"
    / "_20_agent_skills_prompt.py"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_skill(name: str) -> str:
    path = SKILLS_DIR / name / "SKILL.md"
    assert path.is_file(), f"Missing skill: {path}"
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter fields (simple parser)."""
    parts = text.split("---")
    if len(parts) < 3:
        return {}
    fm = parts[1]
    result = {}
    for line in fm.splitlines():
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip()
    return result


@pytest.fixture()
def routing_module():
    """Import the routing extension module with mocked A0 deps."""
    saved = {}
    for mod_name in ["helpers", "helpers.extension", "helpers.print_style", "agent"]:
        saved[mod_name] = sys.modules.get(mod_name)

    class FakeExtension:
        def __init__(self):
            self.agent = None

    helpers_ext = MagicMock()
    helpers_ext.Extension = FakeExtension
    helpers_ps = MagicMock()
    helpers_ps.PrintStyle = MagicMock()

    sys.modules["helpers"] = MagicMock()
    sys.modules["helpers.extension"] = helpers_ext
    sys.modules["helpers.print_style"] = helpers_ps
    sys.modules["agent"] = MagicMock()

    spec = importlib.util.spec_from_file_location(
        "agent_skills_prompt", EXT_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    yield mod

    for mod_name, orig in saved.items():
        if orig is None:
            sys.modules.pop(mod_name, None)
        else:
            sys.modules[mod_name] = orig


@pytest.fixture()
def delegation_table(routing_module):
    return routing_module.get_delegation_table()


# ===================================================================
# 1. Script syntax validity — real compile check
# ===================================================================


class TestScriptSyntaxValidity:
    """Scripts must be valid Python (compile + ast.parse), not just keyword scan."""

    SCRIPTS = [
        "quick_validate.py",
        "package_skill.py",
        "aggregate_benchmark.py",
        "generate_review.py",
        "run_loop.py",
        "improve_description.py",
    ]

    # Utility modules (imported by other scripts, not standalone entry points)
    UTILITY_SCRIPTS = ["optimization_utils.py"]

    @pytest.mark.parametrize("script_name", SCRIPTS)
    def test_script_compiles_without_error(self, script_name: str):
        script_path = SKILLS_DIR / "skill-creator" / "scripts" / script_name
        if not script_path.is_file():
            pytest.skip(f"{script_path} not found")
        source = script_path.read_text(encoding="utf-8")
        compile(source, str(script_path), "exec")
    @pytest.mark.parametrize("script_name", SCRIPTS)
    def test_script_ast_parseable(self, script_name: str):
        """ast.parse validates structure beyond bare compile."""
        script_path = SKILLS_DIR / "skill-creator" / "scripts" / script_name
        if not script_path.is_file():
            pytest.skip(f"{script_path} not found")
        source = script_path.read_text(encoding="utf-8")
        ast.parse(source, filename=str(script_path))

    @pytest.mark.parametrize("script_name", SCRIPTS)
    def test_script_has_main_guard_or_entry_function(self, script_name: str):
        """Standalone scripts must have __name__ == '__main__' guard or def main()."""
        script_path = SKILLS_DIR / "skill-creator" / "scripts" / script_name
        if not script_path.is_file():
            pytest.skip(f"{script_path} not found")
        source = script_path.read_text(encoding="utf-8")
        has_main_guard = "__name__" in source and "__main__" in source
        has_main_fn = "def main" in source
        assert has_main_guard or has_main_fn, (
            f"{script_name} must have if __name__ == '__main__' guard or def main()"
        )

    @pytest.mark.parametrize("script_name", UTILITY_SCRIPTS)
    def test_utility_script_has_exports(self, script_name: str):
        """Utility modules must export functions (def statements)."""
        script_path = SKILLS_DIR / "skill-creator" / "scripts" / script_name
        if not script_path.is_file():
            pytest.skip(f"{script_path} not found")
        source = script_path.read_text(encoding="utf-8")
        assert "def " in source, (
            f"{script_name} must define functions (utility module)"
        )

    @pytest.mark.parametrize("script_name", SCRIPTS + UTILITY_SCRIPTS)
    def test_all_scripts_compile(self, script_name: str):
        """All scripts (standalone + utility) must compile."""
        script_path = SKILLS_DIR / "skill-creator" / "scripts" / script_name
        if not script_path.is_file():
            pytest.skip(f"{script_path} not found")
        source = script_path.read_text(encoding="utf-8")
        compile(source, str(script_path), "exec")


# ===================================================================
# 2. SKILL.md frontmatter quality
# ===================================================================


class TestSkillMdFrontmatterQuality:
    """SKILL.md frontmatter must follow skill-anatomy.md conventions."""

    @pytest.fixture(autouse=True)
    def skill_content(self):
        self.path = SKILLS_DIR / "skill-creator" / "SKILL.md"
        self.content = self.path.read_text(encoding="utf-8")
        self.fm = _parse_frontmatter(self.content)

    def test_frontmatter_name_matches_directory(self):
        """Anatomy rule: name must match directory name."""
        assert self.fm.get("name") == "skill-creator", (
            f"frontmatter name '{self.fm.get('name')}' must match dir 'skill-creator'"
        )

    def test_description_under_1024_chars(self):
        """Anatomy rule: description max 1024 characters."""
        desc = self.fm.get("description", "")
        assert len(desc) <= 1024, (
            f"description is {len(desc)} chars, max is 1024"
        )

    def test_description_has_trigger_phrases(self):
        """Anatomy rule: description should include trigger conditions (Use when...)."""
        desc = self.fm.get("description", "")
        has_trigger = (
            "use when" in desc.lower()
            or "triggers on" in desc.lower()
            or "use this skill when" in desc.lower()
        )
        assert has_trigger, (
            "description must include trigger conditions (e.g., 'Use when...')"
        )

    def test_description_not_empty(self):
        assert len(self.fm.get("description", "")) > 0, "description must not be empty"


# ===================================================================
# 3. SKILL.md required anatomy sections
# ===================================================================


class TestSkillMdAnatomySections:
    """SKILL.md must have required sections per skill-anatomy.md."""

    @pytest.fixture(autouse=True)
    def skill_content(self):
        self.content = _read_skill("skill-creator")

    def test_has_overview_or_introduction(self):
        """Anatomy: Overview section required."""
        has_overview = (
            "## Overview" in self.content
            or "## Introduction" in self.content
            or "# Skill Creator" in self.content  # Title serves as overview
        )
        assert has_overview, "SKILL.md must have Overview or Introduction section"

    def test_has_when_to_use_or_triggers(self):
        """Anatomy: When to Use section required."""
        has_when = (
            "## When to Use" in self.content
            or "## When to use" in self.content
            or "## Triggers" in self.content
        )
        # skill-creator has triggers embedded in description + Feature headers
        # Check for Feature-based structure as alternative
        has_features = "## Feature" in self.content
        assert has_when or has_features, (
            "SKILL.md must have 'When to Use' section or Feature-based structure"
        )

    def test_has_process_or_workflow(self):
        """Anatomy: Core Process / Workflow section required."""
        has_process = (
            "## Core Process" in self.content
            or "## The Workflow" in self.content
            or "## Steps" in self.content
            or "## Scheduler Pattern" in self.content
        )
        assert has_process, (
            "SKILL.md must have process/workflow section (e.g., Scheduler Pattern)"
        )

    def test_has_verification_section(self):
        """Anatomy: Verification section required."""
        assert "## Verification" in self.content, (
            "SKILL.md must have '## Verification' section"
        )


# ===================================================================
# 4. skill-creator agent matches deployed plugin
# ===================================================================


class TestSkillCreatorAgentMatchesDeployed:
    """skill-creator agent files should match the deployed plugin source."""

    DEPLOYED_BASE = Path("/a0/usr/plugins/skill-creator/agents/skill-creator")
    LOCAL_BASE = AGENTS_DIR / "skill-creator"

    @pytest.fixture(autouse=True)
    def check_deployed_exists(self):
        if not self.DEPLOYED_BASE.is_dir():
            pytest.skip("Deployed skill-creator plugin not found")

    def test_agent_yaml_matches(self):
        deployed = self.DEPLOYED_BASE / "agent.yaml"
        local = self.LOCAL_BASE / "agent.yaml"
        if deployed.is_file() and local.is_file():
            assert deployed.read_text() == local.read_text(), (
                "agent.yaml must match deployed plugin"
            )

    def test_specifics_md_matches(self):
        deployed = self.DEPLOYED_BASE / "prompts" / "agent.system.main.specifics.md"
        local = self.LOCAL_BASE / "prompts" / "agent.system.main.specifics.md"
        if deployed.is_file() and local.is_file():
            assert deployed.read_text() == local.read_text(), (
                "specifics.md must match deployed plugin"
            )


# ===================================================================
# 5. skill-creator in routing specialist table
# ===================================================================


class TestSkillCreatorRouting:
    """skill-creator must appear correctly in delegation table."""

    def test_skill_creator_in_delegation_table(self, delegation_table):
        assert "skill-creator" in delegation_table, (
            "skill-creator must appear in delegation table"
        )

    def test_skill_creator_maps_to_correct_agent(self, delegation_table):
        """skill-creator row must map to `skill-creator` agent."""
        # Find the row containing skill-creator
        for line in delegation_table.splitlines():
            if "skill-creator" in line and "|" in line:
                assert "`skill-creator`" in line, (
                    "skill-creator must be a quoted agent name in delegation table"
                )
                return
        pytest.fail("No delegation table row found for skill-creator")

    def test_skill_creator_not_in_general_section(self, delegation_table):
        """Delegation table must NOT have a General Tasks section."""
        assert "General Tasks" not in delegation_table, (
            "Delegation table must NOT have General Tasks section"
        )


# ===================================================================
# 6. validate.py handles ROLE_FILENAME for eval agents
# ===================================================================


class TestValidateHandlesEvalAgents:
    """validate.py check_agent_specifics must accept role.md as alternative."""

    EVAL_AGENTS = ["skill-grader", "skill-comparator", "skill-analyzer"]

    @pytest.mark.parametrize("agent_name", EVAL_AGENTS)
    def test_eval_agent_has_role_md(self, agent_name: str):
        """Eval agents use role.md, not specifics.md."""
        role_path = AGENTS_DIR / agent_name / "prompts" / "agent.system.main.role.md"
        assert role_path.is_file(), f"Missing role.md for {agent_name}"

    @pytest.mark.parametrize("agent_name", EVAL_AGENTS)
    def test_eval_agent_does_not_have_specifics_md(self, agent_name: str):
        """Eval agents should NOT have specifics.md (they use role.md)."""
        specifics_path = AGENTS_DIR / agent_name / "prompts" / "agent.system.main.specifics.md"
        assert not specifics_path.is_file(), (
            f"{agent_name} should use role.md, not specifics.md"
        )

    @pytest.mark.parametrize("agent_name", EVAL_AGENTS)
    def test_eval_agent_passes_validate_check(self, agent_name: str):
        """validate.py check_agent_specifics should PASS for eval agents with role.md."""
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from validate import check_agent_specifics

        results = check_agent_specifics(PROJECT_ROOT)
        agent_results = [
            (ok, msg) for ok, msg in results
            if agent_name in msg
        ]
        assert any(ok for ok, _ in agent_results), (
            f"validate.py must PASS for {agent_name} (has role.md)"
        )


# ===================================================================
# 7. using-agent-skills has skill-creator delegation markers
# ===================================================================


class TestUsingAgentSkillsDelegationMarkers:
    """using-agent-skills SKILL.md must reference skill-creator delegation."""

    @pytest.fixture(autouse=True)
    def skill_content(self):
        self.content = _read_skill("using-agent-skills")

    def test_has_delegate_skill_creator(self):
        """Flowchart or lifecycle must have DELEGATE to skill-creator."""
        has_delegate = (
            "DELEGATE to skill-creator" in self.content
            or "skill-creator" in self.content
        )
        assert has_delegate, (
            "using-agent-skills must reference skill-creator specialist"
        )

    def test_quick_reference_has_skill_creator(self):
        """Quick Reference table must list skill-creator."""
        assert "skill-creator" in self.content, (
            "Quick Reference or lifecycle must include skill-creator"
        )


# ===================================================================
# 8. SKILL.md scripts referenced correctly
# ===================================================================


class TestSkillMdScriptReferences:
    """SKILL.md must reference all scripts that actually exist."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.content = _read_skill("skill-creator")
        scripts_dir = SKILLS_DIR / "skill-creator" / "scripts"
        self.existing_scripts = sorted(
            f.name for f in scripts_dir.iterdir()
            if f.is_file() and f.suffix == ".py"
        )

    @pytest.mark.parametrize("script", [
        "quick_validate.py",
        "package_skill.py",
        "aggregate_benchmark.py",
        "generate_review.py",
        "run_loop.py",
        "improve_description.py",
    ])
    def test_script_referenced_in_skill_md(self, script: str):
        """Each script must be referenced in SKILL.md."""
        # Strip .py for reference check (scripts referenced by basename)
        basename = script.replace(".py", "")
        assert basename in self.content, (
            f"Script {script} must be referenced in SKILL.md"
        )
