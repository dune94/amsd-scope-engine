# S5.1: blast radius = changed + importing + tests + 2 x external; logic files count importers, exports_only and new do not.
import pytest
from scope.measure import Index, measure

@pytest.fixture
def repo(tmp_path):
    r = tmp_path / 'site'; (r / 'src/lib').mkdir(parents=True); (r / 'src/__tests__').mkdir()
    (r / 'src/lib/fare.ts').write_text('export const fare = 1\n')
    (r / 'src/lib/types.ts').write_text('export type T = {a: 1}\n')
    for i in range(3): (r / f'src/page{i}.tsx').write_text("import { fare } from './lib/fare'\nimport { T } from './lib/types'\n")
    (r / 'src/__tests__/fare.test.ts').write_text("import { fare } from '../lib/fare'\n")
    return tmp_path

def test_logic_counts_importers_and_tests(repo):
    m = measure(Index(repo), {'repos': {'site': {'logic': ['src/lib/fare.ts']}}, 'external': ['CMS-X']})
    assert (m['changed'], m['importing'], m['tests'], m['external'], m['blast']) == (1, 3, 1, 1, 7)
    assert m['scope'] == 'Medium'

def test_exports_only_and_new_count_no_importers(repo):
    m = measure(Index(repo), {'repos': {'site': {'exports_only': ['src/lib/types.ts'], 'new': ['src/lib/new.ts']}}, 'external': []})
    assert (m['changed'], m['importing'], m['tests'], m['blast']) == (2, 0, 0, 2)

def test_planned_file_must_exist(repo):
    with pytest.raises(AssertionError): measure(Index(repo), {'repos': {'site': {'logic': ['src/missing.ts']}}, 'external': []})
