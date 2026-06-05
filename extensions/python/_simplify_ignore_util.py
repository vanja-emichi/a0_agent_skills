"""Shared utilities for simplify-ignore extensions.

Hides `simplify-ignore-start/end` blocks during file reads by replacing them
with `BLOCK_<hash>` placeholders. After edits, expands placeholders back.
On session end, restores original content.

Cache storage: .a0proj/simplify-ignore-cache/
Cache files per file_id:
  <file_id>.bak    — backup of original (expanded) content
  <file_id>.path   — original file path
  <file_id>.block.<hash>   — block content
  <file_id>.reason.<hash>  — reason text
  <file_id>.prefix.<hash>  — comment prefix
  <file_id>.suffix.<hash>  — comment suffix

Dependencies: stdlib only (hashlib, os, re, shutil, glob, logging).
"""

import hashlib
import logging
import os
import re
import shutil

logger = logging.getLogger(__name__)

CACHE_SUBDIR = os.path.join(".a0proj", "simplify-ignore-cache")

# Pattern to detect start markers
_START_RE = re.compile(r"simplify-ignore-start")
_END_RE = re.compile(r"simplify-ignore-end")


def _cache_dir(agent) -> str:
    """Resolve the cache directory from agent config or plugin location."""
    if hasattr(agent, "config") and hasattr(agent.config, "project_folder"):
        base = agent.config.project_folder
        if base:
            return os.path.join(base, CACHE_SUBDIR)
    plugin_dir = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    return os.path.join(plugin_dir, CACHE_SUBDIR)


def _file_id(path: str) -> str:
    """Return SHA-1 hex digest of path, truncated to 16 chars."""
    return hashlib.sha1(path.encode("utf-8")).hexdigest()[:16]


def _block_hash(content: str) -> str:
    """Return SHA-1 hex digest of block content, truncated to 8 chars."""
    return hashlib.sha1(content.encode("utf-8")).hexdigest()[:8]


def _read_file(path: str) -> str:
    """Read file content, return empty string on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except (OSError, UnicodeDecodeError):
        return ""


def _write_file(path: str, content: str) -> None:
    """Write content to file, creating parent dirs as needed."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _has_trailing_newline(content: str) -> bool:
    """Check if content ends with a newline."""
    return content.endswith("\n") if content else False


def _detect_comment_suffix(line: str) -> str:
    """Detect comment suffix (*/ or -->) from a start marker line."""
    # Check for */ and --> after simplify-ignore-start
    start_idx = line.find("simplify-ignore-start")
    if start_idx >= 0:
        rest = line[start_idx + len("simplify-ignore-start"):]
        if "*/" in rest:
            return " */"
        if "-->" in rest:
            return " -->"
    return ""


def _extract_reason(line: str) -> str:
    """Extract reason text from a simplify-ignore-start line.

    Handles: /* simplify-ignore-start: reason */
             // simplify-ignore-start: reason
             # simplify-ignore-start: reason
    """
    start_idx = line.find("simplify-ignore-start")
    if start_idx < 0:
        return ""
    rest = line[start_idx + len("simplify-ignore-start"):]
    # Check for colon followed by reason
    match = re.match(r":\s*(.+)", rest)
    if not match:
        return ""
    reason = match.group(1)
    # Strip comment suffixes
    reason = re.sub(r"\s*\*/.*$", "", reason)
    reason = re.sub(r"\s*-->.*$", "", reason)
    reason = reason.rstrip()
    return reason


def filter_content(content: str, file_id: str, cache_dir: str) -> str:
    """Replace simplify-ignore blocks with BLOCK_<hash> placeholders.

    Saves block data to cache. Returns filtered content.
    If no blocks found, returns original content unchanged.
    """
    lines = content.split("\n")
    result_lines = []
    in_block = False
    block_buf = []
    block_start_line = ""
    prefix = ""
    suffix = ""
    reason = ""
    count = 0

    # Clean previous block cache files for this file_id
    _clean_block_cache(file_id, cache_dir)

    for line in lines:
        if not in_block:
            if _START_RE.search(line):
                in_block = True
                block_buf = [line]
                block_start_line = line
                prefix = line[:line.find("simplify-ignore-start")]
                suffix = _detect_comment_suffix(line)
                reason = _extract_reason(line)

                # Single-line block check
                if _END_RE.search(line):
                    in_block = False
                    block_content = "\n".join(block_buf)
                    h = _block_hash(block_content)
                    count += 1
                    _save_block(file_id, h, block_content, reason, prefix, suffix, cache_dir)
                    placeholder = _make_placeholder(prefix, h, reason, suffix)
                    result_lines.append(placeholder)
                    block_buf = []
                    continue
                continue
            result_lines.append(line)
        else:
            block_buf.append(line)
            if _END_RE.search(line):
                in_block = False
                block_content = "\n".join(block_buf)
                h = _block_hash(block_content)
                count += 1
                _save_block(file_id, h, block_content, reason, prefix, suffix, cache_dir)
                placeholder = _make_placeholder(prefix, h, reason, suffix)
                result_lines.append(placeholder)
                block_buf = []
                continue

    # Unclosed block → flush as-is with warning
    if in_block and block_buf:
        logger.warning("Unclosed simplify-ignore-start in content (block not hidden)")
        result_lines.extend(block_buf)

    filtered = "\n".join(result_lines)

    # Preserve trailing newline status of source
    if content and not content.endswith("\n") and filtered.endswith("\n"):
        filtered = filtered[:-1]
    elif content and content.endswith("\n") and not filtered.endswith("\n"):
        filtered += "\n"

    return filtered


