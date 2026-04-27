# test_clean_orchestrator.py — Tests for compact delegation table
"""Tests for the clean orchestrator architecture.

Verifies:
1. Agent0 loads ZERO skills (no first-turn auto-loader)
2. Extension generates a compact delegation table (~500 chars)
3. Table has Intent -> Agent mapping (2 columns)
4. All 6 agents listed in delegation table
5. Table does NOT contain skills_tool:load or General Tasks
6. Extension file is under 100 lines
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from .conftest import EXT_PATH, ML_DIR, REPO_ROOT


# ---------------------------------------------------------------------------
# 1. First-turn auto-loader must NOT exist
# ---------------------------------------------------------------------------


class TestNoAutoLoader:
    """Agent0 must not auto-load any skills."""

    def test_first_turn_file_deleted(self):
        first_turn = REPO_ROOT / "extensions" / "python" / "message_loop_start" / "_10_agent_skills_first_turn.py"
        assert not first_turn.is_file(), (
            f"First-turn auto-loader must be deleted: {first_turn}"
        )

    def test_no_message_loop_start_extensions(self):
        if ML_DIR.is_dir():
            py_files = list(ML_DIR.glob("*.py"))
            hook_files = [f for f in py_files if f.name != "__init__.py"]
            assert len(hook_files) == 0, (
                f"No message_loop_start hooks should exist, found: {hook_files}"
            )


# ---------------------------------------------------------------------------
# 2. Extension file structure
# ---------------------------------------------------------------------------


class TestExtensionStructure:
    """Extension file must be compact and clean."""

    def test_file_exists(self):
        assert EXT_PATH.is_file(), f"Missing: {EXT_PATH}"

    def test_valid_python_syntax(self, extension_source):
        try:
            ast.parse(extension_source)
        except SyntaxError as exc:
            pytest.fail(f"Syntax error: {exc}")

    def test_under_100_lines(self, extension_source):
        lines = extension_source.splitlines()
        assert len(lines) < 100, (
            f"Extension has {len(lines)} lines, must be < 100 for compactness"
        )

    def test_no_frontmatter_parser(self, extension_source):
        assert "_parse_frontmatter" not in extension_source, (
            "Extension must not have _parse_frontmatter (no SKILL.md scanning)"
        )

    def test_no_build_routing_table(self, extension_source):
        assert "build_routing_table" not in extension_source, (
            "Extension must not have build_routing_table (no dynamic generation)"
        )

    def test_no_specialist_skills_dict(self, extension_source):
        assert "SPECIALIST_SKILLS" not in extension_source, (
            "Extension must not have SPECIALIST_SKILLS dict"
        )


# ---------------------------------------------------------------------------
# 3. Delegation table content
# ---------------------------------------------------------------------------


class TestDelegationTableContent:
    """The generated output must be a compact delegation table."""

    EXPECTED_AGENTS = [
        "researcher",
        "code-reviewer",
        "test-engineer",
        "security-auditor",
        "skill-creator",
        "developer",
    ]

    def test_output_is_non_empty_string(self, delegation_table):
        assert isinstance(delegation_table, str) and len(delegation_table) > 0

    def test_has_delegation_header(self, delegation_table):
        assert "Task Delegation" in delegation_table

    def test_has_delegate_rule(self, delegation_table):
        assert "Delegate" in delegation_table

    def test_has_no_skills_tool_load(self, delegation_table):
        assert "skills_tool:load" not in delegation_table

    def test_has_no_general_tasks_section(self, delegation_table):
        assert "General Tasks" not in delegation_table

    def test_has_two_column_table(self, delegation_table):
        assert "| Intent |" in delegation_table

    @pytest.mark.parametrize("agent", EXPECTED_AGENTS)
    def test_lists_all_agents(self, delegation_table, agent):
        assert agent in delegation_table

    def test_output_under_1000_chars(self, delegation_table):
        assert len(delegation_table) < 1000

    def test_has_simple_answer_guidance(self, delegation_table):
        assert "simple" in delegation_table.lower()


# ---------------------------------------------------------------------------
# 4. Extension class contract
# ---------------------------------------------------------------------------


class TestExtensionContract:
    """Extension class must inject into system_prompt correctly."""

    def test_has_agent_skills_prompt_class(self, extension_module):
        assert hasattr(extension_module, "AgentSkillsPrompt")

    def test_class_has_execute_method(self, extension_module):
        cls = extension_module.AgentSkillsPrompt
        assert hasattr(cls, "execute")
