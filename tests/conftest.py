"""Shared fixtures for e2e tests requiring a live Agent Zero server.

Supports parallel execution via pytest-xdist (``-n auto``).  Each worker
creates its own ``A0E2EClient`` session.  Task cleanup is per-test using
tracked UUIDs to avoid cross-worker interference.
"""

from __future__ import annotations

import os

import pytest

from tests._a0_e2e_client import A0E2EClient, A0E2EClientError

# Credentials MUST come from environment variables only
_DEFAULT_USERNAME = os.environ.get("A0_E2E_USERNAME", "")
_DEFAULT_PASSWORD = os.environ.get("A0_E2E_PASSWORD", "")


@pytest.fixture(scope="session")
def a0_client() -> A0E2EClient:
    """Session-scoped client (one per xdist worker)."""
    return A0E2EClient(
        username=_DEFAULT_USERNAME,
        password=_DEFAULT_PASSWORD,
    )


def pytest_collection_modifyitems(items):
    """Skip e2e tests if the server is not reachable."""
    try:
        import requests
        base_url = A0E2EClient._auto_detect_base_url()
        requests.get(f"{base_url}/api/health", timeout=3, allow_redirects=False)
        server_up = True
    except Exception:
        server_up = False

    if not server_up:
        skip_reason = pytest.mark.skip(reason="Agent Zero server is not running")
        for item in items:
            if item.get_closest_marker("e2e"):
                item.add_marker(skip_reason)


@pytest.fixture()
def task_tracker():
    """Track task UUIDs created during a test for reliable per-test cleanup."""
    uuids: list[str] = []
    yield uuids


@pytest.fixture()
def clean_tasks(a0_client: A0E2EClient, task_tracker: list[str]):
    """Delete only the tasks created in the current test (by tracked UUIDs)."""
    yield
    for tid in task_tracker:
        try:
            a0_client.delete_task(tid)
        except Exception:
            pass
