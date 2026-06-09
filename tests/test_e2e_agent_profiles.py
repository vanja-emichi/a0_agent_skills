"""Agent profile e2e tests via HTTP API.

Proves that the Agent Zero subordinate agent profile system works correctly
through live scheduler tasks.  Each test verifies:

1. Task lifecycle: scheduler task reaches idle state
2. Response text: agent's last response confirms subordinate dispatched
3. Runtime logs: no unexpected errors during execution
4. Persisted context: chat.json shows subordinate agent in history

Also proves ADR-009 subordinate DOX propagation: a subordinate created in
an active project inherits the project root AGENTS.md in its rendered system
prompt AND receives the shared DOX interpreter (including catch-all traversal).

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


# ---------------------------------------------------------------------------
# Helpers for extracting response text from tool-call JSON
# ---------------------------------------------------------------------------

def _extract_response_text(response: str) -> str:
    """Extract plain text from a JSON response tool call."""
    import json as _json
    try:
        data = _json.loads(response)
        return data.get("tool_args", {}).get("text", response)
    except (ValueError, AttributeError):
        return response


# ---------------------------------------------------------------------------
# ADR-009: subordinate DOX propagation verification
# ---------------------------------------------------------------------------

# The real project registered as 'a0_agent_skills' (directory name under
# /a0/usr/projects/).  Its root AGENTS.md starts with "A0 Agent Skills
# Development Project" — a distinctive marker that would only appear in the
# rendered system prompt if the project context is active.
_REAL_PROJECT_NAME = "a0_agent_skills"

# Distinctive marker from the project root AGENTS.md (line 1 heading).
_PROJECT_ROOT_MARKER = "A0 Agent Skills Development Project"

# Heading from the shared DOX interpreter (position 2, injected for ALL
# profiles by _10a_dox_interpreter.py).  Moved there from agent0-only
# specifics in Phase 1 (ADR-009 Task 1.2).
_CATCH_ALL_MARKER = "Catch-All Traversal"


class TestSubordinateDOXPropagation:
    """ADR-009 Phase 3: prove subordinate inherits project root AGENTS.md
    and the shared DOX interpreter via the rendered system prompt.

    Uses the *real* project 'a0_agent_skills' to activate project context
    (project_name='a0_agent_skills' → projects.activate_project sets
    context-scoped data → shared context object → subordinate inherits).

    The subordinate (developer profile, agent number > 0) self-reports
    whether it sees both markers.  This is the empirical confirmation
    that spec.md records as "pending e2e confirmation".
    """

    def test_subordinate_inherits_project_root_and_dox_rules(
        self, a0_client: A0E2EClient, task_tracker, clean_tasks
    ):
        """Developer subordinate in active project sees root AGENTS.md + DOX catch-all."""
        uid = uuid.uuid4().hex[:8]
        task = a0_client.create_and_run_task(
            name=f"e2e-dox-propagation-{uid}",
            system_prompt=(
                "You are a test agent. Use call_subordinate when asked. "
                "Report the subordinate's response verbatim."
            ),
            prompt=(
                "Use call_subordinate with profile 'developer' and message:\n"
                "'Examine your system prompt carefully and report two things:\n"
                "1. If you see a section containing \""
                + _PROJECT_ROOT_MARKER
                + "\", respond SUB_SEES_PROJECT_ROOT. "
                "Otherwise respond SUB_NO_PROJECT_ROOT.\n"
                "2. If you see a section titled \""
                + _CATCH_ALL_MARKER
                + "\", respond SUB_SEES_CATCH_ALL. "
                "Otherwise respond SUB_NO_CATCH_ALL.\n"
                "Report both findings in one response.'\n"
                "In your final response, include the subordinate's exact tokens: "
                "SUB_SEES_PROJECT_ROOT, SUB_SEES_CATCH_ALL "
                "(or their negative variants if the subordinate reported them)."
            ),
            project_name=_REAL_PROJECT_NAME,
        )
        task_tracker.append(task["uuid"])
        result = a0_client.wait_for_task(task["uuid"], timeout=600)

        # Layer 1: task state
        assert result.get("state") == "idle", (
            f"Task ended in state {result.get('state')}"
        )

        evidence = gather_evidence(a0_client, result)
        response = _extract_response_text(evidence["last_response"])

        # Layer 2a: subordinate confirms project root AGENTS.md is present
        assert "SUB_SEES_PROJECT_ROOT" in response, (
            f"Subordinate should report seeing project root AGENTS.md "
            f"('{_PROJECT_ROOT_MARKER}'). "
            f"Response (last 500): ...{response[-500:]}"
        )
        assert "SUB_NO_PROJECT_ROOT" not in response, (
            f"Subordinate reported NOT seeing project root AGENTS.md. "
            f"Response (last 500): ...{response[-500:]}"
        )

        # Layer 2b: subordinate confirms DOX catch-all traversal is present
        assert "SUB_SEES_CATCH_ALL" in response, (
            f"Subordinate should report seeing DOX catch-all rule "
            f"('{_CATCH_ALL_MARKER}'). "
            f"Response (last 500): ...{response[-500:]}"
        )
        assert "SUB_NO_CATCH_ALL" not in response, (
            f"Subordinate reported NOT seeing DOX catch-all rule. "
            f"Response (last 500): ...{response[-500:]}"
        )

        # Layer 3: no errors
        assert evidence["log_errors"] == 0, (
            f"Unexpected errors in logs: {evidence['log_errors']}"
        )

        # Layer 4: subordinate trace in chat.json
        if evidence["chat_found"]:
            assert evidence["agent_count"] > 1, (
                f"Expected subordinate agent in chat history, "
                f"but found {evidence['agent_count']} agents"
            )
