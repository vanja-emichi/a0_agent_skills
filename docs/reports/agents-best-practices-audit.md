# Agent Zero & a0_agent_skills Audit vs agents-best-practices

**Date:** 2026-05-31 | **Auditor:** Deep Research | **Reference:** agents-best-practices skill (12 ref files)

## Summary Ratings

| # | Dimension | Rating | Key Issue |
|---|-----------|--------|-----------|
| 1 | Architecture & Harness Maturity | 🟡 Partial | No typed events, no approval manager, no authority hierarchy |
| 2 | Agentic Loop | 🟡 Partial | `while True` with no budgets (step/time/cost) |
| 3 | Tools & Permissions | 🔴 Gap | No permission engine, no risk taxonomy, no schema validation |
| 4 | Context & Compaction | 🟡 Partial | Compaction loses plan/goal/approval/skill state |
| 5 | Planning & Goals | 🟡 Partial | Plugin adds durable state but no planning mode in core |
| 6 | Skills & Connectors | ✅ Strong | Best-in-class progressive disclosure + enforcement gate |
| 7 | System Prompts & Instructions | 🟡 Partial | No trust labels, no injection boundary markers |
| 8 | Security | 🟡 Partial | Infection checker + Docker sandbox, but no layered guardrails |
| 9 | Observability & Evals | 🔴 Gap | Logging exists but no traces, no evals, no cost tracking |
| 10 | Prompt Caching & Cost | 🔴 Gap | Cache param exists but no telemetry or stable-prefix design |
| 11 | Agent Legibility | 🟡 Partial | Plugin adds workflow state + handoff, but no entropy mgmt |
| 12 | Mechanical Invariants | 🔴 Gap | Plugin adds enforcement; core lacks validators and policy gates |

---

## Dimension 1: Architecture & Harness Maturity — 🟡

**Findings:** Agent Zero has a well-designed component model with clear separation via its extension/plugin architecture. 15+ component types exist: instruction manager, context builder (`prepare_prompt`), model adapter (`call_chat_model`), tool registry (`get_tool`), state store (`history.py`), memory layer (`_memory/`), compactor (`_chat_compaction/`), skill registry (`_skills/`), MCP connector (`mcp_handler.py`), sandbox (`_code_execution/`).

**Gaps:** No typed event model (state stored as chat messages, not `tool_call`/`tool_result`/`approval_request` events). No explicit authority hierarchy labeling content by trust level. No approval manager plugin. Durable state is ad-hoc — `Agent.data` dict is in-memory only; only the plugin's `workflow_state.py` adds file persistence.

**Recommendations:**
1. Add typed event metadata to `history.py` entries
2. Implement authority hierarchy labels in `prepare_prompt()`
3. Create `_approval_manager` plugin

---

## Dimension 2: Agentic Loop — 🟡

**Findings:** Core loop in `agent.py:Agent.monologue()` follows canonical pattern: build context → call model → parse tool requests → execute tools → append results → loop. Model never executes directly (correct boundary). Intervention mechanism (`handle_intervention`) enables HITL. Error retry via `_error_retry` plugin.

**Gaps:** `while True` with **no step limit, token budget, cost budget, or wall-time limit**. No structured stop result on termination. No parallel tool call support. The reference requires `max_model_turns`, `max_tool_calls`, `max_wall_time_seconds`, `max_total_cost`.

**Recommendations:**
1. Add `max_iterations` counter to `monologue()` — file: `agent.py`
2. Track cumulative tokens per monologue — file: `tokens.py`
3. Return typed `StopResult` on budget exceeded

---

## Dimension 3: Tools & Permissions — 🔴

**Findings:** Clean `Tool` base class with `execute()`/`before_execution()`/`after_execution()`. Dynamic tool discovery from agent folder hierarchy. MCP tool integration alongside local tools. Docker sandbox for code execution.

**Gaps:** **No permission engine** — any tool found is executed without checks. No risk taxonomy (tools have no `risk_class`). No strict schema validation (uses `dirty_json` parsing). No draft/commit separation for risky actions. No tool result size limits. No tool visibility management. This is the largest gap area.

**Recommendations:**
1. Extend `Tool.__init__()` with `risk_class`, `side_effects`, `timeout`, `max_result_chars` — file: `tool.py`
2. Create `_permission_engine` plugin with allow/deny/approval_required decisions
3. Add result size limiting in `after_execution()`
4. Add strict schema validation — file: `extract_tools.py`

