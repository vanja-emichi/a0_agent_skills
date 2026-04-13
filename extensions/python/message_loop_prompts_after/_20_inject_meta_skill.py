"""_20_inject_meta_skill.py — message_loop_prompts_after hook

Injects a compact agent-skills routing table into every turn's extras.
This is the A0 equivalent of the original session-start.sh hook that injected
the `using-agent-skills` meta-skill at every Claude Code session start.

Without this, 10/21 skills have no activation path — they are never triggered
because no slash command references them. This routing table ensures the agent
auto-discovers and applies the correct skill for ANY task, not just the 11
reachable via explicit slash commands.

Design: compact routing table (~40 lines) injected into extras_persistent
every turn. Token cost is negligible. Follows the ladybug_memory pattern.
"""
from __future__ import annotations

from agent import LoopData
from helpers.extension import Extension
from helpers.print_style import PrintStyle

PLUGIN_NAME = "agent-skills"

# Compact routing table injected every turn.
# Source: skills/using-agent-skills/SKILL.md — routing flowchart + rules.
# Full skill content is loaded on demand via skills_tool:load.
_ROUTING_TABLE = """## agent-skills active — skill routing

For any non-trivial task, identify the phase and load the matching skill:
```
skills_tool:load <skill-name>
```

| Intent | Skill |
|--------|-------|
| Vague idea / needs refinement | `idea-refine` |
| New feature / project / change | `spec-driven-development` |
| Have spec, need tasks | `planning-and-task-breakdown` |
| Implementing code | `incremental-implementation` |
| UI / frontend work | `frontend-ui-engineering` |
| API or interface design | `api-and-interface-design` |
| Need doc-verified code | `source-driven-development` |
| Managing agent context | `context-engineering` |
| Writing or running tests | `test-driven-development` |
| Browser-based verification | `browser-testing-with-devtools` |
| Something broke | `debugging-and-error-recovery` |
| Reviewing code | `code-review-and-quality` |
| Security concerns | `security-and-hardening` |
| Performance concerns | `performance-optimization` |
| Simplifying code | `code-simplification` |
| Committing / branching | `git-workflow-and-versioning` |
| CI/CD pipeline work | `ci-cd-and-automation` |
| Writing docs / ADRs | `documentation-and-adrs` |
| Removing old systems | `deprecation-and-migration` |
| Deploying / launching | `shipping-and-launch` |
| Discover which skill applies | `using-agent-skills` |

**Rules:** Check for an applicable skill before starting. Skills are workflows,
not suggestions — follow steps in order. Multiple skills can chain (e.g.
spec → plan → build → test → review → ship).
"""


class InjectMetaSkill(Extension):
    """Injects agent-skills routing table into every turn's extras.

    Equivalent to the original session-start.sh hook that ran at each
    Claude Code session start and injected using-agent-skills content.
    This activates all 21 skills via natural language intent matching,
    not just the 11 reachable through slash commands.
    """

    async def execute(self, loop_data: LoopData = LoopData(), **kwargs):
        try:
            if not self.agent:
                return
            loop_data.extras_persistent["agent_skills_routing"] = _ROUTING_TABLE
        except Exception as exc:
            PrintStyle.error(f"[{PLUGIN_NAME}] inject-meta-skill error: {exc}")