def _make_placeholder(prefix: str, h: str, reason: str, suffix: str) -> str:
    """Build a BLOCK_<hash> placeholder line."""
    if reason:
        return f"{prefix}BLOCK_{h}: {reason}{suffix}"
    return f"{prefix}BLOCK_{h}{suffix}"


def _save_block(file_id: str, h: str, content: str, reason: str,
                 prefix: str, suffix: str, cache_dir: str) -> None:
    """Save block data to cache files."""
    os.makedirs(cache_dir, exist_ok=True)
    _write_file(os.path.join(cache_dir, f"{file_id}.block.{h}"), content)
    if reason:
        _write_file(os.path.join(cache_dir, f"{file_id}.reason.{h}"), reason)
    if prefix:
        _write_file(os.path.join(cache_dir, f"{file_id}.prefix.{h}"), prefix)
    if suffix:
        _write_file(os.path.join(cache_dir, f"{file_id}.suffix.{h}"), suffix)


def _clean_block_cache(file_id: str, cache_dir: str) -> None:
    """Remove all block cache files for a file_id."""
    if not os.path.isdir(cache_dir):
        return
    for fname in os.listdir(cache_dir):
        if fname.startswith(f"{file_id}."):
            # Only clean block-related files, not .bak or .path
            for kind in ("block.", "reason.", "prefix.", "suffix."):
                if kind in fname:
                    try:
                        os.remove(os.path.join(cache_dir, fname))
                    except OSError:
                        pass
                    break


def expand_content(content: str, file_id: str, cache_dir: str) -> str:
    """Expand BLOCK_<hash> placeholders back to original content.

    Uses progressive matching: full placeholder → prefix+hash+suffix → hash-only.
    Returns content with blocks expanded.
    """
    if not os.path.isdir(cache_dir):
        return content

    # Build block map: hash -> (block_content, prefix, suffix, reason)
    blocks = {}
    for fname in os.listdir(cache_dir):
        if not fname.startswith(f"{file_id}.block."):
            continue
        h = fname[len(f"{file_id}.block."):]
        block_content = _read_file(os.path.join(cache_dir, fname))
        if not block_content:
            continue
        prefix = _read_file(os.path.join(cache_dir, f"{file_id}.prefix.{h}"))
        suffix = _read_file(os.path.join(cache_dir, f"{file_id}.suffix.{h}"))
        reason = _read_file(os.path.join(cache_dir, f"{file_id}.reason.{h}"))
        blocks[h] = (block_content, prefix, suffix, reason)

    if not blocks:
        return content

    lines = content.split("\n")
    result_lines = []

    for line in lines:
        if "BLOCK_" not in line:
            result_lines.append(line)
            continue

        expanded = line
        for h, (block_content, prefix, suffix, reason) in blocks.items():
            if f"BLOCK_{h}" not in expanded:
                continue

            # Try full placeholder match
            placeholder = _make_placeholder(prefix, h, reason, suffix)
            if placeholder in expanded:
                expanded = expanded.replace(placeholder, block_content)
                continue

            # Fallback: prefix + BLOCK_hash + suffix (model altered reason)
            if reason:
                fuzzy = f"{prefix}BLOCK_{h}{suffix}"
                if fuzzy in expanded:
                    logger.warning(f"Placeholder BLOCK_{h} modified by model, using fuzzy match")
                    expanded = expanded.replace(fuzzy, block_content)
                    continue

            # Last resort: match just the hash token
            # Only if the hash isn't part of the original block content
            if f"BLOCK_{h}" not in block_content:
                if f"BLOCK_{h}" in expanded:
                    logger.warning(f"Placeholder BLOCK_{h} using hash-only fallback")
                    expanded = expanded.replace(f"BLOCK_{h}", block_content)

        result_lines.append(expanded)

    # Check for deleted protected blocks
    expanded_content = "\n".join(result_lines)
    for h, (block_content, _, _, _) in blocks.items():
        if f"BLOCK_{h}" not in expanded_content:
            first_line = block_content.split("\n")[0] if block_content else ""
            if first_line and first_line not in expanded_content:
                logger.warning(f"Protected block BLOCK_{h} was deleted by model")

    # Preserve trailing newline status
    if content and not content.endswith("\n") and expanded_content.endswith("\n"):
        expanded_content = expanded_content[:-1]
    elif content and content.endswith("\n") and not expanded_content.endswith("\n"):
        expanded_content += "\n"

    return expanded_content


