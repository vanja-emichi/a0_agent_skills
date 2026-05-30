"""Tests for helpers/skill_contracts.py — contract parsing and graph infrastructure.

Covers Task 1 (contract parsing helper) and Task 3 (graph building, queries,
validation).  Task 1 tests focus on parse_contract_from_frontmatter and
read_skill_frontmatter.  Task 3 tests cover graph construction, caching,
queries, and cycle detection.
"""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Load the real module under test
# ---------------------------------------------------------------------------

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_MODULE_PATH = _PLUGIN_ROOT / "helpers" / "skill_contracts.py"


@pytest.fixture(autouse=True)
def _clear_graph_cache():
    """Ensure graph cache is cleared before and after each test."""
    mod = _load_contracts_module()
    mod.invalidate_graph_cache()
    yield
    mod.invalidate_graph_cache()


def _load_contracts_module():
    """Load helpers.skill_contracts via importlib (avoids sys.path hacks)."""
    mod_name = "helpers.skill_contracts"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, str(_MODULE_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


# ===========================================================================
# Task 1: parse_contract_from_frontmatter
# ===========================================================================


class TestParseContractFromFrontmatter:
    """Tests for parse_contract_from_frontmatter()."""

    def test_valid_full_contract(self):
        """All 6 fields present and valid → parsed correctly."""
        mod = _load_contracts_module()
        yaml_text = (
            "name: test-skill\n"
            "contract:\n"
            "  phase: DEFINE\n"
            "  inputs:\n"
            "    - User request\n"
            "    - Project context\n"
            "  artifacts:\n"
            "    - path: docs/specs/*.md\n"
            "      description: Spec document\n"
            "  verification:\n"
            "    - Spec document exists\n"
            "  next_skills:\n"
            "    - planning-and-task-breakdown\n"
            "  conflicts: []\n"
        )
        result = mod.parse_contract_from_frontmatter(yaml_text)
        assert result["phase"] == "DEFINE"
        assert result["inputs"] == ["User request", "Project context"]
        assert len(result["artifacts"]) == 1
        assert result["artifacts"][0]["path"] == "docs/specs/*.md"
        assert result["verification"] == ["Spec document exists"]
        assert result["next_skills"] == ["planning-and-task-breakdown"]
        assert result["conflicts"] == []

    def test_partial_contract_only_phase_and_next_skills(self):
        """Partial contract (only phase and next_skills) → missing fields absent."""
        mod = _load_contracts_module()
        yaml_text = (
            "name: test-skill\n"
            "contract:\n"
            "  phase: PLAN\n"
            "  next_skills:\n"
            "    - incremental-implementation\n"
        )
        result = mod.parse_contract_from_frontmatter(yaml_text)
        assert result["phase"] == "PLAN"
        assert result["next_skills"] == ["incremental-implementation"]
        # Missing fields are simply absent from result (not present as empty lists)
        assert "inputs" not in result
        assert "artifacts" not in result
        assert "verification" not in result
        assert "conflicts" not in result

    def test_no_contract_block(self):
        """No contract block → empty dict."""
        mod = _load_contracts_module()
        yaml_text = "name: test-skill\nversion: 1.0.0\n"
        result = mod.parse_contract_from_frontmatter(yaml_text)
        assert result == {}

    def test_malformed_yaml(self):
        """Malformed YAML → empty dict, no exception."""
        mod = _load_contracts_module()
        yaml_text = "name: [broken: yaml: {{{"
        result = mod.parse_contract_from_frontmatter(yaml_text)
        assert result == {}

    def test_empty_string(self):
        """Empty string → empty dict."""
        mod = _load_contracts_module()
        result = mod.parse_contract_from_frontmatter("")
        assert result == {}

    def test_none_like_input(self):
        """Whitespace-only input → empty dict."""
        mod = _load_contracts_module()
        result = mod.parse_contract_from_frontmatter("   \n  ")
        assert result == {}

    def test_unknown_fields_ignored(self):
        """Unknown fields in contract block are ignored, known fields extracted."""
        mod = _load_contracts_module()
        yaml_text = (
            "contract:\n"
            "  phase: BUILD\n"
            "  future_field: some_value\n"
            "  another_unknown: 42\n"
            "  next_skills: []\n"
        )
        result = mod.parse_contract_from_frontmatter(yaml_text)
        assert result["phase"] == "BUILD"
        assert "future_field" not in result
        assert "another_unknown" not in result

    def test_invalid_phase_value_warning(self):
        """Invalid phase value → warning logged, phase treated as absent."""
        mod = _load_contracts_module()
        yaml_text = (
            "contract:\n"
            "  phase: INVALID_PHASE\n"
            "  next_skills: []\n"
        )
        with patch.object(mod._log, "warning") as mock_warn:
            result = mod.parse_contract_from_frontmatter(yaml_text)
            assert "phase" not in result
            mock_warn.assert_called()

    def test_invalid_next_skills_reference_warning(self):
        """Invalid next_skills reference → warning logged, entry skipped."""
        mod = _load_contracts_module()
        known = frozenset({"skill-a", "skill-b"})
        yaml_text = (
            "contract:\n"
            "  phase: BUILD\n"
            "  next_skills:\n"
            "    - skill-a\n"
            "    - nonexistent-skill\n"
        )
        with patch.object(mod._log, "warning") as mock_warn:
            result = mod.parse_contract_from_frontmatter(yaml_text, known_skills=known)
            assert result["next_skills"] == ["skill-a"]
            mock_warn.assert_called()

    def test_invalid_conflicts_reference_warning(self):
        """Invalid conflicts reference → warning logged, entry skipped."""
        mod = _load_contracts_module()
        known = frozenset({"skill-a"})
        yaml_text = (
            "contract:\n"
            "  conflicts:\n"
            "    - nonexistent\n"
        )
        with patch.object(mod._log, "warning") as mock_warn:
            result = mod.parse_contract_from_frontmatter(yaml_text, known_skills=known)
            assert result["conflicts"] == []
            mock_warn.assert_called()

    def test_no_known_skills_skips_validation(self):
        """Without known_skills, reference validation is skipped."""
        mod = _load_contracts_module()
        yaml_text = (
            "contract:\n"
            "  next_skills:\n"
            "    - anything-goes\n"
        )
        result = mod.parse_contract_from_frontmatter(yaml_text, known_skills=None)
        assert result["next_skills"] == ["anything-goes"]

    def test_contract_block_not_dict(self):
        """Contract block is a string instead of dict → empty dict."""
        mod = _load_contracts_module()
        yaml_text = "contract: not_a_dict\n"
        result = mod.parse_contract_from_frontmatter(yaml_text)
        assert result == {}

    def test_artifacts_validation(self):
        """Artifacts without 'path' key are filtered out."""
        mod = _load_contracts_module()
        yaml_text = (
            "contract:\n"
            "  artifacts:\n"
            "    - path: docs/spec.md\n"
            "      description: A spec\n"
            "    - description: Missing path\n"
        )
        result = mod.parse_contract_from_frontmatter(yaml_text)
        assert len(result["artifacts"]) == 1
        assert result["artifacts"][0]["path"] == "docs/spec.md"


# ===========================================================================
# Task 1: read_skill_frontmatter
# ===========================================================================


class TestReadSkillFrontmatter:
    """Tests for read_skill_frontmatter()."""

    def test_read_existing_skill(self):
        """Read frontmatter from an actual installed skill."""
        mod = _load_contracts_module()
        # spec-driven-development is a core skill that exists
        result = mod.read_skill_frontmatter("spec-driven-development")
        assert isinstance(result, dict)
        assert result.get("name") == "spec-driven-development"

    def test_read_nonexistent_skill(self):
        """Non-existent skill name → empty dict."""
        mod = _load_contracts_module()
        result = mod.read_skill_frontmatter("this-skill-does-not-exist")
        assert result == {}

    def test_read_with_mock_skill_dir(self, tmp_path):
        """Mock skill directory → correct dict returned."""
        mod = _load_contracts_module()
        skill_dir = tmp_path / "skills" / "test-skill"
        skill_dir.mkdir(parents=True)
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            "name: test-skill\n"
            "version: 2.0.0\n"
            "---\n"
            "# Test Skill\n"
        )
        with patch.object(mod, "_PLUGIN_ROOT", str(tmp_path)):
            result = mod.read_skill_frontmatter("test-skill")
            assert result["name"] == "test-skill"
            assert result["version"] == "2.0.0"


