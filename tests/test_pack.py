# Story pack: build, load, reviewer notes (design section 4.2 / 4.3 / 4.12).
import json
import pytest
from scope import contract, jira, pack


@pytest.fixture
def fake_story(monkeypatch):
    def story(key, inputs_dir):
        inputs_dir.mkdir(parents=True, exist_ok=True)
        img = inputs_dir / '00-shot.png'
        img.write_bytes(b'png')
        return 'Title one', 'Body text', [str(img)], {'comments': 2, 'attachments_not_read': []}
    monkeypatch.setattr(jira, 'story', story)


def test_build_pack_writes_file_and_copies_images(tmp_path, fake_story):
    p = pack.build_pack('KEY-1', tmp_path)
    data = json.loads(p.read_text())
    assert p == tmp_path / 'pack.json'
    assert data['schema_version'] == 1 and data['key'] == 'KEY-1'
    assert data['images'] == ['images/00-shot.png']
    assert (tmp_path / 'images' / '00-shot.png').exists()


def test_load_pack_returns_story_tuple(tmp_path, fake_story):
    title, text, images, inputs = pack.load_pack(pack.build_pack('KEY-1', tmp_path))
    assert (title, text) == ('Title one', 'Body text')
    assert images == [str(tmp_path / 'images' / '00-shot.png')]
    assert inputs['comments'] == 2


def test_load_pack_rejects_unknown_version(tmp_path, fake_story):
    p = pack.build_pack('KEY-1', tmp_path)
    data = json.loads(p.read_text()); data['schema_version'] = 2; p.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='schema_version'):
        pack.load_pack(p)
    data.pop('schema_version'); p.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='schema_version'):
        pack.load_pack(p)


def test_load_pack_drops_missing_image_and_lists_it(tmp_path, fake_story):
    p = pack.build_pack('KEY-1', tmp_path)
    (tmp_path / 'images' / '00-shot.png').unlink()
    _, _, images, inputs = pack.load_pack(p)
    assert images == []
    assert {'filename': '00-shot.png', 'reason': 'image file missing'} in inputs['attachments_not_read']


def test_append_notes_adds_dated_section_and_changes_story_hash(tmp_path, fake_story):
    p = pack.build_pack('KEY-1', tmp_path)
    before = contract.story_hash(*pack.load_pack(p)[:2])
    pack.append_notes(p, 'Please recheck the second rule', '2026-10-20')
    title, text, _, _ = pack.load_pack(p)
    assert 'REVIEWER NOTES (2026-10-20)' in text and 'Please recheck the second rule' in text
    assert contract.story_hash(title, text) != before
    assert json.loads(p.read_text())['reviewer_notes'][0]['date'] == '2026-10-20'


def test_append_notes_truncates_long_notes(tmp_path, fake_story):
    p = pack.build_pack('KEY-1', tmp_path)
    pack.append_notes(p, 'x' * 5000, '2026-10-20')
    assert json.loads(p.read_text())['reviewer_notes'][0]['notes'] == 'x' * 4000


def test_notes_with_markup_are_stored_verbatim(tmp_path, fake_story):
    p = pack.build_pack('KEY-1', tmp_path)
    pack.append_notes(p, '<b>bold</b> & {{braces}} $(rm -rf)', '2026-10-20')
    assert '<b>bold</b> & {{braces}} $(rm -rf)' in pack.load_pack(p)[1]


def test_empty_notes_are_a_no_op(tmp_path, fake_story):
    p = pack.build_pack('KEY-1', tmp_path)
    before = p.read_text()
    pack.append_notes(p, '   ', '2026-10-20')
    assert p.read_text() == before
