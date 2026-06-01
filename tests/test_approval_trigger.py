"""Tests for the approval gate extension (Task 1).

Verifies that:
- detect_approval_in_text detects explicit approval phrases
- detect_approval_in_text rejects non-approval phrases (including questions)
- The extension calls mark_artifact_approved when approval is detected + artifact exists
- The extension skips when no phase or no artifact exists
- The extension is fail-safe (never raises)

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_approval_trigger.py -v
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    return asyncio.run(coro)


def _make_agent(
    *,
    last_user_message: str = "approved",
):
    """Create a mock agent suitable for the approval gate extension."""
    agent = MagicMock()

    # last_user_message attribute (agent.last_user_message)
    # Framework Message class stores text in .content, not .message
    msg = MagicMock()
    msg.content = last_user_message
    agent.last_user_message = msg

    # Prevent MagicMock file leaks: set context to None so that
    # resolve_state_dir() and resolve_visible_root() bail out early.
    agent.context = None

    return agent


# ===========================================================================
# detect_approval_in_text — positive cases
# ===========================================================================


class TestDetectApprovalPositive:
    """Verify approval is detected for explicit positive phrases."""

    @pytest.mark.parametrize("text", [
        "approved",
        "I approve this",
        "looks good to me",
        "this is good to go",
        "please proceed",
        "ship it!",
        "lgtm",
        "let's go ahead",
        "LGTM",
        "APPROVED",
        "Looks Good",
        "ok",
        "OK",
        "Okay",
        "okay",
    ])
    def test_detects_approval_phrase(self, text):
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(text) is True

    def test_detects_approval_in_longer_message(self):
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(
            "I've reviewed the spec and it looks good, thanks!"
        ) is True

    def test_approval_with_trailing_question_detected(self):
        """I-2: 'This looks good, proceed?' should be detected as approval."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(
            "This looks good, proceed?"
        ) is True

    def test_approval_in_message_with_question_mark(self):
        """I-2: Approval phrase in a message that also has a question mark."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(
            "Ready to go? It looks good to me."
        ) is True


# ===========================================================================
# detect_approval_in_text — negative cases
# ===========================================================================


class TestDetectApprovalNegative:
    """Verify approval is NOT detected for non-approval text."""

    @pytest.mark.parametrize("text", [
        "unapproved",
        "fix section 3",
        "approved by whom?",       # approval phrase directly followed by ?
        "not approved",
        "disapproved",
        "can you approve this?",   # question word before approval phrase
        "I need to review this more",
        "let me think about it",
    ])
    def test_does_not_detect_non_approval(self, text):
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(text) is False

    def test_none_returns_false(self):
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(None) is False

    def test_empty_string_returns_false(self):
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text("") is False

    def test_negation_in_window_not_detected(self):
        """M-2: Negation within 4-word window should block approval."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(
            "I don't think it looks good"
        ) is False

    def test_negation_never_with_approval(self):
        """M-2: 'never' in window blocks approval."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text(
            "I will never approve this"
        ) is False

    def test_negation_far_outside_window_allows(self):
        """M-2: Negation more than 4 words before phrase should NOT block."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        # "not" is 5+ words before "approved" — should still detect approval
        assert detect_approval_in_text(
            "I was not sure at first, but now it is approved"
        ) is True

    def test_approval_phrase_followed_by_question_mark(self):
        """I-2: 'approved?' is a question, not an approval."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text("approved?") is False

    def test_question_word_before_approval_phrase(self):
        """I-2: 'can approve' — question about approval, not approval."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            detect_approval_in_text,
        )
        assert detect_approval_in_text("can you approve this?") is False


# ===========================================================================
# ApprovalGate extension execute()
# ===========================================================================


