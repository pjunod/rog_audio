"""Pure stage selection for the live acceptance wrapper; no process effects."""


def select_stage(stage, test_ids, cases, joc_input, graph_quantum=None):
    integration_selection = bool(cases or joc_input or graph_quantum is not None)
    if test_ids and integration_selection:
        raise ValueError('unit and integration retry selectors cannot be mixed')
    if stage == 'all' and (test_ids or integration_selection):
        raise ValueError('all takes no retry selectors or integration options; select one stage')
    selected = stage or ('units' if test_ids else 'integration' if integration_selection else 'all')
    if selected == 'units' and integration_selection:
        raise ValueError('integration options cannot select a units-only run')
    if selected == 'integration' and test_ids:
        raise ValueError('unit methods cannot select an integration-only run')
    return selected
