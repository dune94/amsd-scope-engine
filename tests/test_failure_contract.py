# Failure contract: a failed run says why in result.json, a run from a story pack exits non-zero, and nothing builds a shell command from the key.
import json
import pytest
from scope import __main__ as cli
from scope import flow, jira, pack


def _fake_story(key, inputs_dir):
    inputs_dir.mkdir(parents=True, exist_ok=True)
    return 'Title one', 'Body text', [], {'comments': 1, 'attachments_not_read': []}


@pytest.fixture
def a_pack(tmp_path, monkeypatch):
    monkeypatch.setattr(jira, 'story', _fake_story)
    return pack.build_pack('KEY-1', tmp_path / 'packdir')


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(flow, 'clones', lambda: [])
    monkeypatch.setitem(flow.S['paths'], 'runs_dir', str(tmp_path / 'runs'))
    monkeypatch.setitem(flow.S['paths'], 'proof_unchanged', [])
    return tmp_path / 'runs'


def _fail(*a, **k):
    raise RuntimeError('agent failed')


def test_failed_run_records_the_error_in_result_json(a_pack, isolated, monkeypatch):
    monkeypatch.setattr(flow.llm, 'call', _fail)
    with pytest.raises(RuntimeError):
        flow.go('KEY-1', pack_path=a_pack)
    result = json.loads(next(isolated.glob('run-KEY-1-*/result.json')).read_text())
    assert result['error'] == 'RuntimeError: agent failed'
    assert result['schema_version'] == 1
    assert 'planning' not in result


def test_a_successful_result_has_no_error_key():
    from scope import contract
    res = {'planning': {'pert': {'expected_sp': 5}}}
    contract.add_contract_fields(res)
    assert 'error' not in res


def test_run_never_builds_a_shell_command(a_pack, isolated, monkeypatch):
    seen = []
    real_run = flow.run
    monkeypatch.setattr(flow, 'run', lambda cmd, *a, **k: (seen.append(list(cmd)), real_run(cmd, *a, **k))[1])
    monkeypatch.setattr(flow.llm, 'call', _fail)
    with pytest.raises(RuntimeError):
        flow.go('KEY-1', pack_path=a_pack)
    assert seen, 'the clean-up checks should have run'
    assert not any(c[:2] == ['bash', '-c'] for c in seen)


def test_story_pack_failure_exits_non_zero(monkeypatch):
    monkeypatch.setattr(flow, 'go', _fail)
    with pytest.raises(SystemExit) as e:
        cli.main(['KEY-1', '--run', '--story-pack', '/tmp/p.json'])
    assert e.value.code == 1


def test_other_modes_keep_exit_zero_on_failure(monkeypatch):
    monkeypatch.setattr(flow, 'go', _fail)
    assert cli.main(['KEY-1', '--run']) is None


@pytest.mark.parametrize('bad', ['../x', 'KEY-1; touch /tmp/x', 'key', 'KEY-', '-1', 'KEY-1 KEY-2'])
def test_keys_must_look_like_issue_keys(bad):
    with pytest.raises(SystemExit):
        cli.parse([bad, '--plan'])


def test_normal_keys_are_accepted():
    assert cli.parse(['PROJ-2388', 'ABC-2981', 'key_x-5', '--plan'])['keys'] == ['PROJ-2388', 'ABC-2981', 'key_x-5']
