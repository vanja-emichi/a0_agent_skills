---
name: code-simplification
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Simplifies code for clarity. Use when refactoring code for clarity without
  changing behavior. Use when code works but is harder to read, maintain, or
  extend than it should be. Use when reviewing code that has accumulated
  unnecessary complexity.
tags:
  - refactoring
  - simplification
  - readability
  - code-quality
  - cleanup
trigger_patterns:
  - code-simplification
  - simplify this code
  - refactor for clarity
  - too complex
  - hard to read
  - clean up code
  - reduce complexity
  - make this simpler
  - code is confusing
  - unnecessary complexity
---

# Code Simplification

## Overview

Simplify code by reducing complexity while preserving exact behavior. The goal is not fewer lines — it's code that is easier to read, understand, modify, and debug. Every simplification must pass a simple test: "Would a new team member understand this faster than the original?"

## When to Use

- After a feature is working and tests pass, but the implementation feels heavier than it needs to be
- During code review when readability or complexity issues are flagged
- When you encounter deeply nested logic, long functions, or unclear names
- When refactoring code written under time pressure
- When consolidating related logic scattered across files
- After merging changes that introduced duplication or inconsistency

**When NOT to use:**

- Code is already clean and readable — don't simplify for the sake of it
- You don't understand what the code does yet — comprehend before you simplify
- The code is performance-critical and the "simpler" version would be measurably slower
- You're about to rewrite the module entirely — simplifying throwaway code wastes effort

## The Five Principles

### 1. Preserve Behavior Exactly

Don't change what the code does — only how it expresses it. All inputs, outputs, side effects, error behavior, and edge cases must remain identical. If you're not sure a simplification preserves behavior, don't make it.

```
ASK BEFORE EVERY CHANGE:
→ Does this produce the same output for every input?
→ Does this maintain the same error behavior?
→ Does this preserve the same side effects and ordering?
→ Do all existing tests still pass without modification?
```

### 2. Follow Project Conventions

Simplification means making code more consistent with the codebase, not imposing external preferences. Before simplifying:

```
1. Read project conventions (CLAUDE.md or equivalent) using text_editor:read
2. Use code_execution_tool with grep -rn to study how neighboring code handles similar patterns
3. Match the project's style for imports, function declarations, naming, error handling
```

Simplification that breaks project consistency is not simplification — it's churn.

### 3. Prefer Clarity Over Cleverness

Explicit code is better than compact code when the compact version requires a mental pause to parse.

```typescript
// UNCLEAR: Dense ternary chain
const label = isNew ? 'New' : isUpdated ? 'Updated' : isArchived ? 'Archived' : 'Active';

// CLEAR: Readable mapping
function getStatusLabel(item: Item): string {
  if (item.isNew) return 'New';
  if (item.isUpdated) return 'Updated';
  if (item.isArchived) return 'Archived';
  return 'Active';
}
```

### 4. Maintain Balance

Simplification has a failure mode: over-simplification. Watch for these traps:

- **Inlining too aggressively** — removing a helper that gave a concept a name makes the call site harder to read
- **Combining unrelated logic** — two simple functions merged into one complex function is not simpler
- **Removing "unnecessary" abstraction** — some abstractions exist for extensibility or testability
- **Optimizing for line count** — fewer lines is not the goal; easier comprehension is

### 5. Scope to What Changed

Default to simplifying recently modified code. Avoid drive-by refactors of unrelated code unless explicitly asked. Unscoped simplification creates noise in diffs and risks unintended regressions.

## The Simplification Process

### Step 1: Understand Before Touching (Chesterton's Fence)

Before changing or removing anything, understand why it exists. Don't tear down a fence before understanding why it was built.

```
BEFORE SIMPLIFYING, ANSWER:
- What is this code's responsibility?
- What calls it? What does it call?
- What are the edge cases and error paths?
- Are there tests that define the expected behavior?
- Why might it have been written this way?
- Check git blame: what was the original context?
```

Use `code_execution_tool` with `git blame <file>` and `grep -rn` to trace usages. If you can't answer these questions, read more context with `text_editor:read` first.

### Step 2: Identify Simplification Opportunities

Scan for these patterns:

**Structural complexity:**

| Pattern | Signal | Simplification |
|---------|--------|----------------|
| Deep nesting (3+ levels) | Hard to follow control flow | Extract conditions into guard clauses or helper functions |
| Long functions (50+ lines) | Multiple responsibilities | Split into focused functions with descriptive names |
| Nested ternaries | Requires mental stack to parse | Replace with if/else chains, switch, or lookup objects |
| Boolean parameter flags | `doThing(true, false, true)` | Replace with options objects or separate functions |
| Repeated conditionals | Same `if` check in multiple places | Extract to a well-named predicate function |

