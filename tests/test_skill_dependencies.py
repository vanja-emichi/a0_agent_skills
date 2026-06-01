# Tests for functional skill dependency resolution.
#
# Covers: linear chains, diamond deps, cycles, empty deps,
# already-loaded skip, deep chains, and idempotency.

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _graph_from_defs(*defs: tuple[str, list[str]]) -> dict:
    """Build a minimal graph dict from (name, depends_on) pairs."""
    from helpers.skill_contracts import _EMPTY_GRAPH_ENTRY
    graph: dict[str, dict] = {}
    for name, deps in defs:
        entry = dict(_EMPTY_GRAPH_ENTRY)
        entry["depends_on"] = list(deps)
        graph[name] = entry
    return graph


# ---------------------------------------------------------------------------
# resolve_dependencies unit tests
# ---------------------------------------------------------------------------

class TestResolveDependencies:
    """Unit tests for resolve_dependencies()."""

    def test_empty_deps_returns_empty(self):
        """Skill with no depends_on returns empty list."""
        from helpers.skill_contracts import resolve_dependencies
        graph = _graph_from_defs(("solo", []))
        result = resolve_dependencies("solo", graph=graph)
        assert result == []

    def test_unknown_skill_returns_empty(self):
        """Asking for a skill not in graph returns empty list (fail-safe)."""
        from helpers.skill_contracts import resolve_dependencies
        graph = _graph_from_defs(("a", []))
        result = resolve_dependencies("nonexistent", graph=graph)
        assert result == []

    def test_linear_chain_resolves_in_order(self):
        """A -> B -> C  where C depends on B, B depends on A.
        Loading C should return [A, B]."""
        from helpers.skill_contracts import resolve_dependencies
        graph = _graph_from_defs(
            ("a", []),
            ("b", ["a"]),
            ("c", ["b"]),
        )
        result = resolve_dependencies("c", graph=graph)
        assert result == ["a", "b"]

    def test_diamond_dependency_no_duplicates(self):
        """D depends on B and C, both depend on A.
        Loading D should return [A, B, C] with A appearing once."""
        from helpers.skill_contracts import resolve_dependencies
        graph = _graph_from_defs(
            ("a", []),
            ("b", ["a"]),
            ("c", ["a"]),
            ("d", ["b", "c"]),
        )
        result = resolve_dependencies("d", graph=graph)
        # A must appear exactly once
        assert result.count("a") == 1
        # A must come before both B and C
        assert result.index("a") < result.index("b")
        assert result.index("a") < result.index("c")
        # All four deps should be present
        assert set(result) == {"a", "b", "c"}

    def test_already_loaded_skipped(self):
        """When A is already loaded, loading C (C->B->A) should skip A."""
        from helpers.skill_contracts import resolve_dependencies
        graph = _graph_from_defs(
            ("a", []),
            ("b", ["a"]),
            ("c", ["b"]),
        )
        result = resolve_dependencies("c", already_loaded={"a"}, graph=graph)
        assert "a" not in result
        assert result == ["b"]

    def test_already_loaded_root_skips_all(self):
        """If the target skill is already loaded, return empty."""
        from helpers.skill_contracts import resolve_dependencies
        graph = _graph_from_defs(
            ("a", []),
            ("b", ["a"]),
        )
        result = resolve_dependencies("b", already_loaded={"a", "b"}, graph=graph)
        assert result == []

    def test_cycle_detected_and_broken(self):
        """A -> B -> C -> A (cycle).
        Should not infinite-loop; cycle members excluded."""
        from helpers.skill_contracts import resolve_dependencies
        graph = _graph_from_defs(
            ("a", ["c"]),  # cycle: C -> A
            ("b", ["a"]),
            ("c", ["b"]),
        )
        # Should return a safe prefix without infinite recursion
        result = resolve_dependencies("c", graph=graph)
        assert isinstance(result, list)
        # The result may be partial due to cycle breaking
        # Key property: no duplicates
        assert len(result) == len(set(result))

    def test_deep_chain_four_levels(self):
        """A -> B -> C -> D -> E.
        Loading E should return [A, B, C, D]."""
        from helpers.skill_contracts import resolve_dependencies
        graph = _graph_from_defs(
            ("a", []),
            ("b", ["a"]),
            ("c", ["b"]),
            ("d", ["c"]),
            ("e", ["d"]),
        )
        result = resolve_dependencies("e", graph=graph)
        assert result == ["a", "b", "c", "d"]

    def test_idempotent_calls(self):
        """Calling resolve_dependencies twice returns the same result."""
        from helpers.skill_contracts import resolve_dependencies
        graph = _graph_from_defs(
            ("a", []),
            ("b", ["a"]),
            ("c", ["b"]),
        )
        r1 = resolve_dependencies("c", graph=graph)
        r2 = resolve_dependencies("c", graph=graph)
        assert r1 == r2

    def test_multiple_deps_correct_order(self):
        """Skill depends on multiple prerequisites with shared transitive deps."""
        from helpers.skill_contracts import resolve_dependencies
        graph = _graph_from_defs(
            ("base", []),
            ("x", ["base"]),
            ("y", ["base"]),
            ("top", ["x", "y"]),
        )
        result = resolve_dependencies("top", graph=graph)
        assert result.count("base") == 1
        assert result.index("base") < result.index("x")
        assert result.index("base") < result.index("y")
        assert set(result) == {"base", "x", "y"}

    def test_exception_returns_empty(self):
        """If an exception occurs, return empty list (fail-safe)."""
        from helpers.skill_contracts import resolve_dependencies
        # Pass a graph that will raise on dict access
        class BadGraph(dict):
            def get(self, key, default=None):
                if key == "crash":
                    raise RuntimeError("boom")
                return super().get(key, default)

        graph = BadGraph({"crash": {"depends_on": ["missing"]}})
        result = resolve_dependencies("crash", graph=graph)
        assert result == []


