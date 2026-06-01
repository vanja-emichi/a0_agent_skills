"""Tests for helpers/skill_match.py (Task 2).

Covers: is_target_tool, get_loaded_skills, prefilter_match, classify_skill.
Each result state is explicitly tested.

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_skill_match.py -v
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Lightweight stubs – avoid importing framework modules at test time
# ---------------------------------------------------------------------------


def _make_skill(name: str, description: str = "", triggers: list[str] | None = None) -> Any:
    """Create a minimal Skill-like object for testing."""
    return type("Skill", (), {
        "name": name,
        "description": description,
        "tags": [],
        "triggers": triggers or [],
        "path": Path(f"/fake/skills/{name}"),
    })()


_SENTINEL = object()


def _make_agent(
    *,
    loaded_skills: list[str] | None = None,
    utility_response: str | None = _SENTINEL,
    utility_raises: Exception | None = None,
) -> MagicMock:
    """Create a mock agent with configurable loaded skills and utility model."""
    agent = MagicMock()
    agent.data = {"loaded_skills": list(loaded_skills or [])}

    if utility_raises:
        agent.call_utility_model = AsyncMock(side_effect=utility_raises)
    elif utility_response is not _SENTINEL:
        agent.call_utility_model = AsyncMock(return_value=utility_response)
    else:
        agent.call_utility_model = AsyncMock(return_value='{}')

    return agent


# ===========================================================================
# is_target_tool
# ===========================================================================


class TestIsTargetTool:
    """Verify target-tool detection."""

    def test_code_execution_tool_is_target(self):
        from helpers.skill_match import is_target_tool
        assert is_target_tool("code_execution_tool") is True

    def test_text_editor_is_target(self):
        from helpers.skill_match import is_target_tool
        assert is_target_tool("text_editor") is True

    def test_browser_is_not_target(self):
        from helpers.skill_match import is_target_tool
        assert is_target_tool("browser") is False

    def test_response_is_not_target(self):
        from helpers.skill_match import is_target_tool
        assert is_target_tool("response") is False

    def test_none_is_not_target(self):
        from helpers.skill_match import is_target_tool
        assert is_target_tool(None) is False

    def test_empty_string_is_not_target(self):
        from helpers.skill_match import is_target_tool
        assert is_target_tool("") is False


# ===========================================================================
# get_loaded_skills
# ===========================================================================


class TestGetLoadedSkills:
    """Verify loaded-skill name extraction."""

    def test_returns_set_of_names(self):
        from helpers.skill_match import get_loaded_skills
        agent = _make_agent(loaded_skills=["test-driven-development", "incremental-implementation"])
        result = get_loaded_skills(agent)
        assert result == {"test-driven-development", "incremental-implementation"}

    def test_empty_loaded_skills(self):
        from helpers.skill_match import get_loaded_skills
        agent = _make_agent(loaded_skills=[])
        result = get_loaded_skills(agent)
        assert result == set()

    def test_none_agent_returns_empty(self):
        from helpers.skill_match import get_loaded_skills
        result = get_loaded_skills(None)
        assert result == set()

    def test_agent_without_data_returns_empty(self):
        from helpers.skill_match import get_loaded_skills
        agent = MagicMock(spec=[])
        result = get_loaded_skills(agent)
        assert result == set()


# ===========================================================================
# prefilter_match
# ===========================================================================


class TestPrefilterMatch:
    """Verify search_skills-based prefilter."""

    @patch("helpers.skill_match.search_skills")
    def test_returns_matching_skills(self, mock_search):
        from helpers.skill_match import prefilter_match
        skill = _make_skill("test-driven-development", "TDD skill")
        mock_search.return_value = [skill]
        agent = _make_agent()

        result = prefilter_match(agent, "write tests for this function")
        assert len(result) == 1
        assert result[0].name == "test-driven-development"
        mock_search.assert_called_once()

    @patch("helpers.skill_match.search_skills")
    def test_empty_query_returns_empty(self, mock_search):
        from helpers.skill_match import prefilter_match
        mock_search.return_value = []
        agent = _make_agent()

        result = prefilter_match(agent, "")
        assert result == []

    @patch("helpers.skill_match.search_skills")
    def test_none_query_returns_empty(self, mock_search):
        from helpers.skill_match import prefilter_match
        mock_search.return_value = []
        agent = _make_agent()

        result = prefilter_match(agent, None)
        assert result == []

    @patch("helpers.skill_match.search_skills")
    def test_no_matches_returns_empty(self, mock_search):
        from helpers.skill_match import prefilter_match
        mock_search.return_value = []
        agent = _make_agent()

        result = prefilter_match(agent, "deploy to production")
        assert result == []

    @patch("helpers.skill_match.search_skills")
    def test_passes_agent_to_search_skills(self, mock_search):
        from helpers.skill_match import prefilter_match
        mock_search.return_value = []
        agent = _make_agent()

        prefilter_match(agent, "implement feature")
        call_kwargs = mock_search.call_args
        assert call_kwargs[1].get("agent") is agent or (len(call_kwargs[0]) > 2 and call_kwargs[0][2] is agent)


# ===========================================================================
# classify_skill – result states
# ===========================================================================


class TestClassifySkillNoCandidate:
    """classify_skill returns no_candidate when candidates list is empty."""

    def test_empty_candidates_returns_no_candidate(self):
        from helpers.skill_match import classify_skill
        agent = _make_agent()

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {}, [], "implement feature")
        )
        assert result["state"] == "no_candidate"
        assert result["candidate"] is None


class TestClassifySkillAlreadyLoaded:
    """classify_skill returns already_loaded when matching skill is loaded."""

    def test_matching_skill_loaded(self):
        from helpers.skill_match import classify_skill
        skill = _make_skill("test-driven-development")
        agent = _make_agent(loaded_skills=["test-driven-development"])

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {}, [skill], "write tests")
        )
        assert result["state"] == "already_loaded"
        assert result["candidate"] is None


class TestClassifySkillShouldCorrect:
    """classify_skill returns should_correct when classifier says skill needed."""

    @patch("helpers.skill_match.search_skills", return_value=[])
    def test_classifier_says_yes(self, _mock):
        from helpers.skill_match import classify_skill
        skill = _make_skill("test-driven-development", "Write tests first")
        agent = _make_agent(
            loaded_skills=[],
            utility_response='{"should_load": true, "reason": "writing code that needs tests"}'
        )

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {"code": "print('hello')"}, [skill], "implement feature")
        )
        assert result["state"] == "should_correct"
        assert result["candidate"] == "test-driven-development"
        assert "reason" in result


class TestClassifySkillShouldNotCorrect:
    """classify_skill returns should_not_correct when classifier says skill not needed."""

    @patch("helpers.skill_match.search_skills", return_value=[])
    def test_classifier_says_no(self, _mock):
        from helpers.skill_match import classify_skill
        skill = _make_skill("ci-cd-and-automation", "CI/CD pipelines")
        agent = _make_agent(
            loaded_skills=[],
            utility_response='{"should_load": false, "reason": "simple unrelated task"}'
        )

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {"code": "ls -la"}, [skill], "list files")
        )
        assert result["state"] == "should_not_correct"
        assert result["candidate"] is None


class TestClassifySkillClassifierUnavailable:
    """classify_skill returns classifier_unavailable when utility model fails."""

    @patch("helpers.skill_match.search_skills", return_value=[])
    def test_utility_model_raises(self, _mock):
        from helpers.skill_match import classify_skill
        skill = _make_skill("test-driven-development", "TDD")
        agent = _make_agent(
            loaded_skills=[],
            utility_raises=RuntimeError("utility model not configured")
        )

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {"code": "x = 1"}, [skill], "implement")
        )
        assert result["state"] == "classifier_unavailable"
        assert result["candidate"] is None

    @patch("helpers.skill_match.search_skills", return_value=[])
    def test_utility_model_returns_none(self, _mock):
        from helpers.skill_match import classify_skill
        skill = _make_skill("debugging-and-error-recovery", "Debug skill")
        agent = _make_agent(
            loaded_skills=[],
            utility_response=None
        )

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {"code": "x = 1"}, [skill], "debug")
        )
        assert result["state"] == "classifier_unavailable"

    @patch("helpers.skill_match.search_skills", return_value=[])
    def test_utility_model_returns_empty_string(self, _mock):
        from helpers.skill_match import classify_skill
        skill = _make_skill("source-driven-development", "SDD skill")
        agent = _make_agent(
            loaded_skills=[],
            utility_response=""
        )

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {}, [skill], "implement")
        )
        assert result["state"] == "classifier_unavailable"


# ===========================================================================
# classify_skill – non-target tool short-circuit
# ===========================================================================


class TestClassifySkillNonTargetTool:
    """classify_skill returns no_candidate for non-target tools (fast path)."""

    def test_browser_tool_skipped(self):
        from helpers.skill_match import classify_skill
        agent = _make_agent()

        result = asyncio.run(
            classify_skill(agent, "browser", {}, [], "browse the web")
        )
        assert result["state"] == "no_candidate"
        agent.call_utility_model.assert_not_called()


# ===========================================================================
# Edge cases
# ===========================================================================


class TestClassifySkillEdgeCases:
    """Edge cases and robustness."""

    @patch("helpers.skill_match.search_skills", return_value=[])
    def test_malformed_json_from_classifier(self, _mock):
        from helpers.skill_match import classify_skill
        skill = _make_skill("spec-driven-development")
        agent = _make_agent(
            loaded_skills=[],
            utility_response="not json at all"
        )

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {}, [skill], "implement feature")
        )
        # Malformed response should be treated as unavailable
        assert result["state"] in ("classifier_unavailable", "should_not_correct")

    @patch("helpers.skill_match.search_skills", return_value=[])
    def test_multiple_candidates_first_not_loaded(self, _mock):
        from helpers.skill_match import classify_skill
        skill1 = _make_skill("ci-cd-and-automation", "CI skill")
        skill2 = _make_skill("test-driven-development", "TDD skill")
        agent = _make_agent(
            loaded_skills=[],
            utility_response='{"should_load": true, "reason": "need TDD"}'
        )

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {}, [skill1, skill2], "write tests")
        )
        assert result["state"] == "should_correct"
        assert result["candidate"] in ("ci-cd-and-automation", "test-driven-development")

    @patch("helpers.skill_match.search_skills", return_value=[])
    def test_first_candidate_already_loaded_skips(self, _mock):
        from helpers.skill_match import classify_skill
        skill1 = _make_skill("test-driven-development", "TDD skill")
        skill2 = _make_skill("source-driven-development", "SDD skill")
        agent = _make_agent(
            loaded_skills=["test-driven-development"],
            utility_response='{"should_load": true, "reason": "need SDD"}'
        )

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {}, [skill1, skill2], "implement")
        )
        # skill1 is loaded, should check skill2
        assert result["state"] in ("should_correct", "should_not_correct")
        if result["state"] == "should_correct":
            assert result["candidate"] == "source-driven-development"

    @patch("helpers.skill_match.search_skills", return_value=[])
    def test_wrapped_json_in_markdown_fences(self, _mock):
        """Bug #1: classifier returns JSON wrapped in markdown code fences.

        _extract_json_object should find the JSON and the result should be
        should_correct, NOT classifier_unavailable.
        """
        from helpers.skill_match import classify_skill
        skill = _make_skill("spec-driven-development")
        agent = _make_agent(
            loaded_skills=[],
            utility_response='```json\n{"should_load": true, "reason": "need spec"}\n```'
        )

        result = asyncio.run(
            classify_skill(agent, "code_execution_tool", {}, [skill], "write spec")
        )
        assert result["state"] == "should_correct"
        assert result["candidate"] == "spec-driven-development"
        assert "spec" in result["reason"]
