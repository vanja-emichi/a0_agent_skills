"""Tests for extensions/python/message_loop_prompts_after/_20_inject_meta_skill.py

TDD RED → GREEN:
- Write tests describing expected behavior (they should FAIL first if behavior absent)
- Prove the new extension correctly covers all 21 skills in its routing table
- Prove the extension follows plugin conventions (structure, error handling)
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXT_PATH = (
    REPO_ROOT
    / "extensions"
    / "python"
    / "message_loop_prompts_after"
    / "_20_inject_meta_skill.py"
)
SKILLS_DIR = REPO_ROOT / "skills"

# All 21 skills that must appear in the routing table
ALL_SKILLS = [
    "idea-refine",
    "spec-driven-development",
    "planning-and-task-breakdown",
    "incremental-implementation",
    "frontend-ui-engineering",
    "api-and-interface-design",
    "source-driven-development",
    "context-engineering",
    "test-driven-development",
    "browser-testing-with-devtools",
    "debugging-and-error-recovery",
    "code-review-and-quality",
    "security-and-hardening",
    "performance-optimization",
    "code-simplification",
    "git-workflow-and-versioning",
    "ci-cd-and-automation",
    "documentation-and-adrs",
    "deprecation-and-migration",
    "shipping-and-launch",
    "using-agent-skills",
]


def _load_module():
    """Load the extension module without importing A0 framework deps."""
    source = EXT_PATH.read_text(encoding="utf-8")
    # Parse only — don't exec (avoids needing A0 runtime imports)
    return source


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

    def test_file_under_200_lines(self):
        """Extension must stay concise — under 200 lines."""
        lines = EXT_PATH.read_text(encoding="utf-8").splitlines()
        assert len(lines) < 200, f"Extension has {len(lines)} lines, must be < 200"


# ---------------------------------------------------------------------------
# Routing table: all 21 skills must appear
# ---------------------------------------------------------------------------

class TestRoutingTableCoverage:
    @pytest.fixture(autouse=True)
    def routing_table(self):
        """Extract the _ROUTING_TABLE constant from the extension source."""
        source = EXT_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(t, ast.Name) and t.id == "_ROUTING_TABLE"
                    for t in node.targets
                )
            ):
                if isinstance(node.value, ast.Constant):
                    self.table = node.value.value
                    return
        pytest.fail("_ROUTING_TABLE constant not found in extension")

    def test_routing_table_exists(self):
        """_ROUTING_TABLE constant must be defined."""
        assert self.table, "_ROUTING_TABLE must be a non-empty string"

    def test_routing_table_is_markdown_table(self):
        """Routing table must be in markdown table format."""
        assert "|" in self.table, "_ROUTING_TABLE must contain a markdown table"
        assert "Intent" in self.table or "intent" in self.table, (
            "Routing table must have an Intent column header"
        )

    @pytest.mark.parametrize("skill", ALL_SKILLS)
    def test_all_21_skills_in_routing_table(self, skill):
        """Every skill must appear in the routing table — none may be orphaned."""
        assert skill in self.table, (
            f"Skill '{skill}' is missing from _ROUTING_TABLE — "
            f"it will never be auto-activated from natural language"
        )

    def test_routing_table_references_skills_tool_load(self):
        """Routing table must show users how to invoke skills."""
        assert "skills_tool:load" in self.table, (
            "_ROUTING_TABLE must include skills_tool:load usage example"
        )

    def test_routing_table_covers_all_skill_dirs(self):
        """Every skill directory in skills/ must appear in the routing table."""
        skill_dirs = [d.name for d in SKILLS_DIR.iterdir() if d.is_dir()]
        missing = [s for s in skill_dirs if s not in self.table]
        assert not missing, (
            f"Skills in skills/ dir not covered by routing table: {missing}"
        )


# ---------------------------------------------------------------------------
# Class structure conventions
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

    def test_class_named_inject_meta_skill(self):
        """Class must be named InjectMetaSkill."""
        cls = self._get_class("InjectMetaSkill")
        assert cls is not None, "Class InjectMetaSkill not found"

    def test_execute_method_exists(self):
        """InjectMetaSkill must implement execute()."""
        cls = self._get_class("InjectMetaSkill")
        assert cls, "InjectMetaSkill class not found"
        method_names = [
            n.name for n in ast.walk(cls) if isinstance(n, ast.FunctionDef)
            or isinstance(n, ast.AsyncFunctionDef)
        ]
        assert "execute" in method_names, "execute() method not found"

    def test_execute_is_async(self):
        """execute() must be async to match A0 extension contract."""
        cls = self._get_class("InjectMetaSkill")
        assert cls, "InjectMetaSkill class not found"
        for node in ast.walk(cls):
            if (
                isinstance(node, ast.AsyncFunctionDef)
                and node.name == "execute"
            ):
                return  # found async execute — pass
        pytest.fail("execute() is not async")

    def test_execute_has_try_except(self):
        """execute() must wrap logic in try/except — never break tool calls."""
        cls = self._get_class("InjectMetaSkill")
        assert cls, "InjectMetaSkill class not found"
        for node in ast.walk(cls):
            if isinstance(node, ast.Try):
                return  # found a try block — pass
        pytest.fail(
            "execute() has no try/except — extension failures must be swallowed"
        )

    def test_plugin_name_constant_defined(self):
        """PLUGIN_NAME constant must be defined."""
        assert "PLUGIN_NAME" in self.source, "PLUGIN_NAME constant not defined"

    def test_uses_dynamic_path_not_hardcoded(self):
        """Must use Path(__file__) for plugin root — no hardcoded paths."""
        assert "__file__" in self.source, (
            "Must use Path(__file__) for plugin root discovery, not hardcoded paths"
        )
        assert "/a0/usr" not in self.source, (
            "Must not hardcode /a0/usr — use Path(__file__).resolve().parents[N]"
        )

    def test_uses_extras_persistent(self):
        """Must inject into extras_persistent (persists across turns)."""
        assert "extras_persistent" in self.source, (
            "Must use loop_data.extras_persistent to inject routing table"
        )
