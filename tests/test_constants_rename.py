# test_constants_rename.py - Task 1.1 TDD: CONTEXT_KEY_PLAN_* -> CONTEXT_KEY_LIFECYCLE_*
# RED phase: This test SHOULD FAIL until constants.py is updated

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_lifecycle_constants_exist():
    from lib.constants import CONTEXT_KEY_LIFECYCLE_STATE, CONTEXT_KEY_LIFECYCLE_STATE_MTIME
    assert CONTEXT_KEY_LIFECYCLE_STATE == 'lifecycle_state'
    assert CONTEXT_KEY_LIFECYCLE_STATE_MTIME == 'lifecycle_state_mtime'


def test_phase_icons_unchanged():
    from lib.constants import PHASE_ICONS, PHASE_ICON_DEFAULT
    assert PHASE_ICONS == {'pending': chr(0x23F8)+chr(0xFE0F), 'in_progress': chr(0x1F504), 'completed': chr(0x2705)}
    assert PHASE_ICON_DEFAULT == chr(0x23F8)+chr(0xFE0F)


def test_no_plan_prefix_in_constants():
    import lib.constants as c
    plan_names = [n for n in dir(c) if n.startswith('CONTEXT_KEY_PLAN')]
    assert plan_names == [], f'Found stale PLAN constants: {plan_names}'


def test_auto_progress_removed():
    import lib.constants as c
    assert not hasattr(c, 'CONTEXT_KEY_AUTO_PROGRESS_LAST_ACTION')


def test_all_values_use_lifecycle_prefix():
    import lib.constants as c
    for name in dir(c):
        if not name.startswith('CONTEXT_KEY'):
            continue
        val = getattr(c, name)
        if isinstance(val, str):
            assert not val.startswith('plan_'), f'{name}={val!r} still uses plan_ prefix'
