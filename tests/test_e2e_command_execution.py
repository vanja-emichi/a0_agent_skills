"""E2e tests for Agent Zero command resolution.

Tests that plugin commands are discovered and resolved correctly via
the /api/commands endpoint. These are deterministic API tests —
no LLM agents are involved.

Prerequisites:
    - Agent Zero server running (auto-detected by conftest)
    - A0_E2E_USERNAME / A0_E2E_PASSWORD environment variables set
    - a0_agent_skills plugin installed
"""

from __future__ import annotations

import pytest

from tests._a0_e2e_client import A0E2EClient

pytestmark = pytest.mark.e2e

# ------------------------------------------------------------------
# Fixtures — reuse the session-scoped a0_client from conftest.py
# ------------------------------------------------------------------

@pytest.fixture(scope="module")
def client(a0_client: A0E2EClient) -> A0E2EClient:
    """Module-scoped alias for the conftest a0_client fixture."""
    return a0_client


@pytest.fixture(scope="module")
def all_commands(client: A0E2EClient):
    """Fetch all effective commands once for the module."""
    return client.list_effective_commands()


# ------------------------------------------------------------------
# Test: Command discovery
# ------------------------------------------------------------------

class TestCommandDiscovery:
    """Verify all plugin commands are discoverable."""

    PLUGIN_COMMAND_NAMES = [
        "spec",
        "plan",
        "build",
        "test",
        "review",
        "ship",
        "code-simplify",
    ]

    def test_all_plugin_commands_discovered(self, all_commands):
        names = [c["name"] for c in all_commands]
        for expected in self.PLUGIN_COMMAND_NAMES:
            assert expected in names, f"Command '{expected}' not found in effective commands"

    def test_plugin_commands_have_correct_type(self, all_commands):
        by_name = {c["name"]: c for c in all_commands}
        text_commands = ["spec", "plan", "build", "test", "review", "code-simplify"]
        for name in text_commands:
            assert by_name[name]["command_type"] == "text", f"{name} should be text type"
        assert by_name["ship"]["command_type"] == "script", "ship should be script type"

    def test_plugin_commands_have_description(self, all_commands):
        for name in self.PLUGIN_COMMAND_NAMES:
            by_name = {c["name"]: c for c in all_commands}
            assert by_name[name].get("description"), f"{name} missing description"

    def test_plugin_commands_marked_as_plugin_scope(self, all_commands):
        by_name = {c["name"]: c for c in all_commands}
        for name in self.PLUGIN_COMMAND_NAMES:
            assert by_name[name]["scope_key"] == "plugin", f"{name} should have plugin scope"


# ------------------------------------------------------------------
# Test: Text command resolution
# ------------------------------------------------------------------

class TestTextCommandResolution:
    """Verify text commands resolve with template content."""

    TEXT_COMMANDS = [
        ("spec", "specification", "spec-driven"),
        ("plan", "task", "breakdown"),
        ("build", "implement", "incremental"),
        ("test", "test", "TDD"),
        ("review", "review", "correctness"),
        ("code-simplify", "simplif", "complexity"),
    ]

    def test_text_command_resolves_with_content(self, client, all_commands):
        by_name = {c["name"]: c for c in all_commands}
        for name, keyword_a, keyword_b in self.TEXT_COMMANDS:
            cmd = by_name[name]
            result = client.resolve_command(
                path=cmd["path"],
                slash_text=f"/{name}",
            )
            assert result.get("ok"), f"{name} resolution failed: {result}"
            resolution = result["resolution"]
            text = resolution["result"]["text"]
            assert len(text) > 50, f"{name} resolved text too short ({len(text)} chars)"

    def test_spec_command_contains_expected_sections(self, client, all_commands):
        by_name = {c["name"]: c for c in all_commands}
        cmd = by_name["spec"]
        result = client.resolve_command(
            path=cmd["path"],
            slash_text="/spec user login feature",
        )
        text = result["resolution"]["result"]["text"]
        # Should contain arguments
        assert "user login feature" in text, "Arguments should appear in resolved text"

    def test_text_command_with_no_args_still_resolves(self, client, all_commands):
        by_name = {c["name"]: c for c in all_commands}
        cmd = by_name["plan"]
        result = client.resolve_command(
            path=cmd["path"],
            slash_text="/plan",
        )
        assert result.get("ok"), f"plan resolution with no args failed"
        text = result["resolution"]["result"]["text"]
        assert len(text) > 50, "plan resolved text too short"


# ------------------------------------------------------------------
# Test: Script command resolution
# ------------------------------------------------------------------

class TestScriptCommandResolution:
    """Verify script commands (ship) resolve via Python execution."""

    def test_ship_command_resolves(self, client, all_commands):
        by_name = {c["name"]: c for c in all_commands}
        cmd = by_name["ship"]
        result = client.resolve_command(
            path=cmd["path"],
            slash_text="/ship",
        )
        assert result.get("ok"), f"ship resolution failed: {result}"
        resolution = result["resolution"]
        text = resolution["result"]["text"]
        assert len(text) > 50, f"ship resolved text too short ({len(text)} chars)"

    def test_ship_command_returns_expected_structure(self, client, all_commands):
        by_name = {c["name"]: c for c in all_commands}
        cmd = by_name["ship"]
        result = client.resolve_command(
            path=cmd["path"],
            slash_text="/ship",
        )
        resolution = result["resolution"]
        assert "command" in resolution
        assert "invocation" in resolution
        assert "result" in resolution
        assert "text" in resolution["result"]
        assert "effects" in resolution["result"]
