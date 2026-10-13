"""One-off repair: classify the optional trailing fields of each authoring line by content
and rewrite them as labelled segments (f= forms, c= collocations, r= related, why= reason)."""
import re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
AUTH = Path(__file__).resolve().parents[1] / 'authoring'

def kind(tok, pos):
    if not tok:
        return None
    if pos == 'verb' and re.search(r',\s*(hat|ist)\s', tok):
        return 'f'
    if pos in ('adj', 'adv') and re.search(r'^\S+,\s*am\s', tok):
        return 'f'
    if ';' not in tok and (tok.startswith('Germany') or re.search(r'\b(productive|frequent|common|corpus|essential)\b', tok) or len(tok.split()) >= 5):
        return 'why'
    parts = [p.strip() for p in tok.split(';') if p.strip()]
    multi = sum(1 for p in parts if len(re.sub(r'\(.*?\)', '', p).split()) > 1)
    return 'c' if multi * 2 >= len(parts) else 'r'

changes = 0
for path in sorted(AUTH.glob('*.psv')):
    out = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            out.append(line)
            continue
        cols = line.split('|')
        head, tail = cols[:14], cols[14:]
        pos = head[2]
        seg = {}
        for t in (x.strip() for x in tail):
            k = kind(t, pos)
            if k:
                if k in seg:  # second related/colloc list: merge
                    seg[k] += ';' + t
                else:
                    seg[k] = t
        new = '|'.join(head + [f'{k}={seg[k]}' for k in ('f', 'c', 'r', 'why') if k in seg])
        if new != line:
            changes += 1
        out.append(new)
    path.write_text('\n'.join(out) + '\n', encoding='utf-8')
print('lines rewritten:', changes)
