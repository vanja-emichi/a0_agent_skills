---
name: deprecation-and-migration
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Manages safe API deprecation and system migrations. Use when removing or
  changing existing APIs, migrating databases, upgrading dependencies, or
  migrating between architectural patterns without breaking existing consumers.
tags:
  - deprecation
  - migration
  - breaking-changes
  - versioning
  - upgrade
trigger_patterns:
  - deprecation-and-migration
  - deprecate this api
  - migrate the database
  - breaking change
  - upgrade dependencies
  - remove old code
  - migrate to new pattern
  - strangler fig
  - sunset this feature
  - backward compatibility
  - migrate to new api
  - new api migration
  - migrate to the new
  - module to the new api
  - api migration
  - migrate this module
  - upgrade to new api
  - update to new api
  - migration to new api
  - switch to new api
---

# Deprecation and Migration

## Overview

Code is a liability, not an asset. Every line of code has ongoing maintenance cost — bugs to fix, dependencies to update, security patches to apply, and new engineers to onboard. Deprecation is the discipline of removing code that no longer earns its keep, and migration is the process of moving users safely from the old to the new.

Most engineering organizations are good at building things. Few are good at removing them. This skill addresses that gap.

## When to Use

- Replacing an old system, API, or library with a new one
- Sunsetting a feature that's no longer needed
- Consolidating duplicate implementations
- Removing dead code that nobody owns but everybody depends on
- Planning the lifecycle of a new system (deprecation planning starts at design time)
- Deciding whether to maintain a legacy system or invest in migration
- Migrating a database schema
- Upgrading a major dependency version
- Moving from one architectural pattern to another (monolith → microservices, REST → GraphQL)

## Core Principles

### Code Is a Liability

Every line of code has ongoing cost: it needs tests, documentation, security patches, dependency updates, and mental overhead for anyone working nearby. The value of code is the functionality it provides, not the code itself. When the same functionality can be provided with less code, less complexity, or better abstractions — the old code should go.

### Hyrum's Law Makes Removal Hard

With enough users, every observable behavior becomes depended on — including bugs, timing quirks, and undocumented side effects. This is why deprecation requires active migration, not just announcement. Users can't "just switch" when they depend on behaviors the replacement doesn't replicate.

### Deprecation Planning Starts at Design Time

When building something new, ask: "How would we remove this in 3 years?" Systems designed with clean interfaces, feature flags, and minimal surface area are easier to deprecate than systems that leak implementation details everywhere.

## The Deprecation Decision

Before deprecating anything, answer these questions:

```
1. Does this system still provide unique value?
   → If yes, maintain it. If no, proceed.

2. How many users/consumers depend on it?
   → Quantify the migration scope (use grep -rn via code_execution_tool).

3. Does a replacement exist?
   → If no, build the replacement first. Don't deprecate without an alternative.

4. What's the migration cost for each consumer?
   → If trivially automated, do it. If manual and high-effort, weigh against maintenance cost.

5. What's the ongoing maintenance cost of NOT deprecating?
   → Security risk, engineer time, opportunity cost of complexity.
```

## Compulsory vs Advisory Deprecation

| Type | When to Use | Mechanism |
|------|-------------|------------|
| **Advisory** | Migration is optional, old system is stable | Warnings, documentation, nudges. Users migrate on their own timeline. |
| **Compulsory** | Old system has security issues, blocks progress, or maintenance cost is unsustainable | Hard deadline. Old system will be removed by date X. Provide migration tooling. |

**Default to advisory.** Use compulsory only when the maintenance cost or risk justifies forcing migration. Compulsory deprecation requires providing migration tooling, documentation, and support — you MUST NOT just announce a deadline.

## The Deprecation Protocol

### Stage 1: Plan (Before Writing Code)

```
BEFORE DEPRECATING, ANSWER:
1. Who uses this? (Use grep -rn via code_execution_tool to find all usages)
2. What is the migration path? (Don't deprecate without a replacement)
3. How long do consumers need? (Internal: 1-2 weeks. External: 1-6 months)
4. Can I migrate them automatically? (Script > docs > manual)
5. What breaks if I remove it today? (Test with code_execution_tool)
```

### Stage 2: Communicate

For internal code:
```typescript
// Mark with @deprecated JSDoc tag
/**
 * @deprecated Use `createTaskV2(input)` instead. Will be removed in v4.0.0.
 * Migration guide: see docs/migrations/task-api-v4.md
 */
export function createTask(title: string, priority: number): Task {
  console.warn('[DEPRECATED] createTask() is deprecated. Use createTaskV2() instead.');
  return createTaskV2({ title, priority: mapPriority(priority) });
}
```

For external APIs:
```typescript
// HTTP Deprecation headers (RFC 8594)
app.post('/api/v1/tasks', (req, res) => {
  res.set('Deprecation', 'true');
  res.set('Sunset', 'Sat, 01 Jan 2026 00:00:00 GMT');
  res.set('Link', '</api/v2/tasks>; rel="successor-version"');

  // ... existing handler
});
```

