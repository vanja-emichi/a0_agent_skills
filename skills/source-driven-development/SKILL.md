---
name: source-driven-development
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Reads official sources before implementing. Use when using a library, API,
  or framework that might have changed since training. Use when you're unsure
  about current API signatures, best practices, or when working with rapidly
  evolving tools.
tags:
  - research
  - documentation
  - libraries
  - api-usage
  - source-verification
trigger_patterns:
  - source-driven-development
  - check the docs
  - verify the api
  - library documentation
  - latest version
  - how does X work
  - read the source
  - check if this api still exists
  - look up the documentation
  - fetch the docs
contract:
  phase: BUILD
  inputs:
    - Library or framework documentation
    - Task description
  artifacts:
    - path: "src/**"
      description: "Framework-aligned code"
  verification:
    - Code follows official patterns
    - API usage is correct
  next_skills:
    - incremental-implementation
    - test-driven-development
  conflicts: []
---

# Source-Driven Development

## Overview

Every framework-specific code decision must be backed by official documentation. Don't implement from memory — verify, cite, and let the user see your sources. Training data goes stale, APIs get deprecated, best practices evolve. This skill ensures the user gets code they can trust because every pattern traces back to an authoritative source they can check.

## When to Use

- The user wants code that follows current best practices for a given framework
- Building boilerplate, starter code, or patterns that will be copied across a project
- The user explicitly asks for documented, verified, or "correct" implementation
- Implementing features where the framework's recommended approach matters (forms, routing, data fetching, state management, auth)
- Reviewing or improving code that uses framework-specific patterns
- Any time you are about to write framework-specific code from memory

**When NOT to use:**

- Correctness does not depend on a specific version (renaming variables, fixing typos, moving files)
- Pure logic that works the same across all versions (loops, conditionals, data structures)
- The user explicitly wants speed over verification ("just do it quickly")

## The Process

```
DETECT ──→ FETCH ──→ IMPLEMENT ──→ CITE
  │          │           │            │
  ▼          ▼           ▼            ▼
 What       Get the    Follow the   Show your
 stack?     relevant   documented   sources
            docs       patterns
```

### Step 1: Detect Stack and Versions

Read the project's dependency file to identify exact versions:

```
package.json    → Node/React/Vue/Angular/Svelte
composer.json   → PHP/Symfony/Laravel
requirements.txt / pyproject.toml → Python/Django/Flask
go.mod          → Go
Cargo.toml      → Rust
Gemfile         → Ruby/Rails
```

State what you found explicitly:

```
STACK DETECTED:
- React 19.1.0 (from package.json)
- Vite 6.2.0
- Tailwind CSS 4.0.3
→ Fetching official docs for the relevant patterns.
```

If versions are missing or ambiguous, **ask the user**. Don't guess — the version determines which patterns are correct.

### Step 2: Fetch Official Documentation

Fetch the specific documentation page for the feature you're implementing. Not the homepage, not the full docs — the relevant page.

**Source hierarchy (in order of authority):**

| Priority | Source | Example |
|----------|--------|---------|
| 1 | Official documentation | react.dev, docs.djangoproject.com, symfony.com/doc |
| 2 | Official blog / changelog | react.dev/blog, nextjs.org/blog |
| 3 | Web standards references | MDN, web.dev, html.spec.whatwg.org |
| 4 | Browser/runtime compatibility | caniuse.com, node.green |

**Not authoritative — never cite as primary sources:**

- Stack Overflow answers
- Blog posts or tutorials (even popular ones)
- AI-generated documentation or summaries
- Your own training data (that is the whole point — verify it)

**Be precise with what you fetch:**

```
BAD:  Fetch the React homepage
GOOD: Fetch react.dev/reference/react/useActionState

BAD:  Search "django authentication best practices"
GOOD: Fetch docs.djangoproject.com/en/6.0/topics/auth/
```

After fetching, extract the key patterns and note any deprecation warnings or migration guidance.

When official sources conflict with each other (e.g. a migration guide contradicts the API reference), surface the discrepancy to the user and verify which pattern actually works against the detected version.

### Step 3: Implement Following Documented Patterns

Write code that matches what the documentation shows:

- Use the API signatures from the docs, not from memory
- If the docs show a new way to do something, use the new way
- If the docs deprecate a pattern, don't use the deprecated version
- If the docs don't cover something, flag it as unverified

**When docs conflict with existing project code:**

```
CONFLICT DETECTED:
The existing codebase uses useState for form loading state,
but React 19 docs recommend useActionState for this pattern.
(Source: react.dev/reference/react/useActionState)

Options:
A) Use the modern pattern (useActionState) — consistent with current docs
B) Match existing code (useState) — consistent with codebase
→ Which approach do you prefer?
```

Surface the conflict. Don't silently pick one.

### Step 4: Cite Your Sources

Every framework-specific pattern gets a citation. The user must be able to verify every decision.

