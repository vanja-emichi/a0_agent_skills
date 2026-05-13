---
name: context-engineering
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Manages agent context for effective AI-assisted development. Use when
  working on large codebases, when the agent seems to lack necessary context,
  when structuring CLAUDE.md or project guidance files, or when coordinating
  long multi-step development sessions.
tags:
  - context
  - agent
  - prompt-engineering
  - project-setup
  - ai-workflow
trigger_patterns:
  - context-engineering
  - agent lacks context
  - write a claude.md
  - project context file
  - agent keeps forgetting
  - help the agent understand
  - agent context window
  - project guidance
  - set up agent context
  - agent workflow setup
---

# Context Engineering

## Overview

Agent performance is determined by the quality of context provided, not just the quality of the model. Context engineering is the practice of structuring project information, task instructions, and session state so agents can do their best work. This applies whether you're writing a project guidance file, structuring a long conversation, or coordinating a multi-step development task.

## When to Use

- Setting up a new project for agent-assisted development
- Agent is making mistakes that suggest missing context (wrong conventions, wrong tech stack)
- Writing or updating a project guidance file (CLAUDE.md, AGENTS.md, etc.)
- Planning a complex multi-step development session
- Agent keeps losing track of decisions made earlier in a session

## The Context Hierarchy

```
Context sources (highest to lowest priority):
├── 1. Immediate message — what you just said
├── 2. Conversation history — this session's decisions
├── 3. Project guidance file — persistent project conventions
├── 4. Loaded skills — active behavioral protocols
└── 5. Training data — model's built-in knowledge
```

The first source wins when there's a conflict. Use this to override defaults: put critical constraints in the immediate message or project guidance file.

## The Project Guidance File

Every project that uses agent-assisted development should have a guidance file. In Agent Zero, this is typically read via `text_editor:read` at the start of a session. Common names: `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `GEMINI.md`.

### Guidance File Template

```markdown
# Project: [Name]

## What This Is

One paragraph: what the project does, who it's for, and what problem it solves.

## Tech Stack

- **Runtime**: Node.js 20 + TypeScript 5
- **Framework**: Next.js 15 App Router
- **Database**: PostgreSQL + Prisma
- **Testing**: Vitest + Testing Library + Playwright
- **Styling**: Tailwind CSS
- **Deployment**: Vercel

## Development Commands

```bash
npm run dev          # Start dev server (localhost:3000)
npm test             # Run unit tests
npm run test:e2e     # Run Playwright E2E tests
npm run build        # Production build
npm run type-check   # TypeScript check
npm run lint         # ESLint
```

## Code Conventions

- **Components**: Functional components, colocated tests in `ComponentName.test.tsx`
- **API routes**: In `app/api/`, use `route.ts` handlers
- **Imports**: Use `@/` alias for src root
- **Error handling**: Throw domain errors (`NotFoundError`, `ValidationError`), catch in route handlers
- **State**: React Query for server state, `useState` for local UI state

## Project Structure

```
app/
  (auth)/        # Auth routes
  api/           # API route handlers
  tasks/         # Task feature routes
src/
  components/    # Shared UI components
  lib/           # Utilities, DB client, auth helpers
  types/         # Shared TypeScript types
prisma/
  schema.prisma  # Database schema
```

## Key Decisions

- Use Prisma (not raw SQL) for all DB access. For complex queries: `prisma.$queryRaw`.
- All API validation uses Zod schemas defined in `src/lib/validation/`
- Authentication via NextAuth.js with JWT sessions
- Feature flags managed via `src/lib/flags.ts`

## What Not to Do

- Don't use `any` in TypeScript (use `unknown` + type guards)
- Don't bypass Zod validation at API boundaries
- Don't commit `.env` files (use `.env.example` as template)
- Don't use `useEffect` for data fetching (use React Query)
```

### Guidance File Principles

```
✓ Specific and actionable — not vague principles
✓ Current — updated when conventions change
✓ Includes what NOT to do (prevents common mistakes)
✓ Shows examples, not just rules
✓ Short enough to fit in context — focus on what matters

✗ Long philosophical essays
✗ Aspirational rules that aren't followed
✗ Duplicate content that's obvious from the code
```

## Session Context Management

### At Session Start

```
1. Read the project guidance file:
   text_editor:read path AGENTS.md (or CLAUDE.md)

2. Read relevant source files for the task:
   text_editor:read path src/relevant/file.ts

3. Load applicable skills:
   skills_tool:load skill_name=<relevant-skill>

4. State the session goal explicitly:
   "In this session, we're implementing X. The constraints are Y."
```

### During a Long Session

```
When the context window is getting full:
├── Summarize decisions made so far in a text file
│   text_editor:write path /tmp/session-decisions.md
├── Start a new sub-task with a clean summary
│   call_subordinate with the summary + specific task
└── Reference prior outputs with §§include(path)
    instead of repeating them in the message
