"""Phase 0 — subordinate prompt resolution tests.

Verifies that the plugin override mechanism for agent profiles works correctly:

1. Agent0 profile resolves the override specifics (skill discovery, DOX awareness, subordinate delegation)
2. Subordinate profiles (developer, test-engineer, etc.) do NOT get the override
3. Both agent0 and subordinate profiles get the DOX interpreter content
4. Agent numbering is correct (agent0=0, subordinates=1+)

Split into:
- TestPromptOverrideStructure: file-level structural checks (plugin venv)
- TestPromptOverrideRuntime: framework prompt resolution (A0 runtime venv)
- TestPromptOverrideE2E: live server behavioral tests (e2e marker)

All e2e tests skip automatically when the Agent Zero server is not running.
Runtime tests skip when the A0 runtime venv (langchain_core) is not available.
"""

from __future__ import annotations

import importlib.util
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLUGIN_DIR = Path("/a0/usr/plugins/a0_agent_skills")
DOX_MARKER = "Child `AGENTS.md` files are **not** auto-injected"

# Production content markers in the agent0 specifics override
SKILL_DISCOVERY_MARKER = "skill discovery"
AGENT0_EXCLUSIVE_MARKER = "agent0-exclusive"

# Markers now in the shared DOX interpreter (moved from agent0 specifics via Task 1.2)
CATCH_ALL_TRAVERSAL_MARKER = "Catch-All Traversal"
SKILL_DISCOVERY_INTERPRETER_MARKER = "Skill Discovery"
SUBORDINATE_DELEGATION_MARKER = "Subordinate Delegation"

AGENT0_OVERRIDE_SPECIFICS = (
    PLUGIN_DIR / "agents" / "agent0" / "prompts" / "agent.system.main.specifics.md"
)
FRAMEWORK_AGENT0_SPECIFICS = (
    Path("/a0/agents/agent0/prompts/agent.system.main.specifics.md")
)
FRAMEWORK_DEVELOPER_SPECIFICS = (
    Path("/a0/agents/developer/prompts/agent.system.main.specifics.md")
)
PLUGIN_DOX_PROMPT = (
    PLUGIN_DIR / "prompts" / "agent.system.dox_interpreter.md"
)

# Subordinate profiles shipped by the plugin
PLUGIN_PROFILES = ["code-reviewer", "security-auditor", "test-engineer"]

# ---------------------------------------------------------------------------
# Structural tests (plugin venv, no framework deps)
# ---------------------------------------------------------------------------


