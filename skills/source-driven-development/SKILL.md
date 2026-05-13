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
---

# Source-Driven Development

## Overview

Read authoritative sources before writing code that depends on them. AI training data has a cutoff — and even before that cutoff, documentation often reflects correct usage better than the patterns in training data. When building against a library, framework, or API, consulting the real source prevents hallucinated APIs, outdated patterns, and subtle bugs from subtle version differences.

## When to Use

- Using a library or framework that may have changed since training
- Unsure about current API signatures, hooks, or configuration
- Working with rapidly evolving tools (AI SDKs, cloud APIs, build tools)
- Implementing against a third-party API (authentication flows, endpoints, payloads)
- Encountering an error that suggests an API mismatch

**When NOT to use:**
- Writing pure algorithms or logic with no external dependencies
- Working with extremely stable, well-established APIs (e.g., basic array methods)
- You have high confidence the pattern is current and correct

## The Source-Driven Protocol

### Step 1: Identify What Needs Verification

Before writing code that uses an external library or API, list the assumptions you're making:

```
ASSUMPTIONS TO VERIFY:
- Does this hook/function/method still exist with this name?
- Are the arguments in the right order?
- Is this the recommended pattern (not deprecated)?
- Are there new required parameters or options?
- Does the return type match what I expect?
```

### Step 2: Fetch Authoritative Sources

Use Agent Zero tools to retrieve current documentation:

**For package documentation (npm):**
```
document_query: https://www.npmjs.com/package/<package-name>
```

**For GitHub repos:**
```
browser: open → navigate to github.com/<owner>/<repo>/blob/main/README.md
browser: content → read the README
```

**For official docs sites:**
```
browser: open → navigate to the official docs URL
browser: content → read the relevant section
```

**For specific API references:**
```
document_query: <direct URL to the API reference page>
```

**For deep repository analysis:**
```
deep_wiki.ask_question: { repoName: "owner/repo", question: "How do I use X?" }
```

**Search for docs when URL is unknown:**
```
search_engine: "<library name> <version> documentation <feature>"
```

### Step 3: Validate Against Source

After reading documentation:

```
CHECK EACH ASSUMPTION:
✓ Function signature matches docs
✓ Required options are provided
✓ Return type handling is correct
✓ Using the recommended pattern (not a deprecated alternative)
✓ No new required configuration steps
```

### Step 4: Implement With Confidence

Only after validating against the actual source, write the implementation. Reference the source version or URL in a code comment if it's likely to change:

```typescript
// Using Next.js 15 App Router — see https://nextjs.org/docs/app/api-reference
export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;  // params is now async in Next.js 15
  const task = await getTask(id);
  return <TaskView task={task} />;
}
```

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

## Fetching Docs Efficiently

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
document_query: https://github.com/<owner>/<repo>/blob/main/CHANGELOG.md
  query: "What changed in version X? What are the breaking changes?"
```

## When You Find a Discrepancy

If the documentation contradicts what you intended to write:

```
1. Trust the docs over your training data
2. Update your implementation to match the docs
3. Note the change with a comment if it's non-obvious:
   // In v3, this was someApi.doThing() — renamed to doThingNew() in v4
4. If unclear after reading docs, check GitHub issues or search for migration guides
```

## Red Flags That You Need to Verify

- You're using an API you haven't used in the current project yet
- You're getting TypeScript errors on an API you expected to work
- The pattern "feels right" but you can't cite a specific source
- The library had a major version bump (v2 → v3, v3 → v4)
- The library is an AI or ML tool (OpenAI SDK, Vercel AI SDK, Anthropic SDK)
- You're configuring a build tool (Webpack, Vite, Turbopack, esbuild)
- You're setting up auth (NextAuth, Clerk, Auth0 — all change frequently)

## Source Quality Hierarchy

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
| "I know this library well" | APIs change. A 15-second doc check prevents a 30-minute debugging session. |
| "It was right 6 months ago" | Major libraries have major releases. Fetch the current docs. |
| "The TypeScript types will catch it" | Types catch type errors. They don't catch deprecated patterns or behavior changes. |
| "I'll just try it and see" | This works in sandbox experiments. In production codebases, verify first. |
| "Fetching docs takes too long" | Targeted `document_query` or `deep_wiki.ask_question` takes seconds and returns current info. |

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
