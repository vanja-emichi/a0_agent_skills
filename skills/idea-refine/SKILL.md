---
name: idea-refine
version: 1.0.0
author: addyosmani (ported to Agent Zero by a0_agent_skills)
description: >-
  Refines raw ideas into sharp, actionable concepts through structured divergent
  and convergent thinking. Use when starting from a vague idea, brainstorming a
  new feature, exploring design space, or stress-testing a plan before committing.
  Trigger phrases: "ideate", "refine this idea", "stress-test my plan", "ideate on".
tags:
  - ideation
  - planning
  - brainstorming
  - design
  - creativity
trigger_patterns:
  - idea-refine
  - ideate
  - refine this idea
  - stress-test my plan
  - ideate on
  - help me refine
  - brainstorm
  - explore idea
  - sharpen my idea
  - what should i build
---

# Idea Refine

Refines raw ideas into sharp, actionable concepts worth building through structured
divergent and convergent thinking.

> **Supporting files:** After loading this skill, the file tree above shows the skill
> directory path. Use `text_editor:read` (not `skills_tool:read_file`) to open supporting
> files: `frameworks.md`, `refinement-criteria.md`, and `examples.md`. Replace
> `{skill_path}` below with the path shown in the file tree.

## Overview

Refines raw ideas into sharp, actionable concepts worth building through structured
divergent and convergent thinking.

## When to Use

- Starting from a vague idea or gut feeling
- Brainstorming a new feature, product, or process improvement
- Exploring design space before writing a spec
- Stress-testing a plan before committing resources
- When "I want to build X" needs to become "Here is what X actually is and why"

**When NOT to use:** You already have a clear spec with acceptance criteria. Use
`spec-driven-development` instead.

## How It Works

1.  **Understand & Expand (Divergent):** Restate the idea, ask sharpening questions, and generate variations.
2.  **Evaluate & Converge:** Cluster ideas, stress-test them, and surface hidden assumptions.
3.  **Sharpen & Ship:** Produce a concrete markdown one-pager moving work forward.

### Philosophy

- Simplicity is the ultimate sophistication. Push toward the simplest version that still solves the real problem.
- Start with the user experience, work backwards to technology.
- Say no to 1,000 things. Focus beats breadth.
- Challenge every assumption. "How it's usually done" is not a reason.
- Show people the future — don't just give them better horses.
- The parts you can't see should be as beautiful as the parts you can.

## Setup

To initialize the ideas output directory, run the setup script using `code_execution_tool`:

```bash
# The skill path is shown in the file tree when this skill is loaded.
# Replace <skill_path> with the actual path shown above.
bash <skill_path>/scripts/idea-refine.sh
```

This creates `docs/ideas/` in the current working directory if it doesn't exist.

## Output

The final output is a markdown one-pager saved to `docs/ideas/[idea-name].md`
(after user confirmation), containing:

- Problem Statement
- Recommended Direction
- Key Assumptions
- MVP Scope
- Not Doing list

## Process

This skill is primarily an interactive dialogue. When the user invokes this skill
with an idea (from their message), guide them through three phases. Adapt your
approach based on what they say — this is a conversation, not a template.

### Phase 1: Understand & Expand (Divergent)

**Goal:** Take the raw idea and open it up.

1. **Restate the idea** as a crisp "How Might We" problem statement. This forces
   clarity on what's actually being solved.

2. **Ask 3–5 sharpening questions** — no more. Focus on:
   - Who is this for, specifically?
   - What does success look like?
   - What are the real constraints (time, tech, resources)?
   - What's been tried before?
   - Why now?

   Ask these in your response as natural questions. Do NOT proceed until you
   understand who this is for and what success looks like.

3. **Generate 5–8 idea variations** using these lenses:
   - **Inversion:** "What if we did the opposite?"
   - **Constraint removal:** "What if budget/time/tech weren't factors?"
   - **Audience shift:** "What if this were for [different user]?"
   - **Combination:** "What if we merged this with [adjacent idea]?"
   - **Simplification:** "What's the version that's 10x simpler?"
   - **10x version:** "What would this look like at massive scale?"
   - **Expert lens:** "What would [domain] experts find obvious that outsiders wouldn't?"

   Push beyond what the user initially asked for. Create products people don't
   know they need yet.

   Read the file `frameworks.md` from this skill directory (path shown in loaded
   skill file tree above) using `text_editor:read` for additional ideation
   frameworks. Use them selectively — pick the lens that fits the idea, don't
   run every framework mechanically.