class TestPromptOverrideStructure:
    """Validate shipped override files and profile specifics."""

    def test_agent0_override_file_exists(self):
        """Plugin ships an agent0 specifics override."""
        assert AGENT0_OVERRIDE_SPECIFICS.is_file(), (
            f"Override file not found: {AGENT0_OVERRIDE_SPECIFICS}"
        )

    def test_agent0_override_contains_production_content(self):
        """Override file contains agent0-exclusive content (skill discovery, lifecycle, agent0 guard)."""
        content = AGENT0_OVERRIDE_SPECIFICS.read_text(encoding="utf-8").lower()
        assert SKILL_DISCOVERY_MARKER in content, (
            f"Expected '{SKILL_DISCOVERY_MARKER}' in {AGENT0_OVERRIDE_SPECIFICS}. "
            f"Content: {content[:200]}"
        )
        assert AGENT0_EXCLUSIVE_MARKER in content, (
            f"Expected '{AGENT0_EXCLUSIVE_MARKER}' in {AGENT0_OVERRIDE_SPECIFICS}. "
            f"Content: {content[:200]}"
        )

    def test_agent0_override_lacks_moved_sections(self):
        """Agent0 specifics no longer contains DOX awareness or subordinate delegation (moved to interpreter)."""
        content = AGENT0_OVERRIDE_SPECIFICS.read_text(encoding="utf-8").lower()
        assert "dox awareness" not in content, (
            f"'dox awareness' should no longer be in agent0 specifics (moved to interpreter)"
        )
        assert "subordinate delegation" not in content, (
            f"'subordinate delegation' should no longer be in agent0 specifics (moved to interpreter)"
        )

    def test_dox_interpreter_contains_moved_sections(self):
        """DOX interpreter now contains catch-all traversal, subordinate delegation, and skill discovery."""
        content = PLUGIN_DOX_PROMPT.read_text(encoding="utf-8")
        assert CATCH_ALL_TRAVERSAL_MARKER in content, (
            f"Expected '{CATCH_ALL_TRAVERSAL_MARKER}' in DOX interpreter"
        )
        assert SUBORDINATE_DELEGATION_MARKER in content, (
            f"Expected '{SUBORDINATE_DELEGATION_MARKER}' in DOX interpreter"
        )
        assert SKILL_DISCOVERY_INTERPRETER_MARKER in content, (
            f"Expected '{SKILL_DISCOVERY_INTERPRETER_MARKER}' in DOX interpreter"
        )

    def test_framework_agent0_specifics_lacks_override(self):
        """Framework default agent0 specifics does NOT contain the override."""
        if not FRAMEWORK_AGENT0_SPECIFICS.is_file():
            pytest.skip("Framework agent0 specifics not found")
        content = FRAMEWORK_AGENT0_SPECIFICS.read_text(encoding="utf-8")
        assert SKILL_DISCOVERY_MARKER not in content.lower(), (
            f"Framework specifics should NOT contain '{SKILL_DISCOVERY_MARKER}'"
        )

    def test_developer_specifics_lacks_override(self):
        """Developer profile specifics do NOT contain the override."""
        if not FRAMEWORK_DEVELOPER_SPECIFICS.is_file():
            pytest.skip("Framework developer specifics not found")
        content = FRAMEWORK_DEVELOPER_SPECIFICS.read_text(encoding="utf-8")
        assert SKILL_DISCOVERY_MARKER not in content.lower(), (
            f"Developer specifics should NOT contain '{SKILL_DISCOVERY_MARKER}'"
        )

    def test_plugin_profile_specifics_lack_override(self):
        """All plugin-shipped profile specifics (non-agent0) lack the override."""
        for profile in PLUGIN_PROFILES:
            specifics = (
                PLUGIN_DIR / "agents" / profile / "prompts"
                / "agent.system.main.specifics.md"
            )
            if not specifics.is_file():
                continue
            content = specifics.read_text(encoding="utf-8")
            assert SKILL_DISCOVERY_MARKER not in content.lower(), (
                f"Profile '{profile}' specifics should NOT contain '{SKILL_DISCOVERY_MARKER}'. "
                f"File: {specifics}"
            )

    def test_dox_interpreter_prompt_exists_and_contains_rules(self):
        """DOX interpreter prompt exists with core rules."""
        assert PLUGIN_DOX_PROMPT.is_file()
        content = PLUGIN_DOX_PROMPT.read_text(encoding="utf-8")
        assert DOX_MARKER in content, (
            f"DOX interpreter prompt should contain DOX rules. "
            f"File: {PLUGIN_DOX_PROMPT}"
        )

    def test_dox_prompt_available_to_all_plugin_profiles(self):
        """DOX interpreter prompt is accessible to every plugin profile.

        The plugin ships the prompt at plugin root prompts/ level, which is
        searched by all profiles via get_paths(). This structural check ensures
        the file exists and is non-empty regardless of profile path resolution.
        """
        assert PLUGIN_DOX_PROMPT.is_file()
        content = PLUGIN_DOX_PROMPT.read_text(encoding="utf-8")
        assert len(content.strip()) > 50, (
            f"DOX interpreter prompt too short ({len(content.strip())} chars). "
            f"File: {PLUGIN_DOX_PROMPT}"
        )
        # Verify key DOX rules present
        for marker in [
            "Child `AGENTS.md` files are **not** auto-injected",
            "read the applicable `AGENTS.md` chain",
            "Refresh affected Child DOX Index entries",
        ]:
            assert marker in content, (
                f"DOX interpreter missing expected marker: '{marker}'"
            )


