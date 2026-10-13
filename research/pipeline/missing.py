"""Print which of the given words have no entry yet (by head word, case-insensitive). Usage: python missing.py w1 w2 ..."""
import glob, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))
from check_heads import head  # noqa: E402  (module prints a report on import only under __main__ guard)
ROOT = Path(__file__).resolve().parents[1]
have = set()
for f in glob.glob(str(ROOT / 'authoring' / '*.psv')):
    for l in open(f, encoding='utf-8'):
        if l.startswith('#') or not l.strip():
            continue
        g = l.split('|')[0]
        have.add(g.lower())
        h = head(g)
        if h:
            have.add(h)
        for w in re.split(r',\s*', g):
            have.add(w.strip().lower())
print(' '.join(w for w in sys.argv[1:] if w.lower() not in have))
