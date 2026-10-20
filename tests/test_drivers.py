# S4.4: a driver counts only with a quote found in the ticket text; numbers 1-5; each driver once.
from scope import drivers

TEXT = 'Title\nThe API is owed by the vendor.\n\nCOMMENTS\n[comment 2026-10-06] Approach not yet decided between API or CMS'

def test_validate():
    ans = {'complexity': [{'driver': 4, 'quote': 'The API is owed by the vendor.'}, {'driver': 9, 'quote': 'x'}],
           'risk': [{'driver': 3, 'quote': 'the api is owed  by the vendor'}, {'driver': 3, 'quote': 'Approach not yet decided'},
                    {'driver': 5, 'quote': 'Approach not yet decided between API or CMS'}, {'driver': 1, 'quote': 'invented line'}, {'driver': 2, 'quote': ''}]}
    kept, dropped = drivers.validate(ans, TEXT)
    assert [d['driver'] for d in kept['complexity']] == [4] and [d['driver'] for d in kept['risk']] == [3, 5]
    assert sorted(d['reason'] for d in dropped) == ['driver number not 1-5', 'duplicate', 'no quote', 'quote not found in the ticket text']