---

## Dimension 4: Context & Compaction — 🟡

**Findings:** Context builder assembles system prompt + history + extras. Compaction plugin has pre-compaction backup, chunked compaction, model selection, progress streaming. FAISS-based memory with save/load/forget. Promptinclude auto-loads `*.promptinclude.md` files.

**Gaps:** Compaction replaces history with a single summary — it does NOT preserve active plan, goal, approval state, loaded skills, connector state, or tool call references. The reference requires a structured handoff preserving all of these. No auto-compaction trigger (user-initiated only). No rehydration after compaction. No trust labels on context.

**Recommendations:**
1. Use structured handoff format in compactor — file: `compactor.py`
2. Add auto-compaction trigger in `prepare_prompt()` when tokens approach limit
3. Add trust labels to context sections
4. Rehydrate workflow state after compaction — file: `_67_reattach_workflow_state.py`

---

## Dimension 5: Planning & Goals — 🟡

**Findings:** Plugin provides 6-phase lifecycle (DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP) with transition validation, phase-skill mapping, correction deduplication, progress logging. Durable workflow state with `active_plan.json`, `active_goal.json`, `current_phase.json`, `checkpoints.json`, `progress_log.jsonl`, `handoff.md`. Skills produce structured plan documents.

**Gaps:** No planning mode in core (runtime flag blocking mutations during planning). No goal-like loop with done conditions and budgets. No approval tied to plan versions. Phase governance is advisory — agent can ignore phases.

**Recommendations:**
1. Add planning mode flag to `process_tools()` — file: `agent.py`
2. Create `_goal_loop` plugin with budget enforcement
3. Require plan approval before BUILD-phase execution

---

## Dimension 6: Skills & Connectors — ✅

**Findings:** Excellent progressive disclosure (search → load → read_file). Novel skill enforcement gate with utility-model classifier (observe/enforce modes). Skill contracts with YAML frontmatter validation, conflict detection, next-skill recommendations. Full MCP implementation (1350 lines). 23 production skills covering full SDLC. 3 specialist agent profiles with composition rules.

**Gaps:** No skill governance/security review (no publisher verification, version pinning, or static scanning). External MCP tool descriptions not labeled as untrusted. No skill activation evals.

**Recommendations:**
1. Add skill security scan before activation
2. Label MCP tool descriptions as untrusted — file: `mcp_handler.py`
3. Create skill activation eval set

---

## Dimension 7: System Prompts & Instructions — 🟡

**Findings:** Extension-based prompt assembly with deterministic ordering. Promptinclude auto-discovers `*.promptinclude.md` files. Behavior adjustment tool for durable rules. Multiple instruction layers (framework, plugins, user files, runtime extras).

**Gaps:** No authority hierarchy labels on prompt sections. No injection boundary markers around tool results or retrieved content. No prompt template versioning.

**Recommendations:**
1. Add trust labels to all prompt extension points
2. Wrap tool results with untrusted-data markers — file: `hist_add_tool_result()`
3. Hash and version assembled system prompt

---

## Dimension 8: Security — 🟡

**Findings:** Infection checker with background analysis, tool execution gating, ok/terminate/clarify verdicts. Docker sandbox for code execution. Comprehensive secrets management (544 lines) with placeholder injection. Filename sanitization.

**Gaps:** No layered guardrails (only infection checker provides partial tool guardrail; reference requires 6 layers). No output guardrails. No approval records with structured format. No documented threat model. No secret scanning in tool results before adding to history.

**Recommendations:**
1. Add output guardrail plugin for sensitive data
2. Scan tool results for secrets before history — file: `tool.py:after_execution()`
3. Document threat model
4. Create `_approval_manager` plugin

---

## Dimension 9: Observability & Evals — 🔴

**Findings:** Typed log system (tool/error/warning/info/response). State monitor for change tracking. Token counting. Performance timing utilities.

**Gaps:** **No structured traces** (events logged as UI updates, not typed trace records). **No eval framework** (no test cases measuring task success, tool precision, injection resistance). No replay capability. No cost tracking per run. No latency metrics (TTFB, total).

