"""ship — Pre-launch sequential review orchestrator.

Spawns three specialist agents (code-reviewer, security-auditor, test-engineer)
sequentially via call_subordinate, collects their reports, then asks the main
agent to merge findings into a single GO / NO-GO decision with a rollback plan.

Returns a text prompt injected into the main agent's context window.

Note: Agent Zero executes one tool call per turn, so the three specialist
reviews run sequentially (not in parallel as in Claude Code's /ship). The
output is functionally equivalent — three independent perspectives merged
into a single GO / NO-GO decision.
"""
from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------------------
# Scope sanitization
# ---------------------------------------------------------------------------

def _sanitize_scope(scope: str) -> str:
    """Sanitize user-supplied scope text to prevent prompt injection.

    1. Strip control characters
    2. Remove markdown headings
    3. Remove instruction-injection patterns
    4. Cap at 500 characters
    """
    # Strip control characters (0x00-0x1f, 0x7f)
    scope = re.sub(r'[\x00-\x1f\x7f]', '', scope)
    # Remove markdown headings (# through ######)
    scope = re.sub(r'^#{1,6}\s*', '', scope, flags=re.MULTILINE)
    # Remove instruction-injection patterns
    scope = re.sub(
        r'(?i)(ignore|override|disregard)\s+(all\s+)?(previous|above|prior)\s+instructions?',
        '',
        scope,
    )
    # Cap length and strip whitespace
    scope = scope[:500].strip()
    return scope


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run(payload: dict[str, Any]) -> dict[str, str]:
    """Generate a ship-review prompt for the main agent.

    Args:
        payload: Provided by the commands plugin.  Expected keys:
            - invocation.raw_arguments  raw text from /ship <args>
            - arguments                 parsed argument dict
            - context.project_name     active project name (may be empty)

    Returns:
        {"text": <prompt string>} injected into main agent context.
    """
    # Extract optional scope / PR description from invocation
    scope: str = ""
    try:
        invocation = payload.get("invocation") or {}
        raw_args = (invocation.get("raw_arguments") or "").strip()
        scope = raw_args
    except Exception:
        pass

    # Security: scope comes from the /ship CLI argument in a single-user local
    # deployment. Apply comprehensive sanitization to limit prompt injection
    # surface if this plugin is ever used in a multi-tenant context.
    scope = _sanitize_scope(scope)
    scope_line = f"\n**Scope:**\n```\n{scope}\n```\n" if scope else ""
    scope_desc_review = f"Scope: {scope}." if scope else "Review all recent changes."
    scope_desc_audit = f"Scope: {scope}." if scope else "Audit all recent changes."
    scope_desc_coverage = f"Scope: {scope}." if scope else "Analyze all recent changes."

    prompt = f"""# /ship — Pre-Launch Review
{scope_line}
You are the **orchestrator**. Run all three specialist reviews below, then
produce a single GO / NO-GO decision with a rollback plan.

## Phase A — Sequential Specialist Reviews

Call each specialist using `call_subordinate` with the matching profile.
Do **not** let specialists delegate to each other — they report back to you only.

### Step 1 — Code Quality Review

Delegate to `call_subordinate(profile="code-reviewer")` with this message:

> Conduct a five-axis code review (correctness, readability, architecture,
> security, performance) on the current staged changes or most recent commits.
> {scope_desc_review}
> Output the full standard review template with an APPROVE / REQUEST CHANGES
> verdict, Critical / Important / Suggestion findings, and file:line references.

### Step 2 — Security Audit

Delegate to `call_subordinate(profile="security-auditor")` with this message:

> Run a security and vulnerability pass on the current staged changes or most
> recent commits.
> {scope_desc_audit}
> Check OWASP Top 10, secrets handling, auth/authz, dependency CVEs, and input
> validation. Output the full Security Audit Report with severity-classified
> findings (Critical/High/Medium/Low/Info) and actionable mitigations.

### Step 3 — Test Coverage Analysis

Delegate to `call_subordinate(profile="test-engineer")` with this message:

> Analyze test coverage for the current staged changes or most recent commits.
> {scope_desc_coverage}
> Identify gaps in happy path, edge cases, error paths, and concurrency scenarios.
> Output the full Test Coverage Analysis with Recommended Tests list and
> Critical/High/Medium/Low priority classification.

## Phase B — Merge and Decision

Once all three reports are returned, synthesize them as the main agent (not a
subagent) into the following output:

## Ship Decision: GO | NO-GO

### Blockers (must fix before ship)
- [Source persona: Critical finding + file:line]

### Recommended fixes (should fix before ship)
- [Source persona: Important finding + file:line]

### Acknowledged risks (shipping anyway)
- [Risk + mitigation]

### Rollback plan
- Trigger conditions: [what signals would prompt rollback]
- Rollback procedure: [exact steps]
- Recovery time objective: [target]

### Specialist reports (full)
#### Code Review Report
[paste full code-reviewer output]

#### Security Audit Report
[paste full security-auditor output]

#### Test Coverage Report
[paste full test-engineer output]

## Decision Rules

1. If any specialist returns a **Critical** finding — default verdict is **NO-GO**
   unless the user explicitly accepts the risk in writing.
2. The rollback plan is **mandatory** before any GO decision.
3. Resolve duplicate findings across reviewers — keep the most severe.
4. Cross-reference the security-auditor and code-reviewer security axes.
5. Skip the fan-out only if ALL of these are true: ≤2 files changed, <50 lines
   of diff, no changes to auth/payments/data-access/config/env. Otherwise run
   all three reviews regardless of diff size.

Begin with Step 1 now.
"""
    return {"text": prompt.strip()}
