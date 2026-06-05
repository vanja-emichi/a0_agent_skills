"""Ship command — fan-out pre-launch review to specialist agents.

Orchestrates code-reviewer, security-auditor, and test-engineer via
call_subordinate, then synthesizes a go/no-go decision with rollback plan.
"""


def run(payload):
    """Return the fan-out instruction for the agent to execute.

    The commands plugin calls run(payload) for script-type commands.
    The returned string becomes the agent's user message, instructing
    it to call specialist subordinates and synthesize their reports.
    """
    invocation = payload.get("invocation", {})
    raw_args = invocation.get("raw_arguments", "")
    target = " ".join(raw_args.split())[:200].lstrip('#') if raw_args else "staged changes or recent commits"

    parts = []

    parts.append("Run the pre-launch checklist via fan-out to specialist agents.\n")
    parts.append("Load `dox-project-context` using `skills_tool` before fan-out. Read the applicable AGENTS.md chain for the target, or pass the relevant DOX context to each specialist.\n")

    # Phase A
    parts.append("## Phase A — Fan-out to specialists\n")
    parts.append(
        "Use `call_subordinate` to dispatch each specialist. "
        "Issue all three calls in sequence so each report is available for synthesis.\n"
    )

    parts.append(
        f'1. **Code Review** — Call `call_subordinate` with '
        f'`profile: "code-reviewer"` and message: '
        f'"Before reviewing, read the applicable AGENTS.md chain for the target files if available, or use the DOX context supplied by the main agent. Report DOX compliance gaps separately. Conduct a six-axis code review (correctness, readability, '
        f"architecture, security, performance, DOX compliance) on {target}. "
        f'Output a structured review with Critical, Important, and Suggestion categories, '
        f'with file:line references and fix recommendations."\n'
    )

    parts.append(
        f'2. **Security Audit** — Call `call_subordinate` with '
        f'`profile: "security-auditor"` and message: '
        f'"Before reviewing, read the applicable AGENTS.md chain for the target files if available, or use the DOX context supplied by the main agent. Report DOX compliance gaps separately. Run a vulnerability and threat-model pass on {target}. '
        f'Check OWASP Top 10, secrets handling, auth/authz, dependency CVEs. '
        f'Output a structured audit report with severity ratings."\n'
    )

    parts.append(
        f'3. **Test Coverage** — Call `call_subordinate` with '
        f'`profile: "test-engineer"` and message: '
        f'"Before reviewing, read the applicable AGENTS.md chain for the target files if available, or use the DOX context supplied by the main agent. Report DOX compliance gaps separately. Analyze test coverage for {target}. '
        f'Identify gaps in happy path, edge cases, error paths, and concurrency. '
        f'Output a structured coverage analysis with gap recommendations."\n'
    )

    # Phase B
    parts.append("\n## Phase B — Synthesize\n")
    parts.append("Once all three reports are back, synthesize them:\n")
    parts.append(
        "1. **Code Quality** — Aggregate Critical/Important findings from code-reviewer "
        "and any failing tests or build output. Resolve duplicates.\n"
    )
    parts.append(
        "2. **Security** — Promote any Critical/High security-auditor findings to "
        "launch blockers. Cross-reference with code-reviewer's security axis.\n"
    )
    parts.append("3. **Performance** — Pull from code-reviewer's performance axis.\n")
    parts.append("4. **Accessibility** — Verify keyboard nav, screen reader, contrast. _Skip if not applicable (e.g., non-UI plugin)._\n")
    parts.append("5. **Infrastructure** — Env vars, migrations, monitoring, feature flags. _Skip if not applicable._\n")
    parts.append("6. **Documentation** — README, ADRs, changelog.\n")
    parts.append("7. **DOX readiness** — Applicable AGENTS.md contracts read, local contracts followed, Child DOX Indexes current, stale instructions removed.\n")

    # Phase C
    parts.append("\n## Phase C — Decision\n")
    parts.append("Produce a single output:\n")
    parts.append("""```markdown
## Ship Decision: GO | NO-GO

### Blockers (must fix before ship)
- [Source: Critical finding + file:line]

### Recommended fixes (should fix before ship)
- [Source: Important finding + file:line]

### Acknowledged risks (shipping anyway)
- [Risk + mitigation]

### Rollback plan
- Trigger conditions: [what signals would prompt rollback]
- Rollback procedure: [exact steps]
- Recovery time objective: [target]

### DOX readiness
- Contracts checked: [root and child AGENTS.md files]
- Contract gaps: [missing updates, stale indexes, verification gaps]

### Specialist reports (full)
- [code-reviewer report]
- [security-auditor report]
- [test-engineer report]
```
""")

    # Rules
    parts.append("\n## Rules\n")
    parts.append("1. Each specialist operates independently — no shared state, no cross-invocation.\n")
    parts.append("2. The rollback plan is mandatory before any GO decision.\n")
    parts.append(
        "3. If any specialist returns a Critical finding, the default verdict is NO-GO "
        "unless the user explicitly accepts the risk.\n"
    )
    parts.append(
        "4. Skip fan-out only if: change touches 2 files or fewer, diff is under 50 lines, "
        "and it does not touch auth, payments, data access, or config/env.\n"
    )

    return "".join(parts)
