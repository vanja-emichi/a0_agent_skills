"""
Tests for helpers.simplify_ignore_shared — hash, cache, regex, comment detection,
replace_blocks, expand_placeholders, round-trip.

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_simplify_ignore_shared.py -v

Tests the shared module using only stdlib + unittest.mock - no Agent Zero runtime required.
"""

from __future__ import annotations

import hashlib
import logging
from unittest.mock import MagicMock

import pytest

from helpers.simplify_ignore_shared import (
    BlockCache,
    BLOCK_HASH_RE,
    END_RE,
    START_RE,
    detect_comment_style,
    expand_placeholders,
    generate_hash,
    get_cache,
    make_placeholder,
    replace_blocks,
)


# ===========================================================================
# 1. Hash generation
# ===========================================================================


class TestGenerateHash:
    def test_deterministic(self):
        """Same content always produces the same hash."""
        h1 = generate_hash("hello world")
        h2 = generate_hash("hello world")
        assert h1 == h2

    def test_twelve_hex_chars(self):
        """Hash is exactly 12 hex characters."""
        h = generate_hash("test content")
        assert len(h) == 12
        assert all(c in "0123456789abcdef" for c in h)

    def test_sha256_truncation(self):
        """Hash matches first 12 chars of full SHA-256."""
        content = "some test content"
        expected = hashlib.sha256(content.encode("utf-8")).hexdigest()[:12]
        assert generate_hash(content) == expected

    def test_different_content_different_hash(self):
        """Different content produces different hashes."""
        assert generate_hash("foo") != generate_hash("bar")


# ===========================================================================
# 2. Comment style detection
# ===========================================================================


class TestDetectCommentStyle:
    @pytest.mark.parametrize(
        "line, expected_prefix, expected_suffix",
        [
            ("/* simplify-ignore-start */", "/*", "*/"),
            ("/* simplify-ignore-start: reason */", "/*", "*/"),
            ("   /* simplify-ignore-start */", "/*", "*/"),
            ("* simplify-ignore-start", "/*", "*/"),
            ("# simplify-ignore-start", "#", ""),
            ("  # simplify-ignore-start: reason", "#", ""),
            ("<!-- simplify-ignore-start -->", "<!--", "-->"),
            ("  <!-- simplify-ignore-start: reason -->", "<!--", "-->"),
        ],
    )
    def test_comment_styles(self, line, expected_prefix, expected_suffix):
        prefix, suffix = detect_comment_style(line)
        assert prefix == expected_prefix
        assert suffix == expected_suffix

    def test_fallback_to_c_style(self):
        """Unknown prefix falls back to C-style comments."""
        prefix, suffix = detect_comment_style("// simplify-ignore-start")
        assert prefix == "/*"
        assert suffix == "*/"


# ===========================================================================
# 3. Placeholder creation
# ===========================================================================


class TestMakePlaceholder:
    def test_c_style_with_reason(self):
        ph = make_placeholder("a1b2c3d4", "perf-critical", "/*", "*/")
        assert ph == "/* BLOCK_a1b2c3d4: perf-critical */"

    def test_c_style_without_reason(self):
        ph = make_placeholder("a1b2c3d4", None, "/*", "*/")
        assert ph == "/* BLOCK_a1b2c3d4 */"

    def test_python_style_with_reason(self):
        ph = make_placeholder("deadbeef", "hand-optimized", "#", "")
        assert ph == "# BLOCK_deadbeef: hand-optimized"

    def test_python_style_without_reason(self):
        ph = make_placeholder("deadbeef", None, "#", "")
        assert ph == "# BLOCK_deadbeef"

    def test_html_style_with_reason(self):
        ph = make_placeholder("cafe1234", "template", "<!--", "-->")
        assert ph == "<!-- BLOCK_cafe1234: template -->"

    def test_html_style_without_reason(self):
        ph = make_placeholder("cafe1234", None, "<!--", "-->")
        assert ph == "<!-- BLOCK_cafe1234 -->"

    def test_empty_reason_treated_as_none(self):
        ph = make_placeholder("a1b2c3d4", "  ", "/*", "*/")
        assert ph == "/* BLOCK_a1b2c3d4 */"


# ===========================================================================
# 4. Regex patterns
# ===========================================================================


