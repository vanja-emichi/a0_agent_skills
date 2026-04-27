"""Tests for delegation table and command templates.

Tests cover:
1. Command templates delegate correctly
2. Delegation table content (compact version)
3. Skill anatomy compliance
4. using-agent-skills delegation markers
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = REPO_ROOT / "commands"
SKILLS_DIR = REPO_ROOT / "skills"
EXT_PATH = (
    REPO_ROOT
    / "extensions"
    / "python"
    / "system_prompt"
    / "_20_agent_skills_prompt.py"
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_command(name: str) -> str:
    """Read a command template file."""
    path = COMMANDS_DIR / f"{name}.txt"
    assert path.is_file(), f"Missing command template: {path}"
    return path.read_text(encoding="utf-8")


def _read_skill(name: str) -> str:
    """Read a SKILL.md file."""
    path = SKILLS_DIR / name / "SKILL.md"
    assert path.is_file(), f"Missing skill: {path}"
    return path.read_text(encoding="utf-8")


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
    """Get the compact delegation table."""
    return routing_module.get_delegation_table()


# ===================================================================
# 1. Command templates delegate correctly
# ===================================================================


class TestReviewCommand:
    """"/review must delegate to code-reviewer specialist."""

    def test_contains_call_subordinate_code_reviewer(self):
        content = _read_command("review")
        assert "call_subordinate profile=code-reviewer" in content, (
            "/review must contain 'call_subordinate profile=code-reviewer'"
        )

    def test_mentions_code_review_and_quality_skill(self):
        content = _read_command("review")
        assert "code-review-and-quality" in content, (
            "/review must reference the code-review-and-quality skill"
        )


class TestTestCommand:
    """"/test must delegate to test-engineer specialist."""

    def test_contains_call_subordinate_test_engineer(self):
        content = _read_command("test")
        assert "call_subordinate profile=test-engineer" in content, (
            "/test must contain 'call_subordinate profile=test-engineer'"
        )

    def test_mentions_tdd_skill(self):
        content = _read_command("test")
        assert "test-driven-development" in content, (
            "/test must reference the test-driven-development skill"
        )


class TestSecurityCommand:
    """"/security must delegate to security-auditor specialist."""

    def test_security_template_exists(self):
        path = COMMANDS_DIR / "security.txt"
        assert path.is_file(), "Missing security.txt command template"

    def test_contains_call_subordinate_security_auditor(self):
        content = _read_command("security")
        assert "call_subordinate profile=security-auditor" in content, (
            "/security must contain 'call_subordinate profile=security-auditor'"
        )

    def test_mentions_security_and_hardening_skill(self):
        content = _read_command("security")
        assert "security-and-hardening" in content, (
            "/security must reference the security-and-hardening skill"
        )

    def test_security_yaml_exists(self):
        path = COMMANDS_DIR / "security.command.yaml"
        assert path.is_file(), "Missing security.command.yaml"


class TestCodeSimplifyCommand:
    """"/code-simplify final step must delegate to code-reviewer."""

    def test_final_step_delegates_to_code_reviewer(self):
        content = _read_command("code-simplify")
        assert "call_subordinate profile=code-reviewer" in content, (
            "/code-simplify must delegate to code-reviewer in final step"
        )

    def test_loads_code_simplification_skill_first(self):
        content = _read_command("code-simplify")
        assert "skills_tool:load code-simplification" in content, (
            "/code-simplify must load code-simplification skill"
        )

    def test_delegation_comes_after_simplification_steps(self):
        content = _read_command("code-simplify")
        lines = content.splitlines()
        load_idx = None
        delegate_idx = None
        for i, line in enumerate(lines):
            if "skills_tool:load code-simplification" in line:
                load_idx = i
            if "call_subordinate profile=code-reviewer" in line:
                delegate_idx = i
        assert load_idx is not None, "skills_tool:load not found"
        assert delegate_idx is not None, "call_subordinate not found"
        assert delegate_idx > load_idx, (
            "Delegation to code-reviewer must come after loading code-simplification"
        )


class TestDirectLoadCommands:
    """Commands that load skills directly must NOT contain call_subordinate."""

    @pytest.mark.parametrize("cmd", ["spec", "plan", "build"])
    def test_no_call_subordinate(self, cmd):
        content = _read_command(cmd)
        assert "call_subordinate" not in content, (
            f"/{cmd} should NOT contain call_subordinate (loads skill directly)"
        )

    @pytest.mark.parametrize("cmd", ["spec", "plan", "build"])
    def test_loads_skill_directly(self, cmd):
        content = _read_command(cmd)
        assert "skills_tool:load" in content, (
            f"/{cmd} must contain skills_tool:load"
        )


# ===================================================================
# 2. Delegation table content
# ===================================================================


class TestDelegationTableEntries:
    """Compact delegation table must list all 6 agents."""

    EXPECTED_AGENTS = [
        "researcher",
        "code-reviewer",
        "test-engineer",
        "security-auditor",
        "skill-creator",
        "developer",
    ]

    def test_has_task_delegation_header(self, delegation_table):
        assert "Task Delegation" in delegation_table, (
            "Delegation table must have 'Task Delegation' header"
        )

    @pytest.mark.parametrize("agent", EXPECTED_AGENTS)
    def test_lists_all_agents(self, delegation_table, agent):
        assert agent in delegation_table, (
            f"Delegation table must list '{agent}'"
        )

    def test_has_delegate_rule(self, delegation_table):
        assert "Delegate" in delegation_table, (
            "Delegation table must contain delegation rule"
        )

    def test_has_no_skills_tool_load(self, delegation_table):
        assert "skills_tool:load" not in delegation_table, (
            "Delegation table must NOT contain skills_tool:load"
        )

    def test_has_no_general_tasks(self, delegation_table):
        assert "General Tasks" not in delegation_table, (
            "Delegation table must NOT have General Tasks section"
        )

    def test_has_two_column_table(self, delegation_table):
        assert "| Intent |" in delegation_table, (
            "Table must have 'Intent' column header"
        )


