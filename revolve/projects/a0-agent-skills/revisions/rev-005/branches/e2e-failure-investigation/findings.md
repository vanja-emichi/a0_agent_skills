# E2E Test Failure Investigation: `test_subordinate_does_not_see_override`

## Classification: TEST EXPECTATION ISSUE (semantic mismatch with framework behavior)

**Secondary classification**: The test design itself is the root cause — it relies on an LLM's subjective semantic interpretation of "skill discovery" content, which conflicts with the framework's universal skills listing.

---

## Executive Summary

The e2e test `test_subordinate_does_not_see_override` fails because the framework's standard `## skills` prompt section (built by `_13_skills_prompt.py`) is injected into ALL agents including subordinates. This section lists all available skills, including `using-agent-skills`, whose description contains "Discovers and invokes agent skills... discover which skill applies". When the test's subordinate LLM is asked whether it sees "skill discovery" content, it correctly reports `SUB_HAS_SKILL_DISCOVERY` because it sees the skill description listing.

The plugin's actual override mechanism (auto-load extension) is correctly gated to agent 0 only and does NOT fire for subordinates. The developer profile specifics file correctly lacks any "skill discovery" text. The test's structural and runtime integration assertions (which check file contents and prompt resolution) all pass. Only the e2e behavioral assertion fails because it tests a semantic interpretation that conflicts with the framework's universal skills listing.

---

## Detailed Evidence Chain

### 1. Test Structure (3 tiers)

The test file `test_e2e_prompt_override.py` has three test classes:

- **`TestPromptOverrideStructure`** (file-level checks): Reads `agent.system.main.specifics.md` files and asserts `"skill discovery"` is absent. ✅ PASSES — developer specifics genuinely lack this text.
- **`TestPromptOverrideRuntime`** (framework prompt resolution): Uses `FakeAgent` to resolve prompts and checks for the marker. ✅ PASSES — resolved prompts for developer/test-engineer/code-reviewer/security-auditor all lack the marker.
- **`TestPromptOverrideE2E`** (live LLM behavioral): Creates a scheduler task asking a developer subordinate to self-report. ❌ FAILS.

### 2. The Failing E2E Assertion

The test creates a task that calls `call_subordinate` with profile `developer` and asks:

> "Check your system prompt specifics for any section about skill discovery. If you see a skill discovery section, respond SUB_HAS_SKILL_DISCOVERY. If you do NOT see it, respond SUB_NO_SKILL_DISCOVERY."

The test expects `SUB_NO_SKILL_DISCOVERY` in the response.

### 3. Developer Profile Specifics (No Issue)

`/a0/agents/developer/prompts/agent.system.main.specifics.md` (184 lines): Contains extensive developer role description but does NOT contain "skill discovery" anywhere. Confirmed by grep and file read.

### 4. Plugin Auto-Load Extension (Correctly Gated)

`/a0/usr/plugins/a0_agent_skills/extensions/python/message_loop_start/_10_load_using_agent_skills.py`:

- Line 40-42: `agent_number = getattr(self.agent, "number", -1)` / `if agent_number != 0: return`
- This extension correctly ONLY runs for agent 0 (the main agent).
- Subordinates (agent number 1+) never receive this auto-load injection.
- **This is working as designed.**

### 5. ROOT CAUSE: Framework Skills Listing Extension

`/a0/extensions/python/system_prompt/_13_skills_prompt.py`:

```python
class SkillsPrompt(Extension):
    async def execute(self, system_prompt: list[str] = [], loop_data: LoopData = LoopData(), **kwargs: Any):
        if not self.agent:
            return
        prompt = await build_prompt(self.agent)
        if prompt:
            system_prompt.append(prompt)

@extensible
async def build_prompt(agent: Agent) -> str:
    available = skills_helper.list_skills(agent=agent)
    result: list[str] = []
    for skill in available:
        name = skill.name.strip().replace("\n", " ")[:100]
        descr = skill.description.replace("\n", " ").strip()
        if len(descr) > 100:
            descr = descr[:100].rstrip() + "..."
        result.append(f"- {name}: {descr}" if descr else f"- {name}")
    if not result:
        return ""
    return agent.read_prompt("agent.system.skills.md", skills="\n".join(result))
```

**Critical observations:**
1. NO `agent_number` gating — runs for ALL agents including subordinates.
2. Lists ALL available skills via `skills_helper.list_skills(agent=agent)`.
3. Renders via `agent.system.skills.md` template which creates a `## skills` section.

### 6. The Semantic Collision

The `using-agent-skills` skill has this frontmatter:

```yaml
name: using-agent-skills
description: Discovers and invokes agent skills. Use when starting a session or when
  you need to discover which skill applies to the current task. This is the meta-skill
  that governs how all other skills are discovered and invoked.
triggers:
  - "skill discovery"
  - "which skill"
  - "find skill"
  - "agent skills"
  - "meta skill"
```

When `_13_skills_prompt.py` runs for a subordinate agent, it produces a section like:

```
## skills
use skills_tool action search when the user's wording sounds like a task...
available:
- using-agent-skills: Discovers and invokes agent skills. Use when starting a session
  or when you need to discover which skill applies to the current task. This is the me...
- spec-driven-development: Creates specs before coding...
- ...
```

