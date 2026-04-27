"""
simplify_ignore_utils.py
Shared helpers for the simplify-ignore Agent Zero extension.

Ported from simplify-ignore.sh (Claude Code hook) — preserves exact logic:
  - block_hash   : sha1[:8] of raw buf string (start line + content + end line)
  - filter_content: replace simplify-ignore-start/end blocks with BLOCK_<hash> placeholders
  - expand_content: replace BLOCK_<hash> placeholders back with original block content

Cache key and structure used by all three hook-point extensions:
  context.data[CACHE_KEY] = {
      file_path: {
          'original': str,       # real file content (updated after each model edit)
          'blocks': {
              hash8: {
                  'content': str,   # full block text incl. start+end marker lines
                  'reason':  str,   # optional reason label ('' if none)
                  'prefix':  str,   # text before 'simplify-ignore-start' on that line
                  'suffix':  str,   # ' */' | ' -->' | ''
              }
          }
      }
  }
"""
import hashlib
import re
import logging
import sys
import fcntl
import time

CACHE_KEY = 'simplify_ignore_cache'

logger = logging.getLogger(__name__)


# ── File Locking ─────────────────────────────────────────────────────────────

def _acquire_lock(filepath, timeout=5.0):
    """Acquire a non-blocking exclusive lock with timeout.

    Uses fcntl.flock with LOCK_EX | LOCK_NB in a retry loop.
    Creates a <filepath>.lock file on demand.
    Returns the lock file descriptor on success, or None on timeout (fail-open).
    """
    lock_path = str(filepath) + ".lock"
    try:
        lock_fd = open(lock_path, "w")
    except OSError:
        return None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_fd
        except (IOError, OSError):
            time.sleep(0.1)
    lock_fd.close()
    return None  # fail-open


def _release_lock(lock_fd):
    """Release a previously acquired lock.

    Safe to call with None or already-closed fd.
    """
    if lock_fd and not lock_fd.closed:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
        except (IOError, OSError):
            pass


# ── Hashing ───────────────────────────────────────────────────────────────────

def _block_hash(content: str) -> str:
    """SHA-1 of content (encoded UTF-8), first 8 hex chars.
    Mirrors: block_hash() { printf '%s' "$1" | shasum | cut -c1-8; }
    """
    return hashlib.sha1(content.encode('utf-8', errors='replace')).hexdigest()[:8]


def _placeholder_line(h: str, prefix: str, suffix: str, reason: str) -> str:
    if reason:
        return f'{prefix}BLOCK_{h}: {reason}{suffix}'
    return f'{prefix}BLOCK_{h}{suffix}'


# ── Marker line parsing ───────────────────────────────────────────────────────

def _parse_start_line(line: str):
    """
    Parse a line that contains 'simplify-ignore-start'.

    Returns (prefix, suffix, reason):
      prefix  — everything before 'simplify-ignore-start' (the comment opener)
      suffix  — ' */'  if line contains '*/'
                ' -->' if line contains '-->'
                ''     otherwise
      reason  — text after 'simplify-ignore-start:' stripped of suffix/whitespace,
                or '' if no colon-reason is present

    Mirrors the prefix/suffix/reason extraction in bash filter_file().
    """
    idx = line.index('simplify-ignore-start')
    prefix = line[:idx]

    suffix = ''
    if '*/' in line:
        suffix = ' */'
    elif '-->' in line:
        suffix = ' -->'

    reason = ''
    marker = 'simplify-ignore-start:'
    if marker in line:
        after = line[line.index(marker) + len(marker):]
        # Strip closing comment delimiter and trailing whitespace
        after = re.sub(r'\s*\*/.*$', '', after)
        after = re.sub(r'\s*-->.*$', '', after)
        reason = after.strip()

    return prefix, suffix, reason


# ── Filter: real code → placeholders ─────────────────────────────────────────

