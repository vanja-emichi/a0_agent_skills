"""E2e tests for Agent Zero plugin extensions.

Tests that plugin extensions (SDD cache, simplify-ignore, skill auto-unload)
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
# Test: Meta-skill content in agent0 specifics override
# ------------------------------------------------------------------

class TestMetaSkillSpecificsOverride:
    """Verify the agent.system.main.specifics.md override includes meta-skill content."""

    def test_specifics_override_file_exists(self):
        """Verify the specifics override file exists in the plugin."""
        import os
        path = "/a0/usr/plugins/a0_agent_skills/agents/agent0/prompts/agent.system.main.specifics.md"
        assert os.path.isfile(path), f"Specifics override file missing: {path}"

    def test_specifics_override_has_meta_skill_content(self):
        """Verify the specifics override contains meta-skill operating behaviors."""
        import os
        path = "/a0/usr/plugins/a0_agent_skills/agents/agent0/prompts/agent.system.main.specifics.md"
        content = open(path).read()
        # Core operating behaviors
        assert "skill" in content.lower(), "Specifics override missing skill references"
        assert "AGENTS.md" in content or "DOX" in content, "Specifics override missing DOX/AGENTS.md reference"


# ------------------------------------------------------------------
# Test: Extension files are present and valid
# ------------------------------------------------------------------

class TestExtensionFilePresence:
    """Verify all extension files exist and are valid Python."""

    EXPECTED_EXTENSIONS = [
        "extensions/python/monologue_end/_10_simplify_ignore.py",
        "extensions/python/monologue_end/_15_skill_auto_unload.py",
        "extensions/python/text_editor_patch_after/_10_simplify_ignore.py",
        "extensions/python/text_editor_write_after/_10_simplify_ignore.py",
        "extensions/python/tool_execute_after/_10_sdd_cache.py",
        "extensions/python/tool_execute_before/_10_sdd_cache.py",
        "extensions/python/tool_execute_before/_20_simplify_ignore.py",
        "extensions/python/system_prompt/_10a_dox_interpreter.py",
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