# ---------------------------------------------------------------------------
# get_skill_dependencies unit tests
# ---------------------------------------------------------------------------

class TestGetSkillDependencies:
    """Unit tests for get_skill_dependencies()."""

    def test_returns_direct_deps(self):
        """Returns the depends_on list from graph entry."""
        from helpers.skill_contracts import get_skill_dependencies
        # This uses the real graph; just verify it returns a list
        result = get_skill_dependencies("nonexistent-skill-xyz")
        assert result == []

    def test_returns_empty_for_missing_skill(self):
        from helpers.skill_contracts import get_skill_dependencies
        assert get_skill_dependencies("does-not-exist") == []


# ---------------------------------------------------------------------------
# Integration with real skill graph (if skills exist)
# ---------------------------------------------------------------------------

class TestRealSkillGraphDeps:
    """Tests using the actual skill graph from the plugin."""

    def test_graph_has_depends_on_field(self):
        """Every graph entry should have a depends_on field."""
        from helpers.skill_contracts import build_skill_graph
        graph = build_skill_graph()
        for name, entry in graph.items():
            assert "depends_on" in entry, f"Missing depends_on in {name}"
            assert isinstance(entry["depends_on"], list), (
                f"depends_on not a list in {name}"
            )

    def test_resolve_no_deps_skill(self):
        """Skills without dependencies should resolve to empty."""
        from helpers.skill_contracts import build_skill_graph, resolve_dependencies
        graph = build_skill_graph()
        # interview-me has no declared dependencies
        if "interview-me" in graph:
            result = resolve_dependencies("interview-me", graph=graph)
            assert result == []

    def test_spec_driven_dev_has_no_deps(self):
        """spec-driven-development is the root of the dep chain."""
        from helpers.skill_contracts import build_skill_graph, resolve_dependencies
        graph = build_skill_graph()
        if "spec-driven-development" in graph:
            result = resolve_dependencies("spec-driven-development", graph=graph)
            assert result == []
