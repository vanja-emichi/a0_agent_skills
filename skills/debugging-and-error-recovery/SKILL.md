---
name: debugging-and-error-recovery
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Diagnoses and fixes bugs systematically. Use when encountering errors,
  unexpected behavior, or failing tests. Use when you need a structured
  approach to finding root causes rather than guessing at fixes.
tags:
  - debugging
  - error-handling
  - troubleshooting
  - root-cause
  - testing
trigger_patterns:
  - debugging-and-error-recovery
  - fix this bug
  - something is broken
  - error in the logs
  - test is failing
  - unexpected behavior
  - how do I debug
  - root cause analysis
  - error recovery
  - diagnose the issue
---

# Debugging and Error Recovery

## Overview

Debug systematically, not randomly. The most common debugging mistake is jumping to a fix before understanding the problem. Premature fixes mask symptoms, introduce new bugs, and waste time. The correct approach: reproduce the bug, read the error carefully, form a hypothesis, verify it, fix the root cause, confirm the fix.

## When to Use

- Encountering an error message or exception
- Tests are failing unexpectedly
- A feature works in some cases but not others
- Recent changes broke something that was working
- Runtime behavior doesn't match what the code suggests

## The Debugging Protocol

### Step 1: Read the Error (Don't Skim)

The error message contains the answer most of the time. Read it in full:

```
READ THE ERROR:
→ What is the error type? (TypeError, ReferenceError, 404, etc.)
→ What is the exact message?
→ What file and line number?
→ What is the full stack trace (not just the first line)?
→ Is there a "caused by" or inner exception?
```

Use `code_execution_tool` to capture full error output:
```bash
# Run with full stack trace
node --stack-trace-limit=50 script.js 2>&1

# Python with full traceback
python -m traceback script.py 2>&1

# Capture test failures in full
npx vitest run --reporter=verbose 2>&1
```

### Step 2: Reproduce Reliably

Before fixing, make the bug reproducible on demand:

```
REPRODUCTION QUESTIONS:
- Can I trigger this consistently?
- What exact inputs/conditions trigger it?
- Does it happen in isolation, or only with other code?
- Does it happen in test environment? Production? Both?
- Did it ever work? If so, what changed?
```

If you can't reproduce it, you can't verify when it's fixed. Use `code_execution_tool` to write a minimal reproduction:

```typescript
// Minimal reproduction — remove everything not needed to trigger the bug
const { processTask } = require('./task-processor');

const task = { id: '123', title: '', status: 'pending' };
const result = processTask(task);
console.log(result); // Should trigger the bug
```

### Step 3: Locate the Source

Don't guess. Use tools to find where the bug lives:

```bash
# Find error message in codebase
grep -rn "error message text" src/

# Find where a function is called
grep -rn "functionName" src/

# Check what changed recently
git log --oneline -10
git diff HEAD~3..HEAD -- src/

# Check git blame for a specific line
git blame src/task-processor.ts -L 45,60
```

### Step 4: Form a Hypothesis

Before changing code:

```
HYPOTHESIS FORMAT:
"I believe the bug is in [location] because [evidence].
To verify, I will [specific check].
If I'm right, I'll see [expected result]."
```

Example:
```
"I believe the bug is in the task validation function because
the error occurs after the API call succeeds but before the
data is saved. To verify, I'll add a console.log after validation
to check the return value. If I'm right, I'll see undefined
where a valid task object is expected."
```

### Step 5: Verify the Hypothesis

Add targeted logging to confirm — don't skip straight to the fix:

```typescript
// Targeted diagnostic logging
console.log('[DEBUG] task input:', JSON.stringify(task));
console.log('[DEBUG] validation result:', validateTask(task));
console.log('[DEBUG] db save input:', JSON.stringify(savedData));
```

Or use `code_execution_tool` to run a targeted test:
```bash
npx vitest run --filter "task validation"
```

**Remove all diagnostic logging after fixing.**

### Step 6: Fix the Root Cause

Not the symptom. Ask "why did this happen?" until you reach something actionable:

```
SYMPTOM:  The UI shows incorrect task count
CAUSE 1:  The filter function returns wrong results
CAUSE 2:  The filter function receives stale data
CAUSE 3:  State is updated but the query cache isn't invalidated
ROOT CAUSE: Missing queryClient.invalidateQueries() after mutation
```