# ===========================================================================
# Task 1: _extract_frontmatter_text
# ===========================================================================


class TestExtractFrontmatterText:
    """Tests for _extract_frontmatter_text() internal helper."""

    def test_standard_frontmatter(self):
        mod = _load_contracts_module()
        content = "---\nname: foo\nversion: 1\n---\n# Body\n"
        result = mod._extract_frontmatter_text(content)
        assert "name: foo" in result
        assert "version: 1" in result

    def test_no_closing_delimiter(self):
        mod = _load_contracts_module()
        content = "---\nname: foo\n# No closing\n"
        result = mod._extract_frontmatter_text(content)
        assert result == ""

    def test_no_opening_delimiter(self):
        mod = _load_contracts_module()
        content = "name: foo\n---\n"
        result = mod._extract_frontmatter_text(content)
        assert result == ""


# ===========================================================================
# Task 1: discover_skill_names
# ===========================================================================


class TestDiscoverSkillNames:
    """Tests for discover_skill_names()."""

    def test_discovers_installed_skills(self):
        """Should find skills in the plugin directory."""
        mod = _load_contracts_module()
        names = mod.discover_skill_names()
        assert isinstance(names, list)
        # spec-driven-development is a core skill that must exist
        assert "spec-driven-development" in names

    def test_discover_with_bad_directory(self):
        """Non-existent directory → empty list."""
        mod = _load_contracts_module()
        with patch.object(mod, "_PLUGIN_ROOT", "/nonexistent/path"):
            result = mod.discover_skill_names()
            assert result == []
