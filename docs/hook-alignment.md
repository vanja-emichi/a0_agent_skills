# Hook Alignment Policy

> Documents the classification and A0-native policy for each upstream
> `addyosmani/agent-skills/hooks/` asset.
>
> Generated as part of Phase 4, Task 12 of the Managed Fork Alignment.

## Classification Legend

| Classification | Meaning |
|---|---|
| **PORT** | Behavior carried over using an A0-native mechanism (may already be done) |
| **DEFER** | Not blocking for ship; may be implemented in a future iteration |
| **OMIT** | Not applicable to Agent Zero; intentionally excluded |

---

## Hook-by-Hook Classification

### 1. `hooks.json` — OMIT

**Upstream purpose:** Registers `session-start.sh` as a Claude Code `SessionStart` hook via JSON config.

**A0 reasoning:** Agent Zero does not use JSON shell-hook registration. Plugin lifecycle
and runtime hooks are configured through `plugin.yaml` and Python extension points
(`system_prompt`, `tool_execute_before`/`tool_execute_after`, `message_loop_*`). There is no
A0 surface that consumes this file.

**Action:** None. No A0 equivalent needed.

---

### 2. `session-start.sh` — PORT (DONE)

**Upstream purpose:** Injects the `using-agent-skills` meta-skill content into every new session
by reading `skills/using-agent-skills/SKILL.md` and emitting it as a JSON payload with
`priority: "IMPORTANT"`.

**A0 replacement:** The system prompt extension at
`extensions/python/system_prompt/_15_agent_skills_routing.py` injects routing rules
(from `prompts/agent.skills.routing.md`) into the system prompt during assembly. This runs
universally — regardless of whether a project is active — and supersedes the upstream
approach of shell-script JSON payloads.

**Why this is better in A0:**
- No dependency on `jq` or external shell tools
- Works even when a project is active (workdir promptincludes do not)
- Runs at Python-native assembly time, not as a subprocess hook

**Action:** Complete. No further work needed.

---

### 3. `session-start-test.sh` — OMIT

**Upstream purpose:** Node.js test that validates the `session-start.sh` JSON payload has the
correct structure and content.

**A0 reasoning:** Agent Zero's test infrastructure is Python-based (pytest). The session-start
behavior is covered by contract tests in `tests/test_plugin_contract.py` and the system
prompt extension's own correctness guarantees. A Node.js test runner is not part of the
A0 test stack.

**Action:** None. A0-native tests cover the equivalent behavior.

---

### 4. `simplify-ignore.sh` — DEFER

**Upstream purpose:** Block-level protection for `/code-simplify`. Annotated code blocks
(`/* simplify-ignore-start */` … `/* simplify-ignore-end */`) are replaced with
content-hashed placeholders (`BLOCK_<hash>`) before the model reads the file, then
restored after the model writes. Operates via three hook events: `PreToolUse Read`,
`PostToolUse Edit|Write`, and `Stop`.

**A0 reasoning:** This is a valuable feature but requires careful A0-native design:

1. **Different tool surface:** Upstream intercepts Claude Code's `Read`/`Edit`/`Write` tools.
   A0 would need to intercept `text_editor:read`/`write`/`patch` via
   `tool_execute_before`/`tool_execute_after` extensions.
2. **No in-place file modification:** Upstream modifies files on disk (replaces with
   placeholders, restores from backup). An A0-native approach should intercept tool I/O
   in memory rather than touching the filesystem — safer and avoids crash-recovery issues.
3. **Complex implementation:** The upstream script is ~300 lines of Bash with SHA hashing,
   glob escaping, placeholder round-tripping, and backup management. A Python reimplementation
   via extensions would be cleaner but is non-trivial.

**Recommended A0-native approach (future):**
- `tool_execute_before` extension for `text_editor:read` → replace annotated blocks with placeholders in the tool response
- `tool_execute_after` extension for `text_editor:write`/`text_editor:patch` → expand placeholders back to real code in the tool input
- No on-disk backup; operate purely on tool I/O

**Action:** Deferred. Not blocking for ship. Implement as a `tool_execute_before`/`tool_execute_after`
extension in a future iteration.

---

### 5. `simplify-ignore-test.sh` — DEFER

**Upstream purpose:** Bash tests for `simplify-ignore.sh` that exercise `filter_file` by
extracting function definitions.

**A0 reasoning:** Port alongside the A0-native simplify-ignore implementation when it is built.
Tests would be written in Python/pytest, not Bash.

**Action:** Deferred. Port when simplify-ignore is implemented.

---

### 6. `SIMPLIFY-IGNORE.md` — DEFER

**Upstream purpose:** User-facing documentation for the simplify-ignore hook: setup,
annotation syntax, how it works, crash recovery, and known limitations.

**A0 reasoning:** Port when simplify-ignore is implemented. Will need A0-specific setup
instructions (extension configuration, not `.claude/settings.json`).

**Action:** Deferred. Port when simplify-ignore is implemented.

---

### 7. `sdd-cache-pre.sh` — DEFER

