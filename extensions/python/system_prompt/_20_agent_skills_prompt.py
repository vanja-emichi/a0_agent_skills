"""_20_agent_skills_prompt.py — system_prompt hook

Injects a compact delegation table into the system prompt.

Agent0 (orchestrator) loads NO skills. It delegates all work to
specialist subagents. Each subagent loads its own skill as needed.

This replaces the previous 3-tier routing table (3,000+ chars)
with a compact delegation table (~500 chars).
"""
from __future__ import annotations

from helpers.extension import Extension

from helpers.print_style import PrintStyle

PLUGIN_NAME = "a0_agent_skills"

DELEGATION_TABLE = """## Agent Skills — Task Delegation

**Rule: Delegate all specialist work to subagents. You orchestrate lifecycle phases.**

| Intent | Delegate to |
|--------|-------------|
| Ideas, research, planning | `researcher` |
| Specs, implementation, simplification | `developer` |
| Code review, quality | `code-reviewer` |
| Tests, TDD | `test-engineer` |
| Security audit, OWASP | `security-auditor` |
| Skill create/benchmark | `skill-creator` |

**Lifecycle:** /idea → /spec → /plan → /build → /test → /review → /ship. You orchestrate phases, subagents execute. Security audits (`/security`) and code simplification (`/code-simplify`) can run at any phase.

For simple questions, answer directly."""

def get_delegation_table() -> str:
    """Public accessor for testing. Returns the static delegation table."""
    return DELEGATION_TABLE


class AgentSkillsPrompt(Extension):
    """Injects compact delegation table into the system prompt."""

    async def execute(self, system_prompt: list[str] | None = None, **kwargs):
        if system_prompt is None:
            system_prompt = []
        try:
            system_prompt.append(DELEGATION_TABLE)
        except Exception as exc:
            PrintStyle.error(f"[{PLUGIN_NAME}] system_prompt injection error: {exc}")
