"""Contract and parity tests for DOX workflow prerequisites.

These tests verify static DOX contracts, routing, and the AGENTS.md-based
authority model. They are intentionally shallow guardrails; real
scheduler-based behavioral coverage lives in the e2e test suite.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

A0_ROOT = Path("/a0")
PLUGIN_DIR = Path(__file__).resolve().parents[1]
SKILLS_DIR = PLUGIN_DIR / "skills"
PROMPTS_DIR = PLUGIN_DIR / "prompts"

if str(A0_ROOT) not in sys.path:
    sys.path.insert(0, str(A0_ROOT))


def _install_fake_agent_module(monkeypatch):
    """Install minimal agent module stubs for framework imports."""
    fake_agent = types.ModuleType("agent")
    for name in ("Agent", "AgentConfig", "AgentContext", "AgentContextType", "LoopData"):
        setattr(fake_agent, name, type(name, (), {}))
    monkeypatch.setitem(sys.modules, "agent", fake_agent)


def _install_fake_projects_module(monkeypatch):
    """Install minimal projects module stubs for framework imports."""
    fake_projects = types.ModuleType("helpers.projects")
    fake_projects.PROJECT_META_DIR = ".a0proj"
    fake_projects.get_project_meta = lambda *args, **kwargs: ""
    fake_projects.get_context_project_name = lambda *args, **kwargs: ""
    monkeypatch.setitem(sys.modules, "helpers.projects", fake_projects)
    import helpers
    monkeypatch.setattr(helpers, "projects", fake_projects, raising=False)
    sys.modules.pop("helpers.skills", None)


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear framework caches before and after each test."""
    from helpers import cache
    for area in ("*(plugins)*", "*(skills)*", "*(subagent)*"):
        try:
            cache.clear(area)
        except Exception:
            pass
    yield
    for area in ("*(plugins)*", "*(skills)*", "*(subagent)*"):
        try:
            cache.clear(area)
        except Exception:
            pass


@pytest.fixture()
def dox_test_env(monkeypatch, tmp_path):
    """Create a temporary project with nested AGENTS.md contracts for DOX testing."""
    _install_fake_agent_module(monkeypatch)
    _install_fake_projects_module(monkeypatch)
    
    # Create a test project structure with conflicting AGENTS.md contracts
    project_root = tmp_path / "test_project"
    project_root.mkdir()
    
    # Root AGENTS.md requires ROOT_MARKER
    (project_root / "AGENTS.md").write_text(
        "# Root Contract\n\n"
        "## Local Contracts\n\n"
        "- All output must contain `ROOT_MARKER`\n"
    )
    
    # Child docs/AGENTS.md requires DOCS_MARKER and forbids ROOT_MARKER
    docs_dir = project_root / "docs"
    docs_dir.mkdir()
    (docs_dir / "AGENTS.md").write_text(
        "# Docs Contract\n\n"
        "## Local Contracts\n\n"
        "- All output must contain `DOCS_MARKER`\n"
        "- Output must NOT contain `ROOT_MARKER`\n"
    )
    
    # Target file in docs/
    target_file = docs_dir / "example.md"
    target_file.write_text("# Example\n")
    
    # Return the project root and target file for tests to use
    return SimpleNamespace(
        project_root=project_root,
        target_file=target_file,
        docs_dir=docs_dir,
    )


@pytest.mark.dox_contract
def test_dox_project_context_skill_removed():
    """Prove the dox-project-context skill has been removed from both locations."""
    plugin_skill = SKILLS_DIR / "dox-project-context" / "SKILL.md"
    source_skill = Path("/a0/usr/projects/a0_agent_skills/skills/dox-project-context/SKILL.md")
    
    assert not plugin_skill.exists(), (
        "dox-project-context skill should not exist in plugin"
    )
    assert not source_skill.exists(), (
        "dox-project-context skill should not exist in source project"
    )


@pytest.mark.dox_contract
def test_dox_interpreter_teaches_agents_md_chain_reading(dox_test_env, monkeypatch):
    """Prove the DOX interpreter teaches reading AGENTS.md chain before mutation."""
    interpreter_path = PROMPTS_DIR / "agent.system.dox_interpreter.md"
    assert interpreter_path.exists(), "DOX interpreter prompt not found"

    interpreter_content = interpreter_path.read_text()

    # The interpreter must teach reading AGENTS.md chain
    chain_reading = any(phrase in interpreter_content.lower() for phrase in [
        "agents.md chain",
        "read the applicable",
    ])

    assert chain_reading, (
        "DOX interpreter does not teach AGENTS.md chain reading"
    )


@pytest.mark.dox_contract
def test_dox_interpreter_teaches_nearest_contract_wins(dox_test_env, monkeypatch):
    """Prove the DOX interpreter teaches that nearest contract wins for local details."""
    interpreter_path = PROMPTS_DIR / "agent.system.dox_interpreter.md"
    interpreter_content = interpreter_path.read_text()

    # Must mention nearest contract precedence
    nearest_mentioned = any(phrase in interpreter_content.lower() for phrase in [
        "nearest applicable",
        "nearest contract",
    ])

    assert nearest_mentioned, (
        "DOX interpreter does not teach nearest-contract precedence"
    )


