"""
Tests for the tool_execute_after simplify-ignore extension.

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_simplify_ignore_after.py -v

Tests the after-extension class using only stdlib + unittest.mock - no Agent Zero runtime required.
"""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from helpers.simplify_ignore_shared import (
    get_cache,
    replace_blocks,
)


def _run(coro):
    """Run a coroutine in a fresh event loop."""
    return asyncio.run(coro)


# ===========================================================================
# After extension class tests
# ===========================================================================


class TestSimplifyIgnoreAfterExtension:
    """Tests for the tool_execute_after extension class."""

    def _make_after_ext(self):
        """Create a SimplifyIgnoreAfter instance with minimal mocking."""
        from extensions.python.tool_execute_after._simplify_ignore import (
            SimplifyIgnoreAfter,
        )

        ext = SimplifyIgnoreAfter.__new__(SimplifyIgnoreAfter)
        ext.agent = MagicMock()
        ext.kwargs = {}
        return ext

    def test_non_text_editor_tool_ignored(self):
        """Non-text_editor tool calls are ignored."""
        ext = self._make_after_ext()
        response = MagicMock()
        response.message = "something"
        # Should not raise or modify
        _run(ext.execute(tool_name="code_execution_tool", response=response))

    def test_no_markers_unchanged(self):
        """Response without markers is passed through unchanged."""
        ext = self._make_after_ext()
        response = MagicMock()
        response.message = "const x = 1;"
        _run(ext.execute(tool_name="text_editor", response=response))
        assert response.message == "const x = 1;"

    def test_with_markers_replaces_blocks(self):
        """Response with markers has blocks replaced with placeholders."""
        # Clear the global cache first
        get_cache().clear()

        ext = self._make_after_ext()
        response = MagicMock()
        response.message = (
            "line1\n"
            "/* simplify-ignore-start: reason */\n"
            "secret_code();\n"
            "/* simplify-ignore-end */\n"
            "line2"
        )
        _run(ext.execute(tool_name="text_editor", response=response))

        assert "BLOCK_" in response.message
        assert "secret_code()" not in response.message
        assert "line1" in response.message

    def test_none_response_handled(self):
        """None response does not crash."""
        ext = self._make_after_ext()
        _run(ext.execute(tool_name="text_editor", response=None))

    def test_none_tool_name_handled(self):
        """None tool_name does not crash."""
        ext = self._make_after_ext()
        _run(ext.execute(tool_name=None, response=MagicMock()))


# ===========================================================================
# No-op when not relevant
# ===========================================================================


class TestNoOp:
    def test_other_tools_ignored(self):
        """Non-text_editor tool calls are completely ignored."""
        cache = get_cache()
        cache.clear()

        # After extension
        from extensions.python.tool_execute_after._simplify_ignore import (
            SimplifyIgnoreAfter,
        )

        ext_after = SimplifyIgnoreAfter.__new__(SimplifyIgnoreAfter)
        ext_after.agent = MagicMock()
        ext_after.kwargs = {}
        response = MagicMock()
        response.message = "/* simplify-ignore-start */ code /* simplify-ignore-end */"
        _run(ext_after.execute(tool_name="browser", response=response))
        # Message should be unchanged (extension ignored non-text_editor)
        assert "simplify-ignore-start" in response.message

    def test_no_modification_of_disk(self):
        """The extension never writes to disk - only modifies in-memory data."""
        cache = get_cache()
        cache.clear()

        content = (
            "/* simplify-ignore-start */\n"
            "code();\n"
            "/* simplify-ignore-end */"
        )
        result = replace_blocks(content, cache)
        # replace_blocks only returns a string, never touches files
        assert isinstance(result, str)
        assert cache.size() == 1
