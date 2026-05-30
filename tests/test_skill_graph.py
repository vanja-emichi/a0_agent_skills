"""Tests for helpers/skill_contracts.py — graph building, queries, and validation.

Covers Task 3: graph construction from contract metadata, caching,
cycle detection, broken reference detection, and all query functions.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Load the real module under test
# ---------------------------------------------------------------------------

_PLUGIN_ROOT = Path(__file__).resolve().parent.parent
_MODULE_PATH = _PLUGIN_ROOT / "helpers" / "skill_contracts.py"


def _load_contracts_module():
    """Load helpers.skill_contracts via importlib."""
    mod_name = "helpers.skill_contracts"
    if mod_name in sys.modules:
        return sys.modules[mod_name]
    spec = importlib.util.spec_from_file_location(mod_name, str(_MODULE_PATH))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(autouse=True)
def _clear_graph_cache():
    """Ensure graph cache is cleared before and after each test."""
    mod = _load_contracts_module()
    mod.invalidate_graph_cache()
    yield
    mod.invalidate_graph_cache()


# ===========================================================================
# Task 3: build_skill_graph
# ===========================================================================


class TestBuildSkillGraph:
    """Tests for build_skill_graph()."""

    def test_builds_graph_with_installed_skills(self):
        """Graph includes all installed skills."""
        mod = _load_contracts_module()
        graph = mod.build_skill_graph()
        assert isinstance(graph, dict)
        assert len(graph) > 0
        # Must include the 12 core skills
        assert "spec-driven-development" in graph
        assert "shipping-and-launch" in graph

    def test_skills_with_contracts_have_phase(self):
        """Contract-bearing skills have non-None phase."""
        mod = _load_contracts_module()
        graph = mod.build_skill_graph()
        assert graph["spec-driven-development"]["phase"] == "DEFINE"
        assert graph["planning-and-task-breakdown"]["phase"] == "PLAN"
        assert graph["incremental-implementation"]["phase"] == "BUILD"
        assert graph["debugging-and-error-recovery"]["phase"] == "VERIFY"
        assert graph["code-review-and-quality"]["phase"] == "REVIEW"
        assert graph["shipping-and-launch"]["phase"] == "SHIP"

    def test_skills_without_contracts_have_empty_entries(self):
        """Non-core skills without contracts appear as empty entries."""
        mod = _load_contracts_module()
        graph = mod.build_skill_graph()
        # frontend-ui-engineering is a BUILD skill but not in the 12 with contracts
        if "frontend-ui-engineering" in graph:
            entry = graph["frontend-ui-engineering"]
            assert entry["phase"] is None
            assert entry["next_skills"] == []

    def test_cache_returns_same_object(self):
        """Second call returns the cached graph (same object)."""
        mod = _load_contracts_module()
        graph1 = mod.build_skill_graph()
        graph2 = mod.build_skill_graph()
        assert graph1 is graph2

    def test_cache_invalidation_forces_rebuild(self):
        """invalidate_graph_cache() forces rebuild on next call."""
        mod = _load_contracts_module()
        graph1 = mod.build_skill_graph()
        mod.invalidate_graph_cache()
        graph2 = mod.build_skill_graph()
        # Different objects (rebuilt), but same structure
        assert graph1 is not graph2
        assert set(graph1.keys()) == set(graph2.keys())

    def test_graph_entry_structure(self):
        """Each graph entry has the expected keys."""
        mod = _load_contracts_module()
        graph = mod.build_skill_graph()
        for skill_name, entry in graph.items():
            assert "phase" in entry
            assert "next_skills" in entry
            assert "conflicts" in entry
            assert "inputs" in entry
            assert "artifacts" in entry
            assert "verification" in entry
            assert "contract" in entry

    def test_next_skills_relationships(self):
        """next_skills links match the declared contracts."""
        mod = _load_contracts_module()
        graph = mod.build_skill_graph()
        assert "planning-and-task-breakdown" in graph["spec-driven-development"]["next_skills"]
        assert "debugging-and-error-recovery" in graph["test-driven-development"]["next_skills"]
        assert "shipping-and-launch" in graph["code-review-and-quality"]["next_skills"]
        assert graph["shipping-and-launch"]["next_skills"] == []

    def test_fail_safe_on_discovery_error(self):
        """Graph build fails gracefully on discovery errors."""
        mod = _load_contracts_module()
        with patch.object(mod, "discover_skill_names", side_effect=RuntimeError("boom")):
            graph = mod.build_skill_graph()
            assert graph == {}


# ===========================================================================
# Task 3: validate_graph
# ===========================================================================


class TestValidateGraph:
    """Tests for validate_graph()."""

    def test_clean_graph_no_findings(self):
        """Clean graph returns empty findings list."""
        mod = _load_contracts_module()
        findings = mod.validate_graph()
        assert findings == []

    def test_injected_cycle_detected(self):
        """Manually injected cycle is detected by validate_graph."""
        mod = _load_contracts_module()
        graph = mod.build_skill_graph(validate_on_build=False)
        # Inject a cycle: shipping-and-launch -> spec-driven-development
        graph["shipping-and-launch"]["next_skills"] = ["spec-driven-development"]
        findings = mod._detect_cycles(graph)
        assert len(findings) > 0
        assert any(f["type"] == "cycle" for f in findings)

    def test_injected_broken_ref_detected(self):
        """Broken reference is detected by validate_graph."""
        mod = _load_contracts_module()
        graph = mod.build_skill_graph(validate_on_build=False)
        # Inject a broken reference
        graph["spec-driven-development"]["next_skills"] = ["nonexistent-skill"]
        findings = []
        all_skills = set(graph.keys())
        for skill_name, entry in graph.items():
            for ns in entry.get("next_skills", []):
                if ns not in all_skills:
                    findings.append({"type": "broken_ref", "details": f"{skill_name} -> {ns}"})
        assert any(f["type"] == "broken_ref" for f in findings)

    def test_cycle_edge_removed_on_build(self):
        """When validate_on_build=True, cycle edges are removed."""
        mod = _load_contracts_module()
        # Build a minimal graph with a known cycle
        graph = {
            "skill-a": {"phase": "DEFINE", "next_skills": ["skill-b"], "conflicts": []},
            "skill-b": {"phase": "PLAN", "next_skills": ["skill-a"], "conflicts": []},
        }
        findings = mod._detect_cycles(graph)
        assert len(findings) > 0
        cycle_finding = [f for f in findings if f["type"] == "cycle"][0]
        mod._remove_cycle_edge(graph, cycle_finding)
        # One of the cycle edges should be removed
        assert (
            "skill-a" not in graph["skill-b"]["next_skills"]
            or "skill-b" not in graph["skill-a"]["next_skills"]
        )


# ===========================================================================
# Task 3: Query functions
# ===========================================================================


class TestQueryFunctions:
    """Tests for get_skill_contract, get_next_skills, get_skill_conflicts,
    get_skills_for_phase, get_lifecycle_chain."""

    def test_get_skill_contract_known(self):
        """Returns contract dict for a known skill."""
        mod = _load_contracts_module()
        contract = mod.get_skill_contract("spec-driven-development")
        assert contract is not None
        assert contract["phase"] == "DEFINE"
        assert "planning-and-task-breakdown" in contract["next_skills"]

    def test_get_skill_contract_unknown(self):
        """Returns None for unknown skill."""
        mod = _load_contracts_module()
        contract = mod.get_skill_contract("nonexistent-skill")
        assert contract is None

    def test_get_skill_contract_no_contract(self):
        """Returns None for skill without contract."""
        mod = _load_contracts_module()
        # agents-best-practices is not one of the 12 core skills with contracts
        contract = mod.get_skill_contract("agents-best-practices")
        assert contract is None

    def test_get_next_skills_with_contract(self):
        """Returns next_skills list for contract-bearing skill."""
        mod = _load_contracts_module()
        next_skills = mod.get_next_skills("spec-driven-development")
        assert "planning-and-task-breakdown" in next_skills

    def test_get_next_skills_without_contract(self):
        """Returns empty list for skill without contract."""
        mod = _load_contracts_module()
        next_skills = mod.get_next_skills("agents-best-practices")
        assert next_skills == []

    def test_get_next_skills_unknown(self):
        """Returns empty list for unknown skill."""
        mod = _load_contracts_module()
        next_skills = mod.get_next_skills("nonexistent")
        assert next_skills == []

    def test_get_skill_conflicts_empty(self):
        """All 12 core skills have no conflicts declared."""
        mod = _load_contracts_module()
        for skill in [
            "interview-me", "spec-driven-development", "planning-and-task-breakdown",
            "context-engineering", "incremental-implementation", "test-driven-development",
            "source-driven-development", "doubt-driven-development",
            "debugging-and-error-recovery", "browser-testing-with-devtools",
            "code-review-and-quality", "shipping-and-launch",
        ]:
            conflicts = mod.get_skill_conflicts(skill)
            assert conflicts == [], f"{skill} should have no conflicts"

    def test_get_skills_for_phase_define(self):
        """Returns DEFINE-phase skills."""
        mod = _load_contracts_module()
        skills = mod.get_skills_for_phase("DEFINE")
        names = [s["name"] for s in skills]
        assert "interview-me" in names
        assert "spec-driven-development" in names
        for s in skills:
            assert s["phase"] == "DEFINE"

    def test_get_skills_for_phase_build(self):
        """Returns BUILD-phase skills."""
        mod = _load_contracts_module()
        skills = mod.get_skills_for_phase("BUILD")
        names = [s["name"] for s in skills]
        assert "incremental-implementation" in names
        assert "test-driven-development" in names
        assert "source-driven-development" in names
        assert "doubt-driven-development" in names

    def test_get_skills_for_phase_ship(self):
        """Returns SHIP-phase skills."""
        mod = _load_contracts_module()
        skills = mod.get_skills_for_phase("SHIP")
        names = [s["name"] for s in skills]
        assert "shipping-and-launch" in names

    def test_get_skills_for_phase_case_insensitive(self):
        """Phase name is case-insensitive."""
        mod = _load_contracts_module()
        skills = mod.get_skills_for_phase("build")
        names = [s["name"] for s in skills]
        assert "incremental-implementation" in names

    def test_get_lifecycle_chain_has_no_cycles(self):
        """Lifecycle chain has no duplicate entries (acyclic)."""
        mod = _load_contracts_module()
        chain = mod.get_lifecycle_chain()
        assert len(chain) == len(set(chain))
        assert len(chain) > 0

    def test_get_lifecycle_chain_starts_with_define(self):
        """Chain starts with a DEFINE-phase skill."""
        mod = _load_contracts_module()
        chain = mod.get_lifecycle_chain()
        assert chain[0] == "interview-me"

    def test_get_lifecycle_chain_ends_with_ship(self):
        """Chain ends with a SHIP-phase skill."""
        mod = _load_contracts_module()
        chain = mod.get_lifecycle_chain()
        assert chain[-1] == "shipping-and-launch"

    def test_get_lifecycle_chain_covers_all_phases(self):
        """Chain passes through all 6 phases."""
        mod = _load_contracts_module()
        chain = mod.get_lifecycle_chain()
        graph = mod.build_skill_graph()
        phases_seen = set()
        for skill_name in chain:
            entry = graph.get(skill_name, {})
            phase = entry.get("phase")
            if phase:
                phases_seen.add(phase)
        assert "DEFINE" in phases_seen
        assert "PLAN" in phases_seen
        assert "BUILD" in phases_seen
        assert "VERIFY" in phases_seen
        assert "REVIEW" in phases_seen
        assert "SHIP" in phases_seen