**Naming and readability:**

| Pattern | Signal | Simplification |
|---------|--------|----------------|
| Generic names | `data`, `result`, `temp`, `val`, `item` | Rename to describe the content: `userProfile`, `validationErrors` |
| Abbreviated names | `usr`, `cfg`, `btn`, `evt` | Use full words unless the abbreviation is universal |
| Misleading names | Function named `get` that also mutates state | Rename to reflect actual behavior |
| Comments explaining "what" | `// increment counter` above `count++` | Delete the comment — the code is clear enough |
| Comments explaining "why" | `// Retry because the API is flaky under load` | Keep these — they carry intent the code can't express |

**Redundancy:**

| Pattern | Signal | Simplification |
|---------|--------|----------------|
| Duplicated logic | Same 5+ lines in multiple places | Extract to a shared function |
| Dead code | Unreachable branches, unused variables | Remove (after confirming it's truly dead) |
| Unnecessary abstractions | Wrapper that adds no value | Inline the wrapper |
| Over-engineered patterns | Factory-for-a-factory | Replace with the simple direct approach |

### Step 3: Apply Changes Incrementally

Make one simplification at a time. Run tests via `code_execution_tool` after each change.

```
FOR EACH SIMPLIFICATION:
1. Make the change using text_editor:patch
2. Run the test suite via code_execution_tool
3. If tests pass → continue to next simplification
4. If tests fail → revert using text_editor:patch and reconsider
```

**The Rule of 500:** If a refactoring would touch more than 500 lines, use `code_execution_tool` to write automation (sed scripts, etc.) rather than making changes by hand.

### Step 4: Verify the Result

After all simplifications, step back and evaluate:

```
COMPARE BEFORE AND AFTER:
- Is the simplified version genuinely easier to understand?
- Did you introduce any new patterns inconsistent with the codebase?
- Is the diff clean and reviewable?
- Would a teammate approve this change?
```

## Language-Specific Guidance

### TypeScript / JavaScript

```typescript
// SIMPLIFY: Unnecessary async wrapper
async function getUser(id: string): Promise<User> {
  return await userService.findById(id);  // Before
}
function getUser(id: string): Promise<User> {
  return userService.findById(id);  // After
}

// SIMPLIFY: Verbose conditional assignment
let displayName: string;
if (user.nickname) {  // Before
  displayName = user.nickname;
} else {
  displayName = user.fullName;
}
const displayName = user.nickname || user.fullName;  // After

// SIMPLIFY: Manual array building → filter
const activeUsers = users.filter((user) => user.isActive);

// SIMPLIFY: Redundant boolean return
function isValid(input: string): boolean {
  return input.length > 0 && input.length < 100;  // After
}
```

### Python

```python
# SIMPLIFY: Verbose dictionary building
result = {item.id: item.name for item in items}  # After

# SIMPLIFY: Nested conditionals with early return
def process(data):
    if data is None:
        raise TypeError("Data is None")
    if not data.is_valid():
        raise ValueError("Invalid data")
    if not data.has_permission():
        raise PermissionError("No permission")
    return do_work(data)  # After: guard clauses
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "It's working, no need to touch it" | Working code that's hard to read will be hard to fix when it breaks. Simplifying now saves time on every future change. |
| "Fewer lines is always simpler" | A 1-line nested ternary is not simpler than a 5-line if/else. Simplicity is about comprehension speed, not line count. |
| "I'll just quickly simplify this unrelated code too" | Unscoped simplification creates noisy diffs and risks regressions in code you didn't intend to change. |
| "The original author must have had a reason" | Maybe. Check git blame — apply Chesterton's Fence. But accumulated complexity often has no reason. |
| "I'll refactor while adding this feature" | Separate refactoring from feature work. Mixed changes are harder to review, revert, and understand in history. |

## Red Flags

- Simplification that requires modifying tests to pass (you likely changed behavior)
- "Simplified" code that is longer and harder to follow than the original
- Renaming things to match your preferences rather than project conventions
- Removing error handling because "it makes the code cleaner"
- Simplifying code you don't fully understand
- Batching many simplifications into one large, hard-to-review commit
- Refactoring code outside the scope of the current task without being asked

## Verification

After completing a simplification pass:

- [ ] All existing tests pass without modification
- [ ] Build succeeds with no new warnings
- [ ] Linter/formatter passes (no style regressions)
- [ ] Each simplification is a reviewable, incremental change
- [ ] The diff is clean — no unrelated changes mixed in
- [ ] Simplified code follows project conventions
- [ ] No error handling was removed or weakened
- [ ] No dead code was left behind (unused imports, unreachable branches)
- [ ] A teammate or review agent would approve the change as a net improvement
