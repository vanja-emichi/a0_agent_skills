import subprocess
from pathlib import Path


def test_no_importlib_util_in_extensions():
    """Only lib files may use importlib.util - not extensions."""
    EXTENSIONS_DIR = "/a0/usr/plugins/a0_agent_skills/extensions"
    result = subprocess.run(
        ["grep", "-rl", "importlib.util", EXTENSIONS_DIR, "--include=*.py"],
        capture_output=True, text=True
    )
    files = [f for f in result.stdout.strip().split("\n") if f and not f.endswith(".pyc")]
    assert files == [], f"Found importlib.util in extensions: {files}"
