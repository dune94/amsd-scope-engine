# S2.2, S4.5: prompt text carried over unchanged; system instructions and prompt are separate files with named placeholders.
import json, pathlib
import pytest
from scope import config

FIXTURE = config.LOCAL / 'tests/original_prompts.json'   # untracked: the original prompt texts, kept locally
ORIG = json.load(open(FIXTURE)) if FIXTURE.exists() else None
needs_fixture = pytest.mark.skipif(ORIG is None, reason='local fixture config.local/tests/original_prompts.json not present')
T, D = 'Title text [AB]', 'Description line\n\nCOMMENTS\n[comment 2026-10-01] a comment {with braces}'

@needs_fixture
def test_nouns_identical():
    assert config.Agent('nouns').message(title=T, description=D) == ORIG['NOUNS_PROMPT'] % (T, D)

@needs_fixture
def test_pick_identical():
    ev = json.dumps({'site-a': {'rg_files_per_noun': {'fare': 3}}}, indent=1)
    assert config.Agent('pick').message(title=T, description=D, evidence=ev) == ORIG['PICK_PROMPT'] % (T, D, ev)

@needs_fixture
def test_investigate_identical():
    v = dict(repo='site-a', role='required codeline', context='Other codelines ...', title=T, description=D)
    assert config.Agent('investigate').message(**v) == ORIG['INVESTIGATE_PROMPT'] % (v['repo'], v['role'], v['context'], T, D, 15)

def test_si_and_prompt_are_separate_and_complete():
    for n in config.AGENTS:
        a = config.Agent(n); si, pr = a.render(title=T, description=D, evidence='E', repo='r', role='x', context='')
        assert '{' + 'title}' not in si + pr and T in pr and T not in si

def test_missing_value_is_an_error():
    with pytest.raises(KeyError): config.Agent('nouns').render(title=T)