class TestApprovalGateExecute:
    """Verify the extension's execute() method."""

    def test_approve_in_define_phase_marks_spec(self):
        """Approval in DEFINE phase marks the spec artifact."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            ApprovalGate,
        )
        ext = ApprovalGate.__new__(ApprovalGate)
        agent = _make_agent(last_user_message="approved")
        ext.agent = agent

        with patch(
            "extensions.python.tool_execute_before._20_approval_gate._get_helpers",
        ) as mock_get_helpers:
            with patch(
                "extensions.python.tool_execute_before._20_approval_gate._get_phase_artifact_type",
                return_value="spec",
            ) as mock_get_type:
                mock_mark = MagicMock(return_value="/path/to/state")
                mock_read = MagicMock(return_value={"spec_path": "/path/to/spec.md"})
                mock_phase = MagicMock(return_value="DEFINE")
                mock_get_helpers.return_value = (mock_mark, mock_read, mock_phase)

                _run(ext.execute(tool_name="code_execution_tool", tool_args={}))

                mock_phase.assert_called_once_with(agent)
                mock_get_type.assert_called_once_with("DEFINE")
                mock_mark.assert_called_once_with(agent, "spec")

    def test_no_approval_phrase_skips(self):
        """Non-approval text does not trigger mark_artifact_approved."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            ApprovalGate,
        )
        ext = ApprovalGate.__new__(ApprovalGate)
        agent = _make_agent(last_user_message="fix section 3")
        ext.agent = agent

        with patch(
            "extensions.python.tool_execute_before._20_approval_gate._get_helpers",
        ) as mock_get_helpers:
            mock_mark = MagicMock()
            mock_read = MagicMock()
            mock_phase = MagicMock(return_value="DEFINE")
            mock_get_helpers.return_value = (mock_mark, mock_read, mock_phase)

            _run(ext.execute(tool_name="code_execution_tool", tool_args={}))

            mock_mark.assert_not_called()

    def test_no_phase_skips(self):
        """Approval detected but no current phase → skip."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            ApprovalGate,
        )
        ext = ApprovalGate.__new__(ApprovalGate)
        agent = _make_agent(last_user_message="approved")
        ext.agent = agent

        with patch(
            "extensions.python.tool_execute_before._20_approval_gate._get_helpers",
        ) as mock_get_helpers:
            mock_mark = MagicMock()
            mock_read = MagicMock()
            mock_phase = MagicMock(return_value=None)
            mock_get_helpers.return_value = (mock_mark, mock_read, mock_phase)

            _run(ext.execute(tool_name="code_execution_tool", tool_args={}))

            mock_mark.assert_not_called()

    def test_no_artifact_tracked_skips(self):
        """Approval detected but no artifact tracked for phase → skip."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            ApprovalGate,
        )
        ext = ApprovalGate.__new__(ApprovalGate)
        agent = _make_agent(last_user_message="approved")
        ext.agent = agent

        with patch(
            "extensions.python.tool_execute_before._20_approval_gate._get_helpers",
        ) as mock_get_helpers:
            with patch(
                "extensions.python.tool_execute_before._20_approval_gate._get_phase_artifact_type",
                return_value="spec",
            ):
                mock_mark = MagicMock()
                mock_read = MagicMock(return_value={})
                mock_phase = MagicMock(return_value="DEFINE")
                mock_get_helpers.return_value = (mock_mark, mock_read, mock_phase)

                _run(ext.execute(tool_name="code_execution_tool", tool_args={}))

                mock_mark.assert_not_called()

    def test_null_artifacts_skips(self):
        """Approval detected but read_workflow_artifacts returns None → skip."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            ApprovalGate,
        )
        ext = ApprovalGate.__new__(ApprovalGate)
        agent = _make_agent(last_user_message="approved")
        ext.agent = agent

        with patch(
            "extensions.python.tool_execute_before._20_approval_gate._get_helpers",
        ) as mock_get_helpers:
            with patch(
                "extensions.python.tool_execute_before._20_approval_gate._get_phase_artifact_type",
                return_value="spec",
            ):
                mock_mark = MagicMock()
                mock_read = MagicMock(return_value=None)
                mock_phase = MagicMock(return_value="DEFINE")
                mock_get_helpers.return_value = (mock_mark, mock_read, mock_phase)

                _run(ext.execute(tool_name="code_execution_tool", tool_args={}))

                mock_mark.assert_not_called()

    def test_plan_phase_marks_plan(self):
        """Approval in PLAN phase marks the plan artifact."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            ApprovalGate,
        )
        ext = ApprovalGate.__new__(ApprovalGate)
        agent = _make_agent(last_user_message="looks good")
        ext.agent = agent

        with patch(
            "extensions.python.tool_execute_before._20_approval_gate._get_helpers",
        ) as mock_get_helpers:
            with patch(
                "extensions.python.tool_execute_before._20_approval_gate._get_phase_artifact_type",
                return_value="plan",
            ):
                mock_mark = MagicMock(return_value="/path")
                mock_read = MagicMock(return_value={"plan_path": "/path/to/plan.md"})
                mock_phase = MagicMock(return_value="PLAN")
                mock_get_helpers.return_value = (mock_mark, mock_read, mock_phase)

                _run(ext.execute(tool_name="code_execution_tool", tool_args={}))

                mock_mark.assert_called_once_with(agent, "plan")

    def test_build_phase_marks_todo(self):
        """Approval in BUILD phase marks the todo artifact."""
        from extensions.python.tool_execute_before._20_approval_gate import (
            ApprovalGate,
        )
        ext = ApprovalGate.__new__(ApprovalGate)
        agent = _make_agent(last_user_message="proceed")
        ext.agent = agent

        with patch(
            "extensions.python.tool_execute_before._20_approval_gate._get_helpers",
        ) as mock_get_helpers:
            with patch(
                "extensions.python.tool_execute_before._20_approval_gate._get_phase_artifact_type",
                return_value="todo",
            ):
                mock_mark = MagicMock(return_value="/path")
                mock_read = MagicMock(return_value={"todo_path": "/path/to/todo.md"})
                mock_phase = MagicMock(return_value="BUILD")
                mock_get_helpers.return_value = (mock_mark, mock_read, mock_phase)

                _run(ext.execute(tool_name="code_execution_tool", tool_args={}))

                mock_mark.assert_called_once_with(agent, "todo")


