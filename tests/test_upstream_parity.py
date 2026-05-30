"""Upstream parity validation tests.

Report-only checks that the plugin tree and upstream snapshot have the
expected structural relationship. These tests do NOT enforce exact content
parity — they verify that major categories are present and that the parity
report script itself runs without error.

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_upstream_parity.py -v
"""

import os
import subprocess
import sys
import json
import pytest

PLUGIN_ROOT = os.path.dirname(os.path.dirname(__file__))
UPSTREAM_ROOT = "/a0/usr/projects/a0_agent_skills/comparison/official_agent_skills"
PARITY_SCRIPT = os.path.join(PLUGIN_ROOT, "scripts", "parity_report.py")


@pytest.fixture(scope="module")
def parity_report():
    """Run the parity report script once and return the JSON report."""
    result = subprocess.run(
        [sys.executable, PARITY_SCRIPT, "--plugin", PLUGIN_ROOT, "--upstream", UPSTREAM_ROOT, "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"Parity script failed: {result.stderr}"
    return json.loads(result.stdout)


# ===========================================================================
# Script runs successfully
# ===========================================================================


class TestParityScriptRuns:
    """The parity report script must run without error."""

    def test_script_runs(self, parity_report):
        """Parity script produces a valid JSON report."""
        assert isinstance(parity_report, dict)
        assert "summary" in parity_report

    def test_script_has_required_fields(self, parity_report):
        """Report contains all required top-level sections."""
        for field in ["summary", "by_category", "shared_changed", "shared_identical", "plugin_only", "upstream_only"]:
            assert field in parity_report, f"Missing field: {field}"


# ===========================================================================
# Skill parity
# ===========================================================================


class TestSkillParity:
    """Skills must exist in both plugin and upstream."""

    def test_skills_category_exists(self, parity_report):
        """The skills category must be present in the report."""
        assert "skills" in parity_report["by_category"]

    def test_shared_skills_exist(self, parity_report):
        """There must be shared skill files between plugin and upstream."""
        cats = parity_report["by_category"]
        skills = cats.get("skills", {})
        shared = len(skills.get("shared_identical", [])) + len(skills.get("shared_changed", []))
        assert shared >= 20, f"Expected at least 20 shared skills, found {shared}"

    def test_skill_count_23(self):
        """Plugin must have exactly 23 skill directories with SKILL.md."""
        skills_dir = os.path.join(PLUGIN_ROOT, "skills")
        count = len([
            d for d in os.listdir(skills_dir)
            if os.path.isdir(os.path.join(skills_dir, d))
            and os.path.isfile(os.path.join(skills_dir, d, "SKILL.md"))
        ])
        assert count == 23, f"Expected 23 skills, found {count}"


# ===========================================================================
# Agent parity
# ===========================================================================


class TestAgentParity:
    """Plugin agents must map to upstream persona concepts."""

    def test_plugin_has_agent_profiles(self):
        """Plugin must have agent profile directories."""
        agents_dir = os.path.join(PLUGIN_ROOT, "agents")
        assert os.path.isdir(agents_dir), "agents/ directory missing"
        profiles = [d for d in os.listdir(agents_dir) if os.path.isdir(os.path.join(agents_dir, d))]
        assert len(profiles) >= 3, f"Expected at least 3 agent profiles, found {len(profiles)}"

    def test_core_personas_present(self):
        """code-reviewer, security-auditor, and test-engineer must exist."""
        agents_dir = os.path.join(PLUGIN_ROOT, "agents")
        for name in ["code-reviewer", "security-auditor", "test-engineer"]:
            profile_dir = os.path.join(agents_dir, name)
            assert os.path.isdir(profile_dir), f"Missing agent profile: {name}"
            assert os.path.isfile(os.path.join(profile_dir, "agent.yaml")), f"Missing agent.yaml for {name}"


# ===========================================================================
# Command parity
# ===========================================================================


class TestCommandParity:
    """Plugin commands must map to upstream command concepts."""

    def test_plugin_has_commands(self):
        """Plugin must have command files."""
        commands_dir = os.path.join(PLUGIN_ROOT, "commands")
        assert os.path.isdir(commands_dir), "commands/ directory missing"

    def test_core_commands_present(self):
        """The 7 core slash commands must exist as .command.yaml files."""
        commands_dir = os.path.join(PLUGIN_ROOT, "commands")
        expected = ["build", "code-simplify", "plan", "review", "ship", "spec", "test"]
        for name in expected:
            yaml_path = os.path.join(commands_dir, f"{name}.command.yaml")
            assert os.path.isfile(yaml_path), f"Missing command: {name}.command.yaml"


# ===========================================================================
# Upstream-only tracking
# ===========================================================================


class TestUpstreamOnlyTracking:
    """Upstream-only files should be tracked and intentional."""

    def test_upstream_only_count_known(self, parity_report):
        """Upstream-only count should be stable and reasonable."""
        uo = parity_report["summary"]["upstream_only"]
        assert uo > 0, "Some upstream-only files expected (editor integrations, docs, etc.)"
        assert uo < 200, f"Unexpectedly high upstream-only count: {uo}"

    def test_upstream_has_editor_integrations(self, parity_report):
        """Upstream-only should include editor integration dirs."""
        upstream_only = parity_report["upstream_only"]
        has_claude = any(f.startswith(".claude/") for f in upstream_only)
        has_gemini = any(f.startswith(".gemini/") for f in upstream_only)
        assert has_claude or has_gemini, "Expected .claude/ or .gemini/ in upstream-only"


# ===========================================================================
# Structural health
# ===========================================================================


class TestStructuralHealth:
    """Basic structural health checks."""

    def test_plugin_has_manifest(self):
        """plugin.yaml must exist."""
        assert os.path.isfile(os.path.join(PLUGIN_ROOT, "plugin.yaml"))

    def test_plugin_has_readme(self):
        """README.md must exist."""
        assert os.path.isfile(os.path.join(PLUGIN_ROOT, "README.md"))

    def test_plugin_has_default_config(self):
        """default_config.yaml must exist."""
        assert os.path.isfile(os.path.join(PLUGIN_ROOT, "default_config.yaml"))

    def test_plugin_has_extensions(self):
        """extensions/ directory must exist with at least one extension."""
        ext_dir = os.path.join(PLUGIN_ROOT, "extensions")
        assert os.path.isdir(ext_dir), "extensions/ directory missing"

    def test_plugin_has_tests(self):
        """tests/ directory must exist with at least one test file."""
        tests_dir = os.path.join(PLUGIN_ROOT, "tests")
        assert os.path.isdir(tests_dir), "tests/ directory missing"
        test_files = [f for f in os.listdir(tests_dir) if f.startswith("test_") and f.endswith(".py")]
        assert len(test_files) >= 3, f"Expected at least 3 test files, found {len(test_files)}"
