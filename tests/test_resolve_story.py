# Running from a story pack: no Jira fetch, the pack folder is never deleted; and the command-line rules.
import pytest
from scope import __main__ as cli
from scope import flow, jira, pack


def _fake_story(key, inputs_dir):
    inputs_dir.mkdir(parents=True, exist_ok=True)
    (inputs_dir / '00-shot.png').write_bytes(b'png')
    return 'Title one', 'Body text', [str(inputs_dir / '00-shot.png')], {'comments': 1, 'attachments_not_read': []}


@pytest.fixture
def a_pack(tmp_path, monkeypatch):
    monkeypatch.setattr(jira, 'story', _fake_story)
    return pack.build_pack('KEY-1', tmp_path / 'packdir')


def test_with_pack_never_calls_jira(tmp_path, a_pack, monkeypatch):
    def boom(*a, **k): raise AssertionError('jira.story must not be called when a pack is supplied')
    monkeypatch.setattr(jira, 'story', boom)
    title, text, images, inputs, work, owned = flow.resolve_story('KEY-1', tmp_path / 'run', a_pack)
    assert (title, text) == ('Title one', 'Body text')
    assert owned is False
    assert work == a_pack.parent


def test_without_pack_fetches_and_owns(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(jira, 'story', lambda key, d: (calls.append(key), _fake_story(key, d))[1])
    title, text, images, inputs, work, owned = flow.resolve_story('KEY-2', tmp_path / 'run', None)
    assert calls == ['KEY-2']
    assert owned is True
    assert work == tmp_path / 'run' / 'inputs'


def test_failed_run_does_not_delete_pack_folder(tmp_path, a_pack, monkeypatch):
    monkeypatch.setattr(flow, 'clones', lambda: [])
    monkeypatch.setitem(flow.S['paths'], 'runs_dir', str(tmp_path / 'runs'))
    monkeypatch.setitem(flow.S['paths'], 'proof_unchanged', [])
    def boom(*a, **k): raise RuntimeError('agent failed')
    monkeypatch.setattr(flow.llm, 'call', boom)
    with pytest.raises(RuntimeError):
        flow.go('KEY-1', pack_path=a_pack)
    assert a_pack.exists() and (a_pack.parent / 'images' / '00-shot.png').exists()


def test_build_pack_takes_exactly_one_key():
    assert cli.parse(['KEY-1', '--build-pack', '/tmp/x'])['build_pack'] == '/tmp/x'
    with pytest.raises(SystemExit):
        cli.parse(['KEY-1', 'KEY-2', '--build-pack', '/tmp/x'])


def test_story_pack_requires_run_and_one_key():
    assert cli.parse(['KEY-1', '--run', '--story-pack', '/tmp/p.json'])['story_pack'] == '/tmp/p.json'
    with pytest.raises(SystemExit):
        cli.parse(['KEY-1', '--story-pack', '/tmp/p.json'])
    with pytest.raises(SystemExit):
        cli.parse(['KEY-1', 'KEY-2', '--run', '--story-pack', '/tmp/p.json'])