### Stage 3: Announce and Document

```markdown
## Deprecation Notice: OldService

**Status:** Deprecated as of 2025-03-01
**Replacement:** NewService (see migration guide below)
**Removal date:** Advisory — no hard deadline yet
**Reason:** OldService requires manual scaling and lacks observability.
            NewService handles both automatically.

### Migration Guide
1. Replace `import { client } from 'old-service'` with `import { client } from 'new-service'`
2. Update configuration (see examples below)
3. Run the migration verification script: `npx migrate-check`
```

### Stage 4: Migrate Incrementally

Migrate consumers one at a time, not all at once. For each consumer:

```
1. Identify all touchpoints with the deprecated system
2. Update to use the replacement
3. Verify behavior matches (tests, integration checks)
4. Remove references to the old system
5. Confirm no regressions
```

Prefer automated migration over documentation:

```bash
# Codemod for mechanical renames
npx jscodeshift -t ./codemods/rename-createTask.js src/

# Database migration (Prisma)
npx prisma migrate dev --name rename_priority_column

# Check remaining usages after migration
grep -rn "createTask(" src/ --include="*.ts" | grep -v "createTaskV2"
```

**The Churn Rule:** If you own the infrastructure being deprecated, you are responsible for migrating your users — or providing backward-compatible updates that require no migration. Don't announce deprecation and leave users to figure it out.

### Stage 5: Remove the Old System

Only after all consumers have migrated:

```
1. Verify zero active usage (metrics, logs, dependency analysis)
2. Remove the code
3. Remove associated tests, documentation, and configuration
4. Remove the deprecation notices
5. Celebrate — removing code is an achievement
```

Only after:
- [ ] All internal usages migrated
- [ ] External consumers notified (with adequate lead time)
- [ ] Monitoring shows zero/negligible usage
- [ ] Sunset date has passed

## Migration Patterns

### Strangler Pattern

Run old and new systems in parallel. Route traffic incrementally from old to new. When the old system handles 0% of traffic, remove it.

```
Phase 1: New system handles 0%, old handles 100%
Phase 2: New system handles 10% (canary)
Phase 3: New system handles 50%
Phase 4: New system handles 100%, old system idle
Phase 5: Remove old system
```

### Adapter Pattern

Create an adapter that translates calls from the old interface to the new implementation. Consumers keep using the old interface while you migrate the backend.

```typescript
// Adapter: old interface, new implementation
class LegacyTaskService implements OldTaskAPI {
  constructor(private newService: NewTaskService) {}

  // Old method signature, delegates to new implementation
  getTask(id: number): OldTask {
    const task = this.newService.findById(String(id));
    return this.toOldFormat(task);
  }
}
```

### Feature Flag Migration

Use feature flags to switch consumers from old to new system one at a time:

```typescript
function getTaskService(userId: string): TaskService {
  if (featureFlags.isEnabled('new-task-service', { userId })) {
    return new NewTaskService();
  }
  return new LegacyTaskService();
}
```

## Database Migrations

### Safe Migration Patterns

Database migrations MUST be backward compatible during the transition period — the old app version MUST work with the new schema, and the new app version MUST work with the old schema, until both are deployed.

#### Additive Changes (Safe)

```sql
-- Safe: Add new nullable column
ALTER TABLE tasks ADD COLUMN priority VARCHAR(20);

-- Safe: Add new table
CREATE TABLE task_labels (...);

-- Safe: Add new index
CREATE INDEX CONCURRENTLY tasks_status_idx ON tasks (status);
```

#### Rename Column (Multi-Step)

```sql
-- Step 1: Add new column (deploy with code that writes to both)
ALTER TABLE tasks ADD COLUMN priority_level VARCHAR(20);

-- Step 2: Backfill new column
UPDATE tasks SET priority_level = CASE
  WHEN priority = 0 THEN 'low'
  WHEN priority = 1 THEN 'medium'
  ELSE 'high'
END;

-- Step 3: Deploy code that reads from new column, writes to both
-- Step 4: Verify all data migrated
-- Step 5: Deploy code that only uses new column
-- Step 6: Drop old column
ALTER TABLE tasks DROP COLUMN priority;
```

#### Removing a Column (Multi-Step)

```
Step 1: Deploy code that stops reading the column
Step 2: Deploy code that stops writing the column
Step 3: Remove the column from the schema
Step 4: ALTER TABLE tasks DROP COLUMN old_column;
```

**NEVER remove a column before the code that reads it is deployed.**

### Migration Scripts

