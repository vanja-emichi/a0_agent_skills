# test_t8_t9.py - TDD tests for architecture cleanup (Slice 3)
# RED phase: These tests SHOULD FAIL until fixes are applied

import os

PLUGIN_ROOT = "/a0/usr/plugins/a0_agent_skills"
LIB_DIR = os.path.join(PLUGIN_ROOT, "lib")


def test_lifecycle_state_no_importlib_util():
    """lifecycle_state.py should not use importlib.util directly."""
    path = os.path.join(LIB_DIR, "lifecycle_state.py")
    with open(path) as f:
        content = f.read()
    assert "importlib.util" not in content
    assert "_load_constants_module" not in content


def test_config_version_matches_plugin():
    """default_config.yaml version should match plugin version."""
    config_path = os.path.join(PLUGIN_ROOT, "default_config.yaml")
    with open(config_path) as f:
        content = f.read()
    # Plugin is v0.3.1
    assert "0.3.1" in content or "v0.3.1" in content
    assert "0.2.0" not in content
