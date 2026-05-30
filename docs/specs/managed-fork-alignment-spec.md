# Spec: a0_agent_skills — Managed Fork Alignment and Safe Shipping

## Objective

Bring `/a0/usr/plugins/a0_agent_skills` to a **safe-to-ship** state while moving it **closer to upstream behavior and structure** from `/a0/usr/projects/a0_agent_skills/comparison/official_agent_skills`, without losing the Agent Zero-native adaptations that make it a real plugin.

**User:**
- Primary: maintainers of the `a0_agent_skills` plugin
- Secondary: Agent Zero users who depend on consistent skill routing, commands, personas, and plugin behavior

**Why now:**
- The comparison showed the plugin is a valuable Agent Zero port, but also a deep fork with drift, a few correctness issues, inconsistent documentation/configuration, and no formal parity discipline.
- The goal is not to become a literal mirror of upstream, but to become a **well-managed Agent Zero fork** with explicit alignment rules and quality gates.

**Assumptions I’m making:**
1. The plugin should remain **Agent Zero-native**, not a generic multi-editor distribution.
2. Upstream is the behavioral reference for skills, commands, and workflow intent, unless Agent Zero requires a different implementation surface.
3. We want to preserve local-only value such as `plugin.yaml`, runtime extensions, A0 personas, A0 commands, tests, and `call_subordinate_parallel`.
4. Shipping safely means fixing correctness and consistency issues before broadening scope into structural refactors.
5. “Hooks” means either porting upstream hook behavior where it still matters, or documenting why the A0-native equivalent is different.

## Tech Stack

- **Language:** Python 3.12+
- **Plugin runtime:** Agent Zero plugin system
- **Primary code root:** `/a0/usr/plugins/a0_agent_skills`
- **Reference/upstream snapshot:** `/a0/usr/projects/a0_agent_skills/comparison/official_agent_skills`
- **Tests:** pytest
- **Comparison tooling:** shell scripts and/or Python parity tooling living in the plugin repository
- **No required new external runtime dependencies** unless a parity tool or validation step clearly justifies one

## Commands

```bash
# Inspect plugin tree
find /a0/usr/plugins/a0_agent_skills -maxdepth 4 -type f | sort

# Inspect upstream comparison tree
find /a0/usr/projects/a0_agent_skills/comparison/official_agent_skills -maxdepth 4 -type f | sort

# Run plugin tests
cd /a0/usr/plugins/a0_agent_skills && pytest tests/ -v

# Run a targeted test file
cd /a0/usr/plugins/a0_agent_skills && pytest tests/test_call_subordinate_parallel.py -v
cd /a0/usr/plugins/a0_agent_skills && pytest tests/test_skill_telemetry.py -v

# Compare relative file paths
comm -3 \
  <(find /a0/usr/plugins/a0_agent_skills -type f | sed 's#^/a0/usr/plugins/a0_agent_skills/##' | sort) \
  <(find /a0/usr/projects/a0_agent_skills/comparison/official_agent_skills -type f | sed 's#^/a0/usr/projects/a0_agent_skills/comparison/official_agent_skills/##' | sort)

# Read the generated comparison matrix if present
sed -n '1,200p' /tmp/a0_agent_skills_matrix/matrix.tsv

# Validate plugin manifest and key docs manually
sed -n '1,220p' /a0/usr/plugins/a0_agent_skills/plugin.yaml
sed -n '1,260p' /a0/usr/plugins/a0_agent_skills/README.md
```

## Project Structure

