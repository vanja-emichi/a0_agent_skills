"""Simplify-ignore session-end hook for Agent Zero.

When monologue ends (equivalent to Claude Code's Stop hook), restores
all files from backup and cleans up the cache.

Dependencies: stdlib only.
"""

import os
import sys

# Allow imports from the extensions/python directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from _simplify_ignore_util import (
    _cache_dir,
    restore_all,
)
from helpers.extension import Extension


class SimplifyIgnoreEnd(Extension):

    def execute(self, **kwargs):
        """Restore all files from backup when the monologue ends."""
        cache = _cache_dir(self.agent)
        restore_all(cache)