class TestDelegationTableStructure:
    """Delegation table must be compact."""

    def test_output_under_1000_chars(self, delegation_table):
        assert len(delegation_table) < 1000, (
            f"Delegation table is {len(delegation_table)} chars, must be < 1000"
        )

    def test_has_simple_answer_guidance(self, delegation_table):
        assert "simple" in delegation_table.lower(), (
            "Delegation table must have guidance for simple questions"
        )


# ===================================================================
# 3. Skill anatomy compliance
# ===================================================================


class TestIdeaRefineAnatomy:
    """idea-refine SKILL.md must follow anatomy conventions."""

    @pytest.fixture(autouse=True)
    def skill_content(self):
        self.content = _read_skill("idea-refine")

    def test_has_common_rationalizations_section(self):
        assert "## Common Rationalizations" in self.content, (
            "idea-refine must have '## Common Rationalizations' section"
        )

    def test_has_rationalizations_table(self):
        assert "| Rationalization | Reality |" in self.content, (
            "idea-refine must have Common Rationalizations table"
        )

    def test_has_red_flags_section(self):
        assert "## Red Flags" in self.content, (
            "idea-refine must have '## Red Flags' section"
        )

    def test_has_verification_section(self):
        assert "## Verification" in self.content, (
            "idea-refine must have '## Verification' section"
        )

    def test_no_anti_patterns_heading(self):
        assert "## Anti-patterns" not in self.content, (
            "idea-refine should NOT have '## Anti-patterns' (renamed to Common Rationalizations)"
        )


class TestUsingAgentSkillsAnatomy:
    """using-agent-skills SKILL.md must follow anatomy conventions."""

    @pytest.fixture(autouse=True)
    def skill_content(self):
        self.content = _read_skill("using-agent-skills")

    def test_has_common_rationalizations_section(self):
        assert "## Common Rationalizations" in self.content, (
            "using-agent-skills must have '## Common Rationalizations' section"
        )

    def test_has_rationalizations_table(self):
        assert "| Rationalization | Reality |" in self.content, (
            "using-agent-skills must have Common Rationalizations table"
        )

    def test_has_red_flags_section(self):
        assert "## Red Flags" in self.content, (
            "using-agent-skills must have '## Red Flags' section"
        )

    def test_has_verification_section(self):
        assert "## Verification" in self.content, (
            "using-agent-skills must have '## Verification' section"
        )

    def test_no_failure_modes_heading(self):
        assert "## Failure Modes" not in self.content, (
            "using-agent-skills should NOT have '## Failure Modes' (renamed to Common Rationalizations)"
        )


# ===================================================================
# 4. using-agent-skills delegation markers
# ===================================================================


class TestFlowchartDelegationMarkers:
    """Flowchart in using-agent-skills must have DELEGATE markers."""

    @pytest.fixture(autouse=True)
    def skill_content(self):
        self.content = _read_skill("using-agent-skills")

    def test_flowchart_has_delegate_test_engineer(self):
        assert "DELEGATE to test-engineer" in self.content, (
            "Flowchart must contain 'DELEGATE to test-engineer'"
        )

    def test_flowchart_has_delegate_code_reviewer(self):
        assert "DELEGATE to code-reviewer" in self.content, (
            "Flowchart must contain 'DELEGATE to code-reviewer'"
        )

    def test_flowchart_has_delegate_security_auditor(self):
        assert "DELEGATE to security-auditor" in self.content, (
            "Flowchart must contain 'DELEGATE to security-auditor'"
        )


class TestQuickReferenceMethodColumn:
    """Quick Reference table must have Method column."""

    @pytest.fixture(autouse=True)
    def skill_content(self):
        self.content = _read_skill("using-agent-skills")

    def test_has_method_column(self):
        assert "| Method |" in self.content, (
            "Quick Reference table must have 'Method' column"
        )

    def test_delegate_method_for_test_engineer(self):
        assert "Delegate → test-engineer" in self.content, (
            "Quick Reference must show 'Delegate → test-engineer' in Method column"
        )

    def test_delegate_method_for_code_reviewer(self):
        assert "Delegate → code-reviewer" in self.content, (
            "Quick Reference must show 'Delegate → code-reviewer' in Method column"
        )

    def test_delegate_method_for_security_auditor(self):
        assert "Delegate → security-auditor" in self.content, (
            "Quick Reference must show 'Delegate → security-auditor' in Method column"
        )

    def test_load_skill_method_for_general(self):
        assert "Load skill" in self.content, (
            "Quick Reference must show 'Load skill' for general skills"
        )


class TestLifecycleDelegationMarkers:
    """Lifecycle sequence must have DELEGATE markers."""

    @pytest.fixture(autouse=True)
    def skill_content(self):
        self.content = _read_skill("using-agent-skills")

    def test_lifecycle_has_delegate_test_engineer(self):
        assert "test-driven-development     → DELEGATE to test-engineer" in self.content, (
            "Lifecycle must mark test-driven-development as DELEGATE to test-engineer"
        )

    def test_lifecycle_has_delegate_code_reviewer(self):
        assert "code-review-and-quality     → DELEGATE to code-reviewer" in self.content, (
            "Lifecycle must mark code-review-and-quality as DELEGATE to code-reviewer"
        )

    def test_lifecycle_has_security_auditor_reference(self):
        assert "DELEGATE to security-auditor" in self.content, (
            "Lifecycle or notes must reference DELEGATE to security-auditor"
        )
