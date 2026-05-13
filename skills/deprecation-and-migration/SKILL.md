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

Remove and migrate safely. The goal of deprecation is to guide consumers away from old patterns without breaking them — giving adequate notice, providing a clear migration path, and removing dead code only after adoption is confirmed. Rushed deprecations break trust. Abandoned deprecations create maintenance debt.

## When to Use

- Removing or changing a public API endpoint
- Renaming or restructuring modules or functions
- Migrating a database schema
- Upgrading a major dependency version
- Moving from one architectural pattern to another (monolith → microservices, REST → GraphQL)

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

### Stage 3: Migrate

**Prefer automated migration over documentation:**

```bash
# Codemod for mechanical renames
npx jscodeshift -t ./codemods/rename-createTask.js src/

# Database migration (Prisma)
npx prisma migrate dev --name rename_priority_column

# Check remaining usages after migration
grep -rn "createTask(" src/ --include="*.ts" | grep -v "createTaskV2"
```

### Stage 4: Remove

Only after:
- [ ] All internal usages migrated
- [ ] External consumers notified (with adequate lead time)
- [ ] Monitoring shows zero/negligible usage
- [ ] Sunset date has passed

```bash
# Verify no usages remain
grep -rn "createTask(" src/ --include="*.ts" | grep -v "V2"

# Remove the deprecated function
# Remove the migration wrapper
# Remove the deprecation warning
# Update docs
```

## Database Migrations

### Safe Migration Patterns

Database migrations must be backward compatible during the transition period — the old app version must work with the new schema, and the new app version must work with the old schema, until both are deployed.

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

**Never remove a column before the code that reads it is deployed.**

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
# Use document_query: https://github.com/<owner>/<repo>/blob/main/CHANGELOG.md
# Or: browser: navigate to release notes

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

## The Strangler Fig Pattern

For migrating large systems incrementally:

```
1. IDENTIFY the slice to migrate
   └── Choose a bounded piece of functionality, not "rewrite everything"

2. BUILD the replacement alongside the old system
   └── New code exists but isn't routed to yet

3. ROUTE a small percentage of traffic to the new system
   └── Use feature flags or canary routing (1% → 5% → 25% → 100%)

4. VERIFY at each stage
   └── Monitor error rates, latency, data consistency

5. EXPAND routing until 100%
   └── Old system still exists as fallback

6. REMOVE the old system
   └── Only after new system is stable at 100%
```

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
| "Nobody uses this old API" | Use `grep -rn` via `code_execution_tool` to confirm. Don't assume. |
| "We'll just remove it and fix the breakage" | Breakage is discovered by users, not you. Migrate consumers first. |
| "The migration guide is enough" | A codemod that does it automatically is 10x more likely to be adopted. |
| "It's internal, so breaking changes are fine" | Internal consumers still have to update. Give them notice and a migration path. |
| "We'll keep both versions indefinitely" | Maintenance cost of two versions compounds. Commit to a removal date. |

## Red Flags

- Removing a function without searching for its usages first
- Database column removal without a multi-step migration
- Breaking changes in a patch version (violates semver)
- Deprecation without a replacement or migration guide
- No sunset date on deprecated code (it lives forever)
- Migrating all callers in one massive PR (hard to review, hard to revert)

## Verification

Before merging a deprecation or migration:

- [ ] All usages of deprecated code identified with `grep -rn` via `code_execution_tool`
- [ ] Migration path documented or automated
- [ ] Deprecated code still works (no immediate breakage)
- [ ] Database migration is backward compatible
- [ ] Tests cover both the old path and the new path
- [ ] Removal date or version established
- [ ] Monitoring in place to detect unexpected usage
