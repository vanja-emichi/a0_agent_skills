# Tasks: call_subordinate_parallel Implementation

> Generated from spec `call-subordinate-parallel-spec.md` Phase 2 plan.

## Task 1: Tool skeleton — file placement and discovery

- **Description:** Create `tools/call_subordinate_parallel.py` with empty `ParallelDelegation(Tool)` class, correct imports, `execute()` signature, and `get_log_object()`. Verify the framework discovers the tool.
- **Acceptance:** Agent can invoke `call_subordinate_parallel` with empty args and receives a placeholder response.
- **Verify:** Manual test — ask agent to use the tool, confirm it's found and returns a response.
- **Files:** `plugins/a0_agent_skills/tools/call_subordinate_parallel.py` (new)

## Task 2: Task parsing and validation

- **Description:** Implement `tasks` arg parsing inside `execute()`. Handle both JSON string and list-of-dicts input. Validate each task has required `message` field, optional `profile` and `timeout_seconds`. Return clear error on invalid input.
- **Acceptance:** Valid inputs parsed correctly; invalid inputs (missing message, empty list, wrong types) produce descriptive error responses.
- **Verify:** Unit tests for: valid list, valid JSON string, missing message, empty list, non-dict items, extra fields ignored.
- **Files:** `plugins/a0_agent_skills/tools/call_subordinate_parallel.py`, `tests/test_call_subordinate_parallel.py` (new)

## Task 3: Single worker lifecycle

- **Description:** Implement `_run_worker()` method: `initialize_agent()` → profile override → `AgentContext(type=TASK)` → `Agent` → inject message → `monologue()` → collect result → `save_tmp_chat()`. Test with a single worker.
- **Acceptance:** One worker runs end-to-end, returns monologue result, context is persisted for debugging.
- **Verify:** Unit test with mocked `monologue()` — verify context creation, agent initialization, message injection, result collection.
- **Files:** `plugins/a0_agent_skills/tools/call_subordinate_parallel.py`, `tests/test_call_subordinate_parallel.py`

## Task 4: Timeout handling per worker

- **Description:** Wrap `_run_worker()` with `asyncio.wait_for(coro, timeout=timeout_seconds)`. Handle `asyncio.TimeoutError` — return result with `status="fail"`, `error="Timeout after {N}s"`. Default timeout 300s.
- **Acceptance:** Worker exceeding timeout returns error result; worker finishing before timeout returns normally.
- **Verify:** Unit test: mocked slow monologue (sleep) triggers timeout, mocked fast monologue completes.
- **Files:** `plugins/a0_agent_skills/tools/call_subordinate_parallel.py`, `tests/test_call_subordinate_parallel.py`

## Task 5: Concurrent execution with progress reporting

- **Description:** Replace single-worker call with `asyncio.as_completed()` over N workers. After each worker completes, call `await self.set_progress(f"Worker {completed}/{total} ({profile})")`. Support optional `max_concurrency` via `asyncio.Semaphore`.
- **Acceptance:** N workers run concurrently; progress updates fire after each completion; `max_concurrency` limits simultaneous workers when set.
- **Verify:** Unit test: verify all workers execute, progress calls happen, semaphore limits concurrency.
- **Files:** `plugins/a0_agent_skills/tools/call_subordinate_parallel.py`, `tests/test_call_subordinate_parallel.py`

## Task 6: Result formatting and response

- **Description:** Format final results list: `[{profile, result, status, error, duration_ms, order}, ...]`. Support `result_order` ("input" preserves input order, "completion" orders by finish time). Return as `Response(message=formatted_results, break_loop=False)`. Include file-saving hint for long results (same pattern as `call_subordinate.py:39-44`).
- **Acceptance:** Results are correctly formatted, ordered, and include timing. Long results get the include hint.
- **Verify:** Unit tests: mixed success/failure results, input vs completion ordering, long result triggers hint.
- **Files:** `plugins/a0_agent_skills/tools/call_subordinate_parallel.py`, `tests/test_call_subordinate_parallel.py`

## Task 7: Error handling and partial results

- **Description:** Ensure any exception in a worker (timeout, LLM error, unexpected crash) produces a result entry with `status="fail"` and error details. Other workers continue unaffected. `as_completed` with try/except per worker.
- **Acceptance:** One worker failing does not affect others; all N results returned regardless of individual failures.
- **Verify:** Unit test: one worker raises exception, others succeed — all N results returned, failed one has error details.
- **Files:** `plugins/a0_agent_skills/tools/call_subordinate_parallel.py`, `tests/test_call_subordinate_parallel.py`

## Task 8: Update /ship command prompt

- **Description:** Update `commands/ship.py` to instruct the main agent to use `call_subordinate_parallel` with the three specialist tasks as a batch, instead of sequential `call_subordinate` calls. Update the docstring and Phase A description.
- **Acceptance:** `/ship` prompt references `call_subordinate_parallel` with all three specialist tasks in a single invocation. Merge instructions remain the same.
- **Verify:** Read prompt output, confirm tool name and task structure are correct.
- **Files:** `plugins/a0_agent_skills/commands/ship.py`

## Task 9: Final integration test and cleanup

- **Description:** Run all tests. Verify tool discovery works. Check test coverage on core logic. Clean up any debug logging. Ensure no core files were modified.
- **Acceptance:** All tests pass, coverage >90% on core logic, zero core file modifications, `/ship` command prompt is correct.
- **Verify:** `pytest tests/test_call_subordinate_parallel.py -v`
- **Files:** All task files

---

## Dependency graph

```
Task 1 (skeleton)
  └→ Task 2 (parsing)
      └→ Task 3 (single worker)
          └→ Task 4 (timeout)
              └→ Task 5 (concurrency + progress)
                  └→ Task 6 (result formatting)
                      └→ Task 7 (error handling)
                          └→ Task 8 (ship.py update)
                              └→ Task 9 (integration test)
```

All tasks sequential — each builds on the previous.