```typescript
// Prisma migration
// prisma/migrations/20250315_add_priority_level/migration.sql

ALTER TABLE "Task" ADD COLUMN "priorityLevel" TEXT;

UPDATE "Task" SET "priorityLevel" = CASE
  WHEN priority = 0 THEN 'low'
  WHEN priority = 1 THEN 'medium'
  ELSE 'high'
END;

ALTER TABLE "Task" ALTER COLUMN "priorityLevel" SET NOT NULL;
```

```bash
# Apply migration via code_execution_tool
npx prisma migrate deploy

# Verify migration applied
npx prisma migrate status
```

## Dependency Upgrades

### Major Version Upgrade Process

```bash
# 1. Read the changelog first (always)
# Use document_query for release notes

# 2. Check current usage patterns before upgrading
grep -rn "from 'library'" src/ --include="*.ts"

# 3. Create a branch
git checkout -b chore/upgrade-library-v4

# 4. Upgrade
npm install library@^4.0.0

# 5. Run tests immediately
npm test

# 6. Fix breaking changes one at a time
# 7. Verify full test suite passes
npm run type-check && npm test && npm run build
```

### Handling Breaking Changes

```typescript
// Compatibility shim for gradual migration
// Wraps old API in new API signature
export function legacyCreateTask(title: string, priority: number): Task {
  return newLibrary.createTask({
    title,
    priority: ['low', 'medium', 'high'][priority] || 'medium',
  });
}

// TODO(team): Remove this shim by 2025-06-01 after all callers are updated
// Tracking issue: #456
```

## Zombie Code

Zombie code is code that nobody owns but everybody depends on. It's not actively maintained, has no clear owner, and accumulates security vulnerabilities and compatibility issues. Signs:

- No commits in 6+ months but active consumers exist
- No assigned maintainer or team
- Failing tests that nobody fixes
- Dependencies with known vulnerabilities that nobody updates
- Documentation that references systems that no longer exist

**Response:** Either assign an owner and maintain it properly, or deprecate it with a concrete migration plan. Zombie code MUST NOT stay in limbo — it either gets investment or removal.

## Checklist: Before Any Breaking Change

```markdown
### Impact Assessment
- [ ] All usages identified (grep -rn across codebase)
- [ ] External consumers notified (if applicable)
- [ ] Migration guide written
- [ ] Timeline established (deprecation → migration → removal)

### Migration Path
- [ ] Replacement implementation exists
- [ ] Automated migration available (codemod or script)
- [ ] Old API still works during transition period
- [ ] Deprecation warning in old API with migration instructions

### Verification
- [ ] Migrated callers tested
- [ ] Old API tests updated or removed
- [ ] No remaining usages before removal
- [ ] Monitoring shows clean rollout
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It still works, why remove it?" | Working code that nobody maintains accumulates security debt and complexity. Maintenance cost grows silently. |
| "Someone might need it later" | If it's needed later, it can be rebuilt. Keeping unused code "just in case" costs more than rebuilding. |
| "The migration is too expensive" | Compare migration cost to ongoing maintenance cost over 2-3 years. Migration is usually cheaper long-term. |
| "We'll deprecate it after we finish the new system" | Deprecation planning starts at design time. By the time the new system is done, you'll have new priorities. Plan now. |
| "Users will migrate on their own" | They won't. Provide tooling, documentation, and incentives — or do the migration yourself (the Churn Rule). |
| "We can maintain both systems indefinitely" | Two systems doing the same thing is double the maintenance, testing, documentation, and onboarding cost. |
| "Nobody uses this old API" | Use `grep -rn` via `code_execution_tool` to confirm. Don't assume. |
| "We'll just remove it and fix the breakage" | Breakage is discovered by users, not you. Migrate consumers first. |

## Red Flags

- Deprecated systems with no replacement available
- Deprecation announcements with no migration tooling or documentation
- "Soft" deprecation that's been advisory for years with no progress
- Zombie code with no owner and active consumers
- New features added to a deprecated system (invest in the replacement instead)
- Deprecation without measuring current usage
- Removing code without verifying zero active consumers
- Database column removal without a multi-step migration
- Breaking changes in a patch version (violates semver)
- No sunset date on deprecated code (it lives forever)
- Migrating all callers in one massive PR (hard to review, hard to revert)

## Verification

After completing a deprecation or migration:

- [ ] Replacement is production-proven and covers all critical use cases
- [ ] Migration guide exists with concrete steps and examples
- [ ] All active consumers have been migrated (verified by metrics/logs)
- [ ] All usages of deprecated code identified with `grep -rn` via `code_execution_tool`
- [ ] Deprecated code still works during transition (no immediate breakage)
- [ ] Database migration is backward compatible
- [ ] Tests cover both the old path and the new path
- [ ] Old code, tests, documentation, and configuration are fully removed
- [ ] No references to the deprecated system remain in the codebase
- [ ] Deprecation notices are removed (they served their purpose)
- [ ] Removal date or version established
- [ ] Monitoring in place to detect unexpected usage
