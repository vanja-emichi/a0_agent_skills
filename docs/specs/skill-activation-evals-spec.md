# Spec: Skill Activation Evals

## Objective

Create a test harness and eval fixture suite that measures whether the plugin's enforcement gate correctly maps user intents to the right skills. Given a natural-language intent like "fix this bug", the eval asserts that `debugging-and-error-recovery` is the top candidate returned by `skill_match`.

**User:** Plugin developers and maintainers who need confidence that the 23-skill registry is correctly wired to user intents.

**Success criteria:**
- Eval suite with ≥30 test cases covering all 23 skills (at least 1 per skill)
- Near-miss cases where two skills could plausibly match
- Pass rate ≥90% on prefilter accuracy (skill_match returns correct skill as candidate)
- CI-runnable via `pytest`
- Results report showing per-skill accuracy, confusion matrix, and failure examples

## Tech Stack

- Python 3.11+ (matches Agent Zero runtime)
- pytest (already in the project)
- Existing helpers: `skill_match.py`, `skill_contracts.py`, `phase_governance.py`

## Commands

```bash
# Run the full eval suite
python -m pytest tests/test_skill_activation_evals.py -v

# Run with detailed report
python -m pytest tests/test_skill_activation_evals.py -v --tb=long -k "eval"

# Run for a specific skill
python -m pytest tests/test_skill_activation_evals.py -v -k "debugging"
```

## Project Structure

```
tests/
  eval_fixtures/
    skill-activation-evals.json    # NEW: eval fixture data
  test_skill_activation_evals.py  # NEW: eval test runner
helpers/
  skill_match.py                  # Existing: target of evaluation
```

## Code Style

Follow existing test conventions in the project:
- `pytest` class-based tests with descriptive `test_` method names
- Fixture data loaded from JSON files in `eval_fixtures/`
- Assertions use plain `assert` with descriptive messages
- Each test case is a standalone scenario (no shared mutable state)

## Testing Strategy

The eval suite tests two levels:

### Level 1: Prefilter Accuracy (skill_match)

Given a natural-language intent, does `skill_match.search_skills()` return the correct skill as a candidate?

This tests the existing `search_skills()` function in `helpers/skill_match.py` which searches skill descriptions, tags, and trigger_patterns against the input text.

### Level 2: Near-Miss Discrimination

Given ambiguous intents that could match multiple skills, does the system rank the correct skill higher?

Examples:
- "refactor this code" → `code-simplification` over `code-review-and-quality`
- "check if this is secure" → `security-and-hardening` over `code-review-and-quality`
- "plan the next sprint" → `planning-and-task-breakdown` over `spec-driven-development`

## Boundaries

### Always do
- Cover all 23 skills with at least 1 positive test case each
- Include near-miss cases for commonly confused skill pairs
- Report per-skill accuracy, not just overall pass rate
- Make the eval suite runnable in CI alongside existing tests

### Ask first
- Adding new skills to the fixture set beyond the initial 30
- Changing the pass threshold from 90%
- Adding Level 3 evals (full classifier accuracy)

