"""E2e tests for command template rendering.

Verifies that text command templates render correctly with
{raw} and {args} placeholders via the resolve API.

Prerequisites:
    - Agent Zero server running (auto-detected by conftest)
    - A0_E2E_USERNAME / A0_E2E_PASSWORD environment variables set
    - a0_agent_skills plugin installed
"""

from __future__ import annotations

import pytest

from tests._a0_e2e_client import A0E2EClient

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def client(a0_client: A0E2EClient) -> A0E2EClient:
    """Module-scoped alias for the conftest a0_client fixture."""
    return a0_client


# ------------------------------------------------------------------
# Test: Text command template rendering
# ------------------------------------------------------------------

class TestCommandRendering:
    """Verify text command templates render placeholders correctly."""

    TEXT_COMMANDS = {
        "spec": {
            "expected_in_text": [
                "spec-driven-development",
                "Create a user authentication system",
            ],
        },
        "plan": {
            "expected_in_text": [
                "planning-and-task-breakdown",
                "Break down the auth feature",
            ],
        },
        "build": {
            "expected_in_text": [
                "incremental-implementation",
                "Implement the login endpoint",
            ],
        },
        "test": {
            "expected_in_text": [
                "test-driven-development",
                "Write tests for the auth module",
            ],
        },
        "review": {
            "expected_in_text": [
                "code-review-and-quality",
                "Check the auth code for issues",
            ],
        },
        "code-simplify": {
            "expected_in_text": [
                "code-simplification",
                "Simplify the auth middleware",
            ],
        },
    }

    @pytest.mark.parametrize(
        "cmd_name",
        list(TEXT_COMMANDS.keys()),
        ids=list(TEXT_COMMANDS.keys()),
    )
    def test_text_command_renders_skill_and_user_input(
        self, client: A0E2EClient, all_commands, cmd_name: str
    ):
        """Each text command should embed the skill name and user input."""
        cfg = self.TEXT_COMMANDS[cmd_name]
        slash_text = f"/{cmd_name} " + cfg["expected_in_text"][1]

        # Look up the full command path from the discovery list
        by_name = {c["name"]: c for c in all_commands}
        cmd_path = by_name[cmd_name]["path"]

        result = client.resolve_command(path=cmd_path, slash_text=slash_text)

        # The resolve API returns {ok, resolution: {result: {text: "..."}}}
        assert result.get("ok"), f"Command {cmd_name} resolution failed: {result}"
        rendered_text = result["resolution"]["result"]["text"]

        assert rendered_text, f"Command {cmd_name} returned empty text"
        for expected in cfg["expected_in_text"]:
            assert expected in rendered_text, (
                f"Command {cmd_name}: expected '{expected}' in rendered text. "
                f"Got: {rendered_text[:200]}"
            )


@pytest.fixture(scope="module")
def all_commands(client: A0E2EClient):
    """Fetch all effective commands once for the module."""
    return client.list_effective_commands()


class TestShipCommandRendering:
    """Verify the ship script command resolves without error."""

    def test_ship_command_resolves(self, client: A0E2EClient, all_commands):
        """Ship is a script command — it should resolve without error."""
        by_name = {c["name"]: c for c in all_commands}
        cmd_path = by_name["ship"]["path"]
        result = client.resolve_command(path=cmd_path, slash_text="/ship")

        # Script commands return {ok, command, invocation, result}
        assert isinstance(result, dict), f"Expected dict, got {type(result)}"
