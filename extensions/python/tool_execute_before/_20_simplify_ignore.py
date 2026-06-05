"""Simplify-ignore pre-tool hook for Agent Zero.

Intercepts text_editor action=read operations before execution.
When reading a file that contains simplify-ignore-start blocks:
- Backs up the original file
- Replaces blocks with BLOCK_<hash> placeholders in-place
- The text_editor will return the filtered version

Cache key: SHA-1 of file path (first 16 hex chars).
Cache storage: .a0proj/simplify-ignore-cache/

Dependencies: stdlib only.
"""

import os
import sys

# Allow imports from the extensions/python directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from _simplify_ignore_util import (
    _cache_dir,
    _file_id,
    backup_file,
    filter_file_in_place,
    has_backup,
    has_blocks,
    is_excluded_file,
)
from helpers.extension import Extension


class SimplifyIgnoreBefore(Extension):

    def execute(self, **kwargs):
        """Check if text_editor read targets a file with simplify-ignore blocks.

        If so, back up the file and filter blocks in-place so the read
        returns content with BLOCK_<hash> placeholders instead of the
        protected code.
        """
        tool_name = kwargs.get("tool_name", "")
        if tool_name != "text_editor":
            return

        tool_args = kwargs.get("tool_args", {})
        if not isinstance(tool_args, dict):
            return

        action = str(tool_args.get("action", "")).lower()
        if action != "read":
            return

        file_path = str(tool_args.get("path", ""))
        if not file_path:
            return

        # Normalize path
        file_path = os.path.normpath(file_path)

        # Skip excluded files (the hook's own source/docs)
        if is_excluded_file(file_path):
            return

        # File must exist
        if not os.path.isfile(file_path):
            return

        # Resolve cache dir
        cache = _cache_dir(self.agent)
        fid = _file_id(file_path)

        # If backup exists, file is already filtered — skip
        if has_backup(fid, cache):
            return

        # Quick check: does file contain simplify-ignore-start?
        if not has_blocks(file_path):
            return

        # Back up the original file
        backup_file(file_path, fid, cache)

        # Filter in-place (replaces blocks with placeholders on disk)
        filter_file_in_place(file_path, fid, cache)