class TestRegexPatterns:
    def test_start_re_c_style(self):
        m = START_RE.search("/* simplify-ignore-start: perf */")
        assert m is not None
        assert m.group(1) and m.group(1).strip() == "perf"

    def test_start_re_python_style(self):
        m = START_RE.search("# simplify-ignore-start: hand-optimized")
        assert m is not None
        assert m.group(1) and m.group(1).strip() == "hand-optimized"

    def test_start_re_html_style(self):
        m = START_RE.search("<!-- simplify-ignore-start: template -->")
        assert m is not None
        # Regex may capture trailing closer; stripping happens in replace_blocks
        raw = (m.group(1) or "").strip()
        for closer in ("*/", "-->"):
            if raw.endswith(closer):
                raw = raw[:-len(closer)].rstrip()
        assert raw == "template"

    def test_start_re_no_reason(self):
        m = START_RE.search("/* simplify-ignore-start */")
        assert m is not None

    def test_end_re_c_style(self):
        assert END_RE.search("/* simplify-ignore-end */") is not None

    def test_end_re_python_style(self):
        assert END_RE.search("# simplify-ignore-end") is not None

    def test_end_re_html_style(self):
        assert END_RE.search("<!-- simplify-ignore-end -->") is not None

    def test_block_hash_re(self):
        m = BLOCK_HASH_RE.search("/* BLOCK_a1b2c3d4e5f6: reason */")
        assert m is not None
        assert m.group(1) == "a1b2c3d4e5f6"

    def test_block_hash_re_no_match(self):
        assert BLOCK_HASH_RE.search("no block here") is None


# ===========================================================================
# 5. BlockCache
# ===========================================================================


class TestBlockCache:
    def test_store_and_retrieve(self):
        cache = BlockCache()
        cache.store("abc12345", "original code")
        assert cache.retrieve("abc12345") == "original code"

    def test_retrieve_missing(self):
        cache = BlockCache()
        assert cache.retrieve("nonexist") is None

    def test_has(self):
        cache = BlockCache()
        cache.store("abc12345", "code")
        assert cache.has("abc12345") is True
        assert cache.has("missing") is False

    def test_clear(self):
        cache = BlockCache()
        cache.store("a", "code1")
        cache.store("b", "code2")
        assert cache.size() == 2
        cache.clear()
        assert cache.size() == 0
        assert cache.retrieve("a") is None

    def test_overwrite(self):
        cache = BlockCache()
        cache.store("a", "v1")
        cache.store("a", "v2")
        assert cache.retrieve("a") == "v2"


# ===========================================================================
# 6. replace_blocks - protected block detection in read responses
# ===========================================================================


class TestReplaceBlocks:
    def test_single_block_js(self):
        """JS/C-style block is replaced with placeholder."""
        content = (
            "const x = 1;\n"
            "/* simplify-ignore-start: perf */\n"
            "// hand-optimized\n"
            "for (let i = 0; i < 10; i++) {}\n"
            "/* simplify-ignore-end */\n"
            "const y = 2;"
        )
        cache = BlockCache()
        result = replace_blocks(content, cache)

        # Placeholder line should exist
        assert "BLOCK_" in result
        # Original code should be gone from the result
        assert "hand-optimized" not in result
        # Surrounding code preserved
        assert "const x = 1;" in result
        assert "const y = 2;" in result
        # Cache should have the block
        assert cache.size() == 1

    def test_single_block_python(self):
        """Python-style block is replaced with # placeholder."""
        content = (
            "x = 1\n"
            "# simplify-ignore-start: algorithm\n"
            "# hand-tuned loop\n"
            "for i in range(10):\n"
            "    pass\n"
            "# simplify-ignore-end\n"
            "y = 2"
        )
        cache = BlockCache()
        result = replace_blocks(content, cache)

        assert "BLOCK_" in result
        assert "# BLOCK_" in result  # Python-style placeholder
        assert "hand-tuned loop" not in result
        assert "x = 1" in result
        assert "y = 2" in result

    def test_single_block_html(self):
        """HTML-style block is replaced with <!-- placeholder -->."""
        content = (
            "<div>\n"
            "<!-- simplify-ignore-start: template -->\n"
            "<span>complex template logic</span>\n"
            "<!-- simplify-ignore-end -->\n"
            "</div>"
        )
        cache = BlockCache()
        result = replace_blocks(content, cache)

        assert "BLOCK_" in result
        assert "<!-- BLOCK_" in result
        assert "complex template logic" not in result

    def test_placeholder_contains_reason(self):
        """Placeholder includes the reason from the annotation."""
        content = (
            "/* simplify-ignore-start: perf-critical */\n"
            "fast_code();\n"
            "/* simplify-ignore-end */"
        )
        cache = BlockCache()
        result = replace_blocks(content, cache)
        assert "perf-critical" in result

    def test_placeholder_no_reason(self):
        """Block without reason produces placeholder without colon."""
        content = (
            "/* simplify-ignore-start */\n"
            "code();\n"
            "/* simplify-ignore-end */"
        )
        cache = BlockCache()
        result = replace_blocks(content, cache)
        assert ": " not in result.split("BLOCK_")[1].split("*/")[0]

    def test_hash_matches_content(self):
        """Stored hash matches SHA-256[:8] of the original block text."""
        block_text = "/* simplify-ignore-start */\ncode();\n/* simplify-ignore-end */"
        content = f"before\n{block_text}\nafter"
        cache = BlockCache()
        replace_blocks(content, cache)

        expected_hash = generate_hash(block_text)
        assert cache.has(expected_hash)
        assert cache.retrieve(expected_hash) == block_text

    def test_no_blocks_passthrough(self):
        """Content without markers passes through unchanged."""
        content = "const x = 1;\nconst y = 2;"
        cache = BlockCache()
        result = replace_blocks(content, cache)
        assert result == content
        assert cache.size() == 0

    def test_unclosed_block_passthrough(self):
        """Unclosed block passes through unchanged with warning."""
        content = "/* simplify-ignore-start */\ncode();"
        cache = BlockCache()
        result = replace_blocks(content, cache)
        assert "code();" in result
        assert cache.size() == 0


