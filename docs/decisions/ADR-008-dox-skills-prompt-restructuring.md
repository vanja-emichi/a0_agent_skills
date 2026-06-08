# ADR-008: DOX and Skills Prompt-Based Restructuring

## Status

Accepted

## Date

2026-06-08

## Context

The `a0_agent_skills` plugin previously enforced DOX compliance through Python extensions:

- `_10_dox_preflight_check.py` (write_before / patch_before) — blocked file edits when the AGENTS.md chain was unread
- `_20_dox_compliance_check.py` (monologue_end) — logged closeout reminders
- `_30_dox_subordinate_handoff.py` (tool_execute_before) — injected DOX context into subordinate messages
- `_00_inject_meta_skill.py` (agent_init) — auto-loaded the `using-agent-skills` meta skill into EXTRAS
- `_shared/` — shared utilities for chain computation, logging, and blocking logic

### Problems with enforcement

1. **False confidence.** Preflight only intercepted `text_editor` tool calls. Agents could bypass enforcement via `code_execution_tool` (terminal), `browser`, or other tools. The enforcement created an illusion of coverage without actually covering all mutation paths.

2. **Invisible meta skill.** The `_00_inject_meta_skill.py` injector registered `using-agent-skills` in `loaded_skills`, causing it to appear in the `[EXTRAS]` section of context history. EXTRAS is appended to message history, not the system prompt, and is framed as non-instructional context. Agents routinely ignored it.

3. **Complexity.** Six enforcement-related Python files plus shared utilities added maintenance burden, import chain fragility (langchain_core dependency in tests), and false-positive test failures when content changed.

4. **Duplicated content.** Having both an agent_init injector (EXTRAS) and a specifics override (system prompt position 1) duplicated ~200 lines of skill discovery content, wasting tokens.

## Decision

Replace enforcement extensions with prompt-based DOX and skill awareness:

### 1. Agent0 specifics override (position 1)

File: `agents/agent0/prompts/agent.system.main.specifics.md`

A condensed ~50-line override that replaces the framework's default 6-line agent0 specifics. Injected at position 1 of the main prompt (highest possible prominence). Contains:

- Role identity and operating behaviors
- Skill discovery summary and lifecycle reference
- DOX awareness (read chain before work, update after changes)
- Subordinate delegation guidance (include DOX context in messages)

### 2. DOX interpreter (position 2)

File: `prompts/agent.system.dox_interpreter.md`

Replaced the custom 25-line summary with the original 83-line DOX framework from `source_dox/_AGENTS.md`. Comprehensive coverage of all phases: read-before-edit, update-after-edit, hierarchy, child doc shape, style, closeout, and user preferences.

### 3. Removed enforcement extensions

Deleted:
- `_00_inject_meta_skill.py` (agent_init)
- `_10_dox_preflight_check.py` (write_before / patch_before)
- `_20_dox_compliance_check.py` (monologue_end)
- `_30_dox_subordinate_handoff.py` (tool_execute_before)
- `_shared/agents_chain.py`, `_shared/dox_preflight_shared.py`, `_shared/log_utils.py`, `_shared/__init__.py`

Kept: DOX interpreter extension (`_10a_dox_interpreter.py`), simplify-ignore, SDD cache, skill auto-unload.

## Consequences

### Positive

- **Better coverage.** Prompt-based awareness applies to all mutation paths (text_editor, terminal, browser, code_execution), not just text_editor.
- **Simpler codebase.** 8 fewer Python files, no shared utilities, no import chain issues.
- **Higher prominence.** Skill discovery and DOX awareness are in the system prompt at positions 1-2, not buried in EXTRAS.
- **No duplicated content.** One copy of meta skill content (specifics override), not two.
- **Simpler tests.** No enforcement blocking tests, no mock chain computation, no langchain_core dependency issues.

### Negative

- **No hard blocking.** Agents can theoretically ignore DOX rules. In practice, prompt-based awareness has proven more reliable than partial enforcement that only caught text_editor.
- **Relies on model compliance.** The agent must follow prompt instructions. Strong models comply; weaker models may occasionally skip DOX reads.
- **No runtime evidence.** Without enforcement extensions, there's no programmatic evidence that DOX chains were read. Verification depends on observing the agent's actual tool calls.

### Risks mitigated

- The original enforcement only covered text_editor (easy bypass). Prompt coverage is broader even if softer.
- The agent0 specifics override is at position 1 — the most prominent location in the entire system prompt.
- The DOX interpreter at position 2 uses the authoritative upstream framework content, not a custom summary.
