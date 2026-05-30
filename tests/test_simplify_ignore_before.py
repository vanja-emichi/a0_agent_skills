"""
Tests for the tool_execute_before simplify-ignore extension.

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_simplify_ignore_before.py -v

Tests the before-extension class using only stdlib + unittest.mock - no Agent Zero runtime required.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from helpers.simplify_ignore_shared import (
    generate_hash,
    get_cache,
)


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    return asyncio.run(coro)


# ===========================================================================
# Before extension class tests
# ===========================================================================


class TestSimplifyIgnoreBeforeExtension:
    """Tests for the tool_execute_before extension class."""

    def _make_before_ext(self):
        """Create a SimplifyIgnoreBefore instance with minimal mocking."""
        from extensions.python.tool_execute_before._simplify_ignore import (
            SimplifyIgnoreBefore,
        )

        ext = SimplifyIgnoreBefore.__new__(SimplifyIgnoreBefore)
        ext.agent = MagicMock()
        ext.kwargs = {}
        return ext

    def test_non_text_editor_tool_ignored(self):
        """Non-text_editor tool calls are ignored."""
        ext = self._make_before_ext()
        tool_args = {"action": "write", "content": "code"}
        _run(ext.execute(tool_args=tool_args, tool_name="code_execution_tool"))
        assert tool_args["content"] == "code"  # unchanged

    def test_read_action_ignored(self):
        """Read actions are ignored (only write/patch expanded)."""
        ext = self._make_before_ext()
        tool_args = {"action": "read", "content": "BLOCK_abcdef12"}
        _run(ext.execute(tool_args=tool_args, tool_name="text_editor"))
        assert tool_args["content"] == "BLOCK_abcdef12"  # unchanged

    def test_write_with_placeholder_expanded(self):
        """Write action with placeholder has it expanded."""
        cache = get_cache()
        cache.clear()

        original = "/* simplify-ignore-start */\ncode();\n/* simplify-ignore-end */"
        hash_key = generate_hash(original)
        cache.store(hash_key, original)

        ext = self._make_before_ext()
        tool_args = {
            "action": "write",
            "path": "/tmp/test.py",
            "content": f"before\n/* BLOCK_{hash_key} */\nafter",
        }
        _run(ext.execute(tool_args=tool_args, tool_name="text_editor"))

        assert "code()" in tool_args["content"]
        assert "BLOCK_" not in tool_args["content"]

    def test_patch_with_new_text_expanded(self):
        """Patch action with new_text containing placeholder expands it."""
        cache = get_cache()
        cache.clear()

        original = "/* simplify-ignore-start */\nsecret();\n/* simplify-ignore-end */"
        hash_key = generate_hash(original)
        cache.store(hash_key, original)

        ext = self._make_before_ext()
        tool_args = {
            "action": "patch",
            "path": "/tmp/test.py",
            "new_text": f"/* BLOCK_{hash_key} */",
        }
        _run(ext.execute(tool_args=tool_args, tool_name="text_editor"))

        assert "secret()" in tool_args["new_text"]

    def test_empty_cache_no_expansion(self):
        """With empty cache, no expansion happens."""
        cache = get_cache()
        cache.clear()

        ext = self._make_before_ext()
        tool_args = {
            "action": "write",
            "content": "/* BLOCK_deadbeef */",
        }
        _run(ext.execute(tool_args=tool_args, tool_name="text_editor"))

        # No crash, content unchanged (cache was empty so extension exited early)
        assert tool_args["content"] == "/* BLOCK_deadbeef */"

    def test_none_args_handled(self):
        """None tool_args does not crash."""
        ext = self._make_before_ext()
        _run(ext.execute(tool_args=None, tool_name="text_editor"))

    def test_non_dict_args_handled(self):
        """Non-dict tool_args does not crash."""
        ext = self._make_before_ext()
        _run(ext.execute(tool_args="not a dict", tool_name="text_editor"))