# ---------------------------------------------------------------------------
# Runtime integration tests (A0 runtime venv with langchain_core)
# ---------------------------------------------------------------------------

_HAS_A0_RUNTIME = importlib.util.find_spec("langchain_core") is not None

A0_ROOT = Path("/a0")

if str(A0_ROOT) not in sys.path:
    sys.path.insert(0, str(A0_ROOT))


def _clear_runtime_caches():
    try:
        from helpers import cache
        for area in ("*(plugins)*", "*(subagent)*"):
            try:
                cache.clear(area)
            except Exception:
                pass
    except ImportError:
        pass


@pytest.fixture(autouse=True)
def clear_caches():
    _clear_runtime_caches()
    yield
    _clear_runtime_caches()


class FakeContext:
    id = "prompt-override-test"

    def __init__(self):
        self.log = SimpleNamespace(logs=[])

    def get_data(self, key, default=None):
        return default


class FakeAgent:
    """Minimal agent stub that delegates read_prompt to the real framework."""

    def __init__(self, profile: str, number: int = 0):
        self.agent_name = profile
        self.number = number
        self.config = SimpleNamespace(profile=profile)
        self.data = {}
        self.context = FakeContext()

    def read_prompt(self, name, **kwargs):
        from helpers import files, subagents
        dirs = subagents.get_paths(self, "prompts")
        return files.read_prompt_file(
            name, _directories=dirs, _agent=self, **kwargs
        )


@pytest.mark.runtime_integration
@pytest.mark.skipif(not _HAS_A0_RUNTIME, reason="A0 runtime venv required (langchain_core)")
class TestPromptOverrideRuntime:
    """Framework-level prompt resolution for profile overrides."""

    def test_agent0_resolves_override_specifics(self):
        """Agent0 profile resolves specifics containing skill discovery."""
        agent = FakeAgent(profile="agent0", number=0)
        prompt = agent.read_prompt("agent.system.main.specifics.md")
        assert prompt, "agent0 specifics resolved to empty"
        assert SKILL_DISCOVERY_MARKER in prompt.lower(), (
            f"agent0 specifics should contain '{SKILL_DISCOVERY_MARKER}'. "
            f"Got: {prompt[:200]}"
        )

    def test_developer_does_not_resolve_override(self):
        """Developer profile specifics do NOT contain skill discovery override."""
        agent = FakeAgent(profile="developer", number=1)
        prompt = agent.read_prompt("agent.system.main.specifics.md")
        assert SKILL_DISCOVERY_MARKER not in (prompt or "").lower(), (
            f"Developer specifics should NOT contain '{SKILL_DISCOVERY_MARKER}'. "
            f"Got: {prompt[:200] if prompt else '(empty)'}"
        )

    def test_test_engineer_does_not_resolve_override(self):
        """Test-engineer profile specifics do NOT contain skill discovery override."""
        agent = FakeAgent(profile="test-engineer", number=1)
        prompt = agent.read_prompt("agent.system.main.specifics.md")
        assert SKILL_DISCOVERY_MARKER not in (prompt or "").lower(), (
            f"test-engineer specifics should NOT contain '{SKILL_DISCOVERY_MARKER}'. "
            f"Got: {prompt[:200] if prompt else '(empty)'}"
        )

    def test_code_reviewer_does_not_resolve_override(self):
        """Code-reviewer profile specifics do NOT contain skill discovery override."""
        agent = FakeAgent(profile="code-reviewer", number=1)
        prompt = agent.read_prompt("agent.system.main.specifics.md")
        assert SKILL_DISCOVERY_MARKER not in (prompt or "").lower(), (
            f"code-reviewer specifics should NOT contain '{SKILL_DISCOVERY_MARKER}'. "
            f"Got: {prompt[:200] if prompt else '(empty)'}"
        )

    def test_security_auditor_does_not_resolve_override(self):
        """Security-auditor profile specifics do NOT contain skill discovery override."""
        agent = FakeAgent(profile="security-auditor", number=1)
        prompt = agent.read_prompt("agent.system.main.specifics.md")
        assert SKILL_DISCOVERY_MARKER not in (prompt or "").lower(), (
            f"security-auditor specifics should NOT contain '{SKILL_DISCOVERY_MARKER}'. "
            f"Got: {prompt[:200] if prompt else '(empty)'}"
        )

    def test_dox_interpreter_resolves_for_all_profiles(self):
        """DOX interpreter prompt resolves for both agent0 and subordinate."""
        for profile in ["agent0", "developer", "test-engineer"]:
            agent = FakeAgent(profile=profile, number=(0 if profile == "agent0" else 1))
            prompt = agent.read_prompt("agent.system.dox_interpreter.md")
            assert prompt, f"DOX interpreter empty for profile '{profile}'"
            assert DOX_MARKER in prompt, (
                f"DOX interpreter for '{profile}' should contain core rules. "
                f"Got: {prompt[:200]}"
            )


