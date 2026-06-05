"""E2e tests for Agent Zero plugin extensions.

Tests that plugin extensions (meta-skill injection, SDD cache, simplify-ignore)
work correctly in a live agent session.

Prerequisites:
    - Agent Zero server running (auto-detected by conftest)
    - A0_E2E_USERNAME / A0_E2E_PASSWORD environment variables set
    - a0_agent_skills plugin installed
"""

from __future__ import annotations

import pytest

from tests._a0_e2e_client import A0E2EClient, gather_evidence

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def client(a0_client: A0E2EClient) -> A0E2EClient:
    return a0_client


# ------------------------------------------------------------------
# Test: Meta-skill injection via agent_init extension
# ------------------------------------------------------------------

class TestMetaSkillInjection:
    """Verify the _00_inject_meta_skill.py extension auto-loads using-agent-skills."""

    def test_meta_skill_injected_in_scheduler_task(self, client, task_tracker):
        """Create a scheduler task and verify using-agent-skills is loaded."""
        task = client.create_and_run_task(
            name="e2e-meta-skill-inject",
            system_prompt="You are a test agent. Respond with 'META_OK' in your response.",
            prompt="Say hello and confirm you are ready.",
        )
        task_tracker.append(task["uuid"])

        result = client.wait_for_task(task["uuid"])
        assert result is not None, "Task did not complete"

        context_id = result.get("context_id")
        assert context_id, "No context_id in task result"

        # Check chat.json for loaded skills
        chat = client.get_chat_json(context_id)
        assert chat is not None, "Chat not found"

        agents = chat.get("agents", [])
        assert agents, "No agents in chat"

        data = agents[0].get("data", {})
        loaded = data.get("loaded_skills", [])
        assert "using-agent-skills" in loaded, (
            f"using-agent-skills not in loaded_skills: {loaded}"
        )


# ------------------------------------------------------------------
# Test: Extension files are present and valid
# ------------------------------------------------------------------

class TestExtensionFilePresence:
    """Verify all extension files exist and are valid Python."""

    EXPECTED_EXTENSIONS = [
        "extensions/python/agent_init/_00_inject_meta_skill.py",
        "extensions/python/monologue_end/_10_simplify_ignore.py",
        "extensions/python/text_editor_patch_after/_10_simplify_ignore.py",
        "extensions/python/text_editor_write_after/_10_simplify_ignore.py",
        "extensions/python/tool_execute_after/_10_sdd_cache.py",
        "extensions/python/tool_execute_before/_10_sdd_cache.py",
        "extensions/python/tool_execute_before/_20_simplify_ignore.py",
    ]

    def test_all_extension_files_present(self):
        """Verify all extension files exist in the plugin directory."""
        import os
        plugin_dir = "/a0/usr/plugins/a0_agent_skills"
        for ext_path in self.EXPECTED_EXTENSIONS:
            full_path = os.path.join(plugin_dir, ext_path)
            assert os.path.isfile(full_path), f"Extension file missing: {ext_path}"

    def test_all_extension_files_compile(self):
        """Verify all extension files are valid Python."""
        import py_compile
        import os
        plugin_dir = "/a0/usr/plugins/a0_agent_skills"
        for ext_path in self.EXPECTED_EXTENSIONS:
            full_path = os.path.join(plugin_dir, ext_path)
            py_compile.compile(full_path, doraise=True)
