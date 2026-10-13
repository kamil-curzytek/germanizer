"""How much of the long tail is compounds/derivatives of already-known lemmas?
For lemmas ranked beyond K in a corpus, count (token-weighted) those whose last component is
one of the top-K lemmas (length >= 4, at least 3 extra characters in front): e.g.
'kinderbett' -> head 'bett', 'mietvertrag' -> 'vertrag'. Rough, but shows the scale.
Also counts derivatives sharing a known stem with productive suffixes (-ung, -heit, -keit, -lich, -bar, -er, -in)."""
import json
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / 'sources'
SUFFIX = ('ung', 'heit', 'keit', 'lich', 'bar', 'schaft', 'erin', 'in', 'er')

def analyse(name, K):
    freq = json.loads((SRC / f'freq_{name}.json').read_text(encoding='utf-8'))
    items = list(freq.items())
    known = {w for w, _ in items[:K] if len(w) >= 4}
    known_stems = {w[:-2] for w in known if w.endswith('en')} | known
    total = sum(n for _, n in items)
    tail = items[K:]
    tail_tokens = sum(n for _, n in tail)
    comp = deriv = 0
    for w, n in tail:
        if any(w.endswith(h) and len(w) - len(h) >= 3 for h in known if len(h) >= 4 and w != h):
            comp += n
        elif any(w.endswith(s) and w[:-len(s)] in known_stems for s in SUFFIX):
            deriv += n
    return {'known_top_K': K, 'tail_share_of_all_tokens_pct': round(100 * tail_tokens / total, 1),
            'compound_of_known_pct_of_tail': round(100 * comp / tail_tokens, 1),
            'derivative_of_known_pct_of_tail': round(100 * deriv / tail_tokens, 1)}

if __name__ == '__main__':
    out = {f'{n}@{k}': analyse(n, k) for n in ('subtitles_lemma', 'web', 'news') for k in (2000, 4000)}
    (Path(__file__).resolve().parents[1] / 'compounds.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=1))
