"""E2e tests for extension runtime behavior.

Tests that SDD cache and simplify-ignore extensions work correctly
inside real agent sessions.
"""

import os
import shutil
import uuid

import pytest

from _a0_e2e_client import A0E2EClient, gather_evidence

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("task_tracker")
class TestSDDCacheBehavior:
    """Verify SDD cache extension caches documentation."""

    def test_agent_reads_documentation_twice(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        """Agent reads the same file twice; second read should use cache."""
        uid = uuid.uuid4().hex[:8]
        task_name = f"sdd-cache-{uid}"
        task = a0_client.create_and_run_task(
            name=task_name,
            prompt=(
                "Read the file /a0/usr/plugins/a0_agent_skills/skills/using-agent-skills/SKILL.md "
                "using text_editor action=read. "
                "Then read the SAME file again using text_editor action=read. "
                "In your final response, include the marker SDD_CACHE_OK "
                "and report whether both reads succeeded."
            ),
        )
        task_uuid = task["uuid"]
        result = a0_client.wait_for_task(task_uuid)
        evidence = gather_evidence(a0_client, result)

        assert evidence["task_state"] == "idle", (
            f"Task {task_name} did not complete. State: {evidence.get('task_state')}"
        )
        assert evidence["chat_found"], f"No agent response found for {task_name}"
        assert "SDD_CACHE_OK" in evidence["last_response"], (
            f"Agent did not confirm SDD cache behavior. "
            f"Response: {evidence['last_response'][:300]}"
        )


@pytest.mark.usefixtures("task_tracker")
class TestSimplifyIgnoreBehavior:
    """Verify simplify-ignore extension protects code blocks."""

    def test_simplify_ignore_guard_exists(self):
        """Guard extension files should exist."""
        base = "/a0/usr/plugins/a0_agent_skills/extensions/python"
        assert os.path.isfile(
            os.path.join(base, "tool_execute_before", "_20_simplify_ignore.py")
        ), "Pre-tool simplify-ignore guard not found"
        assert os.path.isfile(
            os.path.join(base, "_simplify_ignore_util.py")
        ), "Simplify-ignore utility not found"

    def test_simplify_ignore_util_exists(self):
        """Utility module should exist and compile."""
        import importlib.util

        util_path = (
            "/a0/usr/plugins/a0_agent_skills/extensions/python"
            "/_simplify_ignore_util.py"
        )
        spec = importlib.util.spec_from_file_location(
            "_simplify_ignore_util", util_path
        )
        assert spec is not None, f"Could not load spec from {util_path}"

    def test_agent_respects_block_level_protection(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        """Agent should not modify code inside simplify-ignore blocks."""
        uid = uuid.uuid4().hex[:8]
        task_name = f"simplify-ignore-{uid}"
        test_dir = f"/tmp/test_simplify_ignore_{uid}"
        # Build markers using concatenation to avoid triggering the extension
        start_m = "# simplify" + "-ignore-start: critical config"
        end_m = "# simplify" + "-ignore-end"
        protected = "secret_value = 42  # DO NOT SIMPLIFY"
        file_lines = [
            "x = 1 + 1  # add numbers",
            start_m,
            protected,
            end_m,
            "y = 2 + 2  # more math",
        ]
        file_content = "\\n".join(file_lines)
        task = a0_client.create_and_run_task(
            name=task_name,
            prompt=(
                f"Create a file at {test_dir}/example.py with this EXACT content:\n"
                "```python\n" + file_content + "\n```\n"
                "Then read the file back with text_editor action=read. "
                "Then try to simplify the entire file (replace x = 1 + 1 with x = 2). "
                "In your final response, include the marker SIMPLIFY_IGNORE_OK "
                "and confirm whether the protected block was preserved or not."
            ),
        )
        task_uuid = task["uuid"]
        result = a0_client.wait_for_task(task_uuid)
        evidence = gather_evidence(a0_client, result)

        assert evidence["task_state"] == "idle", (
            f"Task {task_name} did not complete. State: {evidence.get('task_state')}"
        )
        assert evidence["chat_found"], f"No agent response found for {task_name}"
        assert "SIMPLIFY_IGNORE_OK" in evidence["last_response"], (
            f"Agent did not confirm simplify-ignore behavior. "
            f"Response: {evidence['last_response'][:300]}"
        )

        # Clean up temp files
        shutil.rmtree(test_dir, ignore_errors=True)
