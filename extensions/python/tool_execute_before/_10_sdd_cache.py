"""SDD cache pre-tool hook for Agent Zero.

Intercepts browser tool calls (navigate/content actions) before execution.
If a cached response exists for the URL and the server confirms it is still
fresh (HTTP 304 Not Modified), serves the cached content and blocks the
actual browser call by redirecting to a safe no-op action.

Cache key: SHA-256 of URL (first 32 hex chars).
Cache storage: .a0proj/sdd-cache/<hash>.json

Dependencies: stdlib only (hashlib, json, os, urllib.request, datetime).
"""

import hashlib
import json
import logging
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone

from helpers.extension import Extension

logger = logging.getLogger(__name__)

DATA_KEY_SDD_CACHE_HIT = "sdd_cache_pending_hit"
CACHE_SUBDIR = os.path.join(".a0proj", "sdd-cache")
HEAD_TIMEOUT = 5


def _cache_key(url: str) -> str:
    """Return SHA-256 hex digest of URL, truncated to 32 chars (128 bits)."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]


def _cache_dir(agent) -> str:
    """Resolve the cache directory from agent config or plugin location."""
    # Try to get project-based path from agent config
    if hasattr(agent, "config") and hasattr(agent.config, "project_folder"):
        base = agent.config.project_folder
        if base:
            return os.path.join(base, CACHE_SUBDIR)
    # Fallback: plugin directory (3 levels up from this file)
    plugin_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
    )
    return os.path.join(plugin_dir, CACHE_SUBDIR)


def _debug_enabled(agent) -> bool:
    """Check if debug logging is enabled via env var or sentinel file."""
    if os.environ.get("SDD_CACHE_DEBUG", "0") == "1":
        return True
    cache_dir = _cache_dir(agent)
    return os.path.isfile(os.path.join(cache_dir, ".debug"))


def _dbg(agent, msg: str):
    """Write debug log entry if debug mode is active."""
    if not _debug_enabled(agent):
        return
    cache_dir = _cache_dir(agent)
    os.makedirs(cache_dir, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_path = os.path.join(cache_dir, ".debug.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"{ts} [pre]  {msg}\n")
    except OSError:
        pass


def _head_revalidate(url: str, etag: str = "", last_modified: str = "") -> int:
    """Send a HEAD request with If-None-Match / If-Modified-Since.

    Returns the HTTP status code, or 0 on error.
    """
    req = urllib.request.Request(url, method="HEAD")
    if etag:
        req.add_header("If-None-Match", etag)
    if last_modified:
        req.add_header("If-Modified-Since", last_modified)
    try:
        with urllib.request.urlopen(req, timeout=HEAD_TIMEOUT) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except (OSError, urllib.error.URLError):
        return 0


def _format_hit_message(url: str, content: str, fetched_at: float,
                         original_prompt: str = "") -> str:
    """Build the cache-hit payload delivered to the agent."""
    try:
        dt = datetime.fromtimestamp(fetched_at, tz=timezone.utc)
        verified_iso = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OSError, ValueError, OverflowError):
        verified_iso = "unknown"

    parts = [
        f"[sdd-cache] Cache hit for {url}\n",
        f"Revalidated via HTTP 304; unchanged since {verified_iso}. Use the cached",
        "content below as if the browser had just returned it.\n",
    ]
    if original_prompt:
        parts.append(
            f'Original prompt: "{original_prompt}". If your angle differs,'
            " judge whether this reading still covers it.\n"
        )
    parts.append("----- BEGIN CACHED CONTENT -----")
    parts.append(content)
    parts.append("----- END CACHED CONTENT -----")
    return "\n".join(parts)


class SddCachePre(Extension):

    def execute(self, **kwargs):
        """Check cache before browser tool executes.

        If a cache hit is confirmed via HTTP 304, redirects the tool call
        to a safe no-op (action=list) and stores the cached content in
        agent.data for the post-extension to surface.
        """
        tool_name = kwargs.get("tool_name", "")
        tool_args = kwargs.get("tool_args", {})

        if tool_name != "browser":
            return

        if not isinstance(tool_args, dict):
            return

        action = tool_args.get("action", "")
        if action not in ("navigate", "content"):
            return

        url = tool_args.get("url", "")
        if not url:
            return

        _dbg(self.agent, f"fired action={action} url={url}")

        # Always store URL in agent.data so post-extension can cache responses
        if hasattr(self.agent, "data") and isinstance(self.agent.data, dict):
            self.agent.data[DATA_KEY_SDD_CACHE_HIT] = {"url": url}

        # Resolve cache entry
        cdir = _cache_dir(self.agent)
        key = _cache_key(url)
        cache_file = os.path.join(cdir, f"{key}.json")

        if not os.path.isfile(cache_file):
            _dbg(self.agent, "no cache file, exit")
            return

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                entry = json.load(f)
        except (OSError, json.JSONDecodeError):
            _dbg(self.agent, "cache file corrupt, exit")
            return

        etag = entry.get("etag", "")
        last_mod = entry.get("last_modified", "")

        # No validator means cannot revalidate — never serve from cache
        if not etag and not last_mod:
            _dbg(self.agent, "no etag/last-modified, cannot revalidate, bypass")
            return

        status = _head_revalidate(url, etag=etag, last_modified=last_mod)
        _dbg(self.agent, f"HEAD status={status}")

        if status != 304:
            _dbg(self.agent, "not 304, letting browser proceed")
            return

        content = entry.get("content", "")
        if not content:
            _dbg(self.agent, "cache file has empty content, bypass")
            return

        # Cache HIT — redirect to safe no-op and store hit data
        fetched_at = entry.get("fetched_at", 0)
        original_prompt = entry.get("prompt", "")
        hit_message = _format_hit_message(url, content, fetched_at, original_prompt)

        _dbg(self.agent, f"cache HIT, redirecting to list, {len(content)} bytes")

        # Mutate tool_args to a safe no-op action
        tool_args["action"] = "list"
        # Remove url-specific args to prevent side effects
        for key in ("url", "ref", "selector", "script", "text", "paths", "path"):
            tool_args.pop(key, None)

        # Update stored data with cache hit details for post-extension
        if hasattr(self.agent, "data") and isinstance(self.agent.data, dict):
            self.agent.data[DATA_KEY_SDD_CACHE_HIT] = {
                "url": url,
                "message": hit_message,
                "content": content,
                "hit": True,
            }
