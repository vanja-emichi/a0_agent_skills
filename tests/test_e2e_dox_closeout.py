"""E2e test for DOX closeout behavior.

Verifies that an agent reads a DOX contract, makes a change,
and then updates the nearest AGENTS.md after the change.
"""

import os
import shutil
import uuid

import pytest

from _a0_e2e_client import A0E2EClient, gather_evidence

pytestmark = pytest.mark.e2e


@pytest.mark.usefixtures("task_tracker")
class TestDOXCloseout:
    """Verify DOX closeout updates AGENTS.md after changes."""

    def test_agent_updates_agents_md_after_change(self, a0_client: A0E2EClient, task_tracker, clean_tasks):
        """Agent should read a DOX contract, make a change, and update AGENTS.md.

        Creates a fixture project with an AGENTS.md that defines a rule,
        asks the agent to add a new file, then checks that the agent
        updates AGENTS.md to reflect the new file.
        """
        uid = uuid.uuid4().hex[:8]
        task_name = f"dox-closeout-{uid}"
        test_dir = f"/tmp/test_dox_closeout_{uid}"

        # Create fixture project with AGENTS.md
        os.makedirs(test_dir, exist_ok=True)
        agents_md_content = (
            "# Test Project DOX\n\n"
            "## Rules\n\n"
            "- All Python files must have a docstring\n"
            "- Files: none yet\n"
        )
        with open(os.path.join(test_dir, "AGENTS.md"), "w") as f:
            f.write(agents_md_content)

        task = a0_client.create_and_run_task(
            name=task_name,
            prompt=(
                f"Read the AGENTS.md file at {test_dir}/AGENTS.md. "
                "It defines rules for this project. "
                f"Now create a new Python file at {test_dir}/calculator.py "
                "with a simple add function and a module docstring. "
                "After creating the file, update the AGENTS.md at "
                f"{test_dir}/AGENTS.md to list calculator.py under 'Files'. "
                "In your final response, include the marker DOX_CLOSEOUT_OK "
                "and confirm you read the contract, created the file, "
                "and updated AGENTS.md."
            ),
        )
        task_uuid = task["uuid"]
        result = a0_client.wait_for_task(task_uuid)
        evidence = gather_evidence(a0_client, result)

        assert evidence["task_state"] == "idle", (
            f"Task {task_name} did not complete. State: {evidence.get('task_state')}"
        )
        assert evidence["chat_found"], f"No agent response found for {task_name}"
        assert "DOX_CLOSEOUT_OK" in evidence["last_response"], (
            f"Agent did not confirm DOX closeout. "
            f"Response: {evidence['last_response'][:300]}"
        )

        # Verify AGENTS.md was actually updated
        updated_agents = ""
        agents_path = os.path.join(test_dir, "AGENTS.md")
        if os.path.isfile(agents_path):
            with open(agents_path, "r") as f:
                updated_agents = f.read()

        assert "calculator" in updated_agents.lower(), (
            f"AGENTS.md was not updated to mention calculator.py. "
            f"Content: {updated_agents[:200]}"
        )

        # Clean up temp files
        shutil.rmtree(test_dir, ignore_errors=True)
