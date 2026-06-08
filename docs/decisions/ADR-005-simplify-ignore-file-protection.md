# ADR-005: Simplify-Ignore File Protection

## Status

Accepted

## Date

2026-06-05

## Context

The `code-simplification` skill helps agents refactor code for clarity — removing unnecessary complexity, consolidating duplicate logic, and improving readability. However, some code blocks must never be simplified:

- **Performance-critical sections** — manually unrolled loops, SIMD-friendly layouts, bit manipulation tricks that look complex but exist for speed
- **Compatibility shims** — code that handles browser quirks, version-specific fallbacks, or platform edge cases
- **Security-sensitive logic** — constant-time comparisons, anti-timing-attack patterns, cryptographic padding
- **Intentionally verbose sections** — lookup tables, state machine definitions, protocol parsers with explicit state names

Without protection, an LLM agent following the simplification skill may aggressively refactor these blocks, breaking correctness, performance, or security guarantees. The agent cannot distinguish "accidentally complex" from "intentionally complex" without explicit annotations.

## Decision

Implement block-level file protection via annotated guard comments and tool-intercept hooks:

### Annotation Syntax

```js
/* simplify-ignore-start: perf-critical */
// manually unrolled XOR — 3x faster than a loop
result[0] = buf[0] ^ key[0];
result[1] = buf[1] ^ key[1];
/* simplify-ignore-end */
```

Any comment style works (`//`, `/*`, `#`, `<!--`). Multiple blocks per file and single-line blocks are supported.

### Hook Flow

| Event | Action |
|---|---|
| Pre-read | Back up file, replace annotated blocks with `BLOCK_<hash>` placeholders in-place |
| Post-edit/write | Expand placeholders back to real code, save model's changes, re-filter remaining blocks |
| Session end | Restore all files from backup to ensure no placeholders remain on disk |

Each block is content-hashed (8 hex chars via `sha1sum`) so the round-trip is unambiguous even if the model duplicates or reorders placeholders.

### Agent Zero Plugin Implementation

In the Agent Zero plugin, the shell hook is converted to a Python extension under `extensions/python/`. The protection logic remains the same but is implemented as a Python class with access to `self.agent` for context and framework tool interception.

## Alternatives Considered

### Directory-Level Ignore

- **Pros:** Simple configuration — mark entire directories as no-simplify zones
- **Cons:** Too coarse. A directory may contain files with both simplifiable and protected code. Forces all-or-nothing protection at directory granularity
- **Rejected:** Block-level granularity is needed; most files have a mix of simplifiable and protected code

### Prompt-Only Protection

- **Pros:** No hooks, no file manipulation, no backup/restore complexity
- **Cons:** LLM agents routinely ignore soft instructions when simplifying. A prompt saying "don't touch performance-critical code" provides no hard guarantee. The agent still sees the code and may refactor it
- **Rejected:** Soft guidance is insufficient; the agent must not see the protected code at all

### No Protection

- **Pros:** Simplest implementation, no hook infrastructure needed
- **Cons:** `code-simplification` will break performance-critical and security-sensitive code. Users will stop using the skill rather than risk damage
- **Rejected:** Defeats the purpose of the simplification skill

### Separate File Strategy

- **Pros:** Protected code lives in separate files that simplification never touches
- **Cons:** Forces artificial code organization. Performance-critical blocks are often embedded in otherwise normal functions. Extracting them to separate files breaks code locality and readability
- **Rejected:** Imposes unwanted architectural constraints

## Consequences

### Positive

- **Hard protection** — protected blocks are invisible to the agent during simplification. The model cannot refactor what it cannot see
- **Granular control** — individual blocks within a file can be protected, leaving surrounding code free for simplification
- **Self-documenting** — the `: reason` annotation explains *why* the block is protected, visible to all developers
- **Crash recovery** — backups survive session crashes; a manual restore command recovers all files
- **Comment-style agnostic** — works with any language's comment syntax

### Negative

- **File manipulation overhead** — every read/write involves backup, filter, and restore operations. Adds latency to each tool call
- **Placeholder leakage risk** — if the session crashes without triggering the Stop hook, files on disk may contain `BLOCK_<hash>` placeholders. Requires manual recovery
- **File renaming edge case** — if the model renames or moves a file via shell command, the new file retains placeholders. Original code is saved as `<old-filename>.recovered`
- **Single-line block limitation** — if start and end annotations appear on the same line as other code, the whole line is hidden

### Risks Mitigated

- **Placeholder persistence** — Stop hook restores all files; crash recovery command (`echo '{}' | bash hooks/simplify-ignore.sh`) provides manual restore
- **Hash collision** — 8 hex chars (32 bits) provides sufficient uniqueness for per-project block counts. Progressive matching (full placeholder → prefix+hash+suffix → hash-only) handles formatting changes
- **Cross-session interference** — cache is project-scoped to prevent cross-session pollution