# ===========================================================================
# Fail-safe behavior
# ===========================================================================


class TestApprovalGateFailSafe:
    """Verify the extension never raises exceptions."""

    def test_exception_in_get_helpers_does_not_propagate(self):
        from extensions.python.tool_execute_before._20_approval_gate import (
            ApprovalGate,
        )
        ext = ApprovalGate.__new__(ApprovalGate)
        agent = MagicMock()
        agent.last_user_message = MagicMock()
        agent.last_user_message.content = "approved"
        agent.context = None
        ext.agent = agent

        with patch(
            "extensions.python.tool_execute_before._20_approval_gate._get_helpers",
            side_effect=RuntimeError("boom"),
        ):
            # Must NOT raise
            _run(ext.execute(tool_name="code_execution_tool", tool_args={}))

    def test_no_last_user_message_does_not_raise(self):
        from extensions.python.tool_execute_before._20_approval_gate import (
            ApprovalGate,
        )
        ext = ApprovalGate.__new__(ApprovalGate)
        agent = MagicMock()
        agent.last_user_message = None
        agent.context = None
        ext.agent = agent

        # Must NOT raise
        _run(ext.execute(tool_name="code_execution_tool", tool_args={}))

    def test_mark_approved_failure_does_not_raise(self):
        from extensions.python.tool_execute_before._20_approval_gate import (
            ApprovalGate,
        )
        ext = ApprovalGate.__new__(ApprovalGate)
        agent = _make_agent(last_user_message="approved")
        ext.agent = agent

        with patch(
            "extensions.python.tool_execute_before._20_approval_gate._get_helpers",
        ) as mock_get_helpers:
            with patch(
                "extensions.python.tool_execute_before._20_approval_gate._get_phase_artifact_type",
                return_value="spec",
            ):
                mock_mark = MagicMock(side_effect=RuntimeError("state error"))
                mock_read = MagicMock(return_value={"spec_path": "/path/to/spec.md"})
                mock_phase = MagicMock(return_value="DEFINE")
                mock_get_helpers.return_value = (mock_mark, mock_read, mock_phase)

                # Must NOT raise even when mark_artifact_approved fails
                _run(ext.execute(tool_name="code_execution_tool", tool_args={}))
