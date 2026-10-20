# Story pack: the ticket as one saved folder (pack.json + images/) so the app and the engine see exactly the same text.
# build_pack reads the ticket (read only, via jira.story); load_pack feeds a run; append_notes adds reviewer notes.
import datetime, json, pathlib
from . import config, jira

VERSION = 1
S = config.load('scope')


def build_pack(key, dest):
    dest = pathlib.Path(dest); dest.mkdir(parents=True, exist_ok=True)
    title, text, images, inputs = jira.story(key, dest / 'images')
    rel = [str(pathlib.Path(p).relative_to(dest)) for p in images]
    pack = dict(schema_version=VERSION, key=key, title=title, text=text, images=rel, inputs=inputs, reviewer_notes=[],
                built_at=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'))
    path = dest / 'pack.json'; path.write_text(json.dumps(pack, indent=1, default=str))
    return path


def load_pack(path):
    path = pathlib.Path(path); data = json.loads(path.read_text())
    if data.get('schema_version') != VERSION:
        raise ValueError(f"story pack schema_version {data.get('schema_version')!r} is not supported (expected {VERSION})")
    inputs = dict(data.get('inputs') or {}); missing = list(inputs.get('attachments_not_read') or [])
    images = []
    for rel in data.get('images') or []:
        p = path.parent / rel
        if p.exists(): images.append(str(p))
        else: missing.append(dict(filename=pathlib.Path(rel).name, reason='image file missing'))
    inputs['attachments_not_read'] = missing
    return data['title'], data['text'], images, inputs


def append_notes(path, notes, date):
    """Adds a dated REVIEWER NOTES section to the pack text. Verbatim, capped at pack.max_notes_chars; empty notes do nothing."""
    path = pathlib.Path(path); notes = (notes or '').strip()
    if not notes: return
    notes = notes[:S['pack']['max_notes_chars']]
    data = json.loads(path.read_text())
    data['text'] = f"{data['text']}\n\nREVIEWER NOTES ({date})\n{notes}"
    data.setdefault('reviewer_notes', []).append(dict(date=date, notes=notes))
    path.write_text(json.dumps(data, indent=1, default=str))