# ===========================================================================
# 7. Multi-block support
# ===========================================================================


class TestMultiBlock:
    def test_multiple_blocks(self):
        """Multiple protected blocks each get their own placeholder."""
        content = (
            "line1\n"
            "/* simplify-ignore-start: block1 */\n"
            "code_a();\n"
            "/* simplify-ignore-end */\n"
            "line_middle\n"
            "/* simplify-ignore-start: block2 */\n"
            "code_b();\n"
            "/* simplify-ignore-end */\n"
            "line_last"
        )
        cache = BlockCache()
        result = replace_blocks(content, cache)

        assert cache.size() == 2
        assert "code_a()" not in result
        assert "code_b()" not in result
        assert "line1" in result
        assert "line_middle" in result
        assert "line_last" in result
        # Both reasons present
        assert "block1" in result
        assert "block2" in result

    def test_mixed_comment_styles(self):
        """Multiple blocks with different comment styles."""
        content = (
            "/* simplify-ignore-start: js-block */\n"
            "js_code();\n"
            "/* simplify-ignore-end */\n"
            "# simplify-ignore-start: py-block\n"
            "py_code()\n"
            "# simplify-ignore-end"
        )
        cache = BlockCache()
        result = replace_blocks(content, cache)

        assert cache.size() == 2
        # JS placeholder uses /* */ style
        assert "/* BLOCK_" in result
        # Python placeholder uses # style
        assert "# BLOCK_" in result

    def test_single_line_block(self):
        """Start and end on same line produces a single placeholder line."""
        content = (
            "before\n"
            "/* simplify-ignore-start: inline */ single_line /* simplify-ignore-end */\n"
            "after"
        )
        cache = BlockCache()
        result = replace_blocks(content, cache)

        assert cache.size() == 1
        assert "single_line" not in result
        assert "BLOCK_" in result


# ===========================================================================
# 8. expand_placeholders - placeholder expansion in write/patch args
# ===========================================================================


