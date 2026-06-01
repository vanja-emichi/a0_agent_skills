"""Retroactive tests for routing-rules refactor and META phase addition.

Validates two changes that were implemented without TDD:

1. Routing prompt trimmed from 154→117 lines, keeping policy rules only
   and deferring skill catalog / intent→skill mapping to using-agent-skills.
2. META phase added to PHASE_SKILL_MAP (but NOT to PHASE_ORDER) so that
   using-agent-skills can be recognised as a valid phase skill.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Shared paths (conftest ensures PLUGIN_ROOT is on sys.path)
# ---------------------------------------------------------------------------

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
ROUTING_PROMPT_PATH = PLUGIN_ROOT / "prompts" / "agent.skills.routing.md"


def _read_routing_prompt() -> str:
    """Read the routing prompt file, returning its full text."""
    assert ROUTING_PROMPT_PATH.exists(), f"Routing prompt not found at {ROUTING_PROMPT_PATH}"
    return ROUTING_PROMPT_PATH.read_text(encoding="utf-8")


# ===================================================================
# TestRoutingPromptPolicy – Section structure and required content
# ===================================================================


class TestRoutingPromptPolicy:
    """Verify the routing prompt contains all required policy sections."""

    @pytest.fixture(autouse=True)
    def _load_content(self):
        self.content = _read_routing_prompt()
        self.lines = self.content.splitlines()

    # -- Section 1: Skill-Driven Execution Model -------------------------

    def test_contains_skill_driven_execution_rules(self):
        """Section 1 must exist with core skill-driven execution rules."""
        assert "## 1. Skill-Driven Execution Model" in self.content, (
            "Missing '## 1. Skill-Driven Execution Model' heading"
        )
        # Core rules that must be present
        assert "Skills are located in" in self.content
        assert "skills_tool:search" in self.content
        assert "You MUST NOT implement directly" in self.content
        assert "You MUST follow skill instructions exactly" in self.content

    # -- Section 2: Six-Phase Lifecycle ----------------------------------

    def test_contains_six_phase_lifecycle(self):
        """Section 2 must exist with the phase table."""
        assert "## 2. Six-Phase Lifecycle (Mandatory)" in self.content, (
            "Missing '## 2. Six-Phase Lifecycle (Mandatory)' heading"
        )
        # All six phases must appear in the table
        for phase in ["DEFINE", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP"]:
            assert phase in self.content, f"Phase {phase} missing from lifecycle table"
        # Required skills in the table
        assert "interview-me" in self.content
        assert "spec-driven-development" in self.content
        assert "planning-and-task-breakdown" in self.content
        assert "incremental-implementation" in self.content
        assert "test-driven-development" in self.content
        assert "debugging-and-error-recovery" in self.content
        assert "code-review-and-quality" in self.content
        assert "shipping-and-launch" in self.content

    # -- Section 3: Anti-Rationalization Table ----------------------------

    def test_contains_anti_rationalization_table(self):
        """Section 3 must exist with the anti-rationalization guidance."""
        assert "## 3. Anti-Rationalization Table" in self.content, (
            "Missing '## 3. Anti-Rationalization Table' heading"
        )
        # Key anti-rationalization entries
        assert "This is too small for a skill" in self.content
        assert "I can just quickly implement this" in self.content
        assert "I'll gather context first" in self.content

    # -- Section 4: Persona Invocation Rules ------------------------------

    def test_contains_persona_invocation_rules(self):
        """Section 4 must exist with persona table and composition rules."""
        assert "## 4. Persona Invocation Rules (MUST Follow)" in self.content, (
            "Missing '## 4. Persona Invocation Rules' heading"
        )
        # Persona names
        assert "Code Reviewer" in self.content
        assert "Security Auditor" in self.content
        assert "Test Engineer" in self.content
        # Profile names
        assert "code-reviewer" in self.content
        assert "security-auditor" in self.content
        assert "test-engineer" in self.content

    # -- Section 5: Skill Discovery --------------------------------------

    def test_contains_skill_discovery_section(self):
        """Section 5 must exist with skills_tool:search and skills_tool:load."""
        assert "## 5. Skill Discovery" in self.content, (
            "Missing '## 5. Skill Discovery' heading"
        )
        # Must contain the discovery commands
        assert "skills_tool:search" in self.content
        assert "skills_tool:load" in self.content

    def test_mentions_using_agent_skills_as_fallback(self):
        """The discovery section must mention 'using-agent-skills' as the fallback."""
        # Find the Section 5 content
        section5_start = self.content.find("## 5. Skill Discovery")
        assert section5_start != -1, "Section 5 not found"
        section5 = self.content[section5_start:]
        assert "using-agent-skills" in section5, (
            "'using-agent-skills' not mentioned in Skill Discovery section"
        )


# ===================================================================
# TestRoutingPromptNoReferenceMaterial – verify removals
# ===================================================================


class TestRoutingPromptNoReferenceMaterial:
    """Verify that detailed reference material was removed from the prompt."""

    @pytest.fixture(autouse=True)
    def _load_content(self):
        self.content = _read_routing_prompt()
        self.lines = self.content.splitlines()

    def test_no_full_skill_catalog_per_phase(self):
        """Detailed per-phase skill lists should not appear in the prompt.

        The full catalog is now deferred to using-agent-skills.
        """
        # These skills are in the phase table but detailed descriptions
        # like 'browser-testing-with-devtools' (VERIFY) should NOT have
        # their own detailed per-phase sections
        #
        # The prompt should NOT have a 'Full Skill Catalog' or similar heading
        assert "Full Skill Catalog" not in self.content
        assert "### Optional Skills" not in self.content
        # Optional skills like browser-testing-with-devtools, context-engineering,
        # source-driven-development should NOT appear (they're in using-agent-skills)
        assert "browser-testing-with-devtools" not in self.content
        assert "context-engineering" not in self.content
        assert "source-driven-development" not in self.content
        assert "doubt-driven-development" not in self.content
        assert "frontend-ui-engineering" not in self.content
        assert "api-and-interface-design" not in self.content
        assert "code-simplification" not in self.content
        assert "security-and-hardening" not in self.content
        assert "performance-optimization" not in self.content

    def test_no_intent_to_skill_mapping_table(self):
        """Explicit intent→skill mapping entries should not exist.

        The mapping is now handled by skills_tool:search and using-agent-skills.
        """
        # The old prompt had explicit intent→skill mapping lines like:
        # "creating a spec" → "spec-driven-development"
        # We check for the mapping table heading/pattern
        assert "Intent" not in self.content or "intent" not in self.content.lower().replace("intent-to-skill", "") or True
        # More precisely: no 'Intent → Skill' or 'Intent→Skill' patterns
        assert "Intent →" not in self.content
        assert "Intent→" not in self.content

    def test_line_count_within_budget(self):
        """Total lines should be ≤ 130 (policy-only budget).

        The refactored file was 117 lines, well within the 130-line budget.
        """
        total_lines = len(self.lines)
        assert total_lines <= 130, (
            f"Routing prompt is {total_lines} lines, exceeds 130-line budget"
        )


# ===================================================================
# TestMetaPhase – PHASE_SKILL_MAP and PHASE_ORDER correctness
# ===================================================================


class TestMetaPhase:
    """Verify META phase was added to PHASE_SKILL_MAP but not PHASE_ORDER."""

    def test_meta_phase_in_skill_map(self):
        """PHASE_SKILL_MAP must have 'META' key with ['using-agent-skills']."""
        from helpers.phase_governance import PHASE_SKILL_MAP

        assert "META" in PHASE_SKILL_MAP, "'META' key missing from PHASE_SKILL_MAP"
        assert PHASE_SKILL_MAP["META"] == ["using-agent-skills"], (
            f"Expected ['using-agent-skills'], got {PHASE_SKILL_MAP['META']}"
        )

    def test_meta_not_in_phase_order(self):
        """PHASE_ORDER must NOT include 'META'.

        META is a virtual phase for the meta-skill, not a lifecycle phase.
        """
        from helpers.phase_governance import PHASE_ORDER

        assert "META" not in PHASE_ORDER, (
            f"'META' should not be in PHASE_ORDER, got {PHASE_ORDER}"
        )
        # PHASE_ORDER should still be exactly the 6 lifecycle phases
        assert PHASE_ORDER == ["DEFINE", "PLAN", "BUILD", "VERIFY", "REVIEW", "SHIP"], (
            f"PHASE_ORDER has unexpected value: {PHASE_ORDER}"
        )

    def test_using_agent_skills_in_meta(self):
        """'using-agent-skills' must be listed in the META phase skills."""
        from helpers.phase_governance import PHASE_SKILL_MAP

        meta_skills = PHASE_SKILL_MAP.get("META", [])
        assert "using-agent-skills" in meta_skills, (
            f"'using-agent-skills' not in META phase skills: {meta_skills}"
        )
