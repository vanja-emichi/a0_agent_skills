---
name: doubt-driven-development
description: Subjects every non-trivial decision to a fresh-context adversarial review before it stands. Use when correctness matters more than speed, when working in unfamiliar code, when stakes are high (production, security-sensitive logic, irreversible operations), or any time a confident output would be cheaper to verify now than to debug later.
triggers:
  - "adversarial review"
  - "challenge decision"
  - "second opinion"
  - "doubt driven"
  - "stress test decision"
---

# Doubt-Driven Development

## Overview

A confident answer is not a correct one. Long sessions accumulate context that quietly turns assumptions into "facts" without anyone noticing. Doubt-driven development is the discipline of materializing a fresh-context reviewer — biased to **disprove**, not approve — before any non-trivial output stands.

This is not the `review` command. The review command is a verdict on a finished artifact. This is an in-flight posture: non-trivial decisions get cross-examined while course-correction is still cheap.

## When to Use

A decision is **non-trivial** when at least one of these is true:

- It introduces or modifies branching logic
- It crosses a module or service boundary
- It asserts a property the type system or compiler cannot verify (thread safety, idempotence, ordering, invariants)
- Its correctness depends on context the future reader cannot see
- Its blast radius is irreversible (production deploy, data migration, public API change)

Apply the skill when:

- About to make an architectural decision under uncertainty
- About to commit non-trivial code
- About to claim a non-obvious fact ("this is safe", "this scales", "this matches the spec")
- Working in code you don't fully understand

**Related:**

- Use `skills_tool` with action: load, skill_name: "code-review-and-quality" for post-hoc PR review (doubt-driven is complementary, in-flight)
- Use `skills_tool` with action: load, skill_name: "test-driven-development" whose RED step serves as doubt for behavioral claims
- Use `skills_tool` with action: load, skill_name: "source-driven-development" for verifying framework facts against official docs

**When NOT to use:**

- Mechanical operations (renaming, formatting, file moves)
- Following a clear, unambiguous user instruction
- Reading or summarizing existing code
- One-line changes with obvious correctness
- Pure tooling operations (running tests, listing files)
- The user has explicitly asked for speed over verification

If you doubt every keystroke, you ship nothing. The skill applies only to non-trivial decisions as defined above.

## Loading Constraints

This skill is designed for the **main-session orchestrator**, where Step 3 (DOUBT, detailed below) can spawn a fresh-context reviewer.

- **Do NOT add this skill to a subordinate agent profile.** A subordinate that follows Step 3 would spawn another subordinate — the orchestration anti-pattern ("personas do not invoke other personas").
- **If you find yourself applying this skill from inside a subordinate context:** the preferred path is to surface to the user that doubt-driven cannot run nested and let the main session handle it. As a last resort only, a degraded self-questioning fallback exists — rewrite ARTIFACT + CONTRACT as a fresh self-prompt with a hard mental separator from your prior reasoning, and walk Steps 1–5. This is **not fresh-context review** (you carry your own context with you), so flag the result as degraded and prefer escalation whenever the user is reachable.

## The Process

Copy this checklist when applying the skill:

```
Doubt cycle:
- [ ] Step 1: CLAIM — wrote the claim + why-it-matters
- [ ] Step 2: EXTRACT — isolated artifact + contract, stripped reasoning
- [ ] Step 3: DOUBT — invoked fresh-context reviewer with adversarial prompt
- [ ] Step 4: RECONCILE — classified every finding against the artifact text
- [ ] Step 5: STOP — met stop condition (trivial findings, 3 cycles, or user override)
```

### Step 1: CLAIM — Surface what stands

Name the decision in two or three lines:

```
CLAIM: "The new caching layer is thread-safe under the
        read-heavy workload described in the spec."
WHY THIS MATTERS: a race here corrupts user data and is
                  hard to detect in QA.
```

If you can't write the claim that compactly, you have a vibe, not a decision. Surface it before scrutinizing it.

### Step 2: EXTRACT — Smallest reviewable unit

A fresh-context reviewer needs the **artifact** and the **contract**, not the journey.

