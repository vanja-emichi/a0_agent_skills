#!/usr/bin/env python3
"""Live test: call_subordinate_parallel with 3 real subordinate agents.

This test actually invokes the tool with real LLM-backed subordinates.
Each subordinate gets a simple task to verify parallel execution works.
"""
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, "/a0")
os.environ.pop("A0_PARALLEL_DEPTH", None)


async def main():
    from agent import Agent, AgentContext, AgentConfig
    from initialize import initialize_agent

    # Import the tool
    from tools.call_subordinate_parallel import ParallelDelegation

    print("=" * 60)
    print("LIVE TEST: call_subordinate_parallel")
    print("3 subordinate agents running in PARALLEL")
    print("=" * 60)
    print()

    # Create parent agent context
    config = initialize_agent()
    context = AgentContext(config=config)
    agent = Agent(0, config, context)

    tasks_json = json.dumps([
        {
            "message": "Run a quick code review. Just list 3 observations about the project structure at /a0/usr/projects/a0_agent_skills/. Keep it brief - 3 bullet points max.",
            "profile": "code-reviewer",
            "timeout_seconds": 120
        },
        {
            "message": "Run a quick security check. Just list 3 security observations about the project at /a0/usr/projects/a0_agent_skills/. Keep it brief - 3 bullet points max.",
            "profile": "security-auditor",
            "timeout_seconds": 120
        },
        {
            "message": "Analyze test coverage. Just list 3 testing observations about the project at /a0/usr/projects/a0_agent_skills/. Keep it brief - 3 bullet points max.",
            "profile": "test-engineer",
            "timeout_seconds": 120
        }
    ])

    # Create the tool instance
    tool = ParallelDelegation(
        agent=agent,
        name="call_subordinate_parallel",
        method=None,
        args={
            "tasks": tasks_json,
            "result_order": "input"
        },
        message="",
        loop_data=None
    )

    start_time = time.time()
    print(f"Starting 3 parallel subordinates...")
    print(f"  Worker 1: code-reviewer")
    print(f"  Worker 2: security-auditor")
    print(f"  Worker 3: test-engineer")
    print()

    result = await tool.execute(
        tasks=tasks_json,
        result_order="input",
        max_concurrency=0
    )

    elapsed = time.time() - start_time

    print()
    print("=" * 60)
    print(f"COMPLETED in {elapsed:.1f}s")
    print("=" * 60)
    print()

    # Parse and display results
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

        print(f"--- Worker {i}: {profile} [{status}] ({duration}ms) ---")
        if error:
            print(f"Error: {error}")
        else:
            # Show first 500 chars of result
            print(result_text[:500])
        print()

    print("=" * 60)
    print(f"SUMMARY: {successes}/{len(results)} workers succeeded")
    print(f"Wall time: {elapsed:.1f}s")
    durations = [r.get("duration_ms", 0) for r in results]
    sequential_time = sum(durations) / 1000
    print(f"Sequential would take: ~{sequential_time:.1f}s")
    if sequential_time > 0:
        speedup = sequential_time / elapsed
        print(f"Speedup: ~{speedup:.1f}x")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