**In code comments:**

```typescript
// React 19 form handling with useActionState
// Source: https://react.dev/reference/react/useActionState#usage
const [state, formAction, isPending] = useActionState(submitOrder, initialState);
```

**In conversation:**

```
I'm using useActionState instead of manual useState for the
form submission state. React 19 replaced the manual
isPending/setIsPending pattern with this hook.

Source: https://react.dev/blog/2024/12/05/react-19#actions
"useTransition now supports async functions [...] to handle
pending states automatically"
```

**Citation rules:**

- Full URLs, not shortened
- Prefer deep links with anchors where possible (e.g. `/useActionState#usage` over `/useActionState`) — anchors survive doc restructuring better than top-level pages
- Quote the relevant passage when it supports a non-obvious decision
- Include browser/runtime support data when recommending platform features
- If you cannot find documentation for a pattern, say so explicitly:

```
UNVERIFIED: I could not find official documentation for this
pattern. This is based on training data and may be outdated.
Verify before using in production.
```

Honesty about what you couldn't verify is more valuable than false confidence.

## High-Risk Libraries (Always Verify)

These libraries have frequent breaking changes or major version differences in common training data:

| Library | Why Verify | What to Check |
|---------|-----------|---------------|
| **Next.js** | App Router changes, async params, server components | `use client` requirements, data fetching patterns |
| **React** | Hooks, concurrent features, server components | Hook rules, suspense boundaries |
| **Prisma** | Schema syntax, query API evolution | Filter syntax, `include` vs `select` |
| **tRPC** | Procedure definition API changes | Router setup, client usage |
| **Tailwind CSS** | v3→v4 config changes | Config format, utility class changes |
| **Vitest / Jest** | Config syntax differences | `describe`/`it` API, mock patterns |
| **AI SDKs** | Rapid iteration (Vercel AI SDK, OpenAI SDK) | Model names, streaming API, tool calling |
| **Cloud SDKs** | AWS, GCP, Azure change frequently | Auth patterns, service constructors |
| **Drizzle ORM** | Relatively new, evolving API | Schema definition, query builder |

## Fetching Docs with Agent Zero Tools

### Read Targeted Sections

Don't fetch entire docs sites. Target the specific section you need:

```
# Good: specific path to the feature
document_query: https://react.dev/reference/react/useEffect

# Good: deep_wiki for a GitHub repo
deep_wiki.ask_question:
  repoName: "vercel/next.js"
  question: "How do I use dynamic route params in Next.js 15 App Router?"

# Avoid: fetching the entire docs site root
document_query: https://react.dev  # Too broad
```

### Package README for Quick API Verification

For npm packages, the README often has the most current usage examples:

```
document_query: https://raw.githubusercontent.com/<owner>/<repo>/main/README.md
```

### Check CHANGELOG for Breaking Changes

When upgrading or working with a new major version:

```
document_query:
  document: https://github.com/<owner>/<repo>/blob/main/CHANGELOG.md
  query: "What changed in version X? What are the breaking changes?"
```

### Source Quality Hierarchy

```
Highest trust:
├── Official docs site (docs.example.com)
├── GitHub README (raw.githubusercontent.com)
├── GitHub source code (actual implementation)
├── Official changelog/migration guide
├── deep_wiki.ask_question (indexed, sourced from actual repo)
└── npm package page (npmjs.com/<package>)

Lower trust (verify against above):
├── Blog posts, tutorials
├── Stack Overflow answers (check the date)
└── Training data / model memory (most likely to be stale)
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'm confident about this API" | Confidence is not evidence. Training data contains outdated patterns that look correct but break against current versions. Verify. |
| "Fetching docs wastes tokens" | Hallucinating an API wastes more. The user debugs for an hour, then discovers the function signature changed. One fetch prevents hours of rework. |
| "The docs won't have what I need" | If the docs don't cover it, that's valuable information — the pattern may not be officially recommended. |
| "I'll just mention it might be outdated" | A disclaimer doesn't help. Either verify and cite, or clearly flag it as unverified. Hedging is the worst option. |
| "This is a simple task, no need to check" | Simple tasks with wrong patterns become templates. The user copies your deprecated form handler into ten components before discovering the modern approach exists. |

## Red Flags

- Implementing against an API without reading its current docs
- TypeScript types that "should work" but cause runtime errors
- Using patterns from tutorials without checking if they apply to the installed version
- No version comment when using patterns that are version-specific
- Working with AI SDKs or cloud APIs without checking the changelog

## Verification

Before implementing against any external library or API:

- [ ] Current docs or source fetched via `document_query`, `browser`, or `deep_wiki.ask_question`
- [ ] API signature matches documentation
- [ ] Using recommended pattern (not deprecated alternative)
- [ ] Return types and error handling match documentation
- [ ] Version-specific patterns noted with a comment if applicable
- [ ] No assumptions about behavior that aren't confirmed in the source
