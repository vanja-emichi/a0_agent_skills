"""Contract and parity tests for DOX workflow prerequisites.

These tests verify static DOX contracts, routing, and source/plugin parity.
They are intentionally shallow guardrails; real scheduler-based behavioral
coverage lives in the batch scheduler harness tests.
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
def test_framework_plumbing_root_only_injection(dox_test_env, monkeypatch):
    """Prove dox-project-context explicitly states child AGENTS.md files are not auto-injected.

    This is the foundation DOX relies on: the skill must teach that only root
    AGENTS.md is auto-injected and child contracts must be read manually.
    """
    dox_skill_path = SKILLS_DIR / "dox-project-context" / "SKILL.md"
    assert dox_skill_path.exists(), "dox-project-context skill not found"

    skill_content = dox_skill_path.read_text()

    # The skill must explicitly state that child AGENTS.md files are NOT auto-loaded
    child_not_auto_loaded = any(phrase in skill_content for phrase in [
        "child `AGENTS.md` files are not automatically loaded",
        "not automatically injected",
        "not automatically loaded",
        "must be read manually",
    ])

    assert child_not_auto_loaded, (
        "dox-project-context does not explicitly state that child AGENTS.md files "
        "are not automatically loaded by the framework"
    )


@pytest.mark.dox_contract
def test_framework_plumbing_child_not_auto_injected(dox_test_env, monkeypatch):
    """Prove dox-project-context teaches the manual chain-walk requirement.

    If child AGENTS.md files were auto-injected, there would be no need for
    the explicit walk process. The skill must teach manual traversal.
    """
    dox_skill_path = SKILLS_DIR / "dox-project-context" / "SKILL.md"
    skill_content = dox_skill_path.read_text()

    # The skill must teach explicit manual reading of AGENTS.md files
    manual_read_required = all(phrase in skill_content for phrase in [
        "walk from the project root",
        "Read every `AGENTS.md` found along the route",
    ])

    assert manual_read_required, (
        "dox-project-context does not teach explicit manual reading of AGENTS.md "
        "files along the target path, which is required since they are not auto-injected"
    )


@pytest.mark.dox_contract
def test_dox_skill_teaches_chain_walk():
    """Prove dox-project-context skill explicitly teaches the chain-walk process.
    
    The skill must instruct agents to read child AGENTS.md files before
    editing target paths, not just rely on root injection.
    """
    dox_skill_path = SKILLS_DIR / "dox-project-context" / "SKILL.md"
    assert dox_skill_path.exists(), "dox-project-context skill not found"
    
    skill_content = dox_skill_path.read_text()
    
    # The skill must mention reading AGENTS.md files along the path
    assert "walk" in skill_content.lower() or "route" in skill_content.lower(), (
        "dox-project-context does not teach path walking"
    )
    
    # The skill must mention child AGENTS.md files explicitly
    assert "child" in skill_content.lower() and "AGENTS.md" in skill_content, (
        "dox-project-context does not mention child AGENTS.md files"
    )
    
    # The skill must distinguish between root and child injection
    assert "not automatically" in skill_content.lower() or "manually" in skill_content.lower(), (
        "dox-project-context does not teach that child AGENTS.md must be read manually"
    )


@pytest.mark.dox_contract
def test_nearest_contract_precedence_in_dox_skill():
    """Prove dox-project-context teaches that nearest contract wins for local details.
    
    When parent and child AGENTS.md conflict, the skill must instruct
    agents to follow the closer contract for local work.
    """
    dox_skill_path = SKILLS_DIR / "dox-project-context" / "SKILL.md"
    skill_content = dox_skill_path.read_text()
    
    # The skill must mention precedence or conflict resolution
    precedence_mentioned = any(phrase in skill_content.lower() for phrase in [
        "nearest",
        "closest",
        "precedence",
        "conflict",
        "parent and child",
        "local contract",
    ])
    
    assert precedence_mentioned, (
        "dox-project-context does not teach nearest-contract precedence"
    )
    
    # The skill must explicitly state local contracts control local details
    local_controls = any(phrase in skill_content for phrase in [
        "nearest `AGENTS.md` as the local contract",
        "closest file owns local details",
        "use the nearest",
        "local contract wins",
    ])
    
    assert local_controls, (
        "dox-project-context does not state that nearest contract controls local details"
    )


@pytest.mark.dox_contract
def test_subordinate_handoff_in_dox_skill():
    """Prove dox-project-context teaches DOX context must be passed to subordinates.
    
    Subordinate agents do not automatically receive the main agent's loaded
    skills or context, so DOX context must be explicitly handed off.
    """
    dox_skill_path = SKILLS_DIR / "dox-project-context" / "SKILL.md"
    skill_content = dox_skill_path.read_text()
    
    # The skill must mention subordinate handoff
    subordinate_mentioned = any(phrase in skill_content.lower() for phrase in [
        "subordinate",
        "call_subordinate",
        "delegate",
        "handoff",
        "pass.*context",
    ])
    
    assert subordinate_mentioned, (
        "dox-project-context does not mention subordinate context handoff"
    )
    
    # The skill must explicitly state subordinates need DOX context
    dox_context_passed = any(phrase in skill_content for phrase in [
        "include either",
        "relevant DOX contract excerpts",
        "instruction to read the applicable `AGENTS.md` chain",
        "Subordinates should report DOX gaps",
    ])
    
    assert dox_context_passed, (
        "dox-project-context does not teach passing DOX context to subordinates"
    )


@pytest.mark.dox_contract
def test_source_plugin_dox_skill_parity():
    """Prove source and plugin dox-project-context skills are semantically aligned.
    
    The installed plugin skill must match the source authoring truth,
    not drift into a different workflow description.
    """
    source_skill = (
        Path("/a0/usr/projects/a0_agent_skills/skills/dox-project-context/SKILL.md")
    )
    plugin_skill = SKILLS_DIR / "dox-project-context" / "SKILL.md"
    
    assert source_skill.exists(), "Source dox-project-context skill not found"
    assert plugin_skill.exists(), "Plugin dox-project-context skill not found"
    
    source_content = source_skill.read_text()
    plugin_content = plugin_skill.read_text()
    
    # The core workflow sections should match
    for section_marker in ["## Core Process", "### 1. DOX preflight", "### 3. DOX closeout"]:
        if section_marker in source_content:
            assert section_marker in plugin_content, (
                f"Plugin skill missing section: {section_marker}"
            )
    
    # The skill should not have drifted on key behavioral requirements
    key_requirements = [
        "Read every `AGENTS.md` found along the route",
        "nearest `AGENTS.md` as the local contract",
        "Update the nearest owning `AGENTS.md`",
    ]
    
    for requirement in key_requirements:
        if requirement in source_content:
            assert requirement in plugin_content, (
                f"Plugin skill drifted on requirement: {requirement}"
            )


@pytest.mark.dox_contract
def test_using_agent_skills_routes_to_dox():
    """Prove using-agent-skills meta-skill routes project work to dox-project-context.
    
    The meta-skill should explicitly direct agents to load dox-project-context
    before any project/file mutation, not just mention it in passing.
    """
    meta_skill_path = SKILLS_DIR / "using-agent-skills" / "SKILL.md"
    assert meta_skill_path.exists(), "using-agent-skills skill not found"
    
    skill_content = meta_skill_path.read_text()
    
    # The skill must route to dox-project-context for project work
    routing_present = any(phrase in skill_content for phrase in [
        "load `dox-project-context`",
        "load dox-project-context",
        "apply `dox-project-context`",
        "use `dox-project-context`",
    ])
    
    assert routing_present, (
        "using-agent-skills does not route to dox-project-context"
    )
    
    # The routing should be conditional on project/file work
    conditional_routing = any(phrase in skill_content.lower() for phrase in [
        "project.*dox-project-context",
        "file.*dox-project-context",
        "edit.*dox-project-context",
        "before mutation",
        "before editing",
    ])
    
    assert conditional_routing, (
        "using-agent-skills does not conditionally route to dox-project-context for project work"
    )


@pytest.mark.dox_contract
def test_lifecycle_commands_include_dox_gates():
    """Prove lifecycle commands include DOX preflight and closeout gates.
    
    Commands that mutate or review project files must explicitly include
    DOX workflow steps, not just mention DOX in passing.
    """
    commands_dir = PLUGIN_DIR / "commands"
    
    # Commands that should have DOX gates
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
        
        # Each command should mention DOX preflight or closeout
        # The primary gate is loading dox-project-context or mentioning AGENTS.md
        has_dox_gate = (
            "dox-project-context" in cmd_content or
            "dox preflight" in cmd_content.lower() or
            "dox closeout" in cmd_content.lower() or
            "AGENTS.md" in cmd_content
        )

        assert has_dox_gate, (
            f"Command {cmd_file} does not load dox-project-context or include DOX gates"
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
        
        # Look for the main system prompt
        prompt_files = list(profile_dir.glob("prompts/*.md"))
        if not prompt_files:
            continue
        
        prompt_content = "\n".join(f.read_text() for f in prompt_files)
        
        # The profile should mention AGENTS.md as binding
        agents_aware = any(phrase in prompt_content for phrase in [
            "AGENTS.md",
            "project contracts",
            "binding",
            "DOX",
        ])
        
        assert agents_aware, (
            f"Profile {profile_name} does not mention AGENTS.md or DOX contracts"
        )
