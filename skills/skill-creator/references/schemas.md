# JSON Schemas

This document defines the JSON schemas used by skill-creator.

---

## evals.json

Defines the evals for a skill. Located at `evals/evals.json` within the skill directory.

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "prompt": "User's example prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/sample1.pdf"],
      "expectations": [
        "The output includes X",
        "The skill used script Y"
      ]
    }
  ]
}
```

**Fields:**
- `skill_name`: Name matching the skill's frontmatter
- `evals[].id`: Unique integer identifier
- `evals[].prompt`: The task to execute
- `evals[].expected_output`: Human-readable description of success
- `evals[].files`: Optional list of input file paths (relative to skill root)
- `evals[].expectations`: List of verifiable statements
- `evals[].should_trigger` (boolean, required for optimization): Whether this query should trigger the skill. Used for description optimization. Include near-miss false-trigger cases (queries that seem related but shouldn't trigger).

### Optimization Workspace Files

| File | Purpose |
|---|---|
| `train_evals.json` | Training set (60% of evals, stratified) |
| `test_evals.json` | Held-out test set (40% of evals, stratified) |
| `optimization_history.json` | Per-iteration descriptions + scores |
| `improve_context.json` | LLM-ready context for description improvement |
| `optimization_report.md` | Final optimization results in markdown |

---

## grading.json

Output from the grader agent. Located at `<run-dir>/grading.json`.

```json
{
  "expectations": [
    {
      "text": "The output includes the name 'John Smith'",
      "passed": true,
      "evidence": "Found in transcript Step 3: 'Extracted names: John Smith, Sarah Johnson'"
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 1,
    "total": 3,
    "pass_rate": 0.67
  },
  "execution_metrics": {
    "tool_calls": {
      "text_editor:read": 5,
      "text_editor:write": 2,
      "code_execution_tool": 8
    },
    "total_tool_calls": 15,
    "total_steps": 6,
    "errors_encountered": 0,
    "output_chars": 12450,
    "transcript_chars": 3200
  },
  "timing": {
    "executor_duration_seconds": 165.0,
    "total_duration_seconds": 200.0
  },
  "claims": [
    {
      "claim": "The form has 12 fields",
      "type": "factual",
      "verified": true,
      "evidence": "Output PDF contains exactly 12 fillable fields"
    }
  ],
  "user_notes_summary": {
    "uncertainties": ["Not sure if date format is MM/DD/YYYY or DD/MM/YYYY"],
    "needs_review": ["Field 11 may have wrong state abbreviation"],
    "workarounds": ["Used manual field mapping because script failed"]
  },
  "eval_feedback": {
    "suggestions": [
      {
        "reason": "Assertion 'output is a PDF' is trivially satisfied by any PDF regardless of content",
        "assertion": "output is a PDF"
      }
    ],
    "overall": "Assertions check file type and tools used but miss the core task quality"
  }
}
```

**Required fields:**
- `expectations[].text`: The assertion text
- `expectations[].passed`: Boolean
- `expectations[].evidence`: String with cited evidence
- `summary.passed`, `summary.failed`, `summary.total`, `summary.pass_rate`

---

## comparison.json

Output from blind comparator. Located at `<grading-dir>/comparison-N.json`.

```json
{
  "winner": "A",
  "reasoning": "Output A provides a complete solution with proper formatting.",
  "rubric": {
    "A": {
      "content": {
        "correctness": 5,
        "completeness": 5,
        "accuracy": 4
      },
      "structure": {
        "organization": 4,
        "formatting": 5,
        "usability": 4
      },
      "content_score": 4.67,
      "structure_score": 4.33,
      "overall_score": 9.0
    },
    "B": {
      "content": {
        "correctness": 3,
        "completeness": 2,
        "accuracy": 3
      },
      "structure": {
        "organization": 3,
        "formatting": 2,
        "usability": 3
      },
      "content_score": 2.67,
      "structure_score": 2.67,
      "overall_score": 5.34
    }
  },
  "output_quality": {
    "A": {
      "score": 9,
      "strengths": ["Complete solution"],
      "weaknesses": ["Minor style issue"]
    },
    "B": {
      "score": 5,
      "strengths": ["Readable"],
      "weaknesses": ["Missing fields"]
    }
  },
  "expectation_results": {
    "A": {
      "passed": 4,
      "total": 5,
      "pass_rate": 0.80,
      "details": [
        {"text": "Output includes name", "passed": true}
      ]
    },
    "B": {
      "passed": 3,
      "total": 5,
      "pass_rate": 0.60,
      "details": []
    }
  }
}
```

**Required fields:**
- `winner`: "A", "B", or "TIE"
- `reasoning`: String
- `rubric.{A,B}.content_score`, `rubric.{A,B}.structure_score`, `rubric.{A,B}.overall_score`
- `output_quality.{A,B}.score`, `.strengths`, `.weaknesses`

---

## benchmark.json

Output from Benchmark mode. Located at `benchmarks/<timestamp>/benchmark.json`.

```json
{
  "metadata": {
    "skill_name": "pdf",
    "skill_path": "/path/to/pdf",
    "executor_model": "default",
    "analyzer_model": "default",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2, 3],
    "runs_per_configuration": 3
  },
  "runs": [
    {
      "eval_id": 1,
      "eval_name": "Ocean",
      "configuration": "with_skill",
      "run_number": 1,
      "result": {
        "pass_rate": 0.85,
        "passed": 6,
        "failed": 1,
        "total": 7,
        "time_seconds": 42.5,
        "tokens": 3800,
        "tool_calls": 18,
        "errors": 0
      },
      "expectations": [
        {"text": "...", "passed": true, "evidence": "..."}
      ],
      "notes": [
        "Used 2023 data, may be stale"
      ]
    }
  ]
}
```

**Critical field names:** The viewer reads these field names exactly:
- `configuration` (NOT `config`)
- `result.pass_rate` (nested under `result`, NOT top-level)
- `result.passed`, `result.failed`, `result.total`
- `run_number`, `eval_id`, `eval_name`

---

## metrics.json

Output from the executor agent. Located at `<run-dir>/outputs/metrics.json`.

```json
{
  "tool_calls": {
    "text_editor:read": 5,
    "text_editor:write": 2,
    "text_editor:patch": 1,
    "code_execution_tool": 10
  },
  "total_tool_calls": 18,
  "total_steps": 6,
  "files_created": ["filled_form.pdf", "field_values.json"],
  "errors_encountered": 0,
  "output_chars": 12450,
  "transcript_chars": 3200
}
```

---

## timing.json

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3,
  "executor_start": "2026-01-15T10:30:00Z",
  "executor_end": "2026-01-15T10:32:45Z",
  "executor_duration_seconds": 165.0,
  "grader_start": "2026-01-15T10:32:46Z",
  "grader_end": "2026-01-15T10:33:12Z",
  "grader_duration_seconds": 26.0
}
```

---

## history.json

Tracks version progression in Improve mode. Located at workspace root.

```json
{
  "started_at": "2026-01-15T10:30:00Z",
  "skill_name": "example-skill",
  "current_best": "v2",
  "iterations": [
    {
      "version": "v0",
      "parent": null,
      "expectation_pass_rate": 0.60,
      "grading_result": "baseline",
      "is_current_best": false
    },
    {
      "version": "v1",
      "parent": "v0",
      "expectation_pass_rate": 0.80,
      "grading_result": "won",
      "is_current_best": false
    },
    {
      "version": "v2",
      "parent": "v1",
      "expectation_pass_rate": 0.90,
      "grading_result": "won",
      "is_current_best": true
    }
  ]
}
```
