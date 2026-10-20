# S8: nothing organisation-specific in the files git tracks. Terms come from config.local/forbidden.txt (untracked); skipped without it.
import pytest
from scope import config
from scripts import check_clean

TERMS = config.LOCAL / 'forbidden.txt'

@pytest.mark.skipif(not TERMS.exists(), reason='config.local/forbidden.txt not present')
def test_no_forbidden_terms_in_publishable_files():
    assert check_clean.scan(config.PROJECT, check_clean.terms(TERMS)) == []
