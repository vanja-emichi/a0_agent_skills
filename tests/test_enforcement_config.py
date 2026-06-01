"""Tests for enforcement gate configuration surface (Task 1).

Verifies that default_config.yaml defines the enforcement gate keys with safe
defaults and that existing telemetry keys remain unchanged.

Run from /a0/usr/plugins/a0_agent_skills/:
    python -m pytest tests/test_enforcement_config.py -v
"""

from __future__ import annotations

import yaml
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PLUGIN_ROOT / "default_config.yaml"


def _load_config() -> dict:
    """Load and parse default_config.yaml."""
    assert CONFIG_PATH.exists(), "default_config.yaml must exist"
    return yaml.safe_load(CONFIG_PATH.read_text())


# ===========================================================================
# Enforcement gate config keys
# ===========================================================================


class TestEnforcementConfigSurface:
    """Verify enforcement gate configuration keys exist with safe defaults."""

    def test_enforcement_mode_exists(self):
        """default_config.yaml MUST define enforcement_mode."""
        cfg = _load_config()
        assert "enforcement_mode" in cfg, (
            "default_config.yaml must contain enforcement_mode key"
        )

    def test_enforcement_mode_is_enforce(self):
        """enforcement_mode MUST be 'enforce' (Task 6 — enforce mode enabled)."""
        cfg = _load_config()
        assert cfg.get("enforcement_mode") == "enforce", (
            f"enforcement_mode must be 'enforce', got {cfg.get('enforcement_mode')!r}"
        )

    def test_enforcement_classifier_model_exists(self):
        """default_config.yaml MUST define enforcement_classifier_model."""
        cfg = _load_config()
        assert "enforcement_classifier_model" in cfg, (
            "default_config.yaml must contain enforcement_classifier_model key"
        )

    def test_enforcement_classifier_model_defaults_to_none(self):
        """enforcement_classifier_model MUST default to null (use utility model)."""
        cfg = _load_config()
        assert cfg.get("enforcement_classifier_model") is None, (
            f"enforcement_classifier_model must be null, got {cfg.get('enforcement_classifier_model')!r}"
        )

    def test_enforcement_shadow_sample_rate_exists(self):
        """default_config.yaml MUST define enforcement_shadow_sample_rate."""
        cfg = _load_config()
        assert "enforcement_shadow_sample_rate" in cfg, (
            "default_config.yaml must contain enforcement_shadow_sample_rate key"
        )

    def test_enforcement_shadow_sample_rate_defaults_to_0_1(self):
        """enforcement_shadow_sample_rate MUST be 0.1 (10% shadow sampling enabled for Task 4)."""
        cfg = _load_config()
        assert cfg.get("enforcement_shadow_sample_rate") == 0.1, (
            f"enforcement_shadow_sample_rate must be 0.1, got {cfg.get('enforcement_shadow_sample_rate')!r}"
        )


# ===========================================================================
# Existing telemetry defaults preserved
# ===========================================================================


class TestTelemetryDefaultsPreserved:
    """Existing telemetry defaults MUST remain unchanged after enforcement config addition."""

    def test_telemetry_enabled_still_false(self):
        """telemetry_enabled MUST still be false (privacy-safe default)."""
        cfg = _load_config()
        assert cfg.get("telemetry_enabled") is False, (
            f"telemetry_enabled must remain false, got {cfg.get('telemetry_enabled')!r}"
        )

    def test_telemetry_log_path_unchanged(self):
        """telemetry_log_path MUST remain unchanged."""
        cfg = _load_config()
        assert cfg.get("telemetry_log_path") == ".a0proj/skill_activations.jsonl", (
            f"telemetry_log_path unchanged, got {cfg.get('telemetry_log_path')!r}"
        )

    def test_telemetry_max_lines_unchanged(self):
        """telemetry_max_lines MUST remain 0."""
        cfg = _load_config()
        assert cfg.get("telemetry_max_lines") == 0, (
            f"telemetry_max_lines must remain 0, got {cfg.get('telemetry_max_lines')!r}"
        )
