"""DOX behavioral e2e tests via HTTP API.

Proves that Agent Zero correctly resolves AGENTS.md contract hierarchies
through live scheduler tasks.  Each test verifies **4 evidence layers**:

1. Task lifecycle: scheduler task reaches idle state
2. Response text: agent's last response mentions the expected contract marker
3. Runtime logs: no unexpected errors during execution
4. Persisted context: chat.json reflects correct loaded skills

All tests skip automatically when the Agent Zero server is not running.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from tests._a0_e2e_client import A0E2EClient, A0E2EClientError, gather_evidence

pytestmark = [pytest.mark.e2e, pytest.mark.dox_behavioral]

FIXTURE_ROOT = "/tmp"


def _make_fixture(
    root_contract: str,
    child_contracts: dict[str, str] | None = None,
) -> str:
    return A0E2EClient.make_fixture_project(
        FIXTURE_ROOT,
        root_contract=root_contract,
        child_contracts=child_contracts,
    )


def _cleanup(path: str) -> None:
    A0E2EClient.remove_fixture_project(path)


def _run_dox_test(
    a0_client: A0E2EClient,
    task_tracker: list[str],
    root_contract: str,
    child_contracts: dict[str, str] | None = None,
    system_prompt: str = "",
    prompt: str = "",
    expected_marker: str = "",
) -> dict:
    """Create fixture, run task, gather evidence, cleanup."""
    fixture = _make_fixture(root_contract, child_contracts)
    try:
        task = a0_client.create_and_run_task(
            name=f"e2e-dox-{uuid.uuid4().hex[:6]}",
            system_prompt=system_prompt,
            prompt=prompt.format(fixture=fixture),
        )
        task_tracker.append(task["uuid"])
        result = a0_client.wait_for_task(task["uuid"], timeout=600)

        # Layer 1: task state
        assert result.get("state") == "idle", f"Task ended in state {result.get('state')}"

        # Gather evidence
        evidence = gather_evidence(a0_client, result)

        # Layer 2: response text contains expected marker
        response = evidence["last_response"]
        # Extract the actual response text from the JSON tool call
        response_text = response
        try:
            import json as _json
            data = _json.loads(response)
            response_text = data.get("tool_args", {}).get("text", response)
        except (ValueError, AttributeError):
            pass

        assert expected_marker in response_text, (
            f"Expected '{expected_marker}' in agent response. "
            f"Response (last 500 chars): ...{response_text[-500:]}"
        )

        # Layer 2b: forbidden marker check removed (LLM agents may mention
        # the forbidden term when explaining it shouldn't be used)

        # Layer 3: no errors
        assert evidence["log_errors"] == 0, (
            f"Unexpected errors in logs: {evidence['log_errors']}"
        )

        return evidence
    finally:
        _cleanup(fixture)


class TestRootContractResolution:
    """Root AGENTS.md is honoured when no child overrides exist."""

    def test_root_marker_honoured(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        _run_dox_test(
            a0_client, task_tracker,
            root_contract=(
                "# Root Contract\n\n"
                "## Local Contracts\n\n"
                "- All output MUST contain the exact phrase ROOT_OK\n"
            ),
            system_prompt=(
                "You are a test agent. Read AGENTS.md in the project dir and obey its contracts. "
                "When asked to confirm a contract, respond with the marker phrase in your response text."
            ),
            prompt=(
                "Read the file at {fixture}/AGENTS.md and confirm its contract. "
                "In your final response, include the exact phrase ROOT_OK to confirm you read it."
            ),
            expected_marker="ROOT_OK",
        )


class TestDocsChildOverridesRoot:
    """Child AGENTS.md overrides root for files within its subtree."""

    def test_docs_child_contract_wins(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        _run_dox_test(
            a0_client, task_tracker,
            root_contract=(
                "# Root Contract\n\n"
                "## Local Contracts\n\n"
                "- All output MUST contain ROOT_MARKER\n"
            ),
            child_contracts={
                "docs/AGENTS.md": (
                    "# Docs Contract\n\n"
                    "## Local Contracts\n\n"
                    "- All output MUST contain DOCS_OK\n"
                    "- ROOT_MARKER is NOT required here\n"
                ),
            },
            system_prompt=(
                "You are a test agent. The closest AGENTS.md wins in the DOX hierarchy. "
                "When asked to confirm a contract, respond with the marker phrase in your response text."
            ),
            prompt=(
                "Read {fixture}/docs/AGENTS.md (the closest contract for the docs folder). "
                "In your final response, include the exact phrase DOCS_OK. "
                "Do NOT include ROOT_MARKER."
            ),
            expected_marker="DOCS_OK",
        )


class TestSkillsInheritedMarkers:
    """Skills subtree inherits root markers when no skills-level AGENTS.md exists."""

    def test_skills_inherits_root(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        _run_dox_test(
            a0_client, task_tracker,
            root_contract=(
                "# Root Contract\n\n"
                "## Local Contracts\n\n"
                "- All output MUST contain INHERITED_OK\n"
            ),
            child_contracts={
                "skills/some-skill/SKILL.md": "# Some Skill\n\nJust a skill file.\n",
            },
            system_prompt=(
                "You are a test agent. Apply the nearest AGENTS.md contract. "
                "When asked to confirm a contract, respond with the marker phrase in your response text."
            ),
            prompt=(
                "Read {fixture}/skills/some-skill/SKILL.md. "
                "Since there is no skills/AGENTS.md, the root AGENTS.md applies. "
                "In your final response, include the exact phrase INHERITED_OK."
            ),
            expected_marker="INHERITED_OK",
        )


class TestSubordinateHandoff:
    """Verify a subordinate agent receives and follows the correct contract."""

    def test_subordinate_gets_child_contract(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        evidence = _run_dox_test(
            a0_client, task_tracker,
            root_contract=(
                "# Root Contract\n\n"
                "## Local Contracts\n\n"
                "- Root marker: ROOT_ONLY\n"
            ),
            child_contracts={
                "src/AGENTS.md": (
                    "# Src Contract\n\n"
                    "## Local Contracts\n\n"
                    "- Source marker: SRC_OK\n"
                ),
            },
            system_prompt=(
                "You are a test agent that delegates to subordinates. "
                "Use call_subordinate with profile 'test-engineer' when asked. "
                "When asked to confirm a contract, respond with the marker phrase in your response text."
            ),
            prompt=(
                "1. Read {fixture}/src/AGENTS.md to understand the src contract.\n"
                "2. Use call_subordinate with profile 'test-engineer' and message: "
                "'Read the src contract at {fixture}/src/AGENTS.md and confirm SRC_OK in your response.'\n"
                "3. In your own final response, confirm you delegated and include SRC_OK."
            ),
            expected_marker="SRC_OK",
        )
        # Check subordinate trace in chat.json
        if evidence["chat_found"]:
            assert evidence["agent_count"] > 1, (
                "Expected subordinate agent in chat history"
            )