- Code: the diff or the function — not the whole file
- Decision: the proposal in 3–5 sentences plus the constraints it has to satisfy
- Assertion: the claim plus the evidence that supposedly supports it (kept distinct from the Step 1 CLAIM block, which is the orchestrator's hypothesis under scrutiny)

Strip your reasoning. If you hand over conclusions, you'll get back validation of your conclusions. The unit must be small enough that a reviewer can hold it in mind in one read — if it's a 500-line PR, decompose first.

### Step 3: DOUBT — Invoke the fresh-context reviewer

The reviewer's prompt **must be adversarial**. Framing decides the answer.

```
Adversarial review. Find what is wrong with this artifact.
Assume the author is overconfident. Look for:
- Unstated assumptions
- Edge cases not handled
- Hidden coupling or shared state
- Ways the contract could be violated
- Existing conventions this might break
- Failure modes under unexpected input

Do NOT validate. Do NOT summarize. Find issues, or state
explicitly that you cannot find any after thorough examination.

ARTIFACT: <paste artifact>
CONTRACT: <paste contract>
```

**Pass ARTIFACT + CONTRACT only. Do NOT pass the CLAIM.** Handing the reviewer your conclusion biases it toward agreement. The reviewer must independently determine whether the artifact satisfies the contract.

Use `call_subordinate` to invoke a fresh-context reviewer. Available profiles suitable for doubt review:

- `call_subordinate` with `profile: "code-reviewer"` — for code artifacts
- `call_subordinate` with `profile: "security-auditor"` — for security-sensitive artifacts
- `call_subordinate` with `profile: "test-engineer"` — for test correctness claims
- `call_subordinate` with `profile: "researcher"` — for factual/architectural claims
- `call_subordinate` without profile — generic fresh-context reviewer with just the adversarial prompt

**The adversarial prompt above takes precedence over the profile's default response shape.** Profiles like `code-reviewer` are written to produce balanced verdicts; doubt-driven needs issues-only output. Paste the adversarial prompt verbatim in the `message` parameter so it overrides the profile's default. If a profile's response shape can't be overridden cleanly, fall back to a generic subordinate with the adversarial prompt.

#### Cross-model escalation

A single-model reviewer shares blind spots with the original author — a different model catches them. Doubt-driven is already opt-in for non-trivial decisions, so within that scope offering cross-model is part of the skill's value, not optional friction.

**Interactive sessions: always offer. Never silently skip.**

**Step 1: Ask the user**

After the single-model review in Step 3 above, but before RECONCILE, pause and ask via the `response` tool:

> *"Single-model review complete. Want a cross-model second opinion? Options: run an external CLI tool via `code_execution_tool` (you specify which), manual external review (you paste it elsewhere), or skip."*

This question is mandatory in every interactive doubt cycle — even on artifacts that feel low-stakes. The user — not the agent — decides whether the cost is worth it. The agent's job is to surface the choice.

**Step 2: If the user picks an external CLI — verify, then invoke**

1. Use `code_execution_tool` with `runtime=terminal` to check the tool is in PATH (`which <tool_name>`).
2. Test it works (`<tool_name> --version` or equivalent) before passing the full prompt — a stale or broken binary may pass `which` but fail on real input.
3. Confirm the exact invocation with the user via the `response` tool, including required flags, auth, and env vars (e.g., API keys). Implementations vary; never assume.
4. Pass ARTIFACT + CONTRACT + the adversarial prompt **only**. No session context, no CLAIM.
5. Mind shell escaping. If the artifact contains quotes, `$(...)`, or backticks, write the full prompt to a temp file via `text_editor write` and pipe it through stdin. Never interpolate the artifact into a shell-quoted argument.
6. Take the output into Step 4 (RECONCILE).

**Never interpolate the artifact into a shell-quoted argument.** Code, markdown, and review prompts routinely contain backticks, `$(...)`, and quote characters that will either truncate the prompt or execute embedded shell. Use `text_editor write` to write the full prompt to a temp file and pipe it via stdin.

Example invocation shape (verify flags against your installed tool — syntax differs across implementations and versions):

```bash
# Write the adversarial prompt + ARTIFACT + CONTRACT to a temp file first.
# Then pipe via stdin so shell metacharacters in the artifact stay inert.
```

**Concrete CLI tool examples** (use `code_execution_tool` with `runtime=terminal` for all):

> **Note:** These are optional external CLI tools that must be installed separately — they are not bundled with Agent Zero or this plugin. Use whichever your environment provides, or skip cross-model review if none are available.

| CLI Tool | Invocation Pattern | Notes |
|----------|-------------------|-------|
| `codex` | `codex "$(cat /tmp/doubt-prompt.md)"` | OpenAI Codex CLI — check `codex --help` for read-only flags |
| `gemini` | `gemini -p "$(cat /tmp/doubt-prompt.md)"` | Google Gemini CLI — verify sandbox mode availability |
| `claude` | `claude -p "$(cat /tmp/doubt-prompt.md)"` | Anthropic Claude CLI — use `--no-tools` or equivalent read-only flag |
| `aider` | `aider --message "$(cat /tmp/doubt-prompt.md)" --file /tmp/doubt-prompt.md` | Aider — may require `--no-auto-commits` and a temp git repo |

**Why cross-model?** Different models have different training data, alignment post-processing, and inference behaviors. A conclusion that one model rubber-stamps, another may challenge — not because one is smarter, but because they have different blind spots and framing biases. Cross-model review is a diversity hedge, not a quality ladder.

**Full example using `code_execution_tool`:**

```
Step 1: Write the adversarial prompt to a temp file
  → text_editor action=write, path=/tmp/doubt-prompt.md, content=<adversarial prompt + ARTIFACT + CONTRACT>

Step 2: Verify the external tool exists
  → code_execution_tool runtime=terminal, code=

**Step 3: If the CLI is unavailable or fails**

Surface the failure explicitly via the `response` tool. Offer: run it manually, try a different tool, or skip. Do not silently fall back to single-model — the user should know cross-model didn't happen.

**Step 4: If the user skips**

Acknowledge the skip in the output (*"Proceeding with single-model findings only"*) and continue to RECONCILE. Skipping is fine; silent skipping is not.

**Non-interactive contexts** (scheduled runs, autonomous mode):

- Cross-model is **skipped**, and the skip must be **announced** in the output: *"Cross-model skipped: non-interactive context."*
- **Never invoke an external CLI without explicit user authorization** — this is a load-bearing safety property.

Cross-model adds cost, latency, and tool fragility. The agent surfaces the choice every cycle; the user decides whether this artifact warrants it.

### Step 4: RECONCILE — Fold findings back

The reviewer's output is data, not verdict. **You are still the orchestrator.** Re-read the artifact text against each finding before classifying — rubber-stamping the reviewer is the same failure mode as ignoring it.

For each finding, classify in this **precedence order** (first matching class wins):

1. **Contract misread** — reviewer flagged something specifically because the CONTRACT you provided was unclear or incomplete. Fix the contract first, re-classify on the next cycle.
2. **Valid + actionable** — real issue requiring a change to the artifact. Change it, re-loop.
3. **Valid trade-off** — issue is real but cost of fixing exceeds cost of accepting. Document the trade-off explicitly so the user sees it.
4. **Noise** — reviewer flagged something that's actually correct under context the reviewer didn't have. Note it, move on, and ask: would adding that context to the contract have prevented the false flag?

A fresh reviewer can be wrong because it lacks context. Don't defer just because it's "fresh."

### Step 5: STOP — Bounded loop, not recursion

Stop when:

- Next iteration returns only trivial or already-considered findings, **or**
- 3 cycles completed (escalate to user, don't grind a fourth alone), **or**
- User explicitly says "ship it"

If after 3 cycles the reviewer still surfaces substantive issues, the artifact may not be ready. Surface this to the user — three unresolved cycles is information about the artifact, not a reason to keep looping.

If 3 cycles is "obviously insufficient" because the artifact is large: the artifact is too big — return to Step 2 and decompose. Do not lift the bound.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "I'm confident, skip the doubt step" | Confidence correlates poorly with correctness on novel problems. Moments of certainty are exactly when blind spots hide. |
| "Spawning a reviewer is expensive" | Debugging a wrong commit in production is more expensive. The check is bounded; the bug isn't. |
| "The reviewer will just nitpick" | Only if unscoped. Constrain the prompt to "issues that would make this fail under the contract." |
| "I'll do doubt at the end with the review command" | The review command is a final gate. Doubt-driven catches wrong directions early when course-correction is cheap. By PR time it's too late. |
| "If I doubt every step I'll never ship" | The skill applies to non-trivial decisions, not every keystroke. Re-read "When NOT to Use." |
| "Two opinions are always better than one" | Not when the second has less context and produces noise. Reconcile, don't defer. |
| "The reviewer disagreed so I was wrong" | The reviewer lacks your context — disagreement is information, not verdict. Re-read the artifact, classify, then decide. |
| "Cross-model is always better" | Cross-model catches blind spots a single model shares with itself, but it adds cost and tool fragility. Offer it every interactive doubt cycle — the user decides whether the artifact warrants it. The agent's job is to surface the choice, not to gate it. |
| "User said yes once, so I can keep invoking the CLI" | Each invocation is its own authorization. The artifact, the prompt, and the flags change between calls — re-confirm the exact command with the user before every run. |

## Red Flags

- Spawning a fresh-context reviewer for a one-line rename or formatting change
- Treating reviewer output as authoritative without re-reading the artifact text
- Looping >3 cycles without escalating to the user
- Prompting the reviewer with "is this good?" instead of "find issues"
- Skipping doubt under time pressure on a high-stakes decision
- Re-spawning fresh-context on an unchanged artifact (you'll get the same findings; you're stalling)
- **Doubt theater (checkable signal)**: across 2 or more cycles where the reviewer surfaced substantive findings, zero findings were classified as actionable. You are validating, not doubting. Stop and escalate.
- Doubting only after committing — that's the review command, not doubt-driven development
- Hardcoding an external CLI invocation without confirming with the user that the tool exists, is configured, and accepts that exact syntax
- **Silently skipping cross-model in an interactive doubt cycle.** Even when not recommending it, the offer must be visible. Skipping is fine; silent skipping is not.
- Falling back silently when an external CLI errors or is missing — surface the failure and let the user redirect
- Stripping the contract from the reviewer's input
- Passing the CLAIM to the reviewer (biases toward agreement)

## Interaction with Other Skills

- **Code review / review command** (use `skills_tool` with action: load, skill_name: "code-review-and-quality"): complementary. The review command is post-hoc PR verdict; doubt-driven is in-flight per-decision. Use both.
- **Source-driven development** (use `skills_tool` with action: load, skill_name: "source-driven-development"): SDD verifies *facts about frameworks* against official docs. Doubt-driven verifies *your reasoning about the artifact*. SDD checks the API exists; doubt-driven checks you used it correctly under the contract.
- **Test-driven development** (use `skills_tool` with action: load, skill_name: "test-driven-development"): TDD's RED step is doubt made concrete — a failing test is a disproof attempt. When TDD applies, that failing test *is* the doubt step for behavioral claims.
- **Debugging and error recovery** (use `skills_tool` with action: load, skill_name: "debugging-and-error-recovery"): when the reviewer surfaces a real failure mode, use `skills_tool` with `action: load, skill_name: "debugging-and-error-recovery"` to localize and fix.
- **Repo orchestration rules**: use `skills_tool` with `action: read_file, skill_name: "using-agent-skills", file_path: "references/orchestration-patterns.md"` — this skill orchestrates from the main session. A subordinate calling another subordinate is anti-pattern — see Loading Constraints above.

## Verification

After applying doubt-driven development:

- [ ] Every non-trivial decision (per the definition above) was named explicitly as a CLAIM before standing
- [ ] At least one fresh-context review per non-trivial artifact (a failing test produced by TDD's RED step satisfies this for behavioral claims, per Interaction with Other Skills)
- [ ] The reviewer received ARTIFACT + CONTRACT — NOT the CLAIM, NOT your reasoning
- [ ] The reviewer's prompt was adversarial ("find issues"), not validating ("is it good")
- [ ] Findings were classified against the artifact text (not rubber-stamped) using the precedence: contract misread / actionable / trade-off / noise
- [ ] A stop condition was met (trivial findings, 3 cycles, or user override)
- [ ] In interactive mode, cross-model was **explicitly offered** to the user (regardless of artifact stakes) and the response was acknowledged in the output
- [ ] In non-interactive mode, cross-model was skipped and the skip was announced
- [ ] Any external CLI invocation was preceded by a PATH check, a working-binary test, syntax confirmation with the user, and explicit authorization to run

## Files

(use `skills_tool` action `read_file` to open)

- `SKILL.md` — This skill file
- `evals/evals.json` — Behavioral evaluations
