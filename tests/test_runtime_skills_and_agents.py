"""Runtime integration tests for skill and subagent helper discovery."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

A0_ROOT = Path("/a0")
PLUGIN_DIR = Path(__file__).resolve().parents[1]
SKILLS_DIR = PLUGIN_DIR / "skills"
AGENTS_DIR = PLUGIN_DIR / "agents"

if str(A0_ROOT) not in sys.path:
    sys.path.insert(0, str(A0_ROOT))


def _install_fake_agent_module(monkeypatch):
    fake_agent = types.ModuleType("agent")
    for name in ("Agent", "AgentConfig", "AgentContext", "AgentContextType", "LoopData"):
        setattr(fake_agent, name, type(name, (), {}))
    monkeypatch.setitem(sys.modules, "agent", fake_agent)


def _install_fake_projects_module(monkeypatch):
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
def plugin_skill_root(monkeypatch):
    _install_fake_agent_module(monkeypatch)
    _install_fake_projects_module(monkeypatch)
    from helpers import skills as skills_helper

    monkeypatch.setattr(skills_helper, "get_skill_roots", lambda agent=None: [str(SKILLS_DIR)])
    # Prevent helpers.plugins._apply_defaults_from_env from importing helpers.settings -> models -> langchain_core
    from helpers import plugins as plugins_helper
    monkeypatch.setattr(plugins_helper, "_apply_defaults_from_env", lambda *a, **k: None)
    return skills_helper


@pytest.mark.runtime_integration
def test_framework_skill_helpers_discover_plugin_skills(plugin_skill_root):
    skills_helper = plugin_skill_root

    skills = skills_helper.list_skills()
    names = {skill.name for skill in skills}

    for expected in {
        "using-agent-skills",
        "dox-project-context",
        "test-driven-development",
        "security-and-hardening",
    }:
        assert expected in names

    using = skills_helper.find_skill("using-agent-skills")
    assert using is not None
    assert using.path.resolve() == (SKILLS_DIR / "using-agent-skills").resolve()
    assert using.description

    dox = skills_helper.find_skill("dox-project-context")
    assert dox is not None
    assert dox.path.resolve() == (SKILLS_DIR / "dox-project-context").resolve()
    assert "AGENTS.md" in dox.description


@pytest.mark.runtime_integration
def test_skills_tool_read_file_reads_support_file_and_blocks_escape(plugin_skill_root):
    from tools.skills_tool import SkillsTool

    tool = SkillsTool.__new__(SkillsTool)
    tool.agent = SimpleNamespace(data={}, context=SimpleNamespace(log=SimpleNamespace(log=lambda *a, **k: None), get_data=lambda *a, **k: None))
    tool.args = {}
    tool.name = "skills_tool"

    content = tool._read_file("using-agent-skills", "references/testing-patterns.md")
    assert content.startswith("Skill file: using-agent-skills/references/testing-patterns.md")
    assert "testing" in content.lower()

    escaped_relative = tool._read_file("using-agent-skills", "../dox-project-context/SKILL.md")
    assert escaped_relative == "Error: file_path must stay inside the skill directory."

    escaped_absolute = tool._read_file("using-agent-skills", str(PLUGIN_DIR / "plugin.yaml"))
    assert escaped_absolute == "Error: file_path must stay inside the skill directory."

    missing = tool._read_file("using-agent-skills", "references/not-real.md")
    assert "Error: skill file not found" in missing


@pytest.mark.runtime_integration
def test_subagent_helpers_discover_and_load_plugin_profiles(monkeypatch):
    _install_fake_agent_module(monkeypatch)
    _install_fake_projects_module(monkeypatch)
    from helpers import plugins, subagents

    def fake_enabled_paths(agent, *subpaths):
        if subpaths == ("agents",):
            return [str(AGENTS_DIR)]
        return []

    monkeypatch.setattr(plugins, "get_enabled_plugin_paths", fake_enabled_paths)

    agent_dict = subagents.get_agents_dict()
    for name in ("code-reviewer", "security-auditor", "test-engineer"):
        assert name in agent_dict
        item = agent_dict[name]
        assert "plugin" in item.origin
        assert Path(item.path).resolve() == (AGENTS_DIR / name).resolve()
        assert item.title
        assert item.description

    test_engineer = subagents.load_agent_data("test-engineer")
    test_engineer_text = test_engineer.context + " " + " ".join(test_engineer.prompts.values())
    assert test_engineer_text.strip()
    assert "test" in test_engineer_text.lower()
    assert test_engineer.prompts

    code_reviewer = subagents.load_agent_data("code-reviewer")
    assert (code_reviewer.context + " " + " ".join(code_reviewer.prompts.values())).strip()
    assert code_reviewer.prompts

    security_auditor = subagents.load_agent_data("security-auditor")
    assert (security_auditor.context + " " + " ".join(security_auditor.prompts.values())).strip()
    assert security_auditor.prompts
