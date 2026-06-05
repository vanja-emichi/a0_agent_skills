"""Unit tests for SDD cache extensions (pre and post)."""

import hashlib
import importlib
import json
import os
import sys
import time
import tempfile
from dataclasses import dataclass
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

PLUGIN_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
PRE_EXT_DIR = os.path.join(PLUGIN_DIR, "extensions", "python", "tool_execute_before")
POST_EXT_DIR = os.path.join(PLUGIN_DIR, "extensions", "python", "tool_execute_after")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _cache_key(url: str) -> str:
    """Match the extension's cache key algorithm."""
    return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]


def _make_agent(data=None, number=0):
    """Create a mock agent with the attributes the extensions check."""
    agent = MagicMock()
    agent.number = number
    agent.data = data if data is not None else {}
    # Default config without project_folder
    agent.config = MagicMock(spec=[])
    return agent


def _write_cache_entry(cache_dir, url, content="cached content",
                        etag="\"abc123\"", last_modified="Wed, 01 Jan 2025 00:00:00 GMT",
                        fetched_at=None, prompt="original prompt"):
    """Write a cache entry directly to the cache dir."""
    os.makedirs(cache_dir, exist_ok=True)
    key = _cache_key(url)
    entry = {
        "url": url,
        "etag": etag,
        "last_modified": last_modified,
        "content": content,
        "fetched_at": fetched_at or int(time.time()),
        "prompt": prompt,
    }
    path = os.path.join(cache_dir, f"{key}.json")
    with open(path, "w") as f:
        json.dump(entry, f)
    return path


def _import_pre():
    """Import the pre-extension with mocked framework dependencies."""
    class MockExtension:
        def __init__(self, agent=None):
            self.agent = agent

    mock_ext = MagicMock()
    mock_ext.Extension = MockExtension

    with patch.dict(sys.modules, {
        "helpers": MagicMock(),
        "helpers.extension": mock_ext,
    }):
        if "_10_sdd_cache" in sys.modules:
            del sys.modules["_10_sdd_cache"]
        sys.path.insert(0, PRE_EXT_DIR)
        try:
            mod = importlib.import_module("_10_sdd_cache")
            return mod
        finally:
            if PRE_EXT_DIR in sys.path:
                sys.path.remove(PRE_EXT_DIR)


def _import_post():
    """Import the post-extension with mocked framework dependencies."""
    class MockExtension:
        def __init__(self, agent=None):
            self.agent = agent

    mock_ext = MagicMock()
    mock_ext.Extension = MockExtension

    with patch.dict(sys.modules, {
        "helpers": MagicMock(),
        "helpers.extension": mock_ext,
    }):
        # Use unique module name to avoid collision with pre
        mod_name = "_10_sdd_cache_post"
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        if "_10_sdd_cache" in sys.modules:
            del sys.modules["_10_sdd_cache"]
        sys.path.insert(0, POST_EXT_DIR)
        try:
            # The file is named _10_sdd_cache.py so import it, but under a different
            # name by manipulating sys.modules after import
            mod = importlib.import_module("_10_sdd_cache")
            sys.modules[mod_name] = mod
            return mod
        finally:
            if POST_EXT_DIR in sys.path:
                sys.path.remove(POST_EXT_DIR)


# ---------------------------------------------------------------------------
# Pre-extension tests
# ---------------------------------------------------------------------------


