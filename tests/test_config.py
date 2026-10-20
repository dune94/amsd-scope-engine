# S2.1, S2.3, S2.5, S2.6: every agent, path and formula value is loaded from config / agents files.
import jsonschema
from scope import config

def test_every_agent_loads_with_its_files():
    for n in config.AGENTS:
        a = config.Agent(n)
        assert a.si_text.strip() and a.prompt_text.strip()
        jsonschema.Draft202012Validator.check_schema(a.schema_obj)
        assert a.si_mode in ('inline', 'append', 'replace') and a.timeout_s > 0 and a.memory_mb > 0

def test_model_pinned_per_agent():
    assert {n: config.Agent(n).model for n in config.AGENTS} == {
        'nouns': 'claude-haiku-5-5', 'drivers': 'claude-sonnet-5-5', 'pick': 'claude-opus-5-5', 'investigate': 'claude-opus-5-5'}

def test_scope_and_formula_config_load():
    s, f = config.load('scope'), config.load('formula')
    assert s['codelines']['shortlist'] == 7 and s['memory']['driver_mb'] == 1536
    assert s['inputs']['attachments'] == dict(max_files=20, max_total_mb=25, max_pages=30, images=['.png', '.jpg', '.jpeg', '.gif', '.webp'],
                                              text=['.pdf', '.docx', '.md', '.txt', '.pptx'])
    assert s['inputs']['confluence']['follow_links'] is False
    assert f['planning'] == dict(br_multiplier=1.4, complexity_extra=1, risk_extra=1)