def backup_file(file_path: str, file_id: str, cache_dir: str) -> None:
    """Create a backup of the original file."""
    os.makedirs(cache_dir, exist_ok=True)
    shutil.copy2(file_path, os.path.join(cache_dir, f"{file_id}.bak"))
    _write_file(os.path.join(cache_dir, f"{file_id}.path"), file_path)


def has_backup(file_id: str, cache_dir: str) -> bool:
    """Check if a backup exists for this file_id."""
    return os.path.isfile(os.path.join(cache_dir, f"{file_id}.bak"))


def has_blocks(file_path: str) -> bool:
    """Check if file contains simplify-ignore-start markers."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return _START_RE.search(f.read()) is not None
    except (OSError, UnicodeDecodeError):
        return False


def is_excluded_file(file_path: str) -> bool:
    """Check if file should be excluded from processing."""
    basename = os.path.basename(file_path).lower()
    return basename.startswith("simplify-ignore") or basename.startswith("simply-ignore")


def restore_all(cache_dir: str) -> None:
    """Restore all files from backup. Called on monologue_end."""
    if not os.path.isdir(cache_dir):
        return

    for fname in os.listdir(cache_dir):
        if not fname.endswith(".bak"):
            continue
        file_id = fname[:-4]  # strip .bak
        bak_path = os.path.join(cache_dir, fname)
        path_file = os.path.join(cache_dir, f"{file_id}.path")

        if not os.path.isfile(path_file):
            try:
                os.remove(bak_path)
            except OSError:
                pass
            continue

        orig_path = _read_file(path_file).strip()
        if not orig_path:
            try:
                os.remove(bak_path)
                os.remove(path_file)
            except OSError:
                pass
            continue

        if os.path.isfile(orig_path):
            # Restore original content
            shutil.copy2(bak_path, orig_path)
            # Clean up all cache files for this file_id
            _cleanup_file_cache(file_id, cache_dir)
        else:
            # File was moved/deleted — save as .recovered
            recovered = orig_path + ".recovered"
            os.makedirs(os.path.dirname(recovered) or ".", exist_ok=True)
            try:
                shutil.move(bak_path, recovered)
                logger.warning(f"{orig_path} was moved/deleted. Recovered to {recovered}")
            except OSError:
                pass
            _cleanup_file_cache(file_id, cache_dir)


def _cleanup_file_cache(file_id: str, cache_dir: str) -> None:
    """Remove all cache files for a file_id."""
    for fname in os.listdir(cache_dir):
        if fname.startswith(f"{file_id}."):
            try:
                os.remove(os.path.join(cache_dir, fname))
            except OSError:
                pass


def filter_file_in_place(file_path: str, file_id: str, cache_dir: str) -> bool:
    """Filter simplify-ignore blocks in-place. Returns True if blocks were found."""
    content = _read_file(file_path)
    if not content:
        return False
    filtered = filter_content(content, file_id, cache_dir)
    if filtered == content:
        return False
    _write_file(file_path, filtered)
    return True


def expand_file_in_place(file_path: str, file_id: str, cache_dir: str) -> bool:
    """Expand BLOCK_<hash> placeholders in-place. Returns True if expanded."""
    content = _read_file(file_path)
    if not content:
        return False
    expanded = expand_content(content, file_id, cache_dir)
    if expanded == content:
        return False
    _write_file(file_path, expanded)
    return True


def re_filter_file(file_path: str, file_id: str, cache_dir: str) -> bool:
    """Re-filter a file after expansion so blocks stay hidden on disk."""
    # Clean old block cache first (filter_content does this)
    return filter_file_in_place(file_path, file_id, cache_dir)