**If running inside a project/codebase:** Use `code_execution_tool` with `find`
and `grep` commands to scan for relevant context — existing architecture,
patterns, constraints, prior art. Use `text_editor:read` to inspect specific
files. Ground your variations in what actually exists.

### Phase 2: Evaluate & Converge

After the user reacts to Phase 1 (indicates which ideas resonate, pushes back,
adds context), shift to convergent mode:

1. **Cluster** the ideas that resonated into 2–3 distinct directions. Each
   direction should feel meaningfully different, not just variations on a theme.

2. **Stress-test** each direction against three criteria:
   - **User value:** Who benefits and how much? Is this a painkiller or a vitamin?
   - **Feasibility:** What's the technical and resource cost? What's the hardest part?
   - **Differentiation:** What makes this genuinely different? Would someone switch
     from their current solution?

   Read `refinement-criteria.md` from this skill directory (path from file tree,
   use `text_editor:read`) for the full evaluation rubric.

3. **Surface hidden assumptions.** For each direction, explicitly name:
   - What you're betting is true (but haven't validated)
   - What could kill this idea
   - What you're choosing to ignore (and why that's okay for now)

   This is where most ideation fails. Don't skip it.

**Be honest, not supportive.** If an idea is weak, say so with kindness. A good
ideation partner is not a yes-machine. Push back on complexity, question real
value, and point out when the emperor has no clothes.

### Phase 3: Sharpen & Ship

Produce a concrete artifact — a markdown one-pager that moves work forward:

```markdown
# [Idea Name]

## Problem Statement
[One-sentence "How Might We" framing]

## Recommended Direction
[The chosen direction and why — 2–3 paragraphs max]

## Key Assumptions to Validate
- [ ] [Assumption 1 — how to test it]
- [ ] [Assumption 2 — how to test it]
- [ ] [Assumption 3 — how to test it]

## MVP Scope
[The minimum version that tests the core assumption. What's in, what's out.]

## Not Doing (and Why)
- [Thing 1] — [reason]
- [Thing 2] — [reason]
- [Thing 3] — [reason]

## Open Questions
- [Question that needs answering before building]
```

**The "Not Doing" list is arguably the most valuable part.** Focus is about
saying no to good ideas. Make the trade-offs explicit.

Read `examples.md` from this skill directory (path from file tree, use
`text_editor:read`) for examples of what great ideation sessions look like.

Ask the user if they'd like to save this to `docs/ideas/[idea-name].md` (or a
location of their choosing). Use `code_execution_tool` to create the file.
Only save if they confirm.

### Tone

Direct, thoughtful, slightly provocative. You're a sharp thinking partner, not
a facilitator reading from a script. Channel the energy of "that's interesting,
but what if..." — always pushing one step further without being exhausting.

## Anti-Patterns to Avoid

- **MUST NOT generate 20+ ideas.** Quality over quantity. 5–8 well-considered
  variations beat 20 shallow ones.
- **MUST NOT be a yes-machine.** Push back on weak ideas with specificity and kindness.
- **MUST NOT skip "who is this for."** Every good idea starts with a person and
  their problem.
- **MUST NOT produce a plan without surfacing assumptions.** Untested assumptions
  are the #1 killer of good ideas.
- **MUST NOT over-engineer the process.** Three phases, each doing one thing well.
  Resist adding steps.
- **MUST NOT just list ideas — tell a story.** Each variation MUST have a reason
  it exists, not just be a bullet point.
- **MUST NOT ignore the codebase.** If you're in a project, the existing architecture
  is a constraint and an opportunity. Use `code_execution_tool` to scan it.
- **MUST NOT jump to Phase 3** without running Phases 1 and 2.

## Red Flags

- Generating 20+ shallow variations instead of 5–8 considered ones
- Skipping the "who is this for" question
- No assumptions surfaced before committing to a direction
- Yes-machining weak ideas instead of pushing back with specificity
- Producing a plan without a "Not Doing" list
- Ignoring existing codebase constraints when ideating inside a project

## Verification

After completing an ideation session:

- [ ] A clear "How Might We" problem statement exists
- [ ] The target user and success criteria are defined
- [ ] Multiple directions were explored, not just the first idea
- [ ] Hidden assumptions are explicitly listed with validation strategies
- [ ] A "Not Doing" list makes trade-offs explicit
- [ ] The output is a concrete artifact (markdown one-pager), not just conversation
- [ ] The user confirmed the final direction before any implementation work