class TestPreExtension:
    """Tests for tool_execute_before/_10_sdd_cache.py"""

    def test_non_browser_tool_passes_through(self):
        """Non-browser tools should be ignored."""
        mod = _import_pre()
        agent = _make_agent()
        ext = mod.SddCachePre(agent=agent)
        ext.execute(tool_name="code_execution_tool", tool_args={"action": "navigate", "url": "https://example.com"})
        # No data stored
        assert "sdd_cache_pending_hit" not in agent.data

    def test_non_intercepted_action_passes_through(self):
        """Browser actions other than navigate/content should be ignored."""
        mod = _import_pre()
        agent = _make_agent()
        ext = mod.SddCachePre(agent=agent)
        ext.execute(tool_name="browser", tool_args={"action": "click", "ref": "btn1"})
        assert "sdd_cache_pending_hit" not in agent.data

    def test_missing_url_passes_through(self):
        """Browser navigate without URL should be ignored."""
        mod = _import_pre()
        agent = _make_agent()
        ext = mod.SddCachePre(agent=agent)
        ext.execute(tool_name="browser", tool_args={"action": "navigate"})
        assert "sdd_cache_pending_hit" not in agent.data

    def test_url_stored_in_agent_data_on_miss(self):
        """On cache miss, URL should still be stored for post-extension."""
        mod = _import_pre()
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = _make_agent()
            ext = mod.SddCachePre(agent=agent)
            # Patch _cache_dir to use tmpdir
            ext.execute(
                tool_name="browser",
                tool_args={"action": "navigate", "url": "https://example.com"},
            )
            pending = agent.data.get("sdd_cache_pending_hit")
            assert pending is not None
            assert pending["url"] == "https://example.com"
            assert "hit" not in pending

    def test_cache_hit_redirects_to_list(self):
        """On cache hit (HTTP 304), tool_args should be redirected to list action."""
        mod = _import_pre()
        url = "https://example.com/docs"

        with tempfile.TemporaryDirectory() as cache_dir:
            _write_cache_entry(cache_dir, url, content="docs content here")

            agent = _make_agent()
            tool_args = {"action": "navigate", "url": url}

            with patch.object(mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(mod, "_head_revalidate", return_value=304):
                ext = mod.SddCachePre(agent=agent)
                ext.execute(tool_name="browser", tool_args=tool_args)

            # tool_args should be redirected to list
            assert tool_args["action"] == "list"
            assert "url" not in tool_args

            # agent.data should have cache hit
            pending = agent.data["sdd_cache_pending_hit"]
            assert pending.get("hit") is True
            assert "[sdd-cache] Cache hit" in pending["message"]
            assert "docs content here" in pending["message"]
            assert "----- BEGIN CACHED CONTENT -----" in pending["message"]

    def test_cache_miss_lets_browser_proceed(self):
        """On cache miss (HTTP 200), tool_args should NOT be modified."""
        mod = _import_pre()
        url = "https://example.com/docs"

        with tempfile.TemporaryDirectory() as cache_dir:
            _write_cache_entry(cache_dir, url)

            agent = _make_agent()
            tool_args = {"action": "navigate", "url": url}

            with patch.object(mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(mod, "_head_revalidate", return_value=200):
                ext = mod.SddCachePre(agent=agent)
                ext.execute(tool_name="browser", tool_args=tool_args)

            # tool_args should NOT be modified
            assert tool_args["action"] == "navigate"
            assert tool_args["url"] == url

            # pending data should NOT have hit flag
            pending = agent.data["sdd_cache_pending_hit"]
            assert "hit" not in pending

    def test_no_validators_prevents_cache_hit(self):
        """Entry without etag or last_modified should not be served from cache."""
        mod = _import_pre()
        url = "https://example.com/no-validators"

        with tempfile.TemporaryDirectory() as cache_dir:
            _write_cache_entry(cache_dir, url, etag="", last_modified="")

            agent = _make_agent()
            tool_args = {"action": "navigate", "url": url}

            with patch.object(mod, "_cache_dir", return_value=cache_dir):
                ext = mod.SddCachePre(agent=agent)
                ext.execute(tool_name="browser", tool_args=tool_args)

            assert tool_args["action"] == "navigate"

    def test_empty_content_prevents_cache_hit(self):
        """Cache entry with empty content should not be served."""
        mod = _import_pre()
        url = "https://example.com/empty"

        with tempfile.TemporaryDirectory() as cache_dir:
            _write_cache_entry(cache_dir, url, content="")

            agent = _make_agent()
            tool_args = {"action": "navigate", "url": url}

            with patch.object(mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(mod, "_head_revalidate", return_value=304):
                ext = mod.SddCachePre(agent=agent)
                ext.execute(tool_name="browser", tool_args=tool_args)

            assert tool_args["action"] == "navigate"

    def test_content_action_intercepted(self):
        """Browser content action should also be intercepted."""
        mod = _import_pre()
        url = "https://example.com/page"

        with tempfile.TemporaryDirectory() as cache_dir:
            _write_cache_entry(cache_dir, url)

            agent = _make_agent()
            tool_args = {"action": "content", "url": url}

            with patch.object(mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(mod, "_head_revalidate", return_value=304):
                ext = mod.SddCachePre(agent=agent)
                ext.execute(tool_name="browser", tool_args=tool_args)

            assert tool_args["action"] == "list"

    def test_corrupt_cache_file_ignored(self):
        """Corrupt JSON in cache file should be silently ignored."""
        mod = _import_pre()
        url = "https://example.com/corrupt"

        with tempfile.TemporaryDirectory() as cache_dir:
            key = _cache_key(url)
            os.makedirs(cache_dir, exist_ok=True)
            with open(os.path.join(cache_dir, f"{key}.json"), "w") as f:
                f.write("{invalid json")

            agent = _make_agent()
            tool_args = {"action": "navigate", "url": url}

            with patch.object(mod, "_cache_dir", return_value=cache_dir):
                ext = mod.SddCachePre(agent=agent)
                ext.execute(tool_name="browser", tool_args=tool_args)

            assert tool_args["action"] == "navigate"

    def test_original_prompt_in_hit_message(self):
        """Cache hit message should include the original prompt."""
        mod = _import_pre()
        url = "https://example.com/with-prompt"

        with tempfile.TemporaryDirectory() as cache_dir:
            _write_cache_entry(cache_dir, url, content="result", prompt="extract the API")

            agent = _make_agent()
            tool_args = {"action": "navigate", "url": url}

            with patch.object(mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(mod, "_head_revalidate", return_value=304):
                ext = mod.SddCachePre(agent=agent)
                ext.execute(tool_name="browser", tool_args=tool_args)

            pending = agent.data["sdd_cache_pending_hit"]
            assert 'extract the API' in pending["message"]

    def test_head_error_lets_browser_proceed(self):
        """Network error during HEAD should let the browser proceed."""
        mod = _import_pre()
        url = "https://example.com/down"

        with tempfile.TemporaryDirectory() as cache_dir:
            _write_cache_entry(cache_dir, url)

            agent = _make_agent()
            tool_args = {"action": "navigate", "url": url}

            with patch.object(mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(mod, "_head_revalidate", return_value=0):
                ext = mod.SddCachePre(agent=agent)
                ext.execute(tool_name="browser", tool_args=tool_args)

            assert tool_args["action"] == "navigate"


# ---------------------------------------------------------------------------
# Post-extension tests
# ---------------------------------------------------------------------------


class TestPostExtension:
    """Tests for tool_execute_after SDD cache extension."""

    def test_non_browser_tool_passes_through(self):
        """Non-browser tools should be ignored."""
        mod = _import_post()
        agent = _make_agent()
        ext = mod.SddCachePost(agent=agent)
        response = MagicMock()
        ext.execute(tool_name="code_execution_tool", response=response)
        # Response should not be modified
        assert not hasattr(response.message, "__wrapped__")

    def test_no_pending_data_passes_through(self):
        """Without pending data, post-extension should do nothing."""
        mod = _import_post()
        agent = _make_agent()
        ext = mod.SddCachePost(agent=agent)
        response = MagicMock()
        response.message = "original"
        ext.execute(tool_name="browser", response=response)
        assert response.message == "original"

    def test_cache_hit_replaces_response(self):
        """On cache hit, response.message should be replaced with cached content."""
        mod = _import_post()
        agent = _make_agent(data={
            "sdd_cache_pending_hit": {
                "url": "https://example.com",
                "hit": True,
                "message": "[sdd-cache] Cache hit!\n----- BEGIN CACHED CONTENT -----\ncached\n----- END CACHED CONTENT -----",
                "content": "cached",
            }
        })
        ext = mod.SddCachePost(agent=agent)

        @dataclass
        class FakeResponse:
            message: str
            break_loop: bool = False

        response = FakeResponse(message="list output")
        ext.execute(tool_name="browser", response=response)

        assert "[sdd-cache] Cache hit!" in response.message
        assert "sdd_cache_pending_hit" not in agent.data

    def test_cache_miss_stores_response(self):
        """On cache miss, response content should be stored with validators."""
        mod = _import_post()

        with tempfile.TemporaryDirectory() as cache_dir:
            agent = _make_agent(data={
                "sdd_cache_pending_hit": {
                    "url": "https://example.com/docs",
                }
            })

            @dataclass
            class FakeResponse:
                message: str
                break_loop: bool = False

            response = FakeResponse(message="fetched documentation content")

            with patch.object(mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(mod, "_head_validators", return_value=("\"etag123\"", "Wed, 01 Jan 2025 00:00:00 GMT")):
                ext = mod.SddCachePost(agent=agent)
                ext.execute(tool_name="browser", response=response)

            # Verify cache file was created
            key = _cache_key("https://example.com/docs")
            cache_file = os.path.join(cache_dir, f"{key}.json")
            assert os.path.isfile(cache_file)

            with open(cache_file) as f:
                entry = json.load(f)
            assert entry["url"] == "https://example.com/docs"
            assert entry["content"] == "fetched documentation content"
            assert entry["etag"] == "\"etag123\""
            assert entry["last_modified"] == "Wed, 01 Jan 2025 00:00:00 GMT"
            assert "fetched_at" in entry

            # Pending data should be cleaned up
            assert "sdd_cache_pending_hit" not in agent.data

    def test_cache_miss_no_validators_not_cached(self):
        """If origin returns no validators, response should not be cached."""
        mod = _import_post()

        with tempfile.TemporaryDirectory() as cache_dir:
            agent = _make_agent(data={
                "sdd_cache_pending_hit": {
                    "url": "https://example.com/no-validators",
                }
            })

            @dataclass
            class FakeResponse:
                message: str
                break_loop: bool = False

            response = FakeResponse(message="some content")

            with patch.object(mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(mod, "_head_validators", return_value=("", "")):
                ext = mod.SddCachePost(agent=agent)
                ext.execute(tool_name="browser", response=response)

            # No cache file should be created
            key = _cache_key("https://example.com/no-validators")
            cache_file = os.path.join(cache_dir, f"{key}.json")
            assert not os.path.isfile(cache_file)

    def test_pending_data_cleaned_up_after_hit(self):
        """Pending data should always be cleaned up, even on errors."""
        mod = _import_post()
        agent = _make_agent(data={
            "sdd_cache_pending_hit": {
                "url": "https://example.com",
                "hit": True,
                "message": "cached content",
            }
        })
        ext = mod.SddCachePost(agent=agent)

        @dataclass
        class FakeResponse:
            message: str
            break_loop: bool = False

        response = FakeResponse(message="original")
        ext.execute(tool_name="browser", response=response)

        assert "sdd_cache_pending_hit" not in agent.data

    def test_empty_response_not_cached(self):
        """Empty response content should not be cached."""
        mod = _import_post()

        with tempfile.TemporaryDirectory() as cache_dir:
            agent = _make_agent(data={
                "sdd_cache_pending_hit": {
                    "url": "https://example.com/empty",
                }
            })

            @dataclass
            class FakeResponse:
                message: str
                break_loop: bool = False

            response = FakeResponse(message="")

            with patch.object(mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(mod, "_head_validators", return_value=("\"etag\"", "")):
                ext = mod.SddCachePost(agent=agent)
                ext.execute(tool_name="browser", response=response)

            key = _cache_key("https://example.com/empty")
            cache_file = os.path.join(cache_dir, f"{key}.json")
            assert not os.path.isfile(cache_file)

    def test_none_response_handled(self):
        """None response should not crash the extension."""
        mod = _import_post()
        agent = _make_agent(data={
            "sdd_cache_pending_hit": {
                "url": "https://example.com",
            }
        })
        ext = mod.SddCachePost(agent=agent)
        ext.execute(tool_name="browser", response=None)
        assert "sdd_cache_pending_hit" not in agent.data


# ---------------------------------------------------------------------------
# Cache key consistency tests
# ---------------------------------------------------------------------------


class TestCacheKeyConsistency:
    """Ensure pre and post extensions use the same key algorithm."""

    def test_key_algorithm_matches(self):
        """Both extensions should produce the same key for the same URL."""
        url = "https://example.com/test"
        expected = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]

        pre_mod = _import_pre()
        post_mod = _import_post()

        assert pre_mod._cache_key(url) == expected
        assert post_mod._cache_key(url) == expected

    def test_key_is_deterministic(self):
        """Same URL always produces the same key."""
        mod = _import_pre()
        url = "https://react.dev/reference/react/useActionState"
        key1 = mod._cache_key(url)
        key2 = mod._cache_key(url)
        assert key1 == key2
        assert len(key1) == 32

    def test_different_urls_produce_different_keys(self):
        """Different URLs should produce different keys."""
        mod = _import_pre()
        key1 = mod._cache_key("https://example.com/a")
        key2 = mod._cache_key("https://example.com/b")
        assert key1 != key2


# ---------------------------------------------------------------------------
# Integration-style tests
# ---------------------------------------------------------------------------


class TestCacheRoundTrip:
    """Test the pre/post cache round trip."""

    def test_full_round_trip(self):
        """Simulate: miss -> cache -> hit."""
        pre_mod = _import_pre()
        post_mod = _import_post()

        url = "https://example.com/roundtrip"

        with tempfile.TemporaryDirectory() as cache_dir:
            # Step 1: First call (miss) — pre-extension stores URL
            agent = _make_agent()
            tool_args = {"action": "navigate", "url": url}

            with patch.object(pre_mod, "_cache_dir", return_value=cache_dir):
                ext = pre_mod.SddCachePre(agent=agent)
                ext.execute(tool_name="browser", tool_args=tool_args)

            # tool_args unchanged (no cache entry yet)
            assert tool_args["action"] == "navigate"
            pending = agent.data["sdd_cache_pending_hit"]
            assert pending["url"] == url

            # Step 2: Post-extension caches the response
            @dataclass
            class FakeResponse:
                message: str
                break_loop: bool = False

            response = FakeResponse(message="fetched content")

            with patch.object(post_mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(post_mod, "_head_validators", return_value=("\"v1\"", "")):
                ext = post_mod.SddCachePost(agent=agent)
                ext.execute(tool_name="browser", response=response)

            # Verify cache was written
            key = _cache_key(url)
            cache_file = os.path.join(cache_dir, f"{key}.json")
            assert os.path.isfile(cache_file)

            # Step 3: Second call (hit) — pre-extension redirects
            agent2 = _make_agent()
            tool_args2 = {"action": "navigate", "url": url}

            with patch.object(pre_mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(pre_mod, "_head_revalidate", return_value=304):
                ext = pre_mod.SddCachePre(agent=agent2)
                ext.execute(tool_name="browser", tool_args=tool_args2)

            assert tool_args2["action"] == "list"
            pending2 = agent2.data["sdd_cache_pending_hit"]
            assert pending2.get("hit") is True
            assert "fetched content" in pending2["message"]

            # Step 4: Post-extension surfaces cached content
            response2 = FakeResponse(message="list output")

            with patch.object(post_mod, "_cache_dir", return_value=cache_dir):
                ext = post_mod.SddCachePost(agent=agent2)
                ext.execute(tool_name="browser", response=response2)

            assert "[sdd-cache] Cache hit" in response2.message
            assert "fetched content" in response2.message

    def test_stale_entry_removed_on_miss(self):
        """Stale cache entry should be removed if origin returns no validators."""
        pre_mod = _import_pre()
        post_mod = _import_post()

        url = "https://example.com/stale"

        with tempfile.TemporaryDirectory() as cache_dir:
            # Create a stale cache entry
            _write_cache_entry(cache_dir, url, etag="old-etag")

            # Pre-extension: no URL stored (simulating entry exists but pre had no hit)
            agent = _make_agent(data={
                "sdd_cache_pending_hit": {"url": url}
            })

            @dataclass
            class FakeResponse:
                message: str
                break_loop: bool = False

            response = FakeResponse(message="new content")

            # Origin no longer returns validators
            with patch.object(post_mod, "_cache_dir", return_value=cache_dir), \
                 patch.object(post_mod, "_head_validators", return_value=("", "")):
                ext = post_mod.SddCachePost(agent=agent)
                ext.execute(tool_name="browser", response=response)

            # Stale entry should be removed
            key = _cache_key(url)
            cache_file = os.path.join(cache_dir, f"{key}.json")
            assert not os.path.isfile(cache_file)
