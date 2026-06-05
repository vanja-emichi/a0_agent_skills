"""Simplify-ignore post-patch hook for Agent Zero.

After text_editor patches a file, expands BLOCK_<hash> placeholders
back to original content, then re-filters so blocks stay hidden on disk.
Also updates the backup with the expanded version.

Dependencies: stdlib only.
"""

import os
import sys

# Allow imports from the extensions/python directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from _simplify_ignore_util import (
    _cache_dir,
    _file_id,
    _read_file,
    _write_file,
    expand_file_in_place,
    has_backup,
    re_filter_file,
)
from helpers.extension import Extension


class SimplifyIgnorePatchAfter(Extension):

    def execute(self, **kwargs):
        """After a patch, expand placeholders, save expanded backup, re-filter."""
        data = kwargs.get("data", {})
        if not isinstance(data, dict):
            return

        file_path = data.get("path", "")
        if not file_path:
            return

        file_path = os.path.normpath(file_path)

        # Skip if not a real file
        if not os.path.isfile(file_path):
            return

        cache = _cache_dir(self.agent)
        fid = _file_id(file_path)

        # Only process if we have a backup (file was filtered)
        if not has_backup(fid, cache):
            return

        # Expand placeholders back to original content
        expand_file_in_place(file_path, fid, cache)

        # Save expanded version as new backup (includes model's changes)
        expanded = _read_file(file_path)
        if expanded:
            _write_file(os.path.join(cache, f"{fid}.bak"), expanded)

        # Re-filter in-place so blocks stay hidden on disk
        re_filter_file(file_path, fid, cache)
