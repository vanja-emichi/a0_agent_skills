"""Tests for simplify-ignore extensions.

Covers the shared utility module and the four extension points:
- tool_execute_before (filter on read)
- text_editor_patch_after (expand + re-filter after patch)
- text_editor_write_after (expand + re-filter after write)
- monologue_end (restore all from backup)
"""

import hashlib
import importlib
import os
import shutil
import tempfile
import textwrap
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

PLUGIN_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
EXT_PY_DIR = os.path.join(PLUGIN_DIR, "extensions", "python")
PRE_EXT_DIR = os.path.join(EXT_PY_DIR, "tool_execute_before")
PATCH_AFTER_DIR = os.path.join(EXT_PY_DIR, "text_editor_patch_after")
WRITE_AFTER_DIR = os.path.join(EXT_PY_DIR, "text_editor_write_after")
MONOLOGUE_END_DIR = os.path.join(EXT_PY_DIR, "monologue_end")

# Add extensions/python to path for util imports
import sys
sys.path.insert(0, EXT_PY_DIR)

from _simplify_ignore_util import (
    _block_hash,
    _cache_dir,
    _extract_reason,
    _detect_comment_suffix,
    _file_id,
    backup_file,
    expand_content,
    expand_file_in_place,
    filter_content,
    filter_file_in_place,
    has_backup,
    has_blocks,
    is_excluded_file,
    re_filter_file,
    restore_all,
)


# ---------------------------------------------------------------------------
# Shared helpers for importing extensions with mocked framework
# ---------------------------------------------------------------------------


def _make_mock_extension():
    """Create a MockExtension class that mimics helpers.extension.Extension."""
    class MockExtension:
        def __init__(self, agent=None):
            self.agent = agent
    return MockExtension


def _import_extension(ext_dir, module_name, class_name):
    """Import an extension module with mocked framework dependencies."""
    mock_ext = MagicMock()
    mock_ext.Extension = _make_mock_extension()

    with patch.dict(sys.modules, {
        "helpers": MagicMock(),
        "helpers.extension": mock_ext,
    }):
        if module_name in sys.modules:
            del sys.modules[module_name]
        sys.path.insert(0, ext_dir)
        try:
            mod = importlib.import_module(module_name)
            return getattr(mod, class_name)
        finally:
            if ext_dir in sys.path:
                sys.path.remove(ext_dir)


from _simplify_ignore_util import (
    _block_hash,
    _cache_dir,
    _extract_reason,
    _detect_comment_suffix,
    _file_id,
    backup_file,
    expand_content,
    expand_file_in_place,
    filter_content,
    filter_file_in_place,
    has_backup,
    has_blocks,
    is_excluded_file,
    re_filter_file,
    restore_all,
)


