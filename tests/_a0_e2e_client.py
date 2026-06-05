"""Reusable HTTP client for Agent Zero e2e tests.

Wraps the scheduler API (create, run, list, delete, wait) with automatic
CSRF token handling, login-based authentication, and retry on timeout.

Usage::

    from tests._a0_e2e_client import A0E2EClient

    client = A0E2EClient()
    if not client.is_server_alive():
        pytest.skip("Agent Zero server not running")

    task = client.create_and_run_task(
        name="my-test",
        system_prompt="You are a helper.",
        prompt="Say hello.",
    )
    result = client.wait_for_task(task["uuid"])
    client.delete_task(task["uuid"])
"""

from __future__ import annotations

import logging
import shutil
import time
import uuid as _uuid
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger("a0_e2e")

_DEFAULT_PORTS = [8089, 80, 85, 8000]


class A0E2EClientError(Exception):
    """Raised on unrecoverable API errors."""


def _is_response_tool(content: str) -> bool:
    """Check if content is a response tool JSON call.

    Tries proper JSON parse first, falls back to substring match.
    """
    import json as _json
    try:
        data = _json.loads(content)
        return isinstance(data, dict) and data.get("tool_name") == "response"
    except (ValueError, TypeError):
        return '"tool_name": "response"' in content


def gather_evidence(a0_client: "A0E2EClient", task_result: dict) -> dict:
    """Gather all evidence from task result, logs, and chat.json.

    Shared across all e2e test files. Returns a summary dict with:
    - task_state, context_id, log_warnings, log_errors
    - loaded_skills, chat_found, agent_count, last_response
    """
    context_id = task_result.get("context_id")
    summary = {
        "task_state": task_result.get("state"),
        "context_id": context_id,
        "log_warnings": 0,
        "log_errors": 0,
        "loaded_skills": [],
        "chat_found": False,
        "agent_count": 0,
        "last_response": "",
    }

    if context_id:
        # Logs
        try:
            logs = a0_client.get_logs(context_id, length=200)
            items = logs.get("items", [])
            summary["log_warnings"] = sum(
                1 for i in items if i.get("type") == "warning"
            )
            summary["log_errors"] = sum(
                1 for i in items if i.get("type") == "error"
            )
        except Exception:
            pass

        # Chat data
        try:
            chat = a0_client.get_chat_json(context_id)
            if chat:
                summary["chat_found"] = True
                agents = chat.get("agents", [])
                summary["agent_count"] = len(agents)
                if agents:
                    data = agents[0].get("data", {})
                    summary["loaded_skills"] = data.get("loaded_skills", [])
                # Get last response text
                summary["last_response"] = a0_client.get_last_agent_response(context_id)
        except Exception:
            pass

    return summary