class TestExpandPlaceholders:
    def test_expand_single_placeholder(self):
        """A single BLOCK_<hash> placeholder expands to the cached block."""
        cache = BlockCache()
        original = "/* simplify-ignore-start */\ncode();\n/* simplify-ignore-end */"
        hash_key = generate_hash(original)
        cache.store(hash_key, original)

        placeholder = f"/* BLOCK_{hash_key} */"
        text = f"before\n{placeholder}\nafter"
        result = expand_placeholders(text, cache)

        assert result == f"before\n{original}\nafter"

    def test_expand_multiple_placeholders(self):
        """Multiple BLOCK_<hash> placeholders each expand correctly."""
        cache = BlockCache()
        block1 = "/* simplify-ignore-start: a */\nc1();\n/* simplify-ignore-end */"
        block2 = "/* simplify-ignore-start: b */\nc2();\n/* simplify-ignore-end */"
        h1 = generate_hash(block1)
        h2 = generate_hash(block2)
        cache.store(h1, block1)
        cache.store(h2, block2)

        text = f"/* BLOCK_{h1}: a */\nmiddle\n/* BLOCK_{h2}: b */"
        result = expand_placeholders(text, cache)

        assert "c1()" in result
        assert "c2()" in result
        assert "middle" in result

    def test_cache_miss_passthrough(self):
        """Lines with unknown hashes pass through unchanged."""
        cache = BlockCache()
        text = "/* BLOCK_deadbeef: missing */"
        result = expand_placeholders(text, cache)
        assert result == text  # unchanged

    def test_no_placeholders_passthrough(self):
        """Text without BLOCK_ passes through unchanged."""
        cache = BlockCache()
        text = "normal code\nmore code"
        result = expand_placeholders(text, cache)
        assert result == text


# ===========================================================================
# 9. Round-trip: replace then expand
# ===========================================================================


class TestRoundTrip:
    def test_replace_then_expand_roundtrip(self):
        """Content survives a replace then expand round-trip."""
        original_content = (
            "header\n"
            "/* simplify-ignore-start: perf */\n"
            "// hand-optimized XOR\n"
            "for (let i = 0; i < len; i++) { buf[i] ^= key[i]; }\n"
            "/* simplify-ignore-end */\n"
            "footer"
        )
        cache = BlockCache()

        # Phase 1: replace (simulates read response)
        filtered = replace_blocks(original_content, cache)
        assert "hand-optimized XOR" not in filtered
        assert "BLOCK_" in filtered

        # Phase 2: expand (simulates write/patch argument)
        restored = expand_placeholders(filtered, cache)
        assert restored == original_content

    def test_multi_block_roundtrip(self):
        """Multiple blocks survive a replace then expand round-trip."""
        original_content = (
            "a\n"
            "/* simplify-ignore-start: b1 */\n"
            "code1\n"
            "/* simplify-ignore-end */\n"
            "b\n"
            "# simplify-ignore-start: b2\n"
            "code2\n"
            "# simplify-ignore-end\n"
            "c"
        )
        cache = BlockCache()
        filtered = replace_blocks(original_content, cache)
        restored = expand_placeholders(filtered, cache)
        assert restored == original_content


# ===========================================================================
# 10. Graceful handling of malformed markers
# ===========================================================================


class TestGracefulFailure:
    def test_unclosed_start_marker(self):
        """Unclosed start marker passes through without crash."""
        content = "/* simplify-ignore-start */\ncode();\nmore code();"
        cache = BlockCache()
        result = replace_blocks(content, cache)
        # Should contain the original content (passed through)
        assert "code()" in result

    def test_orphan_end_marker(self):
        """End marker without matching start is treated as normal text."""
        content = "code();\n/* simplify-ignore-end */\nmore();"
        cache = BlockCache()
        result = replace_blocks(content, cache)
        assert result == content

    def test_empty_block(self):
        """Start + end with nothing between them."""
        content = "before\n/* simplify-ignore-start */\n/* simplify-ignore-end */\nafter"
        cache = BlockCache()
        result = replace_blocks(content, cache)
        assert "before" in result
        assert "after" in result
        # The empty block should still produce a placeholder
        assert "BLOCK_" in result
        assert cache.size() == 1

    def test_expand_with_malformed_hash(self):
        """BLOCK_ with non-hex hash passes through."""
        cache = BlockCache()
        text = "/* BLOCK_zzzzzzzz: reason */"
        result = expand_placeholders(text, cache)
        assert result == text


# ===========================================================================
# 11. Cache isolation (no cross-contamination)
# ===========================================================================


class TestCacheIsolation:
    def test_separate_caches_dont_share(self):
        """Two BlockCache instances are fully isolated."""
        cache_a = BlockCache()
        cache_b = BlockCache()

        cache_a.store("hash1", "block_from_a")
        cache_b.store("hash2", "block_from_b")

        assert cache_a.retrieve("hash2") is None
        assert cache_b.retrieve("hash1") is None

    def test_clear_does_not_affect_other_cache(self):
        """Clearing one cache does not affect another."""
        cache_a = BlockCache()
        cache_b = BlockCache()

        cache_a.store("key", "value")
        cache_b.store("key", "value")
        cache_a.clear()

        assert cache_a.size() == 0
        assert cache_b.size() == 1
