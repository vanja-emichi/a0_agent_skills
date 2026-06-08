"""E2e tests for reference file access from skills.

Verifies that agents can load skills and read reference files
via skills_tool within a scheduler task.

Prerequisites:
    - Agent Zero server running (auto-detected by conftest)
    - A0_E2E_USERNAME / A0_E2E_PASSWORD environment variables set
    - a0_agent_skills plugin installed
"""

from __future__ import annotations

import uuid

import pytest

from tests._a0_e2e_client import A0E2EClient, gather_evidence

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def client(a0_client: A0E2EClient) -> A0E2EClient:
    """Module-scoped alias for the conftest a0_client fixture."""
    return a0_client


REFERENCE_FILES = [
    "performance-checklist.md",
    "security-checklist.md",
    "testing-patterns.md",
    "accessibility-checklist.md",
    "orchestration-patterns.md",
]


class TestReferenceFileAccess:
    """Verify agents can read reference files via skills_tool."""

    def test_agent_reads_reference_file(self, client: A0E2EClient):
        """Agent should load a skill and read a reference file."""
        uid = uuid.uuid4().hex[:8]
        task = client.create_and_run_task(
            name=f"ref-access-{uid}",
            prompt=(
                "Load the skill 'using-agent-skills' with skills_tool, "
                "then use skills_tool action=read_file to read the file "
                "references/performance-checklist.md from that skill. "
                "In your final response, include the marker REF_OK"
            ),
        )
        result = client.wait_for_task(task["uuid"])
        evidence = gather_evidence(client, result)

        assert evidence["task_state"] == "idle", (
            f"Task did not complete. State: {evidence.get('task_state')}"
        )
        assert evidence["chat_found"], "No agent response found in chat.json"
        assert "REF_OK" in evidence["last_response"], (
            f"Agent did not confirm reference file access. "
            f"Response: {evidence['last_response'][:300]}"
        )

    @pytest.mark.parametrize(
        "ref_file",
        REFERENCE_FILES,
        ids=[f.replace(".md", "") for f in REFERENCE_FILES],
    )
    def test_all_reference_files_exist_and_load(self, ref_file: str):
        """All reference files should exist in the plugin."""
        import os
        ref_path = os.path.join(
            "/a0/usr/plugins/a0_agent_skills/skills/using-agent-skills/references",
            ref_file,
        )
        assert os.path.isfile(ref_path), f"Reference file missing: {ref_path}"
        with open(ref_path) as f:
            content = f.read()
        assert len(content) > 50, f"Reference file too short: {ref_file}"


class TestSkillContentVerification:
    """Verify skill content is valid and loadable."""

    def test_meta_skill_references_section(self):
        """The meta-skill should list all reference files."""
        import os
        skill_path = "/a0/usr/plugins/a0_agent_skills/skills/using-agent-skills/SKILL.md"
        with open(skill_path) as f:
            content = f.read()

        for ref_file in REFERENCE_FILES:
            assert ref_file in content, (
                f"Meta-skill SKILL.md does not reference {ref_file}"
            )