```text
plugins/a0_agent_skills/
├── plugin.yaml                                 ← plugin manifest and product metadata
├── default_config.yaml                         ← plugin defaults, especially telemetry policy
├── README.md                                   ← plugin documentation and public contract
├── hooks.py                                    ← plugin lifecycle hook surface
├── commands/
│   ├── *.command.yaml                          ← Agent Zero command registration/config
│   ├── *.txt                                   ← command prompt text
│   └── ship.py                                 ← highest-risk orchestration/sanitization logic
├── prompts/
│   └── agent.skills.routing.md                 ← routing rules injected into system prompt
├── extensions/
│   └── python/
│       ├── system_prompt/_15_agent_skills_routing.py   ← runtime prompt injection
│       └── tool_execute_after/_05_skill_telemetry.py   ← telemetry/logging
├── agents/
│   ├── code-reviewer/
│   ├── security-auditor/
│   └── test-engineer/                          ← A0 persona profiles replacing upstream markdown personas
├── skills/
│   ├── */SKILL.md                              ← shared skills adapted from upstream
│   └── */*.md                                  ← local support/checklist/reference files
├── tools/
│   └── call_subordinate_parallel.py            ← A0-native parallel fan-out tool
├── tests/
│   └── test_*.py                               ← plugin verification and regression tests
└── scripts/                                    ← NEW: parity/validation tooling to add

comparison/official_agent_skills/
├── skills/                                     ← upstream reference behavior and wording
├── hooks/                                      ← upstream hook scripts and docs
├── references/                                 ← upstream central checklist/reference files
├── agents/*.md                                 ← upstream markdown personas
├── .claude/, .gemini/, .claude-plugin/         ← upstream editor/platform integrations
├── docs/                                       ← upstream setup and contribution docs
├── scripts/validate-skills.js                  ← upstream validation utility
└── .github/workflows/                          ← upstream CI examples
```

## Code Style

Follow existing Agent Zero plugin conventions and prefer minimal, explicit fixes over broad rewrites.

```python
# Good: explicit, narrowly scoped, and testable
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f]")


def _strip_control_chars(text: str) -> str:
    return _CONTROL_CHARS_RE.sub("", text)


def _sanitize_scope(scope: str) -> str:
    scope = _strip_control_chars(scope)
    scope = re.sub(r"^#{1,6}\s*", "", scope, flags=re.MULTILINE)
    scope = re.sub(r"[\"'`]", "", scope)
    return scope[:500].strip()
