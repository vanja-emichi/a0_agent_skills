# Bug Report: Plugin Settings UI Displays Defaults Instead of config.json Overrides

**Date:** 2026-06-01
**Component:** Agent Zero Framework — Plugin Settings Panel
**Severity:** Medium (incorrect UI display, not a data integrity issue)

---

## Summary

The Agent Zero settings panel for installed plugins displays values from `default_config.yaml` instead of the merged configuration (defaults + `config.json` overrides). Users see "all settings enabled" even when `config.json` explicitly sets several settings to `false`.

## Steps to Reproduce

1. Install a plugin with boolean settings in `default_config.yaml` (e.g., `a0_agent_skills`)
2. Open the plugin's settings panel in the Agent Zero UI
3. Set several boolean settings to `false` (disabled)
4. Observe that `config.json` is correctly written with `"false"` (string) values
5. Restart Agent Zero
6. Open the plugin's settings panel again
7. **Bug:** Settings that were set to `false` now appear as `true` (enabled)

## Expected Behavior

The settings panel should display the **merged configuration**:
- Values from `config.json` override values from `default_config.yaml`
- If `config.json` has `"phase_governance_enabled": "false"`, the UI toggle should show **disabled**
- Only settings NOT present in `config.json` should inherit defaults

## Actual Behavior

The settings panel displays values from `default_config.yaml` for ALL settings, ignoring `config.json` overrides.

## Evidence

### `default_config.yaml` (defaults):
```yaml
workflow_state_enabled: true          # default
phase_governance_enabled: true       # default
skill_contracts_enabled: true        # default
skill_graph_validate_on_build: true  # default
skill_next_skill_hints: true         # default
```

### `config.json` (user overrides):
```json
{
  "workflow_state_enabled": "true",
  "artifact_inference_enabled": "true",
  "phase_governance_enabled": "false",
  "skill_contracts_enabled": "false",
  "skill_graph_validate_on_build": "false",
  "skill_next_skill_hints": "false"
}
```

### Plugin code reads config correctly:
```python
# _plugin_loader.py
def get_plugin_config(agent) -> dict:
    from helpers import plugins as _plugins
    return _plugins.get_plugin_config("a0_agent_skills", agent=agent) or {}

# config_bool handles both string and bool:
def config_bool(value, default: bool = True) -> bool:
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value) if value is not None else default
```

The plugin code correctly reads `config.json` and uses `config_bool()` to parse string values. The bug is **only in the UI display**, not in the runtime behavior.

## Impact

- **User confusion:** Users think all features are enabled when some are disabled
- **Trust issue:** Users may re-disable settings thinking they were reset
- **Testing difficulty:** Cannot visually verify which settings are active
- **Runtime is correct:** The plugin extensions read config.json correctly, so behavior is unaffected

## Proposed Fix

The settings panel should:
1. Read `config.json` first (user overrides)
2. For any key NOT in `config.json`, fall back to `default_config.yaml`
3. Display the merged result
4. Handle string `"true"`/`"false"` the same way `config_bool()` does

## Workaround

Users can verify actual runtime config by reading `config.json` directly.

## Notes

- The UI saves settings as strings (`"true"`, `"false"`) while defaults use YAML booleans (`true`, `false`)
- `config_bool()` correctly handles both formats
- This affects any plugin with boolean settings that default to `true` and are overridden to `false`
