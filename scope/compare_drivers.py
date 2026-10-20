"""Compare drivers-only runs with existing Complexity / Risk ratings, story by story.
python3 -m scope.compare_drivers <ratings.json>   ratings.json: {"rows": [{"key", "c_count", "r_count", "c_drivers", "r_drivers"}]}"""
import json, sys
from . import config, score

S = config.load('scope')
rows = {r['key']: r for r in json.load(open(sys.argv[1]))['rows'] if r.get('c_count') is not None}
runs = config.path(S['paths']['runs_dir'])
latest = {}
for p in sorted(runs.glob('drivers-*/result.json')):
    r = json.load(open(p))
    if r.get('drivers'): latest[r['key']] = r
nums = lambda xs: sorted({x['driver'] for x in xs or []})   # a rating can quote the same driver more than once
print('| Story | C rated | C agent | R rated | R agent | C drivers rated → agent | R drivers rated → agent | Level C / R |')
print('|---|---|---|---|---|---|---|---|')
same = lvl_same = 0
lv = lambda c, r: (score.complexity(c + score.F['planning']['complexity_extra'])['level'], score.risk(r + score.F['planning']['risk_extra'])['level'])
for k in sorted(latest):
    if k not in rows: continue
    a, h = latest[k]['drivers'], rows[k]
    ok = nums(a['complexity']) == nums(h.get('c_drivers')) and nums(a['risk']) == nums(h.get('r_drivers'))
    hl, al = lv(len(nums(h.get('c_drivers'))), len(nums(h.get('r_drivers')))), lv(a['c_count'], a['r_count'])
    same += ok; lvl_same += hl == al
    print(f"| {k}{'' if ok else ' ≠'} | {h['c_count']} | {a['c_count']} | {h['r_count']} | {a['r_count']} | "
          f"{nums(h.get('c_drivers'))} → {nums(a['complexity'])} | {nums(h.get('r_drivers'))} → {nums(a['risk'])} | {'same' if hl == al else f'{hl[0]}/{hl[1]} → {al[0]}/{al[1]}'} |")
n = len([k for k in latest if k in rows])
print(f"\n{same} of {n} stories: same drivers · {lvl_same} of {n}: same planning Complexity and Risk levels")
