# lib/strike_tracker.py — 3-strike error tracking for a0_agent_skills v0.2.0
#
# Tracks identical errors by hash. After N consecutive occurrences (default 3),
# should_block() returns True. Counter resets on record_resolution().
#
# Used by gates (T14) and log_error (T12) to enforce the 3-strike rule.
# Source: plan.md T06 acceptance criteria.

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional


class StrikeTracker:
    """Tracks error occurrence counts by hash for 3-strike enforcement.

    Default threshold: 3 (configurable via planning.gates.three_strike setting).
    """

    def __init__(self, threshold: int = 3) -> None:
        self._threshold = threshold
        self._counts: dict[str, int] = {}

    def record(self, error_hash: str) -> None:
        """Record an error occurrence. Increments the count for this hash."""
        self._counts[error_hash] = self._counts.get(error_hash, 0) + 1

    def should_block(self, error_hash: str) -> bool:
        """Check if the error count has reached the block threshold."""
        return self._counts.get(error_hash, 0) >= self._threshold

    def get_count(self, error_hash: str) -> int:
        """Return the current strike count for a hash."""
        return self._counts.get(error_hash, 0)

    def record_resolution(self, error_hash: str) -> None:
        """Reset the strike count after a successful mitigating action."""
        self._counts[error_hash] = 0

    def active_hashes(self) -> list[str]:
        """Return hashes with non-zero strike counts."""
        return [h for h, c in self._counts.items() if c > 0]

    # ------------------------------------------------------------------
    # Persistence — read/write strike state from metadata.json
    # ------------------------------------------------------------------

    def persist(self, plan_dir: Path) -> None:
        """Write current strike state to metadata.json."""
        metadata_path = plan_dir / "metadata.json"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        else:
            metadata = {}

        # Only persist non-zero counts
        metadata["strikes"] = {
            h: c for h, c in self._counts.items() if c > 0
        }

        # Atomic write via LifecycleState helper if available, else direct
        try:
            from lib.lifecycle_state import LifecycleState
            LifecycleState._atomic_write(metadata_path, json.dumps(metadata, indent=2))
        except ImportError:
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    @classmethod
    def rehydrate(cls, plan_dir: Path, threshold: int = 3) -> StrikeTracker:
        """Create a StrikeTracker restored from metadata.json on disk.

        Reads the 'strikes' key from metadata.json and restores counts.
        Returns a fresh tracker if no persisted state exists.
        """
        tracker = cls(threshold=threshold)
        metadata_path = plan_dir / "metadata.json"
        if metadata_path.exists():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                for _hash, _count in metadata.get("strikes", {}).items():
                    if _count > 0:
                        tracker._counts[_hash] = _count
            except (ValueError, OSError):
                pass  # Corrupt metadata — start fresh
        return tracker