### Never do
- Modify existing `skill_match.py` logic to pass specific eval cases (that's overfitting)
- Add network-dependent tests (skill search is local)
- Skip skills because they're "hard to test"

## Fixture Format

`tests/eval_fixtures/skill-activation-evals.json`:

```json
[
  {
    "id": "eval-001",
    "intent": "fix this bug in the login flow",
    "expected_skill": "debugging-and-error-recovery",
    "category": "positive",
    "phase": "VERIFY"
  },
  {
    "id": "eval-002",
    "intent": "write a spec for the new auth system",
    "expected_skill": "spec-driven-development",
    "category": "positive",
    "phase": "DEFINE"
  },
  {
    "id": "eval-025",
    "intent": "refactor this code to be cleaner",
    "expected_skill": "code-simplification",
    "confused_with": "code-review-and-quality",
    "category": "near-miss",
    "phase": "REVIEW"
  }
]
```

Fields:
- `id`: Unique eval case identifier
- `intent`: Natural-language user intent (what the agent receives)
- `expected_skill`: The skill that should be the top candidate
- `confused_with`: (optional) The skill most likely to be incorrectly matched instead
- `category`: `positive` (clear match) or `near-miss` (ambiguous)
- `phase`: Expected lifecycle phase

## Test Runner Design

`tests/test_skill_activation_evals.py`:

```python
"""Skill Activation Eval Suite.

Measures whether skill_match correctly maps user intents to the right skills.
Loads fixture data from eval_fixtures/skill-activation-evals.json.
"""
import json
import pytest
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "eval_fixtures" / "skill-activation-evals.json"


def load_eval_fixtures():
    with open(FIXTURE_PATH) as f:
        return json.load(f)


def _get_skill_match_module():
    """Bootstrap and return the skill_match helper."""
    # Use existing bootstrap pattern
    ...


@pytest.fixture(scope="module")
def skill_match():
    return _get_skill_match_module()


@pytest.fixture(scope="module")
def eval_cases():
    return load_eval_fixtures()


class TestPrefilterAccuracy:
    """Level 1: Does skill_match return the correct skill as a candidate?"""

    @pytest.mark.parametrize("case", load_eval_fixtures(), ids=lambda c: c["id"])
    def test_skill_returned_as_candidate(self, case, skill_match):
        """The expected skill must appear in search results for the intent."""
        results = skill_match.search_skills(case["intent"])
        skill_names = [r["name"] for r in results]
        assert case["expected_skill"] in skill_names, (
            f"{case['id']}: Expected '{case['expected_skill']}' in results "
            f"for intent '{case['intent']}', got {skill_names}"
        )


class TestNearMissDiscrimination:
    """Level 2: Does the system rank the correct skill higher for ambiguous intents?"""

    @pytest.mark.parametrize(
        "case",
        [c for c in load_eval_fixtures() if c.get("confused_with")],
        ids=lambda c: c["id"]
    )
    def test_correct_skill_ranked_higher(self, case, skill_match):
        """Expected skill should rank at or above the confused_with skill."""
        results = skill_match.search_skills(case["intent"])
        skill_names = [r["name"] for r in results]
        expected_idx = skill_names.index(case["expected_skill"]) if case["expected_skill"] in skill_names else 999
        confused_idx = skill_names.index(case["confused_with"]) if case["confused_with"] in skill_names else 999
        assert expected_idx <= confused_idx, (
            f"{case['id']}: '{case['expected_skill']}' (idx {expected_idx}) "
            f"should rank at or above '{case['confused_with']}' (idx {confused_idx}) "
            f"for intent '{case['intent']}'"
        )


class TestCoverageReport:
    """Meta-test: verify all 23 skills are covered by at least one eval case."""

    ALL_SKILLS = [
        "api-and-interface-design", "browser-testing-with-devtools",
        "ci-cd-and-automation", "code-review-and-quality",
        "code-simplification", "context-engineering",
        "debugging-and-error-recovery", "deprecation-and-migration",
        "documentation-and-adrs", "doubt-driven-development",
        "frontend-ui-engineering", "git-workflow-and-versioning",
        "idea-refine", "incremental-implementation",
        "interview-me", "performance-optimization",
        "planning-and-task-breakdown", "security-and-hardening",
        "shipping-and-launch", "source-driven-development",
        "spec-driven-development", "test-driven-development",
        "using-agent-skills",
    ]

    def test_all_skills_have_eval_cases(self):
        cases = load_eval_fixtures()
        covered_skills = {c["expected_skill"] for c in cases}
        missing = set(self.ALL_SKILLS) - covered_skills
        assert not missing, f"Skills without eval cases: {missing}"

    def test_minimum_eval_case_count(self):
        cases = load_eval_fixtures()
        assert len(cases) >= 30, f"Expected ≥30 eval cases, got {len(cases)}"

    def test_at_least_one_near_miss_per_confusable_pair(self):
        cases = load_eval_fixtures()
        near_miss = [c for c in cases if c.get("confused_with")]
        assert len(near_miss) >= 5, f"Expected ≥5 near-miss cases, got {len(near_miss)}"
```

## Eval Case Inventory (30 cases)

### Positive cases (1+ per skill, 23 minimum)

| ID | Intent | Expected Skill | Phase |
|----|--------|---------------|-------|
| eval-001 | "fix this bug in the login flow" | `debugging-and-error-recovery` | VERIFY |
| eval-002 | "write a spec for the new auth system" | `spec-driven-development` | DEFINE |
| eval-003 | "break this feature into tasks" | `planning-and-task-breakdown` | PLAN |
| eval-004 | "implement the POST /tasks endpoint" | `incremental-implementation` | BUILD |
| eval-005 | "write tests for the task creation" | `test-driven-development` | BUILD |
| eval-006 | "review the PR before merge" | `code-review-and-quality` | REVIEW |
| eval-007 | "simplify this function" | `code-simplification` | REVIEW |
| eval-008 | "check for security vulnerabilities" | `security-and-hardening` | REVIEW |
| eval-009 | "optimize the slow query" | `performance-optimization` | REVIEW |
| eval-010 | "deploy to production" | `shipping-and-launch` | SHIP |
| eval-011 | "set up CI/CD pipeline" | `ci-cd-and-automation` | SHIP |
| eval-012 | "create a branch and commit" | `git-workflow-and-versioning` | SHIP |
| eval-013 | "write ADR for database choice" | `documentation-and-adrs` | SHIP |
| eval-014 | "migrate from REST to GraphQL" | `deprecation-and-migration` | SHIP |
| eval-015 | "check the React docs for the latest API" | `source-driven-development` | BUILD |
| eval-016 | "stress-test this plan before committing" | `doubt-driven-development` | BUILD |
| eval-017 | "build the login form component" | `frontend-ui-engineering` | BUILD |
| eval-018 | "design the REST API for tasks" | `api-and-interface-design` | BUILD |
| eval-019 | "test in the browser" | `browser-testing-with-devtools` | VERIFY |
| eval-020 | "manage context for this large codebase" | `context-engineering` | PLAN |
| eval-021 | "interview me about what I want" | `interview-me` | DEFINE |
| eval-022 | "refine this vague idea" | `idea-refine` | DEFINE |
| eval-023 | "which skill should I use" | `using-agent-skills` | META |

### Near-miss cases (7 cases)

| ID | Intent | Expected Skill | Confused With | Phase |
|----|--------|---------------|---------------|-------|
| eval-024 | "refactor this code to be cleaner" | `code-simplification` | `code-review-and-quality` | REVIEW |
| eval-025 | "check if this is secure" | `security-and-hardening` | `code-review-and-quality` | REVIEW |
| eval-026 | "plan the next sprint" | `planning-and-task-breakdown` | `spec-driven-development` | PLAN |
| eval-027 | "make this page load faster" | `performance-optimization` | `frontend-ui-engineering` | REVIEW |
| eval-028 | "verify the app works end to end" | `browser-testing-with-devtools` | `test-driven-development` | VERIFY |
| eval-029 | "document this API" | `documentation-and-adrs` | `spec-driven-development` | SHIP |
| eval-030 | "figure out what the user actually wants" | `interview-me` | `idea-refine` | DEFINE |

## Success Criteria

- [ ] All 23 skills have at least 1 positive eval case
- [ ] ≥7 near-miss cases covering commonly confused skill pairs
- [ ] ≥30 total eval cases in the fixture file
- [ ] `TestPrefilterAccuracy` passes ≥90% of positive cases
- [ ] `TestNearMissDiscrimination` passes ≥80% of near-miss cases
- [ ] `TestCoverageReport` confirms full skill coverage
- [ ] Eval suite runs in <10 seconds
- [ ] CI-runnable alongside existing 658 tests

## Open Questions

- Should Level 3 evals (full classifier accuracy with utility model) be added in a follow-up?
- What pass threshold should gate a release? (proposed: 90% prefilter, 80% near-miss)