def filter_content(content: str, file_path: str = '<unknown>'):
    """
    Scan *content* for simplify-ignore-start/end blocks and replace each
    span (start line, interior, end line) with a single BLOCK_<hash> line.

    Faithfully mirrors bash filter_file():
      - buf starts with the start-marker line itself
      - interior lines are appended (newline-joined)
      - end-marker line is appended before hashing
      - single-line block (start+end on same line): the whole line is the buf
      - unclosed block: flushed verbatim to output with a stderr warning
      - trailing-newline status of *content* is preserved in filtered output

    Returns:
      filtered   (str)  — content with block spans replaced by placeholder lines
      blocks     (dict) — {hash8: {content, reason, prefix, suffix}}
      had_blocks (bool) — True when ≥1 block was replaced
    """
    source_ends_nl = content.endswith('\n')
    lines = content.splitlines()

    output_lines = []
    blocks: dict = {}
    in_block = False
    buf_lines: list = []
    reason = prefix = suffix = ''
    count = 0

    for line in lines:
        # ── Not currently inside a block ──────────────────────────────────────
        if not in_block:
            if 'simplify-ignore-start' not in line:
                output_lines.append(line)
                continue

            # Start marker found
            in_block = True
            buf_lines = [line]
            prefix, suffix, reason = _parse_start_line(line)

            # ── Single-line block: start and end on same line ─────────────────
            if 'simplify-ignore-end' in line:
                in_block = False
                buf = '\n'.join(buf_lines)
                h = _block_hash(buf)
                count += 1
                blocks[h] = {'content': buf, 'reason': reason,
                             'prefix': prefix, 'suffix': suffix}
                output_lines.append(_placeholder_line(h, prefix, suffix, reason))
                buf_lines = []
                reason = prefix = suffix = ''
            # else: multi-line block opened — start line is NOT written to output
            continue

        # ── Inside a multi-line block: accumulate ─────────────────────────────
        buf_lines.append(line)

        if 'simplify-ignore-end' not in line:
            continue

        # End marker found: close block
        in_block = False
        buf = '\n'.join(buf_lines)
        h = _block_hash(buf)
        count += 1
        blocks[h] = {'content': buf, 'reason': reason,
                     'prefix': prefix, 'suffix': suffix}
        output_lines.append(_placeholder_line(h, prefix, suffix, reason))
        buf_lines = []
        reason = prefix = suffix = ''

    # ── Unclosed block: flush verbatim with warning ───────────────────────────
    if in_block and buf_lines:
        logger.warning("Warning: unclosed simplify-ignore-start in %s (block not hidden)", file_path)
        output_lines.extend(buf_lines)

    # ── Reconstruct, preserving trailing-newline status ───────────────────────
    filtered = '\n'.join(output_lines)
    if source_ends_nl:
        filtered += '\n'

    return filtered, blocks, count > 0


# ── Expand: placeholders → real code ─────────────────────────────────────────

def expand_content(content: str, blocks: dict, file_path: str = '<unknown>'):
    """
    Expand BLOCK_<hash> placeholders back to their original block content.

    Implements the same three-level progressive fallback as the bash hook:
      1. Full placeholder  : prefix + 'BLOCK_h: reason' + suffix
      2. No-reason match   : prefix + 'BLOCK_h' + suffix
      3. Hash-only fallback: 'BLOCK_h' anywhere in line

    A line containing a placeholder that spans multiple original lines will be
    expanded to multiple lines in the output.

    Also warns (stderr) if a protected block appears to have been deleted by
    the model (neither placeholder nor first line of block found after expansion).

    Returns expanded (str) — content with all placeholders replaced.
    """
    source_ends_nl = content.endswith('\n')
    lines = content.splitlines()
    output_lines: list = []

    for line in lines:
        if 'BLOCK_' not in line:
            output_lines.append(line)
            continue

        # Try to expand every known hash found on this line
        for h, info in blocks.items():
            if f'BLOCK_{h}' not in line:
                continue

            prefix      = info['prefix']
            suffix      = info['suffix']
            reason      = info['reason']
            block_text  = info['content']

            # ── Level 1: full placeholder (with reason) ───────────────────────
            placeholder = _placeholder_line(h, prefix, suffix, reason)

            if placeholder in line:
                line = line.replace(placeholder, block_text)

            # ── Level 2 & 3: fallbacks if BLOCK_h still present ──────────────
            # (only if the block_text itself doesn't contain the hash token,
            #  to avoid infinite replacement)
            if f'BLOCK_{h}' in line and f'BLOCK_{h}' not in block_text:
                logger.warning("Warning: placeholder BLOCK_%s in %s was modified by model, using fuzzy match", h, file_path)
                # Level 2: prefix+hash+suffix (no reason)
                fuzzy = f'{prefix}BLOCK_{h}{suffix}'
                if fuzzy in line:
                    line = line.replace(fuzzy, block_text)

                # Level 3: bare hash token
                if f'BLOCK_{h}' in line and f'BLOCK_{h}' not in block_text:
                    line = line.replace(f'BLOCK_{h}', block_text)

        # A replaced placeholder may expand to multiple lines
        output_lines.extend(line.split('\n'))

    # ── Warn about deleted blocks ─────────────────────────────────────────────
    expanded_joined = '\n'.join(output_lines)
    for h, info in blocks.items():
        if f'BLOCK_{h}' not in expanded_joined:
            first_line = info['content'].splitlines()[0] if info['content'] else ''
            if first_line and first_line not in expanded_joined:
                logger.warning("Warning: protected block BLOCK_%s was deleted by model in %s", h, file_path)

    result = '\n'.join(output_lines)
    if source_ends_nl:
        result += '\n'
    return result


