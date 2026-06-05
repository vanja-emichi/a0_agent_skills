"""SDD cache post-tool hook for Agent Zero.

Runs after browser tool execution. Two responsibilities:
1. If the pre-extension flagged a cache hit, replaces the tool response with
   the cached content (the actual browser call was redirected to a no-op).
2. On cache misses, stores the response content with ETag/Last-Modified
   metadata captured via a HEAD request for future revalidation.

Cache key: SHA-256 of URL (first 32 hex chars).
Cache storage: .a0proj/sdd-cache/<hash>.json

Dependencies: stdlib only (hashlib, json, os, urllib.request, datetime).
"""

import hashlib
import http.client
import json
import logging
import os
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

from helpers.extension import Extension

logger = logging.getLogger(__name__)

# Must match the pre-extension's constant
DATA_KEY_SDD_CACHE_HIT = "sdd_cache_pending_hit"
CACHE_SUBDIR = os.path.join(".a0proj", "sdd-cache")
HEAD_TIMEOUT = 5


def _cache_key(url: str) -> str:
    """Return SHA-256 hex digest of URL, truncated to 32 chars (128 bits)."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]


def _cache_dir(agent) -> str:
    """Resolve the cache directory from agent config or plugin location."""
    if hasattr(agent, "config") and hasattr(agent.config, "project_folder"):
        base = agent.config.project_folder
        if base:
            return os.path.join(base, CACHE_SUBDIR)
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
            f.write(f"{ts} [post] {msg}\n")
    except OSError:
        pass


def _extract_final_headers(headers: http.client.HTTPMessage) -> tuple[str, str]:
    """Extract ETag and Last-Modified from the final response headers."""
    etag = headers.get("ETag", "") or ""
    last_mod = headers.get("Last-Modified", "") or ""
    return etag, last_mod


def _head_validators(url: str) -> tuple[str, str]:
    """Issue a HEAD request and return (etag, last_modified) from the origin.

    Follows redirects and uses only the final response's headers to avoid
    picking up validators from intermediate hops.
    """
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=HEAD_TIMEOUT) as resp:
            return _extract_final_headers(resp.headers)
    except (urllib.error.URLError, OSError):
        return "", ""


def _extract_content(response) -> str:
    """Extract text content from a tool Response object."""
    if response is None:
        return ""
    # Response is a dataclass with .message attribute
    msg = getattr(response, "message", None)
    if msg and isinstance(msg, str):
        return msg
    # Fallback: try common attribute names
    for attr in ("result", "output", "text", "content", "body"):
        val = getattr(response, attr, None)
        if val and isinstance(val, str):
            return val
    # If response itself is a string
    if isinstance(response, str):
        return response
    return ""


def _write_cache_entry(cache_file: str, url: str, content: str,
                        etag: str, last_modified: str) -> None:
    """Atomically write a cache entry JSON file."""
    cache_dir = os.path.dirname(cache_file)
    os.makedirs(cache_dir, exist_ok=True)

    entry = {
        "url": url,
        "etag": etag,
        "last_modified": last_modified,
        "content": content,
        "fetched_at": int(time.time()),
    }

    tmp = f"{cache_file}.{os.getpid()}.tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
        os.replace(tmp, cache_file)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass


class SddCachePost(Extension):

    def execute(self, **kwargs):
        """Handle cache hit replacement or store new cache entries.

        If the pre-extension flagged a cache hit, the browser tool was
        redirected to a no-op action. Replace the response with the cached
        content.

        Otherwise, if the browser fetched a URL, store the response content
        with ETag/Last-Modified metadata for future revalidation.
        """
        tool_name = kwargs.get("tool_name", "")
        response = kwargs.get("response")

        if tool_name != "browser":
            return

        if not self.agent or not hasattr(self.agent, "data"):
            return
        if not isinstance(self.agent.data, dict):
            return

        pending = self.agent.data.get(DATA_KEY_SDD_CACHE_HIT)
        if not isinstance(pending, dict):
            return

        # Always clean up the pending flag
        try:
            del self.agent.data[DATA_KEY_SDD_CACHE_HIT]
        except KeyError:
            pass

        url = pending.get("url", "")
        if not url:
            _dbg(self.agent, "no url in pending data, exit")
            return

        # --- Case 1: Cache HIT (pre-extension redirected to no-op) ---
        if pending.get("hit"):
            hit_message = pending.get("message", "")
            if hit_message and response is not None:
                _dbg(self.agent, f"serving cache hit for {url}")
                response.message = hit_message
            return

        # --- Case 2: Cache MISS — store response for future use ---
        _dbg(self.agent, f"cache miss for {url}, storing response")

        content = _extract_content(response)
        if not content:
            _dbg(self.agent, "could not extract content from response, exit")
            return

        _dbg(self.agent, f"extracted content bytes={len(content)}")

        # Get validators from origin via HEAD request
        etag, last_mod = _head_validators(url)
        _dbg(self.agent, f"HEAD etag={etag!r} last_modified={last_mod!r}")

        if not etag and not last_mod:
            _dbg(self.agent, "no validator from origin, not caching")
            # Remove any stale entry
            cdir = _cache_dir(self.agent)
            key = _cache_key(url)
            stale = os.path.join(cdir, f"{key}.json")
            try:
                os.unlink(stale)
            except OSError:
                pass
            return

        # Write cache entry
        cdir = _cache_dir(self.agent)
        key = _cache_key(url)
        cache_file = os.path.join(cdir, f"{key}.json")
        _write_cache_entry(cache_file, url, content, etag, last_mod)
        _dbg(self.agent, f"wrote cache file {cache_file}")