The LLM, asked "do you see skill discovery content?", sees "Discovers and invokes agent skills... discover which skill applies" and reasonably answers `SUB_HAS_SKILL_DISCOVERY`.

---

## Why Structural/Runtime Tests Pass But E2E Fails

| Test Tier | What It Checks | Passes? | Why |
|---|---|---|---|
| Structural | `"skill discovery"` literal in specifics.md file | ✅ | The string genuinely isn't in the specifics file |
| Runtime | `"skill discovery"` in resolved `agent.system.main.specifics.md` prompt | ✅ | Prompt resolution of that specific file has no such text |
| E2E | LLM's subjective interpretation of full system prompt | ❌ | The full system prompt includes `## skills` listing with using-agent-skills description |

The structural and runtime tests only check ONE fragment of the system prompt (`agent.system.main.specifics.md`). The e2e test checks the FULL assembled system prompt that the subordinate LLM actually sees — which includes the `## skills` section from `_13_skills_prompt.py`.

---

## Recommended Fix Approaches

### Option A: Fix the Test (Recommended — Lowest Risk)

The test's e2e assertion conflates two distinct concepts:
1. The plugin's skill-discovery auto-load override (agent0-only — correctly gated)
2. The framework's standard skills listing (all agents — by design)

**Fix:** Change the e2e test to ask about the SPECIFIC override content rather than generic "skill discovery". For example:
- Ask the subordinate if it sees the `using-agent-skills` SKILL.md full content (the 252-line discovery tree with "Skill Discovery" heading and the full decision flowchart).
- Ask about agent0-specific override markers like "Follow its skill discovery tree for all tasks" or "Agent Skills (auto-loaded)" — the text injected by `_10_load_using_agent_skills.py`.
- Ask whether the subordinate sees loaded_skills content (the `agent.system.skills.loaded.md` section that only appears when `_65_include_loaded_skills.py` fires, which depends on `agent.data['loaded_skills']`).

### Option B: Fix the Framework (Higher Risk — Changes Core Behavior)

Add agent_number gating to `_13_skills_prompt.py` so the `## skills` section is only shown to agent 0:

```python
async def execute(self, system_prompt: list[str] = [], loop_data: LoopData = LoopData(), **kwargs: Any):
    if not self.agent:
        return
    if getattr(self.agent, "number", 0) != 0:
        return  # Subordinates don't get skills listing
    prompt = await build_prompt(self.agent)
    if prompt:
        system_prompt.append(prompt)
```

**Risk:** This would prevent subordinates from discovering and loading skills, which may be a deliberate framework feature (subordinates can use skills too). This changes core Agent Zero behavior and could break other workflows.

### Option C: Change the Plugin's Skill Description (Partial Mitigation)

Reword `using-agent-skills` SKILL.md description to avoid the phrase "discover which skill applies" so it's less likely to trigger the semantic match. However, this is fragile — any mention of skills discovery in any skill description would re-trigger the issue.

---

## Additional Context

### ADR-008 History

The plugin previously had enforcement extensions (`_00_inject_meta_skill.py`, etc.) that were removed per ADR-008. The ADR explicitly states the override is now prompt-based in the agent0 specifics file at position 1. However, comments in the test file indicate the override was "removed per ADR-008 follow-up" and the protocol is now "baked into root AGENTS.md files". This means the current architecture relies on:
1. Project AGENTS.md files (injected via project prompt extension)
2. The auto-load extension for agent 0 only
3. The framework's universal skills listing for all agents

### Skills Auto-Unload

Per SKILL.md: "Skills auto-unload at monologue_end to keep context clean." This means even if a subordinate loaded a skill, it would be cleaned up. But the skills LISTING (from `_13_skills_prompt.py`) is not a loaded skill — it's a permanent system prompt section.

---

## Verification Commands

```bash
# Confirm developer specifics lack the marker
grep -i 'skill discovery' /a0/agents/developer/prompts/agent.system.main.specifics.md
# Result: no matches

# Confirm plugin extension gates on agent 0
grep -n 'agent_number' /a0/usr/plugins/a0_agent_skills/extensions/python/message_loop_start/_10_load_using_agent_skills.py
# Result: line 40-42, correctly returns if agent_number != 0

# Confirm framework skills extension has NO agent gating
grep -n 'agent_number\|number' /a0/extensions/python/system_prompt/_13_skills_prompt.py
# Result: no matches — runs for all agents

# Confirm using-agent-skills description contains 'discover'
grep -i 'discover' /a0/usr/plugins/a0_agent_skills/skills/using-agent-skills/SKILL.md | head -3
# Result: "Discovers and invokes agent skills... discover which skill applies"
```

---

## Conclusion

This is NOT a plugin bug and NOT a framework bug. It is a test expectation issue where the e2e assertion uses a semantic check that is incompatible with the framework's design (all agents see the skills listing). The plugin's own override mechanism is correctly implemented and properly gated. The recommended fix is Option A: adjust the e2e test to check for the specific auto-load injection text rather than asking an LLM to subjectively identify "skill discovery" content.