Fix the root cause (add the invalidation), not the symptom (don't hardcode a count or add a workaround).

### Step 7: Write a Regression Test

Every bug fix gets a test. This proves the fix works and prevents the bug from returning:

```typescript
describe('processTask', () => {
  // Regression test: was returning undefined for tasks with empty title
  it('returns error result for empty title task', () => {
    const task = { id: '123', title: '', status: 'pending' };
    const result = processTask(task);
    expect(result.success).toBe(false);
    expect(result.error).toContain('title');
  });
});
```

Run the test to confirm it fails before the fix and passes after:
```bash
# Before fix: test should FAIL
git stash && npx vitest run --filter "empty title"

# Apply fix, then:
npx vitest run --filter "empty title"  # Should PASS
```

## Common Bug Patterns

### Async/Await Errors

```typescript
// Bug: missing await causes undefined
const user = getUser(id);  // Returns Promise, not User
console.log(user.name);    // TypeError: Cannot read property 'name' of undefined

// Fix: await the async function
const user = await getUser(id);
console.log(user.name);

// Bug: unhandled promise rejection
fetchData()  // Error swallowed if fetchData rejects

// Fix: handle the error
try {
  await fetchData();
} catch (error) {
  console.error('Failed to fetch:', error);
  throw error;  // Re-throw if you can't recover
}
```

### React State Bugs

```typescript
// Bug: stale closure captures old state
const [count, setCount] = useState(0);
setInterval(() => {
  setCount(count + 1);  // count is always 0 (stale closure)
}, 1000);

// Fix: functional update
setCount(prev => prev + 1);

// Bug: mutating state directly
const [tasks, setTasks] = useState([]);
tasks.push(newTask);  // Doesn't trigger re-render
setTasks(tasks);       // Same reference — React won't re-render

// Fix: return new array
setTasks(prev => [...prev, newTask]);
```

### TypeScript Type Errors

```typescript
// Error: Property 'name' does not exist on type 'User | null'
function displayUser(user: User | null) {
  console.log(user.name);  // Error: user might be null
}

// Fix: narrow the type
function displayUser(user: User | null) {
  if (!user) return;
  console.log(user.name);  // TypeScript knows user is User here
}

// Error: Argument of type 'string' is not assignable to parameter of type 'number'
// → Check the function signature, not just the call site
```

### Network/API Errors

```
DEBUG NETWORK ERRORS:

400 Bad Request
→ Check the request body: log the payload before sending
→ Check Content-Type header is set correctly
→ Check the API schema for required fields

401 Unauthorized
→ Check if auth token is being sent
→ Check if auth token is expired
→ Check Authorization header format: 'Bearer <token>'

404 Not Found
→ Check the URL (typos, wrong version, missing ID)
→ Confirm the resource exists via code_execution_tool (curl/fetch)

500 Internal Server Error
→ Check server logs via code_execution_tool
→ The error is on the server side, not the client

CORS Error
→ Check Origin header matches server's CORS allowlist
→ Check server's CORS configuration
```

### Database Errors

```bash
# Check query via code_execution_tool
npx prisma studio  # Visual DB inspector
npx prisma db execute --file query.sql  # Run raw SQL

# Common issues:
# - Record not found: verify ID exists
# - Constraint violation: check unique/foreign key constraints
# - Connection pool exhausted: check connection count
# - Migration not applied: run npx prisma migrate deploy
```

## Debugging with Agent Zero Tools

### Code Inspection

```bash
# Find usages of the broken function
grep -rn "functionName" src/ --include="*.ts"

# Check recent changes
git log --oneline -5 src/path/to/file.ts
git diff HEAD~1 -- src/path/to/file.ts

# Read the file
text_editor:read path src/path/to/file.ts
```

### Browser Debugging

For UI bugs, use the `browser` tool:

```
browser: open → navigate to the page that has the bug
browser: evaluate → console.error logs
browser: content → DOM structure
browser: screenshot → visual state capture + vision_load to inspect
```

### Test-Driven Debugging

Write a failing test first, then fix:

```bash
# 1. Write the test that captures the bug
text_editor:write path src/__tests__/bug-regression.test.ts

# 2. Run it (should fail)
code_execution_tool: npx vitest run --filter "bug-regression"

# 3. Fix the code
text_editor:patch ...

# 4. Run again (should pass)
code_execution_tool: npx vitest run --filter "bug-regression"

# 5. Run full suite (should not have broken anything)
code_execution_tool: npx vitest run
```

## When You're Stuck

```
IF STUCK FOR MORE THAN 15 MINUTES:
1. Step back — re-read the original error from scratch
2. Check what changed recently: git log --oneline -10
3. Binary search: revert to a known-good commit, re-add changes incrementally
4. Rubber duck: write out what the code is supposed to do vs. what it does
5. Check similar patterns in the codebase: grep -rn for similar function calls
6. Read the library docs: the bug might be a usage error, not a logic error
7. Check GitHub issues for the library: search for the error message
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It must be a framework bug" | It almost never is. Check your code first. |
| "I'll just add a try-catch" | Swallowing errors hides bugs. Handle the actual cause. |
| "This workaround should be fine" | Workarounds become permanent. Fix the root cause. |
| "The fix is obvious, I don't need to reproduce it first" | If you don't reproduce it, you can't verify when it's fixed. |
| "I'll add the regression test later" | Tests written later get skipped. Write it now while the bug is fresh. |

## Red Flags

- Fixing code before reading the full error message
- Adding try-catch to make the error disappear without understanding it
- Making multiple unrelated changes at once to "see if any of them work"
- Fixing a bug by patching the caller instead of the broken function
- No regression test after fixing a bug
- Diagnostic `console.log` statements left in the code

## Verification

After fixing a bug:

- [ ] The original error no longer occurs
- [ ] A regression test exists and passes
- [ ] The full test suite passes (no new failures introduced)
- [ ] The root cause is fixed (not just a symptom)
- [ ] All diagnostic logging removed
- [ ] The fix makes sense to someone who didn't write it
