# S1.2, S2.3, S2.4: every agent call is capped, timed out, uses the pinned model and the configured CLI and tools.
from scope import config, llm, flow

S = config.load('scope')
BOUNDED = str(config.path(S['paths']['bounded']))

def test_every_agent_call_is_memory_capped_with_timeout_and_model():
    for n in config.AGENTS:
        a = config.Agent(n); c = llm.build(a)
        assert c[:4] == [BOUNDED, '--want', str(a.memory_mb), '--'] and c[4:6] == ['timeout', str(a.timeout_s)]
        assert c[6:6 + len(S['llm']['command'])] == S['llm']['command']
        assert c[c.index('--model') + 1] == a.model

def test_no_tool_agents_get_no_tools():
    for n in ('nouns', 'pick', 'drivers'):
        c = llm.build(config.Agent(n)); assert c[c.index('--tools') + 1] == '' and '--allowedTools' not in c

def test_investigator_tools_are_codegraph_and_rg_only():
    c = llm.build(config.Agent('investigate'))
    assert c[c.index('--tools') + 1] == 'Bash'
    allowed = c[c.index('--allowedTools') + 1:c.index('--max-turns')]
    assert all(x.startswith(('Bash(codegraph ', 'Bash(rg:')) for x in allowed) and c[c.index('--max-turns') + 1] == '20'

def test_images_add_read_only_for_agents_that_take_images():
    c = llm.build(config.Agent('drivers'), images=['/x/a.png', '/x/b.png'])
    assert c[c.index('--tools') + 1] == 'Read' and c[c.index('--max-turns') + 1] == '5'
    assert '--max-turns' not in llm.build(config.Agent('nouns'))

def test_system_prompt_mode_uses_configured_flag():
    a = config.Agent('nouns'); a.si_mode = 'append'
    c = llm.build(a, si_file='/tmp/si.md'); assert c[c.index('--append-system-prompt-file') + 1] == '/tmp/si.md'

def test_codegraph_index_is_memory_capped():
    assert flow.index_cmd('/s')[:4] == [BOUNDED, '--want', str(S['memory']['index_mb']), '--']

def test_parse_reply():
    assert llm.parse('{"result": "text ```json\\n{\\"nouns\\": [\\"fare\\"]}\\n``` end"}') == {'nouns': ['fare']}
    assert llm.parse('{"result": "no json"}') is None
