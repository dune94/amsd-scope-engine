# Result contract v1: schema_version, story_hash, and a named pert block (design section 4.3 / 4.12).
from scope import contract


def test_story_hash_ignores_whitespace_differences():
    a = contract.story_hash('Title  one', 'line one\n\nline   two')
    b = contract.story_hash('Title one', 'line one line two')
    assert a == b
    assert a != contract.story_hash('Title one', 'line one line three')
    assert len(a) == 64


def test_stamp_story_sets_hash():
    res = {}
    contract.stamp_story(res, 'T', 'body')
    assert res['story_hash'] == contract.story_hash('T', 'body')


def test_add_contract_fields_copies_pert():
    res = {'planning': {'pert': {'expected_sp': 5}}}
    contract.add_contract_fields(res)
    assert res['pert'] == {'expected_sp': 5}
    assert res['schema_version'] == 1
    assert contract.SCHEMA_VERSION == 1


def test_add_contract_fields_without_planning():
    res = {}
    contract.add_contract_fields(res)
    assert res['pert'] is None
    assert res['schema_version'] == 1
