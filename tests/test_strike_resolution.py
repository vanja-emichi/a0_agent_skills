# tests/test_strike_resolution.py — Tests for StrikeTracker persist/rehydrate (T5)

import json
import pytest
from pathlib import Path
from lib.strike_tracker import StrikeTracker


class TestStrikeTrackerPersistRehydrate:
    """Tests for StrikeTracker persist/rehydrate cycle."""

    def test_persist_writes_strikes_to_metadata(self, tmp_path):
        tracker = StrikeTracker(threshold=3)
        tracker.record("hash_a")
        tracker.record("hash_a")
        tracker.record("hash_b")

        # Create initial metadata
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps({}))

        tracker.persist(tmp_path)

        metadata = json.loads(meta_path.read_text())
        assert metadata["strikes"]["hash_a"] == 2
        assert metadata["strikes"]["hash_b"] == 1

    def test_persist_omits_zero_counts(self, tmp_path):
        tracker = StrikeTracker(threshold=3)
        tracker.record("hash_a")
        tracker.record_resolution("hash_a")  # reset to 0

        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps({}))

        tracker.persist(tmp_path)

        metadata = json.loads(meta_path.read_text())
        assert "hash_a" not in metadata["strikes"]

    def test_rehydrate_restores_counts(self, tmp_path):
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps({"strikes": {"hash_a": 2, "hash_b": 1}}))

        tracker = StrikeTracker.rehydrate(tmp_path)

        assert tracker.get_count("hash_a") == 2
        assert tracker.get_count("hash_b") == 1

    def test_rehydrate_returns_fresh_tracker_when_no_metadata(self, tmp_path):
        tracker = StrikeTracker.rehydrate(tmp_path)
        assert tracker.get_count("any_hash") == 0

    def test_rehydrate_ignores_corrupt_metadata(self, tmp_path):
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text("not valid json")

        tracker = StrikeTracker.rehydrate(tmp_path)
        assert tracker.get_count("any_hash") == 0

    def test_roundtrip_persist_rehydrate(self, tmp_path):
        """Persist then rehydrate should preserve state."""
        meta_path = tmp_path / "metadata.json"
        meta_path.write_text(json.dumps({}))

        tracker1 = StrikeTracker(threshold=3)
        tracker1.record("hash_a")
        tracker1.record("hash_a")
        tracker1.persist(tmp_path)

        tracker2 = StrikeTracker.rehydrate(tmp_path)
        assert tracker2.get_count("hash_a") == 2
        assert tracker2.should_block("hash_a") is False

    def test_active_hashes_returns_nonzero(self):
        tracker = StrikeTracker(threshold=3)
        tracker.record("hash_a")
        tracker.record("hash_b")
        tracker.record_resolution("hash_b")  # reset to 0

        active = tracker.active_hashes()
        assert "hash_a" in active
        assert "hash_b" not in active

    def test_record_resolution_resets_count(self):
        tracker = StrikeTracker(threshold=3)
        tracker.record("hash_a")
        tracker.record("hash_a")
        tracker.record_resolution("hash_a")

        assert tracker.get_count("hash_a") == 0
        assert tracker.should_block("hash_a") is False
