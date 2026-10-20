# Two-step code detective for one story: codeline detective (1a nouns, 1b shortlist, 1c snapshot + index, 1d pick), drivers (1e),
# code-around detective (2a investigate per codeline, 2b blast radius, 2c planning SP + PERT). Agents, prompts, models, caps and
# formula come from agents/ and config/. Live clones are only read (git archive, rg); their .codegraph indexes are never opened.
# Snapshots and downloads are deleted at the end of every run; a run keeps only small result files.
import collections, json, os, re, shlex, shutil, subprocess, time
from . import config, contract, drivers, jira, llm, manifest, score
from .measure import Index, SRC, measure

S = config.load('scope'); C = S['codelines']
ROOT = config.path(S['paths']['codelines_root'])
A = {n: config.Agent(n) for n in config.AGENTS}


def clones():
    """Codelines: git repos under the root whose origin matches the configured pattern, minus excluded / non-product repos."""
    out = []
    for p in sorted(ROOT.iterdir()):
        if not (p / '.git').exists() or p.name in C['exclude'] or p.name in C['not_product']: continue
        url = subprocess.run(['git', '-C', str(p), 'remote', 'get-url', 'origin'], capture_output=True, text=True).stdout
        if re.search(C['origin_pattern'], url, re.I): out.append(p)
    return out


def run(cmd, cwd=None, log=None):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if log:
        log.write(f"\n$ {' '.join(shlex.quote(c) for c in cmd)}  (cwd={cwd}, {time.time() - t0:.0f}s, exit {r.returncode})\n{r.stderr[-2000:]}\n")
        log.flush()
    return r


def index_cmd(snapshot):
    return llm.bounded(S['memory']['index_mb'], ['codegraph', 'init', str(snapshot)])


def plan(key):
    """Print every command a run would execute; runs nothing."""
    L = S['llm']
    print(f"driver   {config.path(S['paths']['bounded'])} --want {S['memory']['driver_mb']} -- python3 -u -m scope {key} --run")
    print(f"inputs   GET Jira {key}: {', '.join(S['jira']['fields'])}, comments, remote links; attachments within "
          f"{S['inputs']['attachments']['max_files']} files / {S['inputs']['attachments']['max_total_mb']} MB; linked Confluence pages "
          f"(max {S['inputs']['confluence']['max_pages']}) -> <run>/inputs")
    for n in ('drivers', 'nouns'):
        print(f"{A[n].step:<8} {' '.join(shlex.quote(c) for c in llm.build(A[n]))}  < {n} message")
    print(f"1b       rg -l -i {' '.join('--glob ' + g for g in C['rg_exclude_globs'])} <noun> <codeline>   for each of {len(clones())} codelines")
    print(f"1c       git -C {ROOT}/<codeline> archive HEAD | tar -x -C <run>/snap/<codeline>;  {' '.join(index_cmd('<run>/snap/<codeline>'))}")
    print(f"1d       {' '.join(shlex.quote(c) for c in llm.build(A['pick']))}  < pick message")
    print(f"2a       (cwd <run>/snap/<codeline>) {' '.join(shlex.quote(c) for c in llm.build(A['investigate']))}  < investigate message")
    print("2b/2c    python: blast radius (live clone import graph) -> planning SP + PERT (config/formula.yml)")
    print(f"clean-up pkill -f 'codegraph.*<run>/snap'; rm -rf <run>/snap <run>/inputs")
    print(f"proof    no file newer than the run start in {', '.join(S['paths']['proof_unchanged'])} or {ROOT}/*/.codegraph; clone git status unchanged")


def shortlist(nouns, title, text):
    hits, co = {}, {}
    for repo in clones():
        per = {}; filecnt = collections.Counter()
        for n in nouns:
            # the noun as prose AND as an identifier: "toast notification" also finds ToastNotification / toast_notification / toast-notification
            pat = r'[\s_\-]?'.join(re.escape(w) for w in n.split())
            g = sum((['--glob', x] for x in C['rg_exclude_globs']), [])
            rr = subprocess.run(['rg', '-l', '-i'] + g + [pat, str(repo)], capture_output=True, text=True)
            fl = [x for x in rr.stdout.splitlines() if x]; per[n] = len(fl)
            for f in fl: filecnt[f] += 1
        hits[repo.name] = per
        co[repo.name] = (sum(1 for v in filecnt.values() if v >= 3), sum(1 for v in filecnt.values() if v >= 2))
    # co-occurrence: files that mention 3+ (then 2+) of the nouns together decide the order, not single-noun hits
    rank = sorted(hits, key=lambda k: (-co[k][0], -co[k][1], -sum(hits[k].values())))
    flat = re.sub(r'[\s._\-]+', '', (title + ' ' + text).lower())
    key_ = lambda r: re.sub(r'[._\-]', '', r.lower().replace('.com', ''))
    named = [r for r in hits if len(key_(r)) >= 4 and key_(r) in flat]          # codelines the ticket names are always shortlisted
    tags = set(t for grp in re.findall(r'\[([A-Z/ ]+)\]', title) for t in re.split(r'[/ ]', grp))
    B = C['brand_codelines']
    named += [B[t] for t in sorted(tags) if t in B and B[t] in hits and B[t] not in named]
    short = named + [k for k in rank if k not in named and sum(hits[k].values())][:max(0, C['shortlist'] - len(named))]
    return short, named, hits, {k: co[k] for k in rank[:10]}, rank


