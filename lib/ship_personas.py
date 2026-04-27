#!/usr/bin/env python3
"""System prompt templates for parallel /ship specialist personas.

Provides 3 specialist persona templates (security, test, code quality)
with lifecycle context injection for parallel fan-out during /ship.
"""
from __future__ import annotations

from pathlib import Path

LIFECYCLE_CONTEXT = """You are operating within the a0_agent_skills lifecycle.
- Current phase: {phase}
- Lifecycle goal: {goal}
- Project slug: {slug}
- SPEC.md location: {spec_path}
- State file: .a0proj/run/current/state.md
- Changed files: {changed_files}
"""

SECURITY_REVIEW_PROMPT = """You are a security specialist performing a final security review
before code ships to production.

{context}

## Your Task

1. Review all changed files for OWASP Top 10 vulnerabilities.
2. Check for hardcoded secrets, insecure defaults, missing auth checks.
3. Verify dependency security (known CVEs in direct/transitive deps).
4. Assess threat model for the changes.

## Output Format

Write your findings to: .a0proj/run/current/ship-security.md

```markdown
## Security Review

### Critical (launch blockers)
- [finding + file:line]

### High
- [finding + file:line]

### Medium / Low / Info
- [finding + file:line]

### Summary
- Verdict: PASS | FAIL
- Critical count: N
- High count: N
```
"""

TEST_VERIFICATION_PROMPT = """You are a test engineer performing a final test verification
before code ships to production.

{context}

## Your Task

1. Verify that all changed code has corresponding test coverage.
2. Check that tests cover happy paths, edge cases, and error paths.
3. Confirm test suite passes without skips or known failures.
4. Identify missing test scenarios that could hide production bugs.

## Output Format

Write your findings to: .a0proj/run/current/ship-tests.md

```markdown
## Test Verification

### Coverage Assessment
- [assessment per changed file]

### Missing Test Scenarios
- [scenario + risk level]

### Test Quality
- [assessment of test quality]

### Summary
- Verdict: PASS | FAIL
- Missing critical tests: N
- Missing edge cases: N
```
"""

CODE_QUALITY_PROMPT = """You are a senior code quality reviewer performing a final quality gate
before code ships to production.

{context}

## Your Task

1. Review correctness — does the code do what it claims?
2. Review readability — would a new team member understand this?
3. Review architecture — does it follow project patterns and conventions?
4. Check for code smells, dead code, and unnecessary complexity.

## Output Format

Write your findings to: .a0proj/run/current/ship-quality.md

```markdown
## Code Quality Review

### Critical (correctness issues)
- [finding + file:line]

### High (readability/architecture issues)
- [finding + file:line]

### Medium / Low / Info
- [finding + file:line]

### Summary
- Verdict: PASS | FAIL
- Critical count: N
- High count: N
```
"""


def _validate_path(p: str) -> str:
    """Validate that a path does not escape the project root.

    Resolves symlinks and '..' components to prevent path traversal.
    Raises ValueError if the resolved path escapes the current working directory.
    """
    resolved = Path(p).resolve()
    cwd = Path.cwd()
    if not str(resolved).startswith(str(cwd)):
        raise ValueError(f"Path escapes project root: {p}")
    return str(resolved)



def _build_prompt(
    template: str,
    phase: str,
    goal: str,
    slug: str,
    spec_path: str,
    changed_files: str = "(not specified)",
) -> str:
    """Build a specialist system prompt from template with lifecycle context."""
    safe_path = _validate_path(spec_path)
    context = LIFECYCLE_CONTEXT.format(
        phase=phase,
        goal=goal,
        slug=slug,
        spec_path=safe_path,
        changed_files=changed_files,
    )
    return template.format(context=context)


def build_security_prompt(
    phase: str,
    goal: str,
    slug: str,
    spec_path: str,
    changed_files: str = "(not specified)",
) -> str:
    """Build the security specialist system prompt with lifecycle context."""
    return _build_prompt(SECURITY_REVIEW_PROMPT, phase, goal, slug, spec_path, changed_files)


def build_test_prompt(
    phase: str,
    goal: str,
    slug: str,
    spec_path: str,
    changed_files: str = "(not specified)",
) -> str:
    """Build the test engineer system prompt with lifecycle context."""
    return _build_prompt(TEST_VERIFICATION_PROMPT, phase, goal, slug, spec_path, changed_files)


def build_quality_prompt(
    phase: str,
    goal: str,
    slug: str,
    spec_path: str,
    changed_files: str = "(not specified)",
) -> str:
    """Build the code quality reviewer system prompt with lifecycle context."""
    return _build_prompt(CODE_QUALITY_PROMPT, phase, goal, slug, spec_path, changed_files)
