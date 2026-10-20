# Blast radius of a planned change set (no name-guessing). Same rules as the PI-12 measure:
#  TS/JS: dependents = files that IMPORT a changed source file (relative paths + tsconfig aliases/baseUrl resolved).
#  C#:    dependents = files referencing a TYPE declared in a changed file (class/interface/record/enum/struct names, >= 6 chars).
#  logic files -> every importer counts; exports_only files -> none yet; new files -> changed, no dependents yet.
#  Tests: test files among the dependents. Excluded: minified / generated files, node_modules, build output.
#  BR = changed + importing + tests + external_weight x external systems. Read only: index() only reads files.
import collections, json, os, re
from . import config

F = config.load('formula')
JS = ('.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.vue'); CS = ('.cs',); SRC = JS + CS + ('.py', '.java', '.sql', '.cshtml')
SKIP = {'node_modules', '.next', '.git', 'dist', 'coverage', 'build', 'out', 'bin', 'obj', 'packages', 'vendor', '.venv', '.turbo', 'storybook-static'}
is_test = lambda p: bool(re.search(r'(\.test\.|\.spec\.|__tests__|/e2e/|cypress|playwright|/tests?/|\.Tests?/|Tests?\.cs$)', p, re.I))
IMP = re.compile(r'''(?:import\s[^'"]*?from\s*|import\s*\(\s*|require\(\s*|export\s[^'"]*?from\s*|import\s+)['"]([^'"]+)['"]''')
CSTYPE = re.compile(r'\b(?:class|interface|record|enum|struct)\s+([A-Z][A-Za-z0-9_]{5,})')


def generated(path, txt):
    if path.endswith(('.min.js', '.bundle.js')) or '/generated/' in path.lower(): return True
    return any(len(l) > 1000 for l in txt.splitlines()[:400])


def tsconfig(repo_dir):
    base, paths = None, {}
    for name in ('tsconfig.json', 'jsconfig.json'):
        p = os.path.join(repo_dir, name)
        if os.path.exists(p):
            try:
                t = re.sub(r'//[^\n]*|/\*.*?\*/', '', open(p, encoding='utf-8', errors='ignore').read(), flags=re.S)
                t = re.sub(r',(\s*[}\]])', r'\1', t)
                co = json.loads(t).get('compilerOptions', {})
                base = co.get('baseUrl'); paths = co.get('paths', {}) or {}
            except Exception: pass
            break
    return base, paths


class Index:
    """Source files, importers and declared C# types per codeline under root. Cached per repo; clear() releases memory."""
    def __init__(self, root):
        self.root = str(root); self._cache = {}

    def clear(self): self._cache.clear()

    def __call__(self, repo):
        if repo in self._cache: return self._cache[repo]
        files, top = {}, os.path.join(self.root, repo)
        for r, dirs, fs in os.walk(top):
            dirs[:] = [d for d in dirs if d not in SKIP]
            for f in fs:
                if f.endswith(SRC):
                    p = os.path.relpath(os.path.join(r, f), top)
                    try: t = open(os.path.join(r, f), encoding='utf-8', errors='ignore').read()
                    except Exception: continue
                    if not generated(p, t): files[p] = t
        base, paths = tsconfig(top); fileset = set(files)

        def resolve(src, spec):
            cands = []
            if spec.startswith('.'): cands.append(os.path.normpath(os.path.join(os.path.dirname(src), spec)))
            else:
                for pat, targets in paths.items():
                    pre = pat.rstrip('*')
                    if spec.startswith(pre) and pat.endswith('*'):
                        for tg in targets: cands.append(os.path.normpath(os.path.join(base or '.', tg.rstrip('*') + spec[len(pre):])))
                    elif spec == pat:
                        for tg in targets: cands.append(os.path.normpath(os.path.join(base or '.', tg)))
                if spec.startswith(('@/', '~/')): cands.append(os.path.join('src', spec[2:]))
                if base: cands.append(os.path.normpath(os.path.join(base, spec)))
            for c in cands:
                for x in [c] + [c + e for e in JS] + [os.path.join(c, 'index' + e) for e in JS]:
                    if x in fileset: return x
            return None
        importers = collections.defaultdict(set)
        for f, t in files.items():
            if not f.endswith(JS): continue
            for spec in IMP.findall(t):
                tgt = resolve(f, spec)
                if tgt and tgt != f: importers[tgt].add(f)
        decl = {f: set(CSTYPE.findall(t)) for f, t in files.items() if f.endswith(CS)}
        self._cache[repo] = (files, importers, decl); return self._cache[repo]


def scope_level(br):
    return sum(br > c for c in F['scope']['cuts'])


def measure(index, plan):
    """plan = {'repos': {repo: {'logic': [...], 'exports_only': [...], 'new': [...]}}, 'external': [...]}"""
    changed = deps = tests = 0; detail = {}
    for repo, p in plan['repos'].items():
        files, importers, decl = index(repo)
        logic, exp, new = p.get('logic', []), p.get('exports_only', []), p.get('new', [])
        missing = [f for f in logic + exp if f not in files]
        assert not missing, f'{repo}: planned files not found in clone: {missing}'
        clash = [f for f in new if f in files]
        assert not clash, f'{repo}: "new" files already exist: {clash}'
        ch = set(logic + exp + new)
        src = [f for f in ch if not is_test(f)]; chg_tests = [f for f in ch if is_test(f)]
        d, t, why = set(), set(chg_tests), {}
        for f in logic:
            if f.endswith(JS):
                for imp in importers.get(f, ()):
                    if imp in ch: continue
                    (t if is_test(imp) else d).add(imp); why.setdefault(imp, f'imports {f}')
            elif f.endswith(CS):
                types = decl.get(f, set())
                if not types: continue
                rx = re.compile(r'\b(' + '|'.join(map(re.escape, sorted(types))) + r')\b')
                for g, txt in files.items():
                    if g in ch or not g.endswith(CS): continue
                    m = rx.search(txt)
                    if m: (t if is_test(g) else d).add(g); why.setdefault(g, f'references {m.group(1)} (declared in {f})')
        changed += len(src); deps += len(d); tests += len(t)
        detail[repo] = dict(changed_files=sorted(src), importing_files=sorted(d), test_files=sorted(t), why=why,
                            logic=logic, exports_only=exp, new=new)
    ext = plan['external']
    blast = changed + deps + tests + F['blast_radius']['external_weight'] * len(ext)
    lvl = scope_level(blast)
    return dict(changed=changed, importing=deps, tests=tests, external=len(ext), external_systems=ext, blast=blast,
                scope=F['scope']['levels'][lvl], scope_pts=F['scope']['points'][lvl], detail=detail)
