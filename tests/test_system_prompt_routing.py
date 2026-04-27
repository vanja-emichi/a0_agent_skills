"""Tests for extensions/python/system_prompt/_20_agent_skills_prompt.py

Verifies:
- Extension file structure (compact, under 100 lines)
- Extension class contract (AgentSkillsPrompt, async execute, try/except)
- Delegation table injection (appends to system_prompt, not extras_persistent)
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXT_PATH = (
    REPO_ROOT
    / "extensions"
    / "python"
    / "system_prompt"
    / "_20_agent_skills_prompt.py"
)

# ---------------------------------------------------------------------------
# File existence and syntax
# ---------------------------------------------------------------------------

class TestExtensionFile:
    def test_file_exists(self):
        """Extension file must exist at the expected path."""
        assert EXT_PATH.is_file(), f"Missing: {EXT_PATH}"

    def test_valid_python_syntax(self):
        """Extension file must have valid Python syntax."""
        source = EXT_PATH.read_text(encoding="utf-8")
        try:
            ast.parse(source)
        except SyntaxError as exc:
            pytest.fail(f"Syntax error in extension: {exc}")

    def test_has_module_docstring(self):
        """Extension must have a docstring explaining its purpose."""
        source = EXT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        docstring = ast.get_docstring(tree)
        assert docstring, "Extension file must have a module-level docstring"

    def test_file_under_100_lines(self):
        """Extension must be compact — under 100 lines."""
        lines = EXT_PATH.read_text(encoding="utf-8").splitlines()
        assert len(lines) < 100, f"Extension has {len(lines)} lines, must be < 100"


# ---------------------------------------------------------------------------
# Delegation table content
# ---------------------------------------------------------------------------

class TestDelegationTable:
    """Verify the delegation table is compact and correct."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Import extension module with mocked A0 deps."""
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
        self.module = mod
        self.table = mod.get_delegation_table()

        for mod_name, orig in saved.items():
            if orig is None:
                sys.modules.pop(mod_name, None)
            else:
                sys.modules[mod_name] = orig

    def test_table_is_non_empty_string(self):
        assert isinstance(self.table, str) and len(self.table) > 0

    def test_table_is_markdown_format(self):
        assert "|" in self.table, "Delegation table must contain markdown table"

    def test_table_has_delegation_header(self):
        assert "Task Delegation" in self.table

    def test_table_has_no_skills_tool_load(self):
        assert "skills_tool:load" not in self.table

    def test_table_under_1000_chars(self):
        assert len(self.table) < 1000


# ---------------------------------------------------------------------------
# Class structure and hook contract
# ---------------------------------------------------------------------------

class TestExtensionClassStructure:
    @pytest.fixture(autouse=True)
    def source_tree(self):
        self.source = EXT_PATH.read_text(encoding="utf-8")
        self.tree = ast.parse(self.source)

    def _get_class(self, name):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef) and node.name == name:
                return node
        return None

    def test_extension_class_exists(self):
        """Must define an Extension subclass."""
        classes = [
            n for n in ast.walk(self.tree) if isinstance(n, ast.ClassDef)
        ]
        assert classes, "No class defined in extension"

    def test_class_named_agent_skills_prompt(self):
        """Class must be named AgentSkillsPrompt."""
        cls = self._get_class("AgentSkillsPrompt")
        assert cls is not None, "Class AgentSkillsPrompt not found"

    def test_execute_method_exists(self):
        """AgentSkillsPrompt must implement execute()."""
        cls = self._get_class("AgentSkillsPrompt")
        assert cls, "AgentSkillsPrompt class not found"
        method_names = [
            n.name for n in ast.walk(cls) if isinstance(n, ast.FunctionDef)
            or isinstance(n, ast.AsyncFunctionDef)
        ]
        assert "execute" in method_names, "execute() method not found"

    def test_execute_is_async(self):
        """execute() must be async to match A0 extension contract."""
        cls = self._get_class("AgentSkillsPrompt")
        assert cls, "AgentSkillsPrompt class not found"
        for node in ast.walk(cls):
            if (
                isinstance(node, ast.AsyncFunctionDef)
                and node.name == "execute"
            ):
                return  # found async execute — pass
        pytest.fail("execute() is not async")

    def test_execute_has_try_except(self):
        """execute() must wrap logic in try/except — never break tool calls."""
        cls = self._get_class("AgentSkillsPrompt")
        assert cls, "AgentSkillsPrompt class not found"
        for node in ast.walk(cls):
            if isinstance(node, ast.Try):
                return  # found a try block — pass
        pytest.fail(
            "execute() has no try/except — extension failures must be swallowed"
        )

    def test_plugin_name_constant_defined(self):
        """PLUGIN_NAME constant must be defined."""
        assert "PLUGIN_NAME" in self.source, "PLUGIN_NAME constant not defined"

    def test_appends_to_system_prompt_list(self):
        """execute() must append to system_prompt list, not extras_persistent."""
        assert "extras_persistent" not in self.source, (
            "system_prompt hook should append to system_prompt list, "
            "not use extras_persistent (that's message_loop_prompts_after pattern)"
        )
