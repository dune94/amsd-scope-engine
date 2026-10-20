# Result contract v1: fields the estimations app relies on (see docs/result-contract-v1.md).
import hashlib, re

SCHEMA_VERSION = 1


def story_hash(title, text):
    """SHA-256 of the title and text with every run of whitespace collapsed to one space."""
    norm = re.sub(r'\s+', ' ', f'{title}\n{text}').strip()
    return hashlib.sha256(norm.encode('utf-8')).hexdigest()


def stamp_story(res, title, text):
    res['story_hash'] = story_hash(title, text)


def add_contract_fields(res):
    res['schema_version'] = SCHEMA_VERSION
    res['pert'] = dict(res['planning']['pert']) if (res.get('planning') or {}).get('pert') else None
