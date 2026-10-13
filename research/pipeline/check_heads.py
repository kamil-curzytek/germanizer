"""Report entries whose head word (placeholders and trailing prepositions removed) already exists
with the same part of speech in another line – catches near-duplicates the exact check misses
('bewerben' vs 'sich bewerben um'). Usage: python check_heads.py [file-prefix]"""
import glob, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
SKIP = {'sich', 'etwas', 'jemand', 'jemanden', 'jemandem', 'an', 'auf', 'für', 'über', 'mit', 'bei',
        'von', 'zu', 'vor', 'in', 'um', 'aus', 'gegen', 'nach', 'der', 'die', 'das', '...', '…'}

def head(g):
    t = [x for x in re.findall(r"[A-Za-zÄÖÜäöüß-]+", g) if x.lower() not in SKIP]
    return t[0].lower() if len(t) == 1 else None

def main():
    prefix = sys.argv[1] if len(sys.argv) > 1 else ''
    idx = {}
    for f in sorted(glob.glob(str(ROOT / 'authoring' / '*.psv'))):
        name = Path(f).name
        for i, l in enumerate(open(f, encoding='utf-8'), 1):
            if l.startswith('#') or not l.strip():
                continue
            c = l.split('|')
            h = head(c[0])
            if h:
                idx.setdefault((h, c[2]), []).append((name, i, c[0]))
    n = 0
    for k, v in idx.items():
        if len(v) > 1 and any(x[0].startswith(prefix) for x in v):
            n += 1
            print(' | '.join(f'{a}:{b} {c}' for a, b, c in v))
    print(f'{n} head collisions')

if __name__ == '__main__':
    main()
