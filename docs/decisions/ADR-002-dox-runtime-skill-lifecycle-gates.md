# ADR-002: DOX as Runtime Skill with Lifecycle Gates

## Status

Accepted

## Date

2026-06-05

## Context

The `AGENTS.md` DOX framework provides hierarchical project contracts — root-level ownership, local contracts per directory, child indexes for traversal. Without active enforcement, agents may ignore or misinterpret these contracts, leading to inconsistent file edits, missed verification steps, and stale instructions.

Agent Zero injects the active project's root `AGENTS.md` when `include_agents_md: true` is set, but does not recursively inject child `AGENTS.md` files. The DOX child traversal (walking from root to target, reading every `AGENTS.md` along the route, using the nearest as the local contract) is an agent workflow requirement, not a framework feature.

The plugin has lifecycle commands (`/spec`, `/plan`, `/build`, `/test`, `/review`, `/ship`) that gate development phases. Without DOX integration, these commands operate without project contract awareness.

Additionally, subordinate agents (code-reviewer, security-auditor, test-engineer) do not automatically receive the `using-agent-skills` meta-skill. DOX context must be explicitly included in subordinate prompts.

## Decision

Implement DOX as a first-class Agent Zero skill with lifecycle command gates and explicit subordinate handoff:

### Skill Architecture

- **`using-agent-skills`** — always-loaded meta-skill that routes project/file work to `dox-project-context`
- **`dox-project-context`** — operational skill for DOX preflight, local contract selection, closeout, and subordinate handoff
  - `SKILL.md` — workflow instructions for agents
  - `AGENTS.template.md` — reusable project starter template
  - `dox-checklist.md` — compact preflight and closeout checklist

### Lifecycle Command Integration

| Phase | DOX Gate |
|---|---|
| `spec` | Load `dox-project-context`, read root `AGENTS.md`, capture durable boundaries in `tasks/spec.md` |
| `plan` | Read DOX chain for target areas, create `tasks/plan.md` and `tasks/todo.md` noting DOX scopes per task |
| `build` | Before editing each target, read applicable DOX chain; after edits, DOX closeout before marking task done |
| `test` | Use nearest `AGENTS.md` Verification section to choose checks |
| `review` | Add DOX compliance: contracts read, local rules followed, indexes updated, stale instructions removed |
| `ship` | Include DOX readiness in go/no-go; pass DOX expectations to subordinate specialists |

### Subordinate Handoff

Commands and main-agent workflows that call subordinates must include DOX context explicitly or instruct the subordinate to read the applicable `AGENTS.md` chain. Specialists report DOX compliance issues when reviewing project files.

## Alternatives Considered

### Framework-Level DOX Feature

- **Pros:** Universal enforcement, no agent can bypass contracts
- **Cons:** Requires changes to Agent Zero core framework. Not plugin-controllable. Would need upstream PRs and release cycles
- **Rejected:** Out of scope for a plugin; framework changes have broader impact and slower iteration

### Promptinclude Files Only

- **Pros:** Already supported by Agent Zero, no skill needed
- **Cons:** Promptincludes are static text injected at session start. Cannot provide lifecycle-aware gates, DOX chain traversal, or closeout verification. Agents would see the root contract but have no workflow for applying it
- **Rejected:** Too passive; does not solve the traversal or lifecycle enforcement problem

### No DOX Integration

- **Pros:** Simplest approach, no additional skill or command changes
- **Cons:** Agents already misapply or ignore project contracts without structured guidance. Testing would have no contract-based verification hooks
- **Rejected:** Core problem remains unsolved

## Consequences

### Positive

- **Consistent contract enforcement** — every lifecycle phase checks DOX contracts before proceeding
- **Explicit subordinate handoff** — specialists receive DOX expectations, reducing blind spots
- **Testable** — DOX gates can be verified via e2e tests checking agent behavior against known contracts
- **Self-documenting** — `dox-project-context` skill itself documents the DOX workflow for agents
- **Incremental** — can be adopted per-command without requiring all commands to change at once

### Negative

- **Token cost** — DOX preflight reads additional files (root + child `AGENTS.md` chains) before each operation
- **Agent compliance is best-effort** — LLM agents may still deviate from DOX instructions; the skill provides guidance, not hard enforcement
- **Maintenance surface** — lifecycle command templates must stay synchronized with DOX skill updates
- **Subordinate prompt bloat** — adding DOX context to every subordinate call increases prompt length

### Risks Mitigated

- **Stale contracts** — closeout step requires updating `AGENTS.md` files after meaningful edits
- **Missing child contracts** — DOX chain traversal walks the full path, not just the root
- **Inconsistent verification** — `test` phase uses the nearest `AGENTS.md` Verification section for check selection
