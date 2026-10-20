# S2: no prompt text, model id or machine path in the code (organisation names: see test_clean.py).
import pathlib
CODE = ''.join(p.read_text() for p in (pathlib.Path(__file__).parents[1] / 'scope').glob('*.py'))

def test_no_prompt_text_model_or_paths_in_code():
    for s in ('You are a code investigator', 'DOMAIN NOUNS', 'You decide which codebases', 'COMPLEXITY DRIVERS',
              'claude-opus', '/home/', "'claude'", '1.4'):
        assert s not in CODE, s