# ---------------------------------------------------------------------------
# E2E tests (live Agent Zero server)
# ---------------------------------------------------------------------------

import os

from tests._a0_e2e_client import A0E2EClient, gather_evidence


def _resolve_e2e_credentials() -> tuple[str, str]:
    """Resolve server credentials for e2e tests.

    Priority:
    1. A0_E2E_USERNAME / A0_E2E_PASSWORD env vars (explicit override)
    2. Framework dotenv AUTH_LOGIN / AUTH_PASSWORD (server's own config)
    """
    username = os.environ.get("A0_E2E_USERNAME", "")
    password = os.environ.get("A0_E2E_PASSWORD", "")
    if username and password:
        return username, password

    # Fall back to the server's own dotenv configuration
    try:
        sys.path.insert(0, str(A0_ROOT))
        from helpers import dotenv as _dotenv
        username = _dotenv.get_dotenv_value("AUTH_LOGIN") or ""
        password = _dotenv.get_dotenv_value("AUTH_PASSWORD") or ""
    except Exception:
        pass

    return username, password


@pytest.fixture(scope="session")
def a0_client() -> A0E2EClient:
    """Session-scoped client with credentials from env vars or server config."""
    username, password = _resolve_e2e_credentials()
    client = A0E2EClient(username=username, password=password)
    if not client.is_server_alive():
        pytest.skip("Agent Zero server is not running")
    return client


def _extract_response_text(response: str) -> str:
    """Extract plain text from a JSON response tool call."""
    import json as _json
    try:
        data = _json.loads(response)
        return data.get("tool_args", {}).get("text", response)
    except (ValueError, AttributeError):
        return response