def go(key, drivers_only=False):
    runs = config.path(S['paths']['runs_dir'])
    R = runs / f"{'drivers' if drivers_only else 'run'}-{key}-{time.strftime('%Y%m%dT%H%M%S')}"
    (R / 'snap').mkdir(parents=True); inp = R / 'inputs'
    log = open(R / 'commands.log', 'w'); (R / 'marker').touch()
    status_before = {p.name: run(['git', '-C', str(p), 'status', '--porcelain']).stdout for p in clones()}
    res = {'key': key, 'agents': {n: dict(model=a.model, step=a.step) for n, a in A.items()}}
    try:
        title, text, images, inputs = jira.story(key, inp)
        contract.stamp_story(res, title, text)
        res.update(title=title, inputs=inputs)
        (R / 'story.txt').write_text(f'Title: {title}\n{text}')
        # 1e Complexity / Risk drivers
        ans, errs = llm.call(A['drivers'], dict(title=title, description=text), cwd=str(inp), images=images, log=log, raw_path=R / 'drivers.raw.json')
        kept, dropped = drivers.validate(ans, f'{title}\n{text}')
        res['drivers'] = dict(complexity=kept['complexity'], risk=kept['risk'], dropped=dropped, schema_errors=errs,
                              c_count=len(kept['complexity']), r_count=len(kept['risk']))
        print('1e drivers: C', res['drivers']['c_count'], 'R', res['drivers']['r_count'], f'({len(dropped)} dropped)', flush=True)
        if ans is None: raise SystemExit('drivers agent returned no JSON – stopping')
        if drivers_only: return res
        # 1a nouns
        ans, errs = llm.call(A['nouns'], dict(title=title, description=text), cwd=str(inp), images=images, log=log)
        nouns = (ans or {}).get('nouns', []); res['nouns'] = nouns; print('1a nouns:', nouns, flush=True)
        if not nouns: raise SystemExit('no nouns returned – stopping')
        # 1b shortlist
        short, named, hits, co, rank = shortlist(nouns, title, text)
        res.update(named_in_ticket=named, shortlist_cooccurrence=co, rg_hits={k: hits[k] for k in rank[:8]}, shortlist=short)
        print('1b shortlist:', short, flush=True)
        # 1c snapshot + index + query evidence
        ev = {}
        for name in short:
            s = R / 'snap' / name; s.mkdir(parents=True)
            big = len(run(['git', '-C', str(ROOT / name), 'ls-files']).stdout.splitlines()) > C['large_repo_files']
            if big:   # too large to index: no snapshot copy; rg evidence only
                ev[name] = dict(rg_files_per_noun=hits[name], codegraph_symbols={}, indexed=False, large_repo_rg_only=True); continue
            a = subprocess.Popen(['git', '-C', str(ROOT / name), 'archive', 'HEAD'], stdout=subprocess.PIPE)
            subprocess.run(['tar', '-x', '-C', str(s)], stdin=a.stdout, check=True); a.wait()
            rr = run(index_cmd(s), log=log)
            sym = {}
            for n in nouns:
                q = run(['codegraph', 'query', n, '--json', '-l', str(C['codegraph_query_limit']), '-p', str(s)], log=log)
                try: sym[n] = [f"{x.get('name')} @ {x.get('filePath') or x.get('file')}" for x in json.loads(q.stdout)][:C['codegraph_query_limit']]
                except Exception: sym[n] = []
            ev[name] = dict(rg_files_per_noun=hits[name], codegraph_symbols=sym, indexed=rr.returncode == 0, large_repo_rg_only=False)
        res['evidence'] = ev
        # 1d pick
        pick, errs = llm.call(A['pick'], dict(title=title, description=text, evidence=json.dumps(ev, indent=1)[:C['evidence_max_chars']]),
                              cwd=str(inp), images=images, log=log)
        pick = pick or {}; res['pick'] = pick; res['pick_schema_errors'] = errs
        req = [x['repo'] for x in pick.get('required', []) if x.get('repo') in short]
        alt = [x['repo'] for x in pick.get('alternatives', []) if x.get('repo') in short and x.get('repo') not in req]
        chosen = req + alt
        brands = tags_in(title) & set(C['brand_tags_for_flag'])
        res['flags'] = [f'title names brands {sorted(brands)} but only {len(req)} required codeline(s)'] if len(brands) > len(req) else []
        print('1d codelines:', chosen, flush=True)
        for n in short:                                   # disk: snapshots of codelines not chosen go straight away
            if n not in chosen: shutil.rmtree(R / 'snap' / n, ignore_errors=True)
        # 2a investigate, 2b measure
        for n in [n for n in chosen if ev.get(n, {}).get('large_repo_rg_only')]:
            res['flags'].append(f'{n}: too large to snapshot/index (>{C["large_repo_files"]} files) – not investigated; rg evidence only')
        chosen = [n for n in chosen if not ev.get(n, {}).get('large_repo_rg_only')]
        req = [n for n in req if n in chosen]; alt = [n for n in alt if n in chosen]
        idx = Index(ROOT); res['codelines'] = {}
        for name in chosen:
            s = R / 'snap' / name
            role = 'required codeline' if name in req else 'alternative-approach codeline: list what would change here only under that alternative'
            others = [x for x in req if x != name]
            ctx = (f"The other required codelines for this ticket are {', '.join(others)}; changes there are investigated separately — "
                   "list here only what changes in this repository (e.g. consuming a new shared-library version counts here).") if others else ''
            inv, errs = llm.call(A['investigate'], dict(repo=name, role=role, context=ctx, title=title, description=text), cwd=str(s),
                                 log=log, raw_path=R / f'investigate-{name}.raw.json')
            inv = inv or {}; out = dict(investigation=inv, schema_errors=errs)
            files = idx(name)[0]
            for case in ('base', 'upper'):
                cs = inv.get(case) or {}
                exist = lambda f: (ROOT / name / f).exists()
                logic = [f for f in cs.get('logic', []) if f in files]; exp = [f for f in cs.get('exports_only', []) if f in files]
                new = list(cs.get('new', [])) + [f for f in cs.get('logic', []) + cs.get('exports_only', []) if not exist(f)]
                p = {'repos': {name: {'logic': logic, 'exports_only': exp, 'new': [f for f in new if not exist(f) and f.endswith(SRC)]}},
                     'external': inv.get(f'external_systems_{case}', inv.get('external_systems', []))}
                try: out[case] = measure(idx, p)
                except AssertionError as e: out[case] = {'error': str(e)}; continue
                ch = logic + exp                          # cross-check: tests CodeGraph links to the changed files
                a = run(['codegraph', 'affected', '--json', '-p', str(s)] + ch, log=log) if ch else None
                try: out[case]['codegraph_affected_tests'] = len(json.loads(a.stdout).get('affected', json.loads(a.stdout))) if a else 0
                except Exception: out[case]['codegraph_affected_tests'] = None
            res['codelines'][name] = out
            idx.clear()                                   # release each codeline's source text
        # a required codeline with no BASE change is an alternative; if none is left, alternatives with BASE changes are promoted
        def has_base(n):
            b = (((res['codelines'].get(n) or {}).get('investigation') or {}).get('base')) or {}
            return any(b.get(k) for k in ('logic', 'exports_only', 'new'))
        for n in list(req):
            if not has_base(n):
                req.remove(n); alt.append(n); res['flags'].append(f'{n}: picked as required but its investigation found no BASE change – moved to alternatives')
        if not req:
            for n in list(alt):
                if has_base(n):
                    alt.remove(n); req.append(n); res['flags'].append(f'{n}: promoted from alternative – the only codeline with BASE changes')
        res['required'], res['alternatives'] = req, alt; res['primary'] = req[0] if req else None
        # 2c planning SP + PERT over the required codelines
        blast = lambda n, c: (res['codelines'].get(n, {}).get(c) or {}).get('blast') or 0
        bsum, usum = sum(blast(n, 'base') for n in req), sum(blast(n, 'upper') for n in req)
        res['blast_required'] = dict(base=bsum, upper=usum, by_codeline={n: blast(n, 'base') for n in req})
        if req: res['planning'] = score.planning(bsum, usum, res['drivers']['c_count'], res['drivers']['r_count'])
        return res
    finally:
        subprocess.run(['pkill', '-f', f'codegraph.*{R}/snap'], capture_output=True)
        shutil.rmtree(R / 'snap', ignore_errors=True); shutil.rmtree(inp, ignore_errors=True)
        ep = []
        for d in S['paths']['proof_unchanged']:
            ep += run(['find', str(config.path(d)), '-path', '*/node_modules', '-prune', '-o', '-type', 'f', '-newer', str(R / 'marker'), '-print']).stdout.split()
        cg = run(['bash', '-c', f'find {ROOT}/*/.codegraph -type f -newer {R}/marker 2>/dev/null']).stdout.split()
        changed = [k for k, v in status_before.items() if run(['git', '-C', str(ROOT / k), 'status', '--porcelain']).stdout != v]
        res['proof'] = dict(unchanged_dirs_files_changed=ep, live_codegraph_files_changed=cg, clones_with_changed_status=changed)
        contract.add_contract_fields(res)
        json.dump(res, open(R / 'result.json', 'w'), indent=1, default=str)
        if not drivers_only and res.get('codelines') is not None: manifest.write(R, res)
        log.close()
        print('proof:', {k: len(v) for k, v in res['proof'].items()}); print('result:', R / 'result.json', flush=True)


def tags_in(title):
    return set(t for grp in re.findall(r'\[([A-Z/ ]+)\]', title) for t in re.split(r'[/ ]', grp))
