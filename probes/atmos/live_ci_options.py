"""Pure stage selection for the live acceptance wrapper; no process effects."""


def select_stage(stage, test_ids, cases, joc_input):
    integration_selection = bool(cases or joc_input)
    if test_ids and integration_selection:
        raise ValueError('unit and integration retry selectors cannot be mixed')
    if stage == 'all' and (test_ids or integration_selection):
        raise ValueError('all takes no retry selectors or JOC input; select one stage')
    selected = stage or ('units' if test_ids else 'integration' if integration_selection else 'all')
    if selected == 'units' and integration_selection:
        raise ValueError('integration options cannot select a units-only run')
    if selected == 'integration' and test_ids:
        raise ValueError('unit methods cannot select an integration-only run')
    return selected