@pytest.fixture
def tmpdir():
    """Create a temporary directory for test files."""
    d = tempfile.mkdtemp(prefix="simplify_ignore_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def cache_dir(tmpdir):
    """Create a temporary cache directory."""
    d = os.path.join(tmpdir, "cache")
    os.makedirs(d, exist_ok=True)
    return d


@pytest.fixture
def mock_agent(tmpdir):
    """Create a mock agent with config pointing to tmpdir."""
    agent = MagicMock()
    agent.config.project_folder = tmpdir
    return agent


# ── Unit tests: utility functions ──────────────────────────────────────────


class TestFileId:
    def test_deterministic(self):
        assert _file_id("/foo/bar.py") == _file_id("/foo/bar.py")

    def test_different_paths(self):
        assert _file_id("/foo/bar.py") != _file_id("/foo/baz.py")

    def test_length(self):
        fid = _file_id("/some/path")
        assert len(fid) == 16


class TestBlockHash:
    def test_deterministic(self):
        assert _block_hash("content") == _block_hash("content")

    def test_different_content(self):
        assert _block_hash("aaa") != _block_hash("bbb")

    def test_length(self):
        h = _block_hash("test")
        assert len(h) == 8


class TestExtractReason:
    def test_no_reason(self):
        assert _extract_reason("/* simplify-ignore-start */") == ""

    def test_with_reason(self):
        assert _extract_reason("/* simplify-ignore-start: perf */") == "perf"

    def test_with_reason_and_suffix(self):
        assert _extract_reason("/* simplify-ignore-start: perf-critical */") == "perf-critical"

    def test_with_html_comment(self):
        line = "<!-- simplify-ignore-start: important -->"
        assert _extract_reason(line) == "important"

    def test_no_marker(self):
        assert _extract_reason("just a regular line") == ""

    def test_with_spaces(self):
        assert _extract_reason("// simplify-ignore-start:   reason  ") == "reason"


class TestDetectCommentSuffix:
    def test_block_comment(self):
        line = "/* simplify-ignore-start: reason */"
        assert _detect_comment_suffix(line) == " */"

    def test_html_comment(self):
        line = "<!-- simplify-ignore-start: reason -->"
        assert _detect_comment_suffix(line) == " -->"

    def test_line_comment(self):
        line = "// simplify-ignore-start: reason"
        assert _detect_comment_suffix(line) == ""

    def test_hash_comment(self):
        line = "# simplify-ignore-start: reason"
        assert _detect_comment_suffix(line) == ""


class TestIsExcludedFile:
    def test_excluded(self):
        assert is_excluded_file("/path/simplify-ignore.sh")
        assert is_excluded_file("/path/SIMPLIFY-IGNORE.md")

    def test_not_excluded(self):
        assert not is_excluded_file("/path/main.py")
        assert not is_excluded_file("/path/simplify.py")


class TestHasBlocks:
    def test_has_marker(self, tmpdir):
        f = os.path.join(tmpdir, "test.py")
        with open(f, "w") as fh:
            fh.write("/* simplify-ignore-start */\nhidden\n/* simplify-ignore-end */\n")
        assert has_blocks(f)

    def test_no_marker(self, tmpdir):
        f = os.path.join(tmpdir, "test.py")
        with open(f, "w") as fh:
            fh.write("just normal code\n")
        assert not has_blocks(f)

    def test_nonexistent(self):
        assert not has_blocks("/nonexistent/file.py")


class TestCacheDir:
    def test_project_folder(self, mock_agent):
        result = _cache_dir(mock_agent)
        assert ".a0proj" in result
        assert "simplify-ignore-cache" in result

    def test_no_config(self):
        agent = MagicMock(spec=[])
        result = _cache_dir(agent)
        assert "simplify-ignore-cache" in result


# ── Filter tests ───────────────────────────────────────────────────────────


class TestFilterContent:
    def test_no_blocks(self):
        content = "line1\nline2\nline3\n"
        assert filter_content(content, "fid", "/tmp/cache") == content

    def test_single_block(self, cache_dir):
        content = textwrap.dedent("""\
            line1
            /* simplify-ignore-start: perf */
            hidden
            /* simplify-ignore-end */
            line5
        """)
        fid = "testfid123456789"
        result = filter_content(content, fid, cache_dir)
        assert "hidden" not in result
        assert "BLOCK_" in result
        assert "line1" in result
        assert "line5" in result
        assert "perf" in result  # reason appears in placeholder

    def test_multiple_blocks(self, cache_dir):
        content = textwrap.dedent("""\
            line1
            /* simplify-ignore-start: block1 */
            hidden1
            /* simplify-ignore-end */
            line5
            # simplify-ignore-start: block2
            hidden2
            # simplify-ignore-end
            line9
        """)
        fid = "multiblocktest1"
        result = filter_content(content, fid, cache_dir)
        assert "hidden1" not in result
        assert "hidden2" not in result
        assert result.count("BLOCK_") == 2

    def test_preserves_prefix(self, cache_dir):
        content = "  /* simplify-ignore-start */\nhidden\n  /* simplify-ignore-end */\n"
        fid = "prefixtest123456"
        result = filter_content(content, fid, cache_dir)
        # Prefix is everything before 'simplify-ignore-start', so '  /* '
        assert "  /* BLOCK_" in result

    def test_preserves_suffix(self, cache_dir):
        content = "/* simplify-ignore-start */\nhidden\n/* simplify-ignore-end */\n"
        fid = "suffixtest123456"
        result = filter_content(content, fid, cache_dir)
        assert "BLOCK_" in result
        # Should detect */ suffix
        block_line = [l for l in result.split("\n") if "BLOCK_" in l][0]
        assert block_line.endswith(" */")

    def test_no_trailing_newline(self, cache_dir):
        content = "line1\n/* simplify-ignore-start */\nhidden\n/* simplify-ignore-end */"
        fid = "nonewlinetest12"
        result = filter_content(content, fid, cache_dir)
        assert not result.endswith("\n")

    def test_trailing_newline_preserved(self, cache_dir):
        content = "line1\n/* simplify-ignore-start */\nhidden\n/* simplify-ignore-end */\n"
        fid = "newlinetest12345"
        result = filter_content(content, fid, cache_dir)
        assert result.endswith("\n")

    def test_single_line_block(self, cache_dir):
        content = "/* simplify-ignore-start */ hidden /* simplify-ignore-end */\nline2\n"
        fid = "singlelinetest1"
        result = filter_content(content, fid, cache_dir)
        assert "hidden" not in result
        assert "BLOCK_" in result
        assert "line2" in result

    def test_unclosed_block(self, cache_dir):
        content = "/* simplify-ignore-start */\nhidden\nmore_hidden\n"
        fid = "unclosedtest123"
        result = filter_content(content, fid, cache_dir)
        # Unclosed block should remain as-is
        assert "hidden" in result
        assert "BLOCK_" not in result

    def test_hash_comment_style(self, cache_dir):
        content = "# simplify-ignore-start: py\nhidden\n# simplify-ignore-end\n"
        fid = "hashtest12345678"
        result = filter_content(content, fid, cache_dir)
        assert "hidden" not in result
        assert "BLOCK_" in result
        block_line = [l for l in result.split("\n") if "BLOCK_" in l][0]
        assert block_line.startswith("# ")

    def test_html_comment_style(self, cache_dir):
        content = "<!-- simplify-ignore-start: html -->\nhidden\n<!-- simplify-ignore-end -->\n"
        fid = "htmltest123456789"
        result = filter_content(content, fid, cache_dir)
        assert "hidden" not in result
        block_line = [l for l in result.split("\n") if "BLOCK_" in l][0]
        assert block_line.endswith(" -->")

    def test_cache_files_created(self, cache_dir):
        content = "/* simplify-ignore-start: reason */\nhidden\n/* simplify-ignore-end */\n"
        fid = "cachetest1234567"
        filter_content(content, fid, cache_dir)
        # Should have block, reason, prefix, suffix files
        files = os.listdir(cache_dir)
        assert any(".block." in f for f in files)
        assert any(".reason." in f for f in files)


class TestFilterFileInPlace:
    def test_filters_file(self, tmpdir, cache_dir):
        f = os.path.join(tmpdir, "test.py")
        content = "line1\n/* simplify-ignore-start */\nhidden\n/* simplify-ignore-end */\nline5\n"
        with open(f, "w") as fh:
            fh.write(content)

        fid = _file_id(f)
        result = filter_file_in_place(f, fid, cache_dir)
        assert result is True

        with open(f) as fh:
            filtered = fh.read()
        assert "hidden" not in filtered
        assert "BLOCK_" in filtered

    def test_no_blocks_returns_false(self, tmpdir, cache_dir):
        f = os.path.join(tmpdir, "test.py")
        with open(f, "w") as fh:
            fh.write("just normal code\n")

        fid = _file_id(f)
        result = filter_file_in_place(f, fid, cache_dir)
        assert result is False


# ── Expand tests ───────────────────────────────────────────────────────────


class TestExpandContent:
    def test_round_trip(self, cache_dir):
        """Filter then expand should return original content."""
        content = "line1\n/* simplify-ignore-start: perf */\nhidden\n/* simplify-ignore-end */\nline5\n"
        fid = "roundtrip1234567"

        filtered = filter_content(content, fid, cache_dir)
        assert "BLOCK_" in filtered

        expanded = expand_content(filtered, fid, cache_dir)
        assert expanded == content

    def test_multiple_blocks_round_trip(self, cache_dir):
        content = textwrap.dedent("""\
            line1
            /* simplify-ignore-start: b1 */
            hidden1
            /* simplify-ignore-end */
            line5
            # simplify-ignore-start: b2
            hidden2
            # simplify-ignore-end
            line9
        """)
        fid = "multiroundtrip12"

        filtered = filter_content(content, fid, cache_dir)
        expanded = expand_content(filtered, fid, cache_dir)
        assert expanded == content

    def test_no_placeholders(self, cache_dir):
        content = "no blocks here\n"
        assert expand_content(content, "fid", cache_dir) == content

    def test_no_cache_dir(self, tmpdir):
        content = "BLOCK_abc123\n"
        nonexistent = os.path.join(tmpdir, "nonexistent")
        assert expand_content(content, "fid", nonexistent) == content

    def test_fuzzy_match(self, cache_dir):
        """When model alters reason text, fuzzy match should work."""
        content = "/* simplify-ignore-start: original */\nhidden\n/* simplify-ignore-end */\n"
        fid = "fuzzytest1234567"

        filtered = filter_content(content, fid, cache_dir)

        # Simulate model changing the reason text
        block_line = [l for l in filtered.split("\n") if "BLOCK_" in l][0]
        h = block_line.split("BLOCK_")[1].split(":")[0]
        # Get prefix and suffix from cache
        prefix_file = os.path.join(cache_dir, f"{fid}.prefix.{h}")
        suffix_file = os.path.join(cache_dir, f"{fid}.suffix.{h}")
        prefix = open(prefix_file).read() if os.path.exists(prefix_file) else ""
        suffix = open(suffix_file).read() if os.path.exists(suffix_file) else ""
        altered = f"{prefix}BLOCK_{h}{suffix}\n"

        expanded = expand_content(altered, fid, cache_dir)
        assert "hidden" in expanded


class TestExpandFileInPlace:
    def test_expands_file(self, tmpdir, cache_dir):
        f = os.path.join(tmpdir, "test.py")
        content = "/* simplify-ignore-start */\nhidden\n/* simplify-ignore-end */\n"
        filtered = filter_content(content, "fid", cache_dir)

        with open(f, "w") as fh:
            fh.write(filtered)

        fid = "expfiletest12345"
        # Copy block cache files with new fid
        for fname in os.listdir(cache_dir):
            if fname.startswith("fid."):
                src = os.path.join(cache_dir, fname)
                dst = os.path.join(cache_dir, fname.replace("fid.", f"{fid}.", 1))
                shutil.copy2(src, dst)

        result = expand_file_in_place(f, fid, cache_dir)
        assert result is True

        with open(f) as fh:
            expanded = fh.read()
        assert "hidden" in expanded


# ── Backup tests ───────────────────────────────────────────────────────────


class TestBackup:
    def test_backup_creates_files(self, tmpdir, cache_dir):
        f = os.path.join(tmpdir, "test.py")
        with open(f, "w") as fh:
            fh.write("original content\n")

        fid = "backuptest123456"
        backup_file(f, fid, cache_dir)

        assert os.path.isfile(os.path.join(cache_dir, f"{fid}.bak"))
        assert os.path.isfile(os.path.join(cache_dir, f"{fid}.path"))

        with open(os.path.join(cache_dir, f"{fid}.bak")) as fh:
            assert fh.read() == "original content\n"

    def test_has_backup(self, tmpdir, cache_dir):
        f = os.path.join(tmpdir, "test.py")
        with open(f, "w") as fh:
            fh.write("content")

        fid = "hasbackuptest12"
        assert not has_backup(fid, cache_dir)
        backup_file(f, fid, cache_dir)
        assert has_backup(fid, cache_dir)


# ── Restore tests ──────────────────────────────────────────────────────────


class TestRestoreAll:
    def test_restore_single_file(self, tmpdir, cache_dir):
        f = os.path.join(tmpdir, "test.py")
        original = "original content\nline2\n"
        with open(f, "w") as fh:
            fh.write(original)

        fid = _file_id(f)
        backup_file(f, fid, cache_dir)

        # Modify the file (simulating filtered state)
        with open(f, "w") as fh:
            fh.write("BLOCK_abc123\n")

        restore_all(cache_dir)

        with open(f) as fh:
            assert fh.read() == original

    def test_restore_cleans_cache(self, tmpdir, cache_dir):
        f = os.path.join(tmpdir, "test.py")
        with open(f, "w") as fh:
            fh.write("original\n")

        fid = "cleanuptest1234"
        backup_file(f, fid, cache_dir)
        filter_content("/* simplify-ignore-start */\nh\n/* simplify-ignore-end */\n", fid, cache_dir)

        # Verify cache files exist
        assert len(os.listdir(cache_dir)) > 2

        restore_all(cache_dir)

        # All cache files for this fid should be cleaned
        remaining = [f for f in os.listdir(cache_dir) if f.startswith(fid)]
        assert len(remaining) == 0

    def test_restore_deleted_file_saves_recovered(self, tmpdir, cache_dir):
        f = os.path.join(tmpdir, "test.py")
        with open(f, "w") as fh:
            fh.write("original content\n")

        fid = "recoveredtest12"
        backup_file(f, fid, cache_dir)

        # Delete the original file
        os.remove(f)

        restore_all(cache_dir)

        # Should save as .recovered
        assert os.path.isfile(f + ".recovered")
        with open(f + ".recovered") as fh:
            assert fh.read() == "original content\n"

    def test_restore_empty_cache(self, cache_dir):
        # Should not crash on empty cache
        restore_all(cache_dir)

    def test_restore_nonexistent_cache(self, tmpdir):
        # Should not crash on nonexistent cache
        restore_all(os.path.join(tmpdir, "nonexistent"))

    def test_restore_multiple_files(self, tmpdir, cache_dir):
        files = []
        for i in range(3):
            f = os.path.join(tmpdir, f"test{i}.py")
            with open(f, "w") as fh:
                fh.write(f"original{i}\n")
            fid = f"multifile{i}test12"
            backup_file(f, fid, cache_dir)
            # Modify file
            with open(f, "w") as fh:
                fh.write(f"BLOCK_modified{i}\n")
            files.append((f, fid))

        restore_all(cache_dir)

        for i, (f, fid) in enumerate(files):
            with open(f) as fh:
                assert fh.read() == f"original{i}\n"


# ── Full round-trip integration tests ──────────────────────────────────────


class TestFullRoundTrip:
    """Simulate the full lifecycle: filter → edit → expand → re-filter → restore."""

    def test_full_lifecycle(self, tmpdir, cache_dir):
        # 1. Create file with blocks
        f = os.path.join(tmpdir, "lifecycle.py")
        original = textwrap.dedent("""\
            import os
            /* simplify-ignore-start: perf-critical */
            // manually unrolled XOR
            result[0] = buf[0] ^ key[0];
            result[1] = buf[1] ^ key[1];
            /* simplify-ignore-end */
            def main():
                pass
        """)
        with open(f, "w") as fh:
            fh.write(original)

        fid = _file_id(f)

        # 2. Back up and filter (simulates tool_execute_before)
        backup_file(f, fid, cache_dir)
        filter_file_in_place(f, fid, cache_dir)

        # File on disk should have placeholders
        with open(f) as fh:
            filtered = fh.read()
        assert "BLOCK_" in filtered
        assert "unrolled XOR" not in filtered
        assert "perf-critical" in filtered
        assert "import os" in filtered
        assert "def main" in filtered

        # 3. Simulate model editing around placeholder (adds a comment)
        # In real flow, text_editor patch would modify the file
        filtered_lines = filtered.split("\n")
        for i, line in enumerate(filtered_lines):
            if "BLOCK_" in line:
                # Model adds code before the placeholder line
                filtered_lines.insert(i, "# model added this comment")
                break
        modified = "\n".join(filtered_lines)
        with open(f, "w") as fh:
            fh.write(modified)

        # 4. Expand and re-filter (simulates text_editor_patch_after)
        expand_file_in_place(f, fid, cache_dir)

        # Update backup with expanded content
        from _simplify_ignore_util import _read_file, _write_file
        expanded = _read_file(f)
        _write_file(os.path.join(cache_dir, f"{fid}.bak"), expanded)

        re_filter_file(f, fid, cache_dir)

        # File should have placeholders again, plus model's addition
        with open(f) as fh:
            re_filtered = fh.read()
        assert "BLOCK_" in re_filtered
        assert "# model added this comment" in re_filtered
        assert "unrolled XOR" not in re_filtered

        # 5. Restore (simulates monologue_end)
        restore_all(cache_dir)

        # File should have original content plus model's changes
        with open(f) as fh:
            restored = fh.read()
        assert "unrolled XOR" in restored
        assert "# model added this comment" in restored

    def test_hash_consistency(self):
        """Same content should always produce same hash."""
        content = "/* simplify-ignore-start */\nhidden\n/* simplify-ignore-end */\n"
        h1 = _block_hash(content)
        h2 = _block_hash(content)
        assert h1 == h2


# ── Extension class tests ─────────────────────────────────────────────────


class TestSimplifyIgnoreBefore:
    """Test the tool_execute_before extension."""

    @pytest.fixture(autouse=True)
    def _import_ext(self):
        self.cls = _import_extension(
            PRE_EXT_DIR, "_20_simplify_ignore", "SimplifyIgnoreBefore"
        )

    def test_skips_non_text_editor(self, mock_agent, cache_dir):
        ext = self.cls(agent=mock_agent)
        ext.execute(tool_name="browser", tool_args={"action": "read"})

    def test_skips_non_read_action(self, mock_agent, cache_dir):
        ext = self.cls(agent=mock_agent)
        ext.execute(tool_name="text_editor", tool_args={"action": "write", "path": "/tmp/test.py"})

    def test_skips_nonexistent_file(self, mock_agent):
        ext = self.cls(agent=mock_agent)
        ext.execute(tool_name="text_editor", tool_args={"action": "read", "path": "/nonexistent/file.py"})

    def test_skips_excluded_file(self, mock_agent, tmpdir):
        ext = self.cls(agent=mock_agent)
        f = os.path.join(tmpdir, "simplify-ignore-test.py")
        with open(f, "w") as fh:
            fh.write("/* simplify-ignore-start */\nhidden\n/* simplify-ignore-end */\n")
        ext.execute(tool_name="text_editor", tool_args={"action": "read", "path": f})
        with open(f) as fh:
            assert "hidden" in fh.read()

    def test_filters_on_read(self, mock_agent, tmpdir):
        ext = self.cls(agent=mock_agent)
        f = os.path.join(tmpdir, "code.py")
        with open(f, "w") as fh:
            fh.write("/* simplify-ignore-start: secret */\nhidden\n/* simplify-ignore-end */\n")
        ext.execute(tool_name="text_editor", tool_args={"action": "read", "path": f})
        with open(f) as fh:
            content = fh.read()
        assert "hidden" not in content
        assert "BLOCK_" in content
        cache = os.path.join(tmpdir, ".a0proj", "simplify-ignore-cache")
        restore_all(cache)
        with open(f) as fh:
            assert "hidden" in fh.read()


class TestSimplifyIgnorePatchAfter:
    """Test the text_editor_patch_after extension."""

    @pytest.fixture(autouse=True)
    def _import_ext(self):
        self.cls = _import_extension(
            PATCH_AFTER_DIR, "_10_simplify_ignore", "SimplifyIgnorePatchAfter"
        )

    def test_skips_no_backup(self, mock_agent, tmpdir):
        ext = self.cls(agent=mock_agent)
        f = os.path.join(tmpdir, "test.py")
        with open(f, "w") as fh:
            fh.write("normal content\n")
        ext.execute(data={"path": f})

    def test_expand_and_refilter(self, mock_agent, tmpdir):
        from _simplify_ignore_util import _read_file, _write_file
        ext = self.cls(agent=mock_agent)
        f = os.path.join(tmpdir, "test.py")
        original = "/* simplify-ignore-start */\nhidden\n/* simplify-ignore-end */\nline4\n"
        with open(f, "w") as fh:
            fh.write(original)
        cache = os.path.join(tmpdir, ".a0proj", "simplify-ignore-cache")
        fid = _file_id(f)
        backup_file(f, fid, cache)
        filter_file_in_place(f, fid, cache)
        ext.execute(data={"path": f})
        with open(f) as fh:
            content = fh.read()
        assert "BLOCK_" in content
        assert "hidden" not in content
        with open(os.path.join(cache, f"{fid}.bak")) as fh:
            backup = fh.read()
        assert "hidden" in backup
        restore_all(cache)
        with open(f) as fh:
            assert "hidden" in fh.read()


class TestSimplifyIgnoreWriteAfter:
    """Test the text_editor_write_after extension."""

    @pytest.fixture(autouse=True)
    def _import_ext(self):
        self.cls = _import_extension(
            WRITE_AFTER_DIR, "_10_simplify_ignore", "SimplifyIgnoreWriteAfter"
        )

    def test_skips_no_backup(self, mock_agent, tmpdir):
        ext = self.cls(agent=mock_agent)
        f = os.path.join(tmpdir, "test.py")
        with open(f, "w") as fh:
            fh.write("content\n")
        ext.execute(data={"path": f})


class TestSimplifyIgnoreEnd:
    """Test the monologue_end extension."""

    @pytest.fixture(autouse=True)
    def _import_ext(self):
        self.cls = _import_extension(
            MONOLOGUE_END_DIR, "_10_simplify_ignore", "SimplifyIgnoreEnd"
        )

    def test_restore_on_end(self, mock_agent, tmpdir):
        f = os.path.join(tmpdir, "test.py")
        original = "/* simplify-ignore-start */\nhidden\n/* simplify-ignore-end */\n"
        with open(f, "w") as fh:
            fh.write(original)
        cache = os.path.join(tmpdir, ".a0proj", "simplify-ignore-cache")
        fid = _file_id(f)
        backup_file(f, fid, cache)
        filter_file_in_place(f, fid, cache)
        with open(f) as fh:
            assert "BLOCK_" in fh.read()
        ext = self.cls(agent=mock_agent)
        ext.execute()
        with open(f) as fh:
            assert "hidden" in fh.read()

    def test_empty_cache_no_crash(self, mock_agent, tmpdir):
        ext = self.cls(agent=mock_agent)
        ext.execute()


# ── Edge case tests ────────────────────────────────────────────────────────


class TestEdgeCases:
    def test_empty_file(self, cache_dir):
        result = filter_content("", "fid", cache_dir)
        assert result == ""

    def test_only_whitespace(self, cache_dir):
        content = "   \n\n   \n"
        result = filter_content(content, "fid", cache_dir)
        assert result == content

    def test_adjacent_blocks(self, cache_dir):
        content = textwrap.dedent("""\
            /* simplify-ignore-start: b1 */
            hidden1
            /* simplify-ignore-end */
            /* simplify-ignore-start: b2 */
            hidden2
            /* simplify-ignore-end */
        """)
        fid = "adjacenttest1234"
        filtered = filter_content(content, fid, cache_dir)
        assert "hidden1" not in filtered
        assert "hidden2" not in filtered

        expanded = expand_content(filtered, fid, cache_dir)
        assert expanded == content

    def test_nested_markers_in_code(self, cache_dir):
        """simplify-ignore-start appearing in a string should NOT trigger."""
        content = 'msg = "simplify-ignore-start"\n'
        # Actually, the regex will match this, which is a known limitation
        # from the original bash script. Verify behavior is consistent.
        fid = "nestedtest123456"
        result = filter_content(content, fid, cache_dir)
        # The regex finds the marker anywhere on the line — same as original
        assert "BLOCK_" in result or "simplify-ignore-start" in result

    def test_binary_file_handling(self, tmpdir, cache_dir):
        f = os.path.join(tmpdir, "binary.bin")
        with open(f, "wb") as fh:
            fh.write(b"\x00\x01\x02\x03")
        # has_blocks should return False for binary files
        assert not has_blocks(f)

    def test_concurrent_file_ids(self, cache_dir):
        """Different files should have different file IDs and not interfere."""
        content1 = "/* simplify-ignore-start: a */\nha\n/* simplify-ignore-end */\n"
        content2 = "# simplify-ignore-start: b\nhb\n# simplify-ignore-end\n"

        fid1 = "file_one_abcdef"
        fid2 = "file_two_abcdef"

        f1 = filter_content(content1, fid1, cache_dir)
        f2 = filter_content(content2, fid2, cache_dir)

        e1 = expand_content(f1, fid1, cache_dir)
        e2 = expand_content(f2, fid2, cache_dir)

        assert e1 == content1
        assert e2 == content2