```

**Key conventions:**
- Prefer small, reviewable patches over repo-wide rewrites.
- Keep A0-specific behavior explicit and documented.
- If behavior intentionally diverges from upstream, document the reason near the code or in parity docs.
- Avoid stale product claims in `README.md`, `plugin.yaml`, and command metadata.
- Prefer deterministic shell or pytest-based verification over narrative claims.

## Testing Strategy

**Framework:** pytest

**Test roots:**
- `/a0/usr/plugins/a0_agent_skills/tests/`

### Test levels

1. **Regression tests for ship-safety fixes**
   - Sanitization preserves valid hyphenated text
   - Actual control characters are removed
   - `/ship` orchestration mode is tested as the intended contract
   - Telemetry default behavior is tested against docs/config expectations

2. **Documentation/config consistency tests**
   - README skill count matches actual skill directory count
   - README telemetry default matches `default_config.yaml` and runtime extension logic
   - README `/ship` behavior matches `commands/ship.py` and `ship.command.yaml`

3. **Parity tests/reports**
   - Shared file path inventory against upstream snapshot
   - Shared file drift report for `skills/*/SKILL.md`
   - Upstream-only omitted assets listed and classified as:
     - intentionally omitted
     - port later
     - not applicable in Agent Zero

4. **Existing plugin tests remain green**
   - Current test suite continues to pass after changes
   - New parity tooling must not break normal plugin operation

## Boundaries

### Always do
- Fix correctness and contract mismatches before structural refactors.
- Keep Agent Zero-native surfaces (`plugin.yaml`, `commands/`, `agents/`, `extensions/`, `tools/`, `tests/`) intact unless there is a compelling reason to change them.
- Preserve or improve test coverage when changing shipping, routing, telemetry, or parity logic.
- Document intentional divergence from upstream.
- Verify behavior with file rereads and pytest before claiming success.

### Ask first
- Adding new third-party dependencies
- Removing existing A0-native features like `call_subordinate_parallel`
- Replacing parallel `/ship` with sequential `/ship` or vice versa if that changes the product contract
- Reintroducing upstream hook behavior in a way that alters runtime side effects
- Large-scale rewrites of all skill bodies to reduce drift

### Never do
- Claim parity without a reproducible comparison report
- Remove tests to make the suite pass
- Rewrite upstream and local skill content wholesale without a clear alignment strategy
- Treat editor-specific upstream assets as mandatory one-to-one ports if Agent Zero requires a different surface
- Ship contradictory behavior across code, docs, and config

## Alignment Strategy

The plugin will be treated as a **managed fork**.

### Managed fork rules
1. **Upstream is the semantic reference** for skill/workflow intent.
2. **Agent Zero is the runtime reference** for implementation surface.
3. Local-only A0 assets are allowed and expected, but they must remain aligned with upstream intent where practical.
4. Shared skills should stay as close to upstream as practical, with A0-specific additions minimized and clearly scoped.
5. Drift must be measured, not guessed.

### Target alignment areas
- **Skills:** align shared skill behavior and wording where possible; minimize unnecessary local prose rewrites
- **Commands:** ensure A0 command behavior matches the upstream workflow intent, even if command file formats differ
- **Hooks:** inspect upstream `hooks/` and decide which behaviors need an A0-native equivalent, which are obsolete, and which are intentionally omitted
- **Docs:** align plugin README and metadata to actual runtime behavior and actual repository contents
- **Parity process:** create repeatable comparison tooling and checklist discipline

## Success Criteria

### Ship-safety
- `commands/ship.py` sanitization bug is fixed and regression-tested
- `/ship` behavior is consistent across implementation, command config, and README
- Telemetry defaults are consistent across config, code, tests, and docs
- Product metadata such as skill counts match actual repository contents

### Upstream alignment
- A documented mapping exists from upstream surfaces to Agent Zero surfaces:
  - personas
  - commands
  - references/checklists
  - hooks
- Shared skills are reviewed and classified into:
  - already acceptably aligned
  - needs wording/behavior alignment
  - intentional divergence
- A decision is recorded for each upstream-only hook/reference asset:
  - port
  - replace with A0-native equivalent
  - intentionally omit

### Managed-fork discipline
- A parity report tool exists in the plugin repository
- A parity-oriented test or validation step exists and is runnable locally
- README explicitly states that the plugin is an Agent Zero-specific managed fork/port of upstream
- Future maintainers can identify drift quickly without repeating this whole analysis manually

## Proposed Work Phases

### Phase 1 — Ship-safety corrections
- Fix `ship.py` sanitization
- Resolve `/ship` contract mismatch
- Resolve telemetry default mismatch
- Correct stale metadata/documentation claims
- Add regression tests for all of the above

### Phase 2 — Upstream alignment pass
- Review shared `skills/*/SKILL.md` changes against upstream
- Reduce unnecessary divergence where low-risk
- Produce a command/persona/reference mapping doc
- Review upstream `hooks/` and define A0-native hook alignment policy

### Phase 3 — Parity process discipline
- Add `scripts/` parity tooling
- Add tests/validation for documented drift and repo-claim consistency
- Document fork policy and update maintenance instructions

## Approved Decisions

1. `/ship` remains **parallel fan-out** as the permanent contract.
2. Telemetry remains **on by default** for workflow observability.
3. For upstream `hooks/`, we use **selective porting + documented omission**:
   - port behaviors that still matter in Agent Zero,
   - replace some with A0-native equivalents where appropriate,
   - explicitly document intentional omissions.
4. We build **parity/reporting machinery first**, then reduce drift incrementally.
5. Parity tooling begins as **report-only**, then becomes enforceable once the fork policy stabilizes.
