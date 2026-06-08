# ADR-004: SDD Documentation Cache

## Status

Accepted

## Date

2026-06-05

## Context

The `source-driven-development` skill fetches official documentation for every framework-specific decision. This guarantees correctness — the agent always verifies against current docs rather than relying on training data that may be outdated.

However, working on the same project across multiple sessions means fetching the same pages repeatedly. Each `WebFetch` call costs time and tokens. For a project using React, the agent may fetch `react.dev/reference/react/useActionState` dozens of times across sessions.

A naive cache — storing fetched content as local memory — would contradict the skill's core guarantee. Documentation changes between releases, and a stale cache would silently serve outdated information, causing the agent to implement against deprecated APIs.

The challenge: reduce redundant fetches without weakening the "verify against current docs" guarantee.

## Decision

Implement a documentation cache that stores fetched content on disk but **revalidates with the origin server on every reuse** via HTTP conditional requests (`If-None-Match` / `If-Modified-Since`). Content is served from cache only when the server responds `304 Not Modified`, which constitutes a fresh verification — not a memory read.

### Design

- **Storage:** One cache entry per URL as JSON in `.claude/sdd-cache/<sha256(url)>.json`
- **Cache key:** `sha256(url)` — prompt-agnostic so reads reuse across sessions
- **Freshness:** Delegated to the origin via `ETag` / `Last-Modified` validators. No TTL
- **Entry structure:** `{url, prompt, etag, last_modified, content, fetched_at}`
- **Original prompt:** Kept as metadata and surfaced on cache hits so the next agent can judge applicability

### Hook Flow

| Event | Action |
|---|---|
| Pre-fetch | If entry exists, send `HEAD` with `If-None-Match` / `If-Modified-Since`. On `304`, block fetch, return cached content via stderr. Otherwise allow fetch |
| Post-fetch | Capture response, issue `HEAD` to record `ETag` / `Last-Modified`, store entry |

### Freshness Rules

- Entries are served only on server-confirmed `304 Not Modified`
- Entries without `ETag` or `Last-Modified` are never cached — without validators, freshness cannot be verified
- Cache key is URL-only; same URL with different prompt hits the same entry. The original prompt is shown alongside the hit for the agent to decide

### Agent Zero Plugin Implementation

In the Agent Zero plugin, the shell hooks are converted to Python extensions under `extensions/python/`. The caching logic remains the same but is implemented as a Python class with access to `self.agent` for context.

## Alternatives Considered

### No Cache

- **Pros:** Simplest, always fresh, no stale data risk
- **Cons:** Redundant fetches across sessions waste time and tokens. For active projects, the same docs may be fetched 10-20 times per day
- **Rejected:** Performance cost is unnecessary when conditional requests provide both freshness and efficiency

### Redis Cache

- **Pros:** Shared across team members, fast lookups, TTL support
- **Cons:** Requires a running Redis instance. Adds infrastructure dependency for what is fundamentally a single-developer cache. No HTTP revalidation built in
- **Rejected:** Over-engineered for the use case; adds operational complexity

### File-Based Cache with TTL

- **Pros:** Simple implementation, no server dependency, automatic expiry
- **Cons:** TTL is a guess — too short wastes the cache, too long risks staleness. A 24-hour TTL may miss same-day doc updates. No freshness guarantee
- **Rejected:** TTL-based expiry is fundamentally weaker than origin-verified freshness

### Prompt-In-Key Cache

- **Pros:** Different prompts for the same URL get different cache entries, ensuring the cached content matches the agent's intent
- **Cons:** Same URL with different prompts creates duplicate entries. The first prompt's reading may be perfectly adequate for the second. Fragmentation reduces cache hit rate
- **Rejected:** URL-only key with prompt metadata gives better hit rates while surfacing applicability information

## Consequences

### Positive

- **Preserves freshness guarantee** — `304 Not Modified` is a server-confirmed verification, not a guess
- **Reduces redundant fetches** — cached docs are reused across sessions without re-downloading
- **Transparent to the skill** — `source-driven-development` continues its `DETECT → FETCH → IMPLEMENT → CITE` flow unchanged
- **Self-healing** — if the cache serves stale content (server bug), deleting the entry forces a fresh fetch
- **No TTL tuning** — freshness is binary (server says yes or no)

### Negative

- **Extra HEAD request per miss** — the post-fetch hook re-queries the origin to capture validators since the initial response headers are not exposed
- **Servers without validators are never cached** — some sites don't emit `ETag` or `Last-Modified`, so those docs are always re-fetched
- **Prompt-content mismatch** — a cache hit returns an earlier agent's reading of the page with a different prompt. The original prompt is surfaced, but the agent must decide applicability
- **Local-only** — no team-wide shared cache; each developer maintains their own

### Risks Mitigated

- **Stale content** — origin revalidation ensures content is current; servers that cannot verify are never cached
- **Corrupt entries** — entries can be deleted individually to force re-fetch
- **Debug visibility** — debug mode logs URL, HEAD status, hit/miss reasoning to `.claude/sdd-cache/.debug.log`