@pytest.mark.e2e
@pytest.mark.dox_behavioral
class TestPromptOverrideE2E:
    """E2e tests proving prompt override behavior through live tasks."""

    def test_agent0_sees_override_in_task(
        self, a0_client: A0E2EClient, task_tracker, clean_tasks
    ):
        """Agent0 reports skill discovery content from its specifics."""
        uid = uuid.uuid4().hex[:8]
        task = a0_client.create_and_run_task(
            name=f"e2e-override-agent0-{uid}",
            system_prompt=(
                "You are a test agent. Report exactly what you see in your "
                "system prompt specifics. Do not add or remove anything."
            ),
            prompt=(
                "Look at your system prompt for the 'agent.system.main.specifics' section. "
                "If you see a section about 'skill discovery', "
                "respond with exactly: SKILL_DISCOVERY_CONFIRMED. "
                "If you do NOT see it, respond with: SKILL_DISCOVERY_MISSING."
            ),
        )
        task_tracker.append(task["uuid"])
        result = a0_client.wait_for_task(task["uuid"], timeout=600)

        assert result.get("state") == "idle", f"Task ended in state {result.get('state')}"

        evidence = gather_evidence(a0_client, result)
        response = _extract_response_text(evidence["last_response"])
        assert "SKILL_DISCOVERY_CONFIRMED" in response, (
            f"Agent0 should confirm skill discovery content. "
            f"Response (last 500): ...{response[-500:]}"
        )

    def test_subordinate_does_not_see_override(
        self, a0_client: A0E2EClient, task_tracker, clean_tasks
    ):
        """Subordinate with developer profile does NOT see skill discovery override."""
        uid = uuid.uuid4().hex[:8]
        task = a0_client.create_and_run_task(
            name=f"e2e-override-sub-{uid}",
            system_prompt=(
                "You are a test agent. Use call_subordinate when asked. "
                "Report the subordinate's response verbatim."
            ),
            prompt=(
                "Use call_subordinate with profile 'developer' and message: "
                "'Check your system prompt specifics for any section about skill discovery. "
                "If you see a skill discovery section, respond SUB_HAS_SKILL_DISCOVERY. "
                "If you do NOT see it, respond SUB_NO_SKILL_DISCOVERY. "
                "Also confirm you see DOX rules by responding SUB_SEES_DOX.'\n"
                "In your final response, include the subordinate's exact response."
            ),
        )
        task_tracker.append(task["uuid"])
        result = a0_client.wait_for_task(task["uuid"], timeout=600)

        assert result.get("state") == "idle", f"Task ended in state {result.get('state')}"

        evidence = gather_evidence(a0_client, result)
        response = _extract_response_text(evidence["last_response"])

        # Subordinate should NOT have the override
        assert "SUB_NO_SKILL_DISCOVERY" in response, (
            f"Subordinate should report no skill discovery content. "
            f"Response (last 500): ...{response[-500:]}"
        )
        # Subordinate should NOT have the override marker in any form
        assert "SUB_HAS_SKILL_DISCOVERY" not in response, (
            f"Subordinate should NOT report having skill discovery override. "
            f"Response (last 500): ...{response[-500:]}"
        )

    def test_both_profiles_get_dox_interpreter(
        self, a0_client: A0E2EClient, task_tracker, clean_tasks
    ):
        """Both agent0 and subordinate confirm DOX interpreter in system prompt."""
        uid = uuid.uuid4().hex[:8]
        task = a0_client.create_and_run_task(
            name=f"e2e-override-dox-{uid}",
            system_prompt=(
                "You are a test agent. Use call_subordinate when asked. "
                "Report what you and the subordinate find."
            ),
            prompt=(
                "1. Check your own system prompt for 'AGENTS.md' interpretation rules. "
                "If present, respond AGENT0_SEES_DOX.\n"
                "2. Use call_subordinate with profile 'developer' and message: "
                "'Check your system prompt for AGENTS.md interpretation rules. "
                "If present, respond SUB_SEES_DOX, otherwise SUB_NO_DOX.'\n"
                "3. In your final response, include both AGENT0_SEES_DOX and "
                "the subordinate's response about DOX."
            ),
        )
        task_tracker.append(task["uuid"])
        result = a0_client.wait_for_task(task["uuid"], timeout=600)

        assert result.get("state") == "idle", f"Task ended in state {result.get('state')}"

        evidence = gather_evidence(a0_client, result)
        response = _extract_response_text(evidence["last_response"])

        assert "AGENT0_SEES_DOX" in response, (
            f"Agent0 should confirm DOX interpreter. "
            f"Response (last 500): ...{response[-500:]}"
        )
        assert "SUB_SEES_DOX" in response, (
            f"Subordinate should also see DOX interpreter. "
            f"Response (last 500): ...{response[-500:]}"
        )
