# ADR-005: Importlib-based Module Loading

**Date**: 2026-05-30
**Status**: Accepted

## Context

Agent Zero's plugin system loads extensions (files in `extensions/python/`) dynamically, but these extensions are not placed on `sys.path`. When an extension needs to import a helper module from the plugin's `helpers/` directory (e.g., `skill_match`, `workflow_state`, `phase_governance`, `skill_contracts`), a standard `import` fails with `ModuleNotFoundError`.

The initial implementation used top-level imports in extension files, which crashed at load time:

```python
# This fails — helpers/ is not on sys.path
from helpers.skill_match import search_skills
```

## Decision

Each extension bootstraps the plugin's `_plugin_loader` module using `importlib.util` — Python's standard mechanism for loading modules from arbitrary file paths. The pattern:

```python
import importlib.util, sys, os

def _load_plugin_loader():
    plugin_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    loader_path = os.path.join(plugin_root, '_plugin_loader.py')
    spec = importlib.util.spec_from_file_location('_plugin_loader', loader_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['_plugin_loader'] = mod
    spec.loader.exec_module(mod)
    return mod

_loader = _load_plugin_loader()
```

Each extension resolves the plugin root independently by walking up the directory tree from its own `__file__` path. The `_plugin_loader` module then provides the plugin root path and config access to helper modules.

## Alternatives Considered

### sys.path injection
- **Pros**: Simple `import` statements work after injection
- **Cons**: Pollutes global sys.path, can cause naming collisions with other plugins, order-dependent, fragile
- **Rejected**: Global namespace pollution is a common source of hard-to-debug plugin conflicts

### Namespace packages (PEP 420)
- **Pros**: Python-standard mechanism for package namespace sharing
- **Cons**: Requires specific directory structure, doesn't work well with Agent Zero's flat extension layout
- **Rejected**: Too much structural change for the plugin system

### Framework patch (add plugin dirs to sys.path in Agent Zero core)
- **Pros**: Cleanest solution; all plugins benefit
- **Cons**: Requires modifying Agent Zero framework code, coupling plugin to specific framework version, not portable
- **Rejected**: Plugin must not require framework changes

## Consequences

- **No framework changes needed**: Entirely self-contained within the plugin
- **Reliable**: `importlib.util` is the standard Python mechanism for dynamic module loading; no hacks required
- **Slightly verbose**: Each extension has a bootstrap function (~10 lines), but this is a one-time cost per extension
- **Consistent pattern**: All 5 extensions use the same bootstrap, making it easy to understand and maintain
- **No global side effects**: Plugin root is resolved per-extension without modifying `sys.path` globally
