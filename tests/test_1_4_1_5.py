# test_1_4_1_5_extension_import.py - Tasks 1.4 & 1.5 TDD
# Tests for extension_base.py rename and import_utils.py rename

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestExtensionBaseStructure:
    """Task 1.4: Verify extension_base.py has correct structure.
    Cannot import directly due to missing deps, so test file content."""

    def test_file_has_lifecycle_extension_class(self):
        """extension_base.py defines LifecycleExtension."""
        path = os.path.join(os.path.dirname(__file__), "..", "lib", "extension_base.py")
        content = open(path).read()
        assert "class LifecycleExtension" in content

    def test_file_no_plan_extension_class(self):
        """extension_base.py does NOT define PlanExtension."""
        path = os.path.join(os.path.dirname(__file__), "..", "lib", "extension_base.py")
        content = open(path).read()
        assert "class PlanExtension" not in content

    def test_file_has_load_lifecycle_method(self):
        path = os.path.join(os.path.dirname(__file__), "..", "lib", "extension_base.py")
        content = open(path).read()
        assert "def _load_lifecycle" in content

    def test_file_has_resolve_lifecycle_dir(self):
        path = os.path.join(os.path.dirname(__file__), "..", "lib", "extension_base.py")
        content = open(path).read()
        assert "def _resolve_lifecycle_dir" in content

    def test_file_no_load_plan_method(self):
        path = os.path.join(os.path.dirname(__file__), "..", "lib", "extension_base.py")
        content = open(path).read()
        assert "def _load_plan" not in content

    def test_file_no_resolve_plan_dir(self):
        path = os.path.join(os.path.dirname(__file__), "..", "lib", "extension_base.py")
        content = open(path).read()
        assert "def _resolve_plan_dir" not in content

    def test_file_has_get_lifecycle_state(self):
        path = os.path.join(os.path.dirname(__file__), "..", "lib", "extension_base.py")
        content = open(path).read()
        assert "_get_lifecycle_state" in content
        assert "get_lifecycle_state_module" in content

    def test_file_compiles(self):
        """extension_base.py compiles cleanly."""
        import py_compile
        path = os.path.join(os.path.dirname(__file__), "..", "lib", "extension_base.py")
        py_compile.compile(path, doraise=True)


class TestImportUtils:
    """Task 1.5: get_plan_state_module -> get_lifecycle_state_module"""

    def test_get_lifecycle_state_module_exists(self):
        from lib.import_utils import get_lifecycle_state_module
        assert callable(get_lifecycle_state_module)

    def test_lifecycle_state_module_has_lifecycle_state(self):
        from lib.import_utils import get_lifecycle_state_module
        mod = get_lifecycle_state_module()
        assert hasattr(mod, "LifecycleState")

    def test_no_get_plan_state_module(self):
        import lib.import_utils as mod
        assert not hasattr(mod, "get_plan_state_module"), "get_plan_state_module should not exist"

    def test_module_name_uses_lifecycle(self):
        import lib.import_utils as mod
        import inspect
        source = inspect.getsource(mod.get_lifecycle_state_module)
        assert "lifecycle_state" in source
        assert "plan_state" not in source

    def test_file_compiles(self):
        import py_compile
        path = os.path.join(os.path.dirname(__file__), "..", "lib", "import_utils.py")
        py_compile.compile(path, doraise=True)


class TestPhase1Checkpoint:
    """Phase 1 Checkpoint: All lib/tool files compile."""

    def test_all_phase1_files_compile(self):
        import py_compile
        base = os.path.join(os.path.dirname(__file__), "..")
        files = [
            "lib/constants.py",
            "lib/lifecycle_state.py",
            "lib/extension_base.py",
            "lib/import_utils.py",
            "tools/lifecycle.py",
        ]
        for f in files:
            py_compile.compile(os.path.join(base, f), doraise=True)