**Upstream purpose:** `PreToolUse` hook for Claude Code's `WebFetch` tool. Implements an
HTTP resource cache keyed by URL with origin-server revalidation via `ETag`/`Last-Modified`.
On cache hit (server returns `304 Not Modified`), blocks the fetch and serves cached content.

**A0 reasoning:**

1. **Different fetch mechanism:** Agent Zero uses `document_query` and `search_engine`
   for document retrieval, not Claude Code's `WebFetch`. There is no `WebFetch` tool to intercept.
2. **Performance optimization only:** Caching does not affect skill correctness — the
   `source-driven-development` skill still follows `DETECT → FETCH → IMPLEMENT → CITE`
   regardless of whether results are cached.
3. **Significant dependencies:** Requires `jq`, `curl`, `shasum`/`sha256sum`, and a
   `.claude/sdd-cache/` directory structure.

**Recommended A0-native approach (future):** If caching becomes valuable for `document_query`
URL fetches, implement as a `tool_execute_before`/`tool_execute_after` extension pair in
Python, storing cache entries in the plugin's data directory rather than `.claude/sdd-cache/`.

**Action:** Deferred. Not blocking for ship. Implement only if document_query caching
becomes a demonstrated need.

---

### 8. `sdd-cache-post.sh` — DEFER

**Upstream purpose:** `PostToolUse` hook for `WebFetch`. After a fetch, captures the response
body and issues a `HEAD` request to record `ETag`/`Last-Modified`, then stores the entry
as JSON in `.claude/sdd-cache/`.

**A0 reasoning:** Same as `sdd-cache-pre.sh` — A0 does not use `WebFetch`, and caching is a
performance optimization only.

**Action:** Deferred alongside `sdd-cache-pre.sh`.

---

### 9. `SDD-CACHE.md` — DEFER

**Upstream purpose:** User-facing documentation for the SDD cache hooks: mental model,
setup, how it works, local testing instructions, and known limitations.

**A0 reasoning:** Port when SDD caching is implemented for `document_query`.

**Action:** Deferred. Port when caching is implemented.

---

## Summary

| # | Upstream Asset | Classification | A0 Status |
|---|---|---|---|
| 1 | `hooks.json` | OMIT | Not applicable |
| 2 | `session-start.sh` | PORT | Done (system_prompt extension) |
| 3 | `session-start-test.sh` | OMIT | Not applicable (pytest instead) |
| 4 | `simplify-ignore.sh` | DEFER | Future tool_execute extension |
| 5 | `simplify-ignore-test.sh` | DEFER | Port with simplify-ignore |
| 6 | `SIMPLIFY-IGNORE.md` | DEFER | Port with simplify-ignore |
| 7 | `sdd-cache-pre.sh` | DEFER | Future tool_execute extension |
| 8 | `sdd-cache-post.sh` | DEFER | Future tool_execute extension |
| 9 | `SDD-CACHE.md` | DEFER | Port with sdd-cache |

**Totals:** 1 PORT (done), 2 OMIT, 6 DEFER. No shipping blockers.

---

## Hook Families

### session-start family

| Asset | Classification |
|---|---|
| `session-start.sh` | PORT (done) |
| `session-start-test.sh` | OMIT |
| `hooks.json` | OMIT |

**Policy:** Session initialization in A0 is handled by the `system_prompt` extension
(`_15_agent_skills_routing.py`), which injects skill routing rules during prompt assembly.
This is more reliable than the upstream shell-script approach and requires no external
dependencies.

### simplify-ignore family

| Asset | Classification |
|---|---|
| `simplify-ignore.sh` | DEFER |
| `simplify-ignore-test.sh` | DEFER |
| `SIMPLIFY-IGNORE.md` | DEFER |

**Policy:** Block-level code protection during simplification is valuable but complex.
A0 should implement this as an in-memory `tool_execute_before`/`tool_execute_after`
extension pair rather than the upstream's on-disk file modification approach. Not blocking
for the initial managed-fork release.

### sdd-cache family

| Asset | Classification |
|---|---|
| `sdd-cache-pre.sh` | DEFER |
| `sdd-cache-post.sh` | DEFER |
| `SDD-CACHE.md` | DEFER |

**Policy:** HTTP response caching for `source-driven-development` is a performance
optimization. A0 does not use `WebFetch`; `document_query` handles URL fetching. Caching
may be implemented as a Python extension if repeated fetches of the same URL become a
bottleneck. Not blocking for the initial managed-fork release.

---

## Relationship to hooks.py

The plugin's `hooks.py` file contains stub functions (`install`, `uninstall`, `pre_update`)
required by the Agent Zero plugin interface. Its module docstring already documents this
hook policy. The stubs are retained for potential future plugin lifecycle needs.

The runtime hook behaviors (session-start injection, telemetry logging) are handled by
A0 extension points, not by `hooks.py`:

- **Session-start routing:** `extensions/python/system_prompt/_15_agent_skills_routing.py`
- **Skill telemetry:** `extensions/python/tool_execute_after/_05_skill_telemetry.py`