```

### Managing Task State

For multi-step tasks, maintain a task tracking file:

```markdown
# Session: Implement Task Priority Feature

## Status: In Progress

## Completed
- [x] Database migration: added `priority` column
- [x] API: extended POST/PATCH /api/tasks
- [x] Validation: Zod schema updated

## In Progress
- [ ] UI: priority selector in TaskForm

## Remaining
- [ ] UI: priority filter in TaskList
- [ ] Tests: API + UI tests
- [ ] Docs: update API docs

## Decisions Made
- Priority values: 'low' | 'medium' | 'high' (not numbers)
- Default: 'medium'
- Displayed as colored badges in TaskItem
```

Write and update this file with `text_editor:write` / `text_editor:patch`.

## Context Anti-Patterns

### Anti-Pattern 1: Starting Cold

```
Bad:  "Add a user profile page"
Good: "Read AGENTS.md, then add a user profile page following our
       Next.js App Router conventions with Prisma for DB access."
```

### Anti-Pattern 2: Vague Instructions

```
Bad:  "Make the app better"
Good: "Improve the performance of the task list page.
       The current p95 load time is 3.2s. Target is < 1s.
       Start by profiling with Lighthouse."
```

### Anti-Pattern 3: Missing Constraints

```
Bad:  "Add authentication"
Good: "Add Google OAuth authentication using NextAuth.js.
       We already have the NextAuth configuration in src/lib/auth.ts.
       MUST NOT add email/password — only OAuth providers."
```

### Anti-Pattern 4: No Success Criteria

```
Bad:  "Write tests for the task service"
Good: "Write unit tests for src/lib/task-service.ts.
       Target 80% line coverage. Focus on: create, update, delete,
       and the permission-checking logic. Use Vitest."
```

## Structuring Complex Tasks

For tasks that require multiple steps:

```markdown
## Task: Implement Task Sharing

### Context
- Codebase: Next.js 15, Prisma, tRPC
- Relevant files: src/lib/task-service.ts, src/api/tasks/route.ts
- Design doc: read docs/designs/task-sharing.md first

### Acceptance Criteria
1. User can share a task with another user by email
2. Shared user can view (not edit) the task
3. Owner can revoke sharing
4. Shared tasks appear in recipient's "Shared with me" list

### Constraints
- Follow existing Prisma patterns in src/lib/
- All API endpoints require authentication
- Don't break existing task ownership model
- Tests required: unit (service) + API (route handlers)

### Approach
1. Schema: add TaskShare table (taskId, sharedWithUserId, createdAt)
2. Service: share/unshare/listShared methods
3. API: POST /api/tasks/:id/share, DELETE /api/tasks/:id/share/:userId
4. UI: Share button in TaskItem, SharedWithMe list page
5. Tests: unit + integration
```

## Delegating Subtasks

When using `call_subordinate` for development subtasks:

```
Good delegation includes:
✓ The specific task (not the whole project)
✓ Relevant context (tech stack, file paths, conventions)
✓ Acceptance criteria (what done looks like)
✓ Constraints (what NOT to do)
✓ Output format (code + tests? just the code? a plan?)

Example:
"You are a backend developer working on a Next.js/Prisma project.
Implement the TaskShare database layer:
- Read src/lib/task-service.ts to understand existing patterns
- Add shareTask(taskId, ownerUserId, sharedWithEmail) method
- Add revokeShare(taskId, ownerUserId, sharedWithUserId) method
- Follow the existing error handling patterns (NotFoundError, etc.)
- Write unit tests using Vitest
Output: the updated task-service.ts with tests."
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The agent should figure it out from the code" | Agents work best with explicit context. The code shows WHAT. The guidance file explains WHY and HOW. |
| "I'll explain it every time" | Repeating context per session is error-prone. Write it once in the guidance file. |
| "The guidance file is too much work" | 30 minutes writing AGENTS.md saves hours of correcting misunderstandings. |
| "Long conversations work fine" | Context windows are finite. Manage state explicitly for sessions over ~20 messages. |
| "I'll just re-prompt if it goes wrong" | Structure the context correctly upfront. Reactive re-prompting wastes both parties' time. |

## Red Flags

- Agent using wrong tech stack despite being corrected
- Agent re-implementing code that already exists
- Tasks requiring 30+ messages that could be structured as smaller subtasks
- No project guidance file for a project with agent-assisted development
- Vague task descriptions with no acceptance criteria
- No tracking of decisions made in multi-step sessions

## Verification

After setting up project context:

- [ ] Project guidance file exists and covers: tech stack, commands, conventions, what-not-to-do
- [ ] Agent can answer "what framework does this project use?" correctly from context
- [ ] Complex tasks have explicit acceptance criteria
- [ ] Long sessions use a task tracking file updated as work progresses
- [ ] Subtask delegations include relevant context, not just the task name
