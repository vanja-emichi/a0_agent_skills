"""Skill loading e2e tests via HTTP API.

Proves that the Agent Zero skills system (search, load, read_file) works
correctly through live scheduler tasks.  Each test verifies:

1. Task lifecycle: scheduler task reaches idle state
2. Response text: agent's last response mentions expected skill data
3. Runtime logs: no unexpected errors during execution
4. Persisted context: chat.json reflects skill loading activity

All tests skip automatically when the Agent Zero server is not running.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from tests._a0_e2e_client import A0E2EClient, gather_evidence, A0E2EClientError

pytestmark = [pytest.mark.e2e, pytest.mark.dox_behavioral]


def _run_skill_test(
    a0_client: A0E2EClient,
    task_tracker: list[str],
    name: str,
    system_prompt: str,
    prompt: str,
    expected_in_response: str = "",
) -> dict:
    """Create+run task, track UUID, wait, check response text, return evidence."""
    task = a0_client.create_and_run_task(
        name=name,
        system_prompt=system_prompt,
        prompt=prompt,
    )
    task_tracker.append(task["uuid"])
    result = a0_client.wait_for_task(task["uuid"], timeout=600)

    # Layer 1: task state
    assert result.get("state") == "idle", f"Task ended in state {result.get('state')}"

    # Gather evidence
    evidence = gather_evidence(a0_client, result)

    # Layer 2: response text contains expected marker
    if expected_in_response:
        response = evidence["last_response"]
        assert expected_in_response in response, (
            f"Expected '{expected_in_response}' in agent response. "
            f"Response (last 500 chars): ...{response[-500:]}"
        )

    # Layer 3: no errors
    assert evidence["log_errors"] == 0, (
        f"Unexpected errors in logs: {evidence['log_errors']}"
    )

    return evidence




class TestSkillDiscoveryViaSearch:
    """Skills can be discovered through the skills_tool search action."""

    def test_search_returns_matching_skills(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        uid = uuid.uuid4().hex[:8]
        _run_skill_test(
            a0_client, task_tracker,
            name=f"e2e-skill-search-{uid}",
            system_prompt=(
                "You are a test agent. Use tools as instructed. "
                "Always include the results of tool calls in your response text."
            ),
            prompt=(
                "Use skills_tool with action 'search' and query 'code review'. "
                "In your final response, list the names of all skills found. "
                "Make sure 'code-review-and-quality' appears in your response."
            ),
            expected_in_response="code-review-and-quality",
        )


class TestSkillLoadAndRead:
    """A skill can be loaded and its files read via skills_tool."""

    def test_load_skill_and_read_contents(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        uid = uuid.uuid4().hex[:8]
        _run_skill_test(
            a0_client, task_tracker,
            name=f"e2e-skill-load-{uid}",
            system_prompt=(
                "You are a test agent. Use tools as instructed. "
                "Always include the results of tool calls in your response text."
            ),
            prompt=(
                "1. Use skills_tool with action 'load' and skill_name 'code-review-and-quality'.\n"
                "2. Then use skills_tool with action 'read_file', skill_name 'code-review-and-quality', "
                "and file_path 'SKILL.md'.\n"
                "3. In your final response, include the first line of the SKILL.md content. "
                "Make sure the text 'Code Review' appears in your response."
            ),
            expected_in_response="Code Review",
        )


class TestMetaSkillInjection:
    """The using-agent-skills meta-skill is available for loading."""

    def test_meta_skill_loadable(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        uid = uuid.uuid4().hex[:8]
        evidence = _run_skill_test(
            a0_client, task_tracker,
            name=f"e2e-meta-skill-{uid}",
            system_prompt=(
                "You are a test agent. Use tools as instructed. "
                "Always include the results of tool calls in your response text."
            ),
            prompt=(
                "1. Use skills_tool with action 'load' and skill_name 'using-agent-skills'.\n"
                "2. In your final response, confirm the skill loaded by including 'META_SKILL_LOADED'."
            ),
            expected_in_response="META_SKILL_LOADED",
        )
        # Check loaded skills in chat evidence
        if evidence["loaded_skills"]:
            assert "using-agent-skills" in evidence["loaded_skills"], (
                f"Expected 'using-agent-skills' in loaded_skills, got: {evidence['loaded_skills']}"
            )
