# Fails when a file that git would commit contains an organisation-specific term (list in config.local/forbidden.txt).
#   python3 scripts/check_clean.py          scan the working tree minus what .gitignore excludes
# Run before every commit. Prints file:line and the term only, never the line.
import pathlib, re, subprocess, sys

def terms(path):
    return [t.strip() for t in pathlib.Path(path).read_text().splitlines() if t.strip() and not t.startswith('#')]

def candidates(root):
    """Files git would commit: tracked + untracked-not-ignored (git ls-files), or the whole tree when not a git repo."""
    r = subprocess.run(['git', '-C', str(root), 'ls-files', '--cached', '--others', '--exclude-standard'], capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip(): return [root / f for f in r.stdout.splitlines()]
    skip = {'.git', 'config.local', 'runs', '__pycache__', '.pytest_cache'}
    return [p for p in root.rglob('*') if p.is_file() and not (skip & set(p.relative_to(root).parts)) and p.name != '.env' and '.bak-' not in p.name]

def scan(root, words):
    rx = re.compile('|'.join(re.escape(w) for w in words), re.I); hits = []
    for p in candidates(root):
        if not p.is_file(): continue
        try: lines = p.read_text(errors='ignore').splitlines()
        except Exception: continue
        hits += [f'{p.relative_to(root)}:{i} ({m.group(0)})' for i, l in enumerate(lines, 1) if (m := rx.search(l))]
    return hits

if __name__ == '__main__':
    root = pathlib.Path(__file__).resolve().parents[1]; t = root / 'config.local/forbidden.txt'
    if not t.exists(): sys.exit('config.local/forbidden.txt missing – cannot check')
    h = scan(root, terms(t)); print('\n'.join(h) or 'clean'); sys.exit(1 if h else 0)
