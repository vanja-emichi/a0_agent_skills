"""Shared block cache and utilities for simplify-ignore extensions.

Used by both tool_execute_before and tool_execute_after extension files.
Provides thread-safe block cache, hash generation, marker detection,
placeholder creation, block replacement, and placeholder expansion.
"""

from __future__ import annotations

import hashlib
import logging
import re
import threading
from typing import Optional

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Marker regex patterns (from upstream spec)
# ---------------------------------------------------------------------------

START_RE = re.compile(
    r"(?:/\*|#|<!--)\s*simplify-ignore-start(?:\s*:\s*([^*\n]*))?\s*(?:\*/|-->|)?"
)

END_RE = re.compile(
    r"(?:/\*|#|<!--)\s*simplify-ignore-end\s*(?:\*/|-->|)?"
)

# Core hash pattern - used to locate placeholders in tool args
BLOCK_HASH_RE = re.compile(r"BLOCK_([0-9a-f]{12})")


# ---------------------------------------------------------------------------
# Thread-safe block cache
# ---------------------------------------------------------------------------


class BlockCache:
    """Thread-safe dict keyed by hash, storing original code block text."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._blocks: dict[str, str] = {}

    def store(self, hash_key: str, content: str) -> None:
        with self._lock:
            self._blocks[hash_key] = content

    def retrieve(self, hash_key: str) -> Optional[str]:
        with self._lock:
            return self._blocks.get(hash_key)

    def has(self, hash_key: str) -> bool:
        with self._lock:
            return hash_key in self._blocks

    def clear(self) -> None:
        with self._lock:
            self._blocks.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._blocks)


# Module-level singleton cache - cleared naturally when the process restarts
# (each Agent Zero conversation starts a fresh Python process).
_cache = BlockCache()


def get_cache() -> BlockCache:
    """Return the global block cache singleton."""
    return _cache


# ---------------------------------------------------------------------------
# Hash generation
# ---------------------------------------------------------------------------


def generate_hash(content: str) -> str:
    """SHA-256 of *content*, truncated to 12 hex characters."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Comment-style detection
# ---------------------------------------------------------------------------


def detect_comment_style(line: str) -> tuple[str, str]:
    """Return (prefix, suffix) for the comment style found in *line*.

    Supported styles:
        C/JS/Java   -> ("/*", "*/")
        Python/Ruby/Shell -> ("#", "")
        HTML/XML    -> ("<!--", "-->")

    Falls back to C-style when nothing matches.
    """
    stripped = line.strip()
    if stripped.startswith("/*") or stripped.startswith("*"):
        return ("/*", "*/")
    if stripped.startswith("<!--"):
        return ("<!--", "-->")
    if stripped.startswith("#"):
        return ("#", "")
    return ("/*", "*/")


# ---------------------------------------------------------------------------
# Placeholder creation
# ---------------------------------------------------------------------------


def make_placeholder(
    hash_key: str, reason: Optional[str], prefix: str, suffix: str
) -> str:
    """Build a placeholder string in the detected comment style.

    Examples::

        make_placeholder("a1b2c3d4", "perf", "/*", "*/")
        -> "/* BLOCK_a1b2c3d4: perf */"
        make_placeholder("a1b2c3d4", None, "#", "")
        -> "# BLOCK_a1b2c3d4"
    """
    if reason and reason.strip():
        parts = f"{prefix} BLOCK_{hash_key}: {reason.strip()}"
    else:
        parts = f"{prefix} BLOCK_{hash_key}"
    if suffix:
        parts += f" {suffix}"
    return parts


# ---------------------------------------------------------------------------
# Block replacement (used by tool_execute_after on read responses)
# ---------------------------------------------------------------------------


def replace_blocks(content: str, cache: BlockCache) -> str:
    """Replace every simplify-ignore block with a placeholder line.

    Scans *content* line-by-line for start/end marker pairs.  Each matched
    block (multi-line or single-line) is stored in *cache* keyed by its
    SHA-256 hash (12 chars) and replaced with a single placeholder line
    preserving the original comment style and optional reason.

    Unclosed blocks are passed through unchanged with a warning.
    """
    lines = content.split("\n")
    result: list[str] = []
    in_block = False
    block_buf: list[str] = []
    reason: Optional[str] = None
    prefix = "/*"
    suffix = "*/"

    for line in lines:
        if not in_block:
            start_match = START_RE.search(line)
            if start_match:
                in_block = True
                block_buf = [line]
                raw_reason = (start_match.group(1) or "").strip()
                # Strip trailing comment closers that the regex may have captured
                for closer in ("*/", "-->"):
                    if raw_reason.endswith(closer):
                        raw_reason = raw_reason[: -len(closer)].rstrip()
                reason = raw_reason or None
                prefix, suffix = detect_comment_style(line)

                # Single-line block (start + end on the same line)
                if END_RE.search(line, start_match.end()):
                    in_block = False
                    block_text = "\n".join(block_buf)
                    hash_key = generate_hash(block_text)
                    cache.store(hash_key, block_text)
                    result.append(make_placeholder(hash_key, reason, prefix, suffix))
                    block_buf = []
                    reason = None
                continue
            result.append(line)
        else:
            block_buf.append(line)
            if END_RE.search(line):
                in_block = False
                block_text = "\n".join(block_buf)
                hash_key = generate_hash(block_text)
                cache.store(hash_key, block_text)
                result.append(make_placeholder(hash_key, reason, prefix, suffix))
                block_buf = []
                reason = None

    # Unclosed block -> pass through unchanged
    if in_block and block_buf:
        _log.warning("simplify-ignore: unclosed block, passing through")
        result.extend(block_buf)

    return "\n".join(result)


# ---------------------------------------------------------------------------
# Placeholder expansion (used by tool_execute_before on write/patch args)
# ---------------------------------------------------------------------------


def expand_placeholders(text: str, cache: BlockCache) -> str:
    """Expand every BLOCK_<hash> placeholder back to its original code.

    Works line-by-line: any line containing BLOCK_<hash> whose hash is
    present in *cache* is replaced in its entirety with the cached block
    content.  Lines whose hash is not found are left unchanged (with a
    warning).
    """
    lines = text.split("\n")
    result: list[str] = []

    for line in lines:
        match = BLOCK_HASH_RE.search(line)
        if match:
            hash_key = match.group(1)
            original = cache.retrieve(hash_key)
            if original is not None:
                result.append(original)
                continue
            _log.warning("simplify-ignore: cache miss for BLOCK_%s", hash_key)
        result.append(line)

    return "\n".join(result)
