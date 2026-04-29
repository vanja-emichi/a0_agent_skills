"""Tests for bug fixes: Phase status normalization and ADR [adr] tag requirement."""

import sys
import os
import tempfile
from pathlib import Path

# Ensure plugin root is on path
plugin_root = os.path.join(os.path.dirname(__file__), '..')
if plugin_root not in sys.path:
    sys.path.insert(0, plugin_root)

from lib.lifecycle_state import Phase
from lib.finding_utils import _is_trusted_finding


class TestPhaseStatusNormalization:
    """Bug 2: Phase dataclass must normalize invalid status values."""

    def test_pending_stays_pending(self):
        p = Phase(title="test", status="pending")
        assert p.status == "pending"

    def test_in_progress_stays_in_progress(self):
        p = Phase(title="test", status="in_progress")
        assert p.status == "in_progress"

    def test_completed_stays_completed(self):
        p = Phase(title="test", status="completed")
        assert p.status == "completed"

    def test_active_normalized_to_in_progress(self):
        p = Phase(title="test", status="active")
        assert p.status == "in_progress"

    def test_running_normalized_to_in_progress(self):
        p = Phase(title="test", status="running")
        assert p.status == "in_progress"

    def test_current_normalized_to_in_progress(self):
        p = Phase(title="test", status="current")
        assert p.status == "in_progress"

    def test_done_normalized_to_completed(self):
        p = Phase(title="test", status="done")
        assert p.status == "completed"

    def test_finished_normalized_to_completed(self):
        p = Phase(title="test", status="finished")
        assert p.status == "completed"

    def test_case_insensitive_normalization(self):
        p = Phase(title="test", status="Active")
        assert p.status == "in_progress"

    def test_case_insensitive_running(self):
        p = Phase(title="test", status="RUNNING")
        assert p.status == "in_progress"

    def test_unknown_status_defaults_to_pending(self):
        p = Phase(title="test", status="bogus")
        assert p.status == "pending"

    def test_empty_status_defaults_to_pending(self):
        p = Phase(title="test", status="")
        assert p.status == "pending"

    def test_default_status_is_pending(self):
        p = Phase(title="test")
        assert p.status == "pending"


class TestIsTrustedFinding:
    """Bug 3: _is_trusted_finding requires [adr] tag."""

    def test_line_with_adr_tag(self):
        assert _is_trusted_finding("Use PostgreSQL for persistence [ADR]") is True

    def test_line_with_lowercase_adr_tag(self):
        assert _is_trusted_finding("Use PostgreSQL [adr]") is True

    def test_line_with_mixed_case_adr_tag(self):
        assert _is_trusted_finding("Use PostgreSQL [Adr]") is True

    def test_line_without_adr_tag(self):
        assert _is_trusted_finding("Use PostgreSQL for persistence") is False

    def test_empty_line(self):
        assert _is_trusted_finding("") is False

    def test_whitespace_only(self):
        assert _is_trusted_finding("   ") is False

    def test_header_line(self):
        assert _is_trusted_finding("# Findings") is False

    def test_table_line(self):
        assert _is_trusted_finding("| col1 | col2 |") is False

    def test_untrusted_line(self):
        assert _is_trusted_finding("[untrusted] some finding") is False

    def test_untrusted_with_adr_tag(self):
        # Even untrusted lines with [adr] should pass - the tag is opt-in
        assert _is_trusted_finding("[untrusted] some finding [adr]") is True

    def test_test_result_line(self):
        assert _is_trusted_finding("PASS: all tests passed") is False

    def test_verification_note(self):
        assert _is_trusted_finding("Verified the implementation works") is False

    def test_adr_in_middle_of_text(self):
        assert _is_trusted_finding("Decision: use Redis [adr] for caching") is True

    def test_adr_at_start(self):
        assert _is_trusted_finding("[adr] Use Redis for caching") is True


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