@pytest.mark.dox_contract
def test_dox_interpreter_teaches_closeout():
    """Prove the DOX interpreter teaches closeout (updating AGENTS.md after mutation)."""
    interpreter_path = PROMPTS_DIR / "agent.system.dox_interpreter.md"
    interpreter_content = interpreter_path.read_text()

    # Must mention closeout (section header or phrase)
    closeout_found = any(phrase in interpreter_content for phrase in [
        "## Closeout",
        "DOX closeout",
    ])
    assert closeout_found, (
        "DOX interpreter does not teach DOX closeout"
    )
    assert "nearest owning" in interpreter_content, (
        "DOX interpreter does not mention updating nearest owning AGENTS.md"
    )


@pytest.mark.dox_contract
def test_dox_interpreter_declares_agents_md_authority():
    """Prove the DOX interpreter states AGENTS.md files are binding work contracts."""
    interpreter_path = PROMPTS_DIR / "agent.system.dox_interpreter.md"
    interpreter_content = interpreter_path.read_text()

    # Must state AGENTS.md files are binding
    assert "binding work contracts" in interpreter_content, (
        "DOX interpreter does not declare AGENTS.md as binding contracts"
    )
    assert "AGENTS.md" in interpreter_content


@pytest.mark.dox_contract
def test_no_dox_project_context_references_remain():
    """Prove no runtime code still references dox-project-context as a dependency."""
    meta_skill_path = SKILLS_DIR / "using-agent-skills" / "SKILL.md"
    skill_content = meta_skill_path.read_text()
    
    assert "dox-project-context" not in skill_content, (
        "using-agent-skills still references removed dox-project-context"
    )
    
    # Also verify command templates don't reference it
    commands_dir = PLUGIN_DIR / "commands"
    for cmd_file in ("spec.txt", "plan.txt", "build.txt", "test.txt", "review.txt", "code-simplify.txt"):
        cmd_path = commands_dir / cmd_file
        if cmd_path.exists():
            content = cmd_path.read_text()
            assert "dox-project-context" not in content, (
                f"{cmd_file} still references removed dox-project-context"
            )


@pytest.mark.dox_contract
def test_dox_interpreter_routes_to_agents_md():
    """Prove the DOX interpreter routes project work to AGENTS.md chain."""
    interpreter_path = PROMPTS_DIR / "agent.system.dox_interpreter.md"
    assert interpreter_path.exists(), "DOX interpreter prompt not found"

    interpreter_content = interpreter_path.read_text()

    # The interpreter must route to AGENTS.md for project work
    assert "AGENTS.md" in interpreter_content, (
        "DOX interpreter does not mention AGENTS.md"
    )

    # Must NOT reference dox-project-context
    assert "dox-project-context" not in interpreter_content, (
        "DOX interpreter still references removed dox-project-context"
    )


@pytest.mark.dox_contract
def test_lifecycle_commands_include_dox_gates():
    """Prove lifecycle commands include DOX preflight and closeout gates.
    
    Commands that mutate or review project files must explicitly include
    DOX workflow steps referencing AGENTS.md chain.
    """
    commands_dir = PLUGIN_DIR / "commands"
    
    commands_needing_dox = [
        "spec.txt",
        "plan.txt",
        "build.txt",
        "test.txt",
        "review.txt",
        "ship.py",
    ]
    
    for cmd_file in commands_needing_dox:
        cmd_path = commands_dir / cmd_file
        if not cmd_path.exists():
            continue
        
        cmd_content = cmd_path.read_text()
        
        has_dox_gate = (
            "dox preflight" in cmd_content.lower()
            or "dox closeout" in cmd_content.lower()
            or "AGENTS.md" in cmd_content
        )

        assert has_dox_gate, (
            f"Command {cmd_file} does not include DOX gates (AGENTS.md reference)"
        )


@pytest.mark.dox_contract
def test_agent_profiles_are_dox_aware():
    """Prove subordinate agent profiles treat AGENTS.md as binding.
    
    Specialist profiles (code-reviewer, security-auditor, test-engineer)
    must explicitly state that project AGENTS.md contracts are binding
    when reviewing project files.
    """
    agents_dir = PLUGIN_DIR / "agents"
    
    specialist_profiles = [
        "code-reviewer",
        "security-auditor",
        "test-engineer",
    ]
    
    for profile_name in specialist_profiles:
        profile_dir = agents_dir / profile_name
        if not profile_dir.exists():
            continue
        
        prompt_files = list(profile_dir.glob("prompts/*.md"))
        if not prompt_files:
            continue
        
        prompt_content = "\n".join(f.read_text() for f in prompt_files)
        
        agents_aware = any(phrase in prompt_content for phrase in [
            "AGENTS.md",
            "project contracts",
            "binding",
            "DOX",
        ])
        
        assert agents_aware, (
            f"Profile {profile_name} does not mention AGENTS.md or DOX contracts"
        )