# ── Disk manifest for crash recovery ─────────────────────────────────────────

import json
from pathlib import Path as _Path

MANIFEST_DIR = _Path("/tmp/.a0_simplify_ignore")


def _safe_manifest_name(file_path: str) -> str:
    """Generate a safe filename for the manifest from a file path."""
    return hashlib.sha256(file_path.encode("utf-8")).hexdigest()[:16] + ".json"


def write_manifest(file_path: str, original: str, blocks: dict) -> None:
    """Write a crash-recovery manifest to disk.

    Called by the before hook after filtering a file. If the process crashes
    before restore, recover_from_manifests() can use this to restore the
    original content.
    """
    try:
        MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
        manifest_path = MANIFEST_DIR / _safe_manifest_name(file_path)
        manifest_path.write_text(
            json.dumps({
                "file_path": file_path,
                "original": original,
                "blocks": {
                    h: {
                        "content": info["content"],
                        "reason": info["reason"],
                        "prefix": info["prefix"],
                        "suffix": info["suffix"],
                    }
                    for h, info in blocks.items()
                },
            }, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception:
        # Manifest write failure must not break the filtering pipeline
        pass


def clear_manifest(file_path: str) -> None:
    """Remove the manifest after successful restore.

    Called by the restore hook after successfully writing back original content.
    """
    try:
        manifest_path = MANIFEST_DIR / _safe_manifest_name(file_path)
        manifest_path.unlink(missing_ok=True)
    except Exception:
        pass


def recover_from_manifests() -> list[str]:
    """Recover files left with BLOCK_ placeholders from a previous crash.

    Scans the manifest directory for recovery manifests. For each manifest,
    if the target file still contains BLOCK_ placeholders, writes back the
    original content and removes the manifest.

    Called at startup (startup_migration) and optionally at monologue_start.
    Returns list of recovered file paths.
    """
    recovered: list[str] = []
    if not MANIFEST_DIR.exists():
        return recovered

    for manifest_path in list(MANIFEST_DIR.glob("*.json")):
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            file_path = data["file_path"]
            original = data["original"]
            target = _Path(file_path)

            if target.exists():
                current = target.read_text(errors="replace")
                if "BLOCK_" in current:
                    target.write_text(original, encoding="utf-8")
                    recovered.append(file_path)
            else:
                # File was deleted — save original to .recovered
                recovered_path = _Path(file_path + ".recovered")
                recovered_path.write_text(original, encoding="utf-8")
                recovered.append(f"{file_path} (saved to .recovered)")

            manifest_path.unlink()
        except Exception:
            pass

    return recovered


def cleanup_stale_lock_files():
    """Remove stale .lock files from the manifest directory.

    Called at startup to clean up any leftover lock files from
    a previous crash.
    """
    try:
        if not MANIFEST_DIR.exists():
            return
        for lock_file in list(MANIFEST_DIR.glob("*.lock")):
            try:
                lock_file.unlink()
            except OSError:
                pass
    except Exception:
        pass
