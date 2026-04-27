# test_simplify_ignore_locking.py - TDD tests for file locking (Slice 4, T10)
# RED phase: These tests SHOULD FAIL until locking is implemented

import fcntl
import os
import tempfile
import time

import pytest

import sys
from pathlib import Path
_PLUGIN_ROOT = str(Path(__file__).resolve().parents[1])
if _PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, _PLUGIN_ROOT)


class TestAcquireReleaseLock:
    """Tests for _acquire_lock and _release_lock functions."""

    def test_acquire_lock_returns_fd(self):
        """Lock acquisition should return a file descriptor (not None)."""
        from lib.simplify_ignore_utils import _acquire_lock, _release_lock

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            test_file = f.name
        try:
            lock_fd = _acquire_lock(test_file, timeout=1.0)
            assert lock_fd is not None, "Should acquire lock immediately"
            assert not lock_fd.closed, "Returned fd should be open"
            _release_lock(lock_fd)
        finally:
            os.unlink(test_file)
            lock_path = test_file + ".lock"
            if os.path.exists(lock_path):
                os.unlink(lock_path)

    def test_release_lock_closes_fd(self):
        """_release_lock should close the lock file descriptor."""
        from lib.simplify_ignore_utils import _acquire_lock, _release_lock

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            test_file = f.name
        try:
            lock_fd = _acquire_lock(test_file, timeout=1.0)
            assert lock_fd is not None
            _release_lock(lock_fd)
            assert lock_fd.closed, "fd should be closed after release"
        finally:
            os.unlink(test_file)
            lock_path = test_file + ".lock"
            if os.path.exists(lock_path):
                os.unlink(lock_path)

    def test_lock_timeout_fails_open(self):
        """If lock is already held, second acquire should return None (fail-open)."""
        from lib.simplify_ignore_utils import _acquire_lock, _release_lock

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            test_file = f.name
        try:
            lock_fd1 = _acquire_lock(test_file, timeout=1.0)
            assert lock_fd1 is not None, "First lock should succeed"

            # Second acquire with short timeout - should fail
            lock_fd2 = _acquire_lock(test_file, timeout=0.3)
            assert lock_fd2 is None, "Should return None when lock is held"

            _release_lock(lock_fd1)
        finally:
            os.unlink(test_file)
            lock_path = test_file + ".lock"
            if os.path.exists(lock_path):
                os.unlink(lock_path)

    def test_lock_released_allows_reacquire(self):
        """After releasing a lock, it should be acquirable again."""
        from lib.simplify_ignore_utils import _acquire_lock, _release_lock

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            test_file = f.name
        try:
            lock_fd1 = _acquire_lock(test_file, timeout=1.0)
            assert lock_fd1 is not None
            _release_lock(lock_fd1)

            lock_fd2 = _acquire_lock(test_file, timeout=1.0)
            assert lock_fd2 is not None, "Should reacquire after release"
            _release_lock(lock_fd2)
        finally:
            os.unlink(test_file)
            lock_path = test_file + ".lock"
            if os.path.exists(lock_path):
                os.unlink(lock_path)

    def test_lock_file_created_on_demand(self):
        """Lock acquisition should create a .lock file beside the target."""
        from lib.simplify_ignore_utils import _acquire_lock, _release_lock

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            test_file = f.name
        try:
            lock_path = test_file + ".lock"
            assert not os.path.exists(lock_path), "No lock file initially"

            lock_fd = _acquire_lock(test_file, timeout=1.0)
            assert lock_fd is not None
            assert os.path.exists(lock_path), ".lock file should exist after acquire"

            _release_lock(lock_fd)
        finally:
            os.unlink(test_file)
            lock_path = test_file + ".lock"
            if os.path.exists(lock_path):
                os.unlink(lock_path)

    def test_release_none_is_noop(self):
        """_release_lock(None) should not raise."""
        from lib.simplify_ignore_utils import _release_lock
        _release_lock(None)  # Should not raise

    def test_release_closed_fd_is_noop(self):
        """_release_lock on a closed fd should not raise."""
        from lib.simplify_ignore_utils import _acquire_lock, _release_lock

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            test_file = f.name
        try:
            lock_fd = _acquire_lock(test_file, timeout=1.0)
            assert lock_fd is not None
            lock_fd.close()  # Close it manually first
            _release_lock(lock_fd)  # Should not raise
        finally:
            os.unlink(test_file)
            lock_path = test_file + ".lock"
            if os.path.exists(lock_path):
                os.unlink(lock_path)


class TestStaleLockCleanup:
    """Tests for stale .lock file cleanup in recovery."""

    def test_cleanup_lock_files_function_exists(self):
        """cleanup_stale_lock_files function should exist in utils."""
        from lib import simplify_ignore_utils as _su
        assert hasattr(_su, "cleanup_stale_lock_files"), \
            "cleanup_stale_lock_files should be exported from simplify_ignore_utils"

    def test_cleanup_lock_files_removes_locks(self):
        """cleanup_stale_lock_files should remove .lock files from manifest dir."""
        from lib.simplify_ignore_utils import MANIFEST_DIR, cleanup_stale_lock_files

        MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
        stale1 = MANIFEST_DIR / "test1.lock"
        stale2 = MANIFEST_DIR / "test2.lock"
        keep = MANIFEST_DIR / "test.json"
        stale1.write_text("")
        stale2.write_text("")
        keep.write_text("{}")

        cleanup_stale_lock_files()

        assert not stale1.exists(), "stale .lock file should be removed"
        assert not stale2.exists(), "stale .lock file should be removed"
        assert keep.exists(), "non-lock files should be preserved"

        keep.unlink()  # cleanup


class TestLockingHelpersUnit:
    """Additional unit tests for edge cases."""

    def test_acquire_lock_non_blocking_no_sleep_when_available(self):
        """Lock should be acquired on first try when uncontested."""
        from lib.simplify_ignore_utils import _acquire_lock, _release_lock

        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as f:
            test_file = f.name
        try:
            start = time.monotonic()
            lock_fd = _acquire_lock(test_file, timeout=5.0)
            elapsed = time.monotonic() - start
            assert lock_fd is not None
            assert elapsed < 0.5, f"Uncontested lock should be fast, took {elapsed:.3f}s"
            _release_lock(lock_fd)
        finally:
            os.unlink(test_file)
            lock_path = test_file + ".lock"
            if os.path.exists(lock_path):
                os.unlink(lock_path)

    def test_acquire_uses_fcntl_flock(self):
        """Verify the implementation uses fcntl.flock with LOCK_EX | LOCK_NB."""
        import inspect
        from lib.simplify_ignore_utils import _acquire_lock
        source = inspect.getsource(_acquire_lock)
        assert "fcntl.flock" in source
        assert "LOCK_EX" in source
        assert "LOCK_NB" in source
