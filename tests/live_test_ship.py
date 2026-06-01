#!/usr/bin/env python3
"""Live test: Real /ship command with 3 parallel specialist subordinates.

This generates the actual /ship prompt, extracts the tool invocation,
and runs call_subordinate_parallel with real LLM-backed subordinates
reviewing the a0_agent_skills project.
"""
import asyncio
import json
import os
import sys
import time
import importlib.util

sys.path.insert(0, "/a0")
os.environ.pop("A0_PARALLEL_DEPTH", None)



async def main():
    from agent import Agent, AgentContext
    from initialize import initialize_agent

    # 1. Generate the ACTUAL /ship prompt
    spec = importlib.util.spec_from_file_location(
        "ship", "/a0/usr/plugins/a0_agent_skills/commands/ship.py"
    )
    ship = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ship)

    ship_result = ship.run({
        "invocation": {"raw_arguments": ""},
        "arguments": {},
        "context": {"project_name": "a0_agent_skills"},
    })

    print("=" * 60)
    print("LIVE /SHIP TEST")
    print("3 real specialist agents in PARALLEL")
    print("Reviewing: /a0/usr/projects/a0_agent_skills")
    print("=" * 60)
    print()

    # 2. Build the actual task list that /ship generates
    tasks = [
        {
            "message": "Conduct a five-axis code review (correctness, readability, architecture, security, performance) on the current staged changes or most recent commits. Review all recent changes. Output the full standard review template with an APPROVE / REQUEST CHANGES verdict, Critical / Important / Suggestion findings, and file:line references. Keep it concise - focus on the most important findings only.",
            "profile": "code-reviewer",
            "timeout_seconds": 180
        },
        {
            "message": "Run a security and vulnerability pass on the current staged changes or most recent commits. Review all recent changes. Check OWASP Top 10, secrets handling, auth/authz, dependency CVEs, and input validation. Output the full Security Audit Report with severity-classified findings (Critical/High/Medium/Low/Info) and actionable mitigations. Keep it concise - focus on the most important findings only.",
            "profile": "security-auditor",
            "timeout_seconds": 180
        },
        {
            "message": "Analyze test coverage for the current staged changes or most recent commits. Review all recent changes. Identify gaps in happy path, edge cases, error paths, and concurrency scenarios. Output the full Test Coverage Analysis with Recommended Tests list and Critical/High/Medium/Low priority classification. Keep it concise - focus on the most important gaps only.",
            "profile": "test-engineer",
            "timeout_seconds": 180
        }
    ]

    tasks_json = json.dumps(tasks)

    # 3. Create parent agent and tool instance
    config = initialize_agent()
    context = AgentContext(config=config)
    agent = Agent(0, config, context)

    # Import tool from plugin directory
    sys.path.insert(0, "/a0/usr/plugins/a0_agent_skills/tools")
    from call_subordinate_parallel import ParallelDelegation

    tool = ParallelDelegation(
        agent=agent,
        name="call_subordinate_parallel",
        method=None,
        args={"tasks": tasks_json, "result_order": "input"},
        message="",
        loop_data=None,
    )

    # 4. Run the parallel execution
    print("Starting parallel execution...")
    print(f"  Worker 0: code-reviewer")
    print(f"  Worker 1: security-auditor")
    print(f"  Worker 2: test-engineer")
    print()

    start_time = time.time()
    result = await tool.execute(
        tasks=tasks_json,
        result_order="input",
        max_concurrency=0,
    )
    elapsed = time.time() - start_time

    # 5. Display results
    print()
    print("=" * 60)
    print(f"COMPLETED in {elapsed:.1f}s")
    print("=" * 60)
    print()

    results = json.loads(result.message)
    successes = 0

    for i, r in enumerate(results):
        profile = r.get("profile", "unknown")
        status = r.get("status", "unknown")
        duration = r.get("duration_ms", 0)
        error = r.get("error")
        result_text = r.get("result", "")

        if status == "ok":
            successes += 1

        print(f"{'=' * 60}")
        print(f"WORKER {i}: {profile} [{status}] ({duration / 1000:.1f}s)")
        print(f"{'=' * 60}")
        if error:
            print(f"ERROR: {error}")
        else:
            print(result_text[:2000])
        print()

    # 6. Summary
    durations = [r.get("duration_ms", 0) for r in results]
    sequential_time = sum(durations) / 1000

    print(f"{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"Workers succeeded: {successes}/{len(results)}")
    print(f"Wall time:         {elapsed:.1f}s")
    print(f"Sequential would:  ~{sequential_time:.1f}s")
    if sequential_time > 0 and elapsed > 0:
        speedup = sequential_time / elapsed
        print(f"Speedup:           ~{speedup:.1f}x")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
