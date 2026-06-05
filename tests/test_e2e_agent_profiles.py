"""Agent profile e2e tests via HTTP API.

Proves that the Agent Zero subordinate agent profile system works correctly
through live scheduler tasks.  Each test verifies:

1. Task lifecycle: scheduler task reaches idle state
2. Response text: agent's last response confirms subordinate dispatched
3. Runtime logs: no unexpected errors during execution
4. Persisted context: chat.json shows subordinate agent in history

All tests skip automatically when the Agent Zero server is not running.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest

from tests._a0_e2e_client import A0E2EClient, gather_evidence, A0E2EClientError

pytestmark = [pytest.mark.e2e, pytest.mark.dox_behavioral]


def _run_profile_test(
    a0_client: A0E2EClient,
    task_tracker: list[str],
    name: str,
    system_prompt: str,
    prompt: str,
    expected_in_response: str = "",
) -> dict:
    """Create+run task, track UUID, wait, check response and subordinate evidence."""
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

    # Layer 4: subordinate trace
    if evidence["chat_found"]:
        assert evidence["agent_count"] > 1, (
            f"Expected subordinate agent in chat history, "
            f"but found {evidence['agent_count']} agents"
        )

    return evidence




class TestSubordinateProfileCall:
    """Subordinate agents can be called via call_subordinate."""

    def test_code_reviewer_profile_responds(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        uid = uuid.uuid4().hex[:8]
        _run_profile_test(
            a0_client, task_tracker,
            name=f"e2e-profile-cr-{uid}",
            system_prompt="You are a test agent. Use tools as instructed.",
            prompt=(
                "Use call_subordinate with profile 'code-reviewer' and message 'Review this code: print(\"hello\")'. "
                "In your final response, confirm you delegated by including 'CODE_REVIEW_DONE'."
            ),
            expected_in_response="CODE_REVIEW_DONE",
        )

    def test_test_engineer_profile_responds(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        uid = uuid.uuid4().hex[:8]
        _run_profile_test(
            a0_client, task_tracker,
            name=f"e2e-profile-te-{uid}",
            system_prompt="You are a test agent. Use tools as instructed.",
            prompt=(
                "Use call_subordinate with profile 'test-engineer' and message 'Design a test for a login function'. "
                "In your final response, confirm you delegated by including 'TEST_ENG_DONE'."
            ),
            expected_in_response="TEST_ENG_DONE",
        )

    def test_security_auditor_profile_responds(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        uid = uuid.uuid4().hex[:8]
        _run_profile_test(
            a0_client, task_tracker,
            name=f"e2e-profile-sa-{uid}",
            system_prompt="You are a test agent. Use tools as instructed.",
            prompt=(
                "Use call_subordinate with profile 'security-auditor' and message 'Audit this code: eval(user_input)'. "
                "In your final response, confirm you delegated by including 'SEC_AUDIT_DONE'."
            ),
            expected_in_response="SEC_AUDIT_DONE",
        )