class A0E2EClient:
    """HTTP client wrapping the Agent Zero scheduler API."""

    def __init__(
        self,
        base_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        timeout: int = 120,
        max_retries: int = 3,
    ) -> None:
        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            self.base_url = self._auto_detect_base_url()

        self.username = username
        self.password = password
        self.timeout = timeout
        self._max_retries = max_retries

        self.session = requests.Session()
        self._csrf_token: str | None = None
        self._authenticated = False

    # ------------------------------------------------------------------
    # Server discovery
    # ------------------------------------------------------------------

    @staticmethod
    def _auto_detect_base_url() -> str:
        """Try common ports and return the first that responds."""
        for port in _DEFAULT_PORTS:
            url = f"http://localhost:{port}"
            try:
                requests.get(f"{url}/api/health", timeout=2, allow_redirects=False)
                return url
            except requests.ConnectionError:
                continue
            except Exception:
                return url
        return "http://localhost:8089"

    # ------------------------------------------------------------------
    # Auth & CSRF
    # ------------------------------------------------------------------

    def _ensure_authenticated(self) -> None:
        """Authenticate if credentials are provided and not yet done."""
        if self._authenticated:
            return

        if self.username and self.password:
            resp = self.session.post(
                f"{self.base_url}/login",
                data={
                    "username": self.username,
                    "password": self.password,
                    "next": "/",
                },
                allow_redirects=True,
                timeout=self.timeout,
            )
            if resp.status_code < 400:
                self._authenticated = True
            else:
                raise A0E2EClientError(
                    f"Login failed: status={resp.status_code}, body={resp.text[:200]}"
                )
        else:
            self._authenticated = True

    def _ensure_csrf(self) -> None:
        """Fetch a CSRF token from /api/csrf_token if needed."""
        if self._csrf_token:
            return
        self._ensure_authenticated()
        try:
            resp = self.session.get(
                f"{self.base_url}/api/csrf_token",
                timeout=self.timeout,
                allow_redirects=False,
            )
            if resp.status_code >= 300:
                logger.warning(
                    "CSRF endpoint returned %d, proceeding without token",
                    resp.status_code,
                )
                return
            data = resp.json()
            if data.get("ok") or data.get("token"):
                self._csrf_token = data["token"]
            else:
                logger.warning("CSRF token fetch returned: %s", data)
        except Exception as exc:
            logger.warning("Failed to fetch CSRF token: %s", exc)

    # ------------------------------------------------------------------
    # Low-level request helpers
    # ------------------------------------------------------------------

    def _post(self, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send an authenticated, CSRF-protected POST with retry on timeout."""
        self._ensure_csrf()
        headers = {"Content-Type": "application/json"}
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token

        last_exc: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                resp = self.session.post(
                    f"{self.base_url}/api/{endpoint}",
                    json=payload or {},
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=False,
                )

                # Auth redirect - re-authenticate once and retry
                if resp.status_code in (301, 302, 303) and "/login" in resp.headers.get("Location", ""):
                    self._authenticated = False
                    self._csrf_token = None
                    self._ensure_csrf()
                    if self._csrf_token:
                        headers["X-CSRF-Token"] = self._csrf_token
                    resp = self.session.post(
                        f"{self.base_url}/api/{endpoint}",
                        json=payload or {},
                        headers=headers,
                        timeout=self.timeout,
                        allow_redirects=False,
                    )

                if resp.status_code == 403 and "CSRF" in resp.text:
                    self._csrf_token = None
                    self._ensure_csrf()
                    if self._csrf_token:
                        headers["X-CSRF-Token"] = self._csrf_token
                    resp = self.session.post(
                        f"{self.base_url}/api/{endpoint}",
                        json=payload or {},
                        headers=headers,
                        timeout=self.timeout,
                        allow_redirects=False,
                    )

                if resp.status_code >= 400:
                    raise A0E2EClientError(
                        f"API error {resp.status_code} on {endpoint}: {resp.text[:300]}"
                    )

                return resp.json()

            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as exc:
                last_exc = exc
                if attempt < self._max_retries - 1:
                    backoff = 5 * (attempt + 1)
                    logger.warning(
                        "Timeout on %s, retrying in %ds (attempt %d/%d)",
                        endpoint, backoff, attempt + 2, self._max_retries,
                    )
                    time.sleep(backoff)

        raise A0E2EClientError(
            f"Failed after {self._max_retries} retries on {endpoint}: {last_exc}"
        )

    # ------------------------------------------------------------------
    # Public API wrappers
    # ------------------------------------------------------------------

    def is_server_alive(self) -> bool:
        """Return True if the Agent Zero server is reachable."""
        try:
            self.session.get(
                f"{self.base_url}/api/health",
                timeout=3,
                allow_redirects=False,
            )
            return True
        except requests.ConnectionError:
            return False
        except Exception:
            return True

    def create_adhoc_task(
        self,
        name: str,
        prompt: str,
        system_prompt: str = "",
        attachments: list[str] | None = None,
        token: str | None = None,
        project_name: str | None = None,
    ) -> dict[str, Any]:
        """Create an ad-hoc scheduler task. Returns the task dict."""
        payload: dict[str, Any] = {
            "name": name,
            "system_prompt": system_prompt,
            "prompt": prompt,
            "attachments": attachments or [],
        }
        if token:
            payload["token"] = token
        if project_name:
            payload["project_name"] = project_name

        data = self._post("scheduler_task_create", payload)
        if "error" in data:
            raise A0E2EClientError(f"Create task failed: {data['error']}")
        return data["task"]

    def run_task(self, task_uuid: str) -> dict[str, Any]:
        """Start a task by UUID. Returns the updated task dict."""
        data = self._post("scheduler_task_run", {"task_id": task_uuid})
        if "error" in data:
            raise A0E2EClientError(f"Run task failed: {data['error']}")
        return data.get("task", data)

    def list_tasks(self) -> list[dict[str, Any]]:
        """Return all scheduler tasks."""
        data = self._post("scheduler_tasks_list", {})
        if not data.get("ok"):
            raise A0E2EClientError(f"List tasks failed: {data.get('error', 'unknown')}")
        return data.get("tasks", [])

    def delete_task(self, task_uuid: str) -> bool:
        """Delete a task by UUID. Returns True on success."""
        data = self._post("scheduler_task_delete", {"task_id": task_uuid})
        return data.get("success", False)

    def get_task_state(self, task_uuid: str) -> str | None:
        """Return the current state of a task, or None if not found."""
        tasks = self.list_tasks()
        for t in tasks:
            if t.get("uuid") == task_uuid:
                return t.get("state")
        return None

    def wait_for_task(
        self,
        task_uuid: str,
        timeout: int = 600,
        poll_interval: float = 5.0,
        terminal_states: tuple[str, ...] = ("idle",),
        activity_timeout: int = 300,
    ) -> dict[str, Any]:
        """Poll until the task reaches a terminal state.

        Uses activity-based keepalive: if the task's context is still
        producing log items, the timeout is extended automatically.

        Args:
            timeout: maximum wall-clock seconds to wait (default 600 = 10min)
            poll_interval: seconds between state polls
            terminal_states: states that mean the task is done
            activity_timeout: seconds since last log activity before giving up
        """
        deadline = time.monotonic() + timeout
        last_activity = time.monotonic()
        prev_log_count = 0

        while time.monotonic() < deadline:
            # Check task state
            try:
                tasks = self.list_tasks()
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
                time.sleep(poll_interval)
                continue

            for t in tasks:
                if t.get("uuid") == task_uuid:
                    state = t.get("state", "unknown")
                    last_run = t.get("last_run")
                    if state in terminal_states and last_run is not None:
                        return t

                    # Activity keepalive: check log progress
                    ctx_id = t.get("context_id")
                    if ctx_id:
                        try:
                            logs = self.get_logs(ctx_id, length=1)
                            current_count = logs.get("total_items", prev_log_count)
                            if current_count != prev_log_count:
                                prev_log_count = current_count
                                last_activity = time.monotonic()
                        except Exception:
                            pass

                    # Check if activity has stalled
                    if time.monotonic() - last_activity > activity_timeout:
                        raise A0E2EClientError(
                            f"Task {task_uuid} stalled (no log activity for "
                            f"{activity_timeout}s, last state: {state})"
                        )
                    break
            else:
                raise A0E2EClientError(f"Task {task_uuid} not found in task list")
            time.sleep(poll_interval)

        raise A0E2EClientError(
            f"Task {task_uuid} did not reach {terminal_states} within {timeout}s "
            f"(last state: {self.get_task_state(task_uuid)})"
        )

    def create_and_run_task(
        self,
        name: str,
        prompt: str,
        system_prompt: str = "",
        attachments: list[str] | None = None,
        token: str | None = None,
        project_name: str | None = None,
    ) -> dict[str, Any]:
        """Convenience: create + run a task. Returns the task dict from create."""
        task = self.create_adhoc_task(
            name=name,
            prompt=prompt,
            system_prompt=system_prompt,
            attachments=attachments,
            token=token,
            project_name=project_name,
        )
        try:
            self.run_task(task["uuid"])
        except A0E2EClientError as exc:
            import logging
            logging.warning("run_task raised %s (task may already be running): %s", type(exc).__name__, exc)
        return task

    def cleanup_tasks(self, prefix: str = "e2e-test-") -> int:
        """Delete all tasks whose name starts with *prefix*. Returns count deleted."""
        tasks = self.list_tasks()
        count = 0
        for t in tasks:
            if t.get("name", "").startswith(prefix):
                try:
                    self.delete_task(t["uuid"])
                    count += 1
                except Exception:
                    pass
        return count

    # ------------------------------------------------------------------
    # Fixture helpers
    # ------------------------------------------------------------------

    @staticmethod
    def make_fixture_project(
        root: str,
        root_contract: str = "",
        child_contracts: dict[str, str] | None = None,
    ) -> str:
        """Create a minimal fixture project with AGENTS.md files.

        Returns:
            Path to the fixture project root.
        """
        project_name = f"e2e-fixture-{_uuid.uuid4().hex[:8]}"
        project_dir = Path(root) / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        (project_dir / "AGENTS.md").write_text(
            root_contract or "# Root Contract\n\n## Purpose\n\nTest fixture.\n"
        )

        for rel_path, content in (child_contracts or {}).items():
            child_file = project_dir / rel_path
            child_file.parent.mkdir(parents=True, exist_ok=True)
            child_file.write_text(content)

        return str(project_dir)

    @staticmethod
    def remove_fixture_project(path: str) -> None:
        """Remove a fixture project directory."""
        p = Path(path)
        if p.exists() and p.is_dir():
            shutil.rmtree(p, ignore_errors=True)

    # ------------------------------------------------------------------
    # Log & chat inspection
    # ------------------------------------------------------------------

    def get_logs(self, context_id: str, length: int = 100) -> dict[str, Any]:
        """Fetch recent log items for a context via the API.

        Returns dict with: total_items, returned_items, progress, items[].
        """
        self._ensure_authenticated()
        resp = self.session.get(
            f"{self.base_url}/api/log_get",
            params={"context_id": context_id, "length": length},
            headers=self._auth_headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            raise A0E2EClientError(f"get_logs failed: {resp.status_code} {resp.text[:200]}")
        return resp.json().get("log", resp.json())

    def get_chat_json(self, context_id: str) -> dict[str, Any] | None:
        """Read the persisted chat.json for a context from disk.

        Returns parsed JSON dict or None if the file does not exist.
        """
        chat_path = Path(f"/a0/usr/chats/{context_id}/chat.json")
        if not chat_path.exists():
            return None
        import json
        return json.loads(chat_path.read_text(encoding="utf-8"))

    def get_chat_files_path(self, context_id: str) -> str | None:
        """Get the effective workdir/project path for a context via API."""
        self._ensure_authenticated()
        resp = self.session.post(
            f"{self.base_url}/api/chat_files_path_get",
            json={"ctxid": context_id},
            headers=self._auth_headers(),
            timeout=30,
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("path")

    def get_last_agent_response(self, context_id: str) -> str:
        """Extract the last agent response text from persisted chat.json.

        History structure:
          {"_cls":"History", "bulks":[{"_cls":"Bulk","records":[
            {"_cls":"Topic","messages":[{"ai":true,"content":"..."}]}
          ]}]}
        Returns the content of the last AI message, or empty string.
        """
        import json as _json

        chat = self.get_chat_json(context_id)
        if not chat:
            return ""
        agents = chat.get("agents", [])
        if not agents:
            return ""

        # History is a JSON string, not a dict
        hist_raw = agents[0].get("history", "")
        if isinstance(hist_raw, str):
            try:
                hist = _json.loads(hist_raw)
            except Exception:
                return ""
        elif isinstance(hist_raw, dict):
            hist = hist_raw
        else:
            return ""

        # Walk bulks → records → messages to find last AI message
        # that uses the 'response' tool (actual final answer)
        # Priority: current (scheduler tasks) → bulks (main agent) → topics (greeting)

        # 1. Scheduler tasks: current has the actual task conversation
        current = hist.get("current")
        if isinstance(current, dict):
            messages = current.get("messages", [])
            for msg in reversed(messages):
                if msg.get("ai"):
                    content = msg.get("content", "")
                    if content and _is_response_tool(content):
                        return content

        # 2. Main agent: bulks → records → messages
        bulks = hist.get("bulks", [])
        for bulk in reversed(bulks):
            records = bulk.get("records", [])
            for record in reversed(records):
                messages = record.get("messages", [])
                for msg in reversed(messages):
                    if msg.get("ai"):
                        content = msg.get("content", "")
                        if content and _is_response_tool(content):
                            return content

        # 3. Topics (greeting-only fallback)
        topics = hist.get("topics", [])
        for topic in reversed(topics):
            messages = topic.get("messages", [])
            for msg in reversed(messages):
                if msg.get("ai"):
                    content = msg.get("content", "")
                    if content and _is_response_tool(content):
                        return content

        # Last resort: return the last AI message from any source
        for source in [bulks, topics]:
            for item in reversed(source):
                records = item.get("records", []) if "records" in item else [item]
                for record in records:
                    messages = record.get("messages", [])
                    for msg in reversed(messages):
                        if msg.get("ai"):
                            content = msg.get("content", "")
                            if content:
                                return content

        if isinstance(current, dict):
            messages = current.get("messages", [])
            for msg in reversed(messages):
                if msg.get("ai"):
                    content = msg.get("content", "")
                    if content:
                        return content

        return ""

    # ------------------------------------------------------------------
    # Commands API
    # ------------------------------------------------------------------

    def list_effective_commands(self, context_id: str = "") -> list[dict[str, Any]]:
        """List all effective commands (project + global + plugin).

        Uses the Commands plugin API at /api/plugins/commands/commands.
        """
        resp = self._post("plugins/commands/commands", {
            "action": "list_effective",
            "context_id": context_id,
        })
        return resp.get("commands", [])

    def resolve_command(self, path: str, slash_text: str, *,
                        context_id: str = "", project_name: str = "") -> dict[str, Any]:
        """Resolve a slash command invocation.

        Returns the full resolution dict with keys: command, invocation, result.
        result.text contains the rendered template or script output.

        Uses the Commands plugin API at /api/plugins/commands/commands.
        """
        return self._post("plugins/commands/commands", {
            "action": "resolve",
            "path": path,
            "slash_text": slash_text,
            "context_id": context_id,
            "project_name": project_name,
        })

    def _auth_headers(self) -> dict[str, str]:
        """Return headers with CSRF token if available."""
        headers: dict[str, str] = {}
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token
        return headers