**Recommendations:**
1. Create `_tracing` plugin emitting typed JSONL events
2. Build eval framework starting with 10-20 cases — new: `/a0/evals/`
3. Add per-run cost accumulation — file: `tokens.py`
4. Add latency metrics to `call_chat_model()`

---

## Dimension 10: Prompt Caching & Cost — 🔴

**Findings:** `call_chat_model()` passes `explicit_caching=True` to model adapter. LangChain adapters support provider-specific caching.

**Gaps:** No stable-prefix design (dynamic content not separated from stable). No deterministic tool ordering. No cache telemetry (provider cache fields not logged). No prompt/tool bundle versioning. No cache hit rate monitoring.

**Recommendations:**
1. Separate stable/volatile context in `prepare_prompt()`
2. Sort tool definitions deterministically
3. Log provider cache usage fields — file: `call_llm.py`
4. Hash system prompt + tool defs for debugging

---

## Dimension 11: Agent Legibility — 🟡

**Findings:** Plugin provides comprehensive workflow state (plans, goals, phases, checkpoints, progress log, handoff). 6-level AGENTS.md intent layer (917 lines). Append-only progress log with typed events. FAISS-indexed memory.

**Gaps:** No entropy management (no cleanup of stale docs/obsolete tools). No feedback loop capture (recurring failures not converted to knowledge). No quality scorecards.

**Recommendations:**
1. Add cleanup command for stale state
2. Capture repeated tool failures as memory fragments
3. Create quality scorecard document

---

## Dimension 12: Mechanical Invariants — 🔴

**Findings:** Plugin adds skill enforcement gate (observe/enforce), phase governance with transition validation, workflow state validators (path traversal prevention, symlink checks, version validation).

**Gaps:** **No core validators** — no schema validators, policy gates, or quality gates in the framework itself. No policy engine. No regression evals. No model-readable error remediation messages.

**Recommendations:**
1. Add per-tool schema validation — file: `tool.py:validate_args()`
2. Create `_budget_gate` plugin
3. Build regression eval suite — new: `/a0/evals/regression/`
4. Standardize error messages with remediation instructions — file: `errors.py`

---

## Prioritized Top 10 Action Plan

| Priority | Action | Dimension | Impact | Effort | Target File |
|----------|--------|-----------|--------|--------|-------------|
| **1** | Add step/time/cost budgets to monologue() | Loop | Critical | S | `agent.py` |
| **2** | Implement permission engine with risk taxonomy | Tools | Critical | M | New plugin + `tool.py` |
| **3** | Fix compaction to preserve active state | Context | Critical | M | `compactor.py` + `workflow_state.py` |
| **4** | Add structured JSONL trace logging | Observability | High | M | New plugin |
| **5** | Add trust labels + injection boundary markers | Prompts/Security | High | S | `agent.py` + extensions |
| **6** | Add auto-compaction trigger on token count | Context | High | S | `agent.py:prepare_prompt()` |
| **7** | Implement planning mode (block mutations) | Planning | High | M | `agent.py:process_tools()` |
| **8** | Add output guardrail for sensitive data | Security | Medium | S | New plugin |
| **9** | Create baseline eval suite (20 cases) | Evals/Invariants | Medium | M | New `/a0/evals/` |
| **10** | Add cache telemetry + stable-prefix design | Caching | Medium | S | `agent.py` + `call_llm.py` |

---

## Key Source Files Analyzed

**Framework:** `agent.py` (1039L), `tool.py` (74L), `history.py` (687L), `skills.py` (1396L), `mcp_handler.py` (1350L), `plugins.py` (894L), `security.py` (49L), `secrets.py` (544L), `tokens.py` (63L), `subagents.py` (435L)

**Plugins:** `_memory/` (885L), `_chat_compaction/` (365L), `_infection_check/` (395L), `_code_execution/` (558L)

**a0_agent_skills:** `plugin.yaml`, `phase_governance.py` (253L), `workflow_state.py` (520+L), `skill_contracts.py`, `skill_match.py`, `_10_skill_enforcer.py` (300+L), `_15_agent_skills_routing.py`

**Reference:** 12 files in `/a0/usr/skills/agents-best-practices/references/` covering architecture, agentic loop, tools, context, planning, skills, prompts, security, caching, legibility, checklists, and MVP blueprint.
