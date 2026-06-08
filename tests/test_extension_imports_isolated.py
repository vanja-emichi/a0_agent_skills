"""Isolated subprocess tests for extension imports.

Each test runs in a fresh Python subprocess so broken imports are caught
without polluting sys.modules in the main test process.

This prevents the scenario where a broken extension import crashes the
entire Agent Zero runtime and requires a process restart to clear.
"""

import subprocess
import sys
import os
import pytest

PLUGIN_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

EXTENSION_FILES = [
    "extensions/python/monologue_end/_10_simplify_ignore.py",
    "extensions/python/text_editor_write_after/_10_simplify_ignore.py",
    "extensions/python/text_editor_patch_after/_10_simplify_ignore.py",
    "extensions/python/tool_execute_before/_10_sdd_cache.py",
    "extensions/python/tool_execute_before/_20_simplify_ignore.py",
    "extensions/python/_simplify_ignore_util.py",
]


def _run_subprocess(script, timeout=10):
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=PLUGIN_ROOT,
    )


def _make_import_script(file_path):
    abs_path = os.path.join(PLUGIN_ROOT, file_path)
    return "import sys, os, types, importlib.util\n" \
        "sys.path.insert(0, %r)\n" % PLUGIN_ROOT + \
        'helpers = types.ModuleType("helpers")\n' \
        'helpers_ext = types.ModuleType("helpers.extension")\n' \
        "class Extension:\n" \
        "    def __init__(self, agent=None, **kwargs):\n" \
        "        self.agent = agent\n" \
        "        self.kwargs = kwargs\n" \
        "helpers_ext.Extension = Extension\n" \
        "helpers.extension = helpers_ext\n" \
        'sys.modules["helpers"] = helpers\n' \
        'sys.modules["helpers.extension"] = helpers_ext\n' \
        "spec = importlib.util.spec_from_file_location('test_ext', %r)\n" % abs_path + \
        "mod = importlib.util.module_from_spec(spec)\n" \
        "spec.loader.exec_module(mod)\n" \
        "print('OK: loaded ' + repr(mod))"


class TestExtensionImports:
    """Verify all extension files import cleanly in isolated subprocesses."""

    @pytest.mark.parametrize("file_path", EXTENSION_FILES, ids=lambda f: f.split("/")[-1])
    def test_extension_imports_cleanly(self, file_path):
        script = _make_import_script(file_path)
        result = _run_subprocess(script)
        assert result.returncode == 0, (
            "Import failed for %s\n  stdout: %s\n  stderr: %s"
            % (file_path, result.stdout.strip(), result.stderr.strip())
        )
        assert "OK:" in result.stdout
