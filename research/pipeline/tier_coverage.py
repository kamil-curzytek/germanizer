"""Token coverage of the curriculum, cumulatively by tier, per genre (and FOLK when present).
Strict figure: lemmas each item teaches as a unit (single words, construction heads, one-word phrases).
Inclusive figure: every word appearing in any headword (what the learner is exposed to)."""
import json, re, sys
from pathlib import Path
import simplemma
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'sources'
sys.path.insert(0, str(Path(__file__).parent))
from frequencies import norm, CONTRACTIONS

PLACEHOLDERS = {'sich', 'etwas', 'jemand', 'jemanden', 'jemandem', 'jemands', 'etw', 'jdn', 'jdm', '...', '…'}
PREPS = {'an', 'auf', 'aus', 'bei', 'für', 'gegen', 'in', 'mit', 'nach', 'über', 'um', 'unter', 'von', 'vor', 'zu'}
ALIASES = {'okay': 'ok', 'gerne': 'gern', 'meisten': 'meist'}
# spelling variants / forms the corpus lemmatizer lists as separate lemmas (counted for the base entry)
VARIANTS = {'gern': ['gerne'], 'allein': ['alleine'], 'wenig': ['weniger'], 'ok': ['okay'], 'darauf': ['drauf'], 'darüber': ['drüber']}

def _keys(w):
    w = w.strip(' ?!.,:;')
    if not w:
        return set()
    low = w.lower()
    out = {norm(low), norm(simplemma.lemmatize(w, lang='de').lower())}
    if low in ALIASES:
        out.add(ALIASES[low])
    for k in list(out):
        out.update(VARIANTS.get(k, []))
    return out

def item_lemmas(e):
    """Strict: lemmas the item itself teaches – single words (incl. comma-listed forms and adjective
    comparatives), the head word of constructions ('sich erinnern an' -> erinnern), one-word phrases."""
    g = e['german']
    toks = [t for t in re.split(r'\s+', g.replace(',', ' ')) if t]
    content = [t for t in toks if t.lower() not in PLACEHOLDERS] or toks
    if e['unitType'] in ('fixedExpression', 'functionalPhrase'):
        if len(content) != 1:
            return set()
    elif e['unitType'] == 'construction' or toks[0] == 'sich':
        while len(content) > 1 and content[-1].lower() in PREPS:
            content.pop()
        if len(content) != 1 and ',' not in g:
            return set()
    elif ' ' in g and ',' not in g:
        return set()
    out = set()
    for w in content:
        out |= _keys(w)
    forms = (e.get('grammar') or {}).get('forms') or {}
    for k in ('comparative', 'superlative'):
        if forms.get(k):
            out |= _keys(forms[k].replace('am ', ''))
    return out

def exposure_lemmas(e):
    """Inclusive: every word of the headword, i.e. everything the learner meets in the item."""
    out = set()
    for w in re.split(r'[\s,/]+', e['german']):
        if w and w.lower() not in PLACEHOLDERS and not w.startswith('da-'):
            out |= _keys(w)
    return out

def main():
    data = json.loads((ROOT.parent / 'data' / 'german-all.json').read_text(encoding='utf-8'))
    genres = [g for g in ('subtitles_lemma', 'web', 'news') if (SRC / f'freq_{g}.json').exists()]
    folk = next(iter(SRC.glob('folk_lemmas*.json')), None)
    freqs = {g: json.loads((SRC / f'freq_{g}.json').read_text(encoding='utf-8')) for g in genres}
    if folk:
        freqs['folk'] = json.loads(folk.read_text(encoding='utf-8'))
    report = {}
    known, exposed = set(), set()
    for tier in (1, 2, 3, 4):
        items = [e for e in data if e['priorityTier'] == tier]
        if not items:
            continue
        for e in items:
            known |= item_lemmas(e)
            exposed |= exposure_lemmas(e) | item_lemmas(e)
        row = {'entries_cumulative': sum(1 for e in data if e['priorityTier'] <= tier), 'lemma_keys': len(known)}
        for g, f in freqs.items():
            tot = sum(f.values())
            row[g] = round(100 * sum(n for l, n in f.items() if l in known) / tot, 1)
            row[g + '_inclusive'] = round(100 * sum(n for l, n in f.items() if l in exposed) / tot, 1)
        report[f'tier<= {tier}'] = row
    (ROOT / 'tier-coverage.json').write_text(json.dumps(report, indent=1), encoding='utf-8')
    print(json.dumps(report, indent=1))

if __name__ == '__main__':
    main()
