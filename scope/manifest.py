# Per-story change manifest by codeline (manifest.md + manifest.json), rendered from the agents' answers and the measure.
import json


def write(R, res):
    L = [f"# Change manifest – {res['key']}: {res.get('title', '')}", '',
         f"Required codelines: {', '.join(res.get('required') or []) or 'none'} · Alternatives: {', '.join(res.get('alternatives') or []) or 'none'}"]
    if res.get('flags'): L.append('FLAGS: ' + '; '.join(res['flags']))
    br = res.get('blast_required') or {}
    L.append(f"Blast radius, required codelines: BASE {br.get('base')} · UPPER {br.get('upper')}")
    pl = res.get('planning')
    if pl:
        pe = pl['pert']
        L.append(f"Planning SP: {pl['planning_sp']} (Scope {pl['scope']}, Complexity {pl['complexity']}, Risk {pl['risk']}; planning BR {pl['planning_br']})")
        L.append(f"PERT: O {pe['o_br']} → {pe['o_sp']} SP · M {pe['m_br']} → {pe['m_sp']} SP · P {pe['p_br']} → {pe['p_sp']} SP · expected BR {pe['expected_br']} → {pe['expected_sp']} SP")
    d = res.get('drivers') or {}
    for dim in ('complexity', 'risk'):
        L += ['', f"## {dim.title()} drivers ({len(d.get(dim) or [])})"]
        L += [f"- {x.get('driver')}. {x.get('name', '')} – {x.get('date', '')} {x.get('source', '')}: “{x.get('quote', '')}”" for x in d.get(dim) or []] or ['- none']
    if d.get('dropped'):
        L += ['', 'Drivers not counted:'] + [f"- {x['dimension']} {x.get('driver')}: {x['reason']}" for x in d['dropped']]
    i = res.get('inputs') or {}
    L += ['', '## Inputs', f"Comments: {i.get('comments', 0)} · Attachments read: {len(i.get('attachments_read') or [])} · Confluence pages read: {len(i.get('confluence_read') or [])}"]
    L += [f"- not read: {x['filename']} ({x['reason']})" for x in i.get('attachments_not_read') or []]
    L += [f"- page not read: {x['id']} ({x['reason']})" for x in i.get('confluence_not_read') or []]
    man = {}
    for name, o in (res.get('codelines') or {}).items():
        inv = o.get('investigation') or {}; role = 'required' if name in (res.get('required') or []) else 'alternative'
        b, u = o.get('base') or {}, o.get('upper') or {}
        man[name] = dict(role=role, base=inv.get('base'), upper=inv.get('upper'), sites=inv.get('sites', []),
                         external_base=inv.get('external_systems_base', inv.get('external_systems')), open_questions=inv.get('open_questions', []),
                         blast_base=b.get('blast'), blast_upper=u.get('blast'),
                         breakdown_base={k: b.get(k) for k in ('changed', 'importing', 'tests', 'external')})
        L += ['', f"## {name} ({role})",
              f"BASE blast radius {b.get('blast')} = {b.get('changed')} changed + {b.get('importing')} importing + {b.get('tests')} tests + 2x{b.get('external')} external · UPPER {u.get('blast')}",
              f"External (BASE): {', '.join(man[name]['external_base'] or []) or 'none'}", '', '| In | Role | File | Function | Change |', '|---|---|---|---|---|']
        for st in inv.get('sites', []):
            L.append(f"| {st.get('in', '')} | {st.get('role', '')} | {st.get('file', '')} | {st.get('function', '')} | {(st.get('change') or '').replace('|', '/')[:160]} |")
        if inv.get('open_questions'): L += ['', 'Open questions:'] + [f"- {q}" for q in inv['open_questions']]
    (R / 'manifest.md').write_text('\n'.join(L) + '\n'); json.dump(man, open(R / 'manifest.json', 'w'), indent=1)
