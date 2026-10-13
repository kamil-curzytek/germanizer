"""Build lemma frequency tables per genre and measure lexical coverage.

Genres are kept separate on purpose (news != web != subtitles != spoken):
  subtitles_lemma : SUBTLEX-DE lemma file (Brysbaert et al. 2011), film/TV subtitles, ~25M tokens
  subtitles_os    : OpenSubtitles 2018 top-50k word forms, lemmatized here
  news            : Leipzig deu_news_2023_300K, lemmatized here
  web             : Leipzig deu-de_web_2021_300K (Germany-domain web), lemmatized here
Only alphabetic tokens count (numbers/punctuation excluded). Lemma keys are lower-cased,
so 'essen' (to eat) and 'Essen' (food) merge; part of speech is decided later, per item.
"""
import csv, json, re
from collections import Counter
from pathlib import Path
import simplemma

SRC = Path(__file__).resolve().parents[1] / 'sources'
WORD = re.compile(r"^[A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß'-]*$")
_cache = {}
# preposition + article contractions count as the preposition
CONTRACTIONS = {'im': 'in', 'ins': 'in', 'am': 'an', 'ans': 'an', 'zum': 'zu', 'zur': 'zu', 'vom': 'von',
                'beim': 'bei', 'aufs': 'auf', 'fürs': 'für', 'übers': 'über', 'durchs': 'durch', 'ums': 'um'}

# one dictionary form per determiner/pronoun (SUBTLEX lemmatizes some of these per form)
DETERMINERS = {'die': 'der', 'das': 'der', 'den': 'der', 'dem': 'der', 'des': 'der', 'eine': 'ein', 'einen': 'ein', 'einem': 'ein',
               'einer': 'ein', 'eines': 'ein', 'keine': 'kein', 'keinen': 'kein', 'keinem': 'kein', 'keiner': 'kein',
               'diese': 'dieser', 'dies': 'dieser', 'dieses': 'dieser', 'diesen': 'dieser', 'diesem': 'dieser',
               'alle': 'all', 'alles': 'all', 'andere': 'anderer', 'anderen': 'anderer', 'jede': 'jeder', 'jeden': 'jeder',
               'jedes': 'jeder', 'welche': 'welcher', 'welchen': 'welcher', 'viele': 'viel', 'vielen': 'viel',
               'meine': 'mein', 'deine': 'dein', 'seine': 'sein', 'ihre': 'ihr', 'unsere': 'unser', 'eure': 'euer'}

def norm(l: str) -> str:
    return DETERMINERS.get(l, l)

def lemma(form: str) -> str:
    if form not in _cache:
        low = form.lower()
        _cache[form] = norm(CONTRACTIONS.get(low) or simplemma.lemmatize(form, lang='de').lower())
    return _cache[form]

def leipzig(name):
    c = Counter()
    with open(SRC / name / f'{name}-words.txt', encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 3:
                continue
            form, n = parts[1], int(parts[2])
            if WORD.match(form):
                c[lemma(form)] += n
    return c

def opensubs_forms():
    # lower-cased word forms (no lemmatization: lower-casing breaks noun lemmas, e.g. 'tagen')
    c = Counter()
    for line in open(SRC / 'opensubtitles_de_50k.txt', encoding='utf-8'):
        form, n = line.split()
        if WORD.match(form):
            c[CONTRACTIONS.get(form, form)] += int(n)
    return c

def subtlex_lemma():
    c = Counter()
    with open(SRC / 'SUBTLEXDE_LemmasJV.csv', encoding='utf-8', errors='replace') as f:
        for row in csv.DictReader(f):
            w = row['Word']
            if WORD.match(w):
                l = CONTRACTIONS.get(w.lower()) or (row['Lemma'] or w).lower()
                if l == '<unknown>':
                    l = w.lower()
                c[norm(l)] += int(float(row['WFfreqcount']))
    return c

def coverage(c: Counter, ns=(100, 250, 500, 1000, 2000, 3000, 4000, 5000, 8000, 10000)):
    total = sum(c.values())
    ranked = [n for _, n in c.most_common()]
    out, cum = {}, 0
    for i, n in enumerate(ranked, 1):
        cum += n
        if i in ns:
            out[i] = round(100 * cum / total, 1)
    return {'tokens': total, 'lemmas': len(ranked), 'coverage_pct_by_top_n': out}

def coverage_of(c: Counter, lemmas: set):
    total = sum(c.values())
    return round(100 * sum(n for l, n in c.items() if l in lemmas) / total, 1)

if __name__ == '__main__':
    tables = {'subtitles_lemma': subtlex_lemma(), 'subtitles_os_forms': opensubs_forms(), 'news': leipzig('deu_news_2023_300K'), 'web': leipzig('deu-de_web_2021_300K')}
    for k, c in tables.items():
        (SRC / f'freq_{k}.json').write_text(json.dumps(dict(c.most_common()), ensure_ascii=False), encoding='utf-8')
    g = json.loads((SRC / 'goethe_headwords.json').read_text(encoding='utf-8'))
    g = {lv: {norm(w.lower()): v for w, v in e.items()} for lv, e in g.items()}
    for lv in g:  # articles/pronouns sit in Goethe's grammar inventory, not the word list: count them for every level
        g[lv].update({w: {} for w in ('der', 'ein', 'kein', 'ich', 'du', 'er', 'sie', 'es', 'wir', 'ihr', 'mein', 'dein', 'sein', 'unser', 'euer', 'man', 'sich', 'mich', 'mir', 'dich', 'dir', 'uns', 'euch', 'ihn', 'ihm', 'ihnen')})
    a1 = {w.lower() for w in g['A1']}
    a2 = a1 | {w.lower() for w in g['A2']}
    b1 = a2 | {w.lower() for w in g['B1']}
    report = {}
    for k, c in tables.items():
        r = coverage(c)
        r['goethe_coverage_pct'] = {'A1 list': coverage_of(c, a1), 'A1+A2 lists': coverage_of(c, a2), 'A1+A2+B1 lists': coverage_of(c, b1)}
        r['goethe_sizes'] = {'A1': len(a1), 'A1+A2': len(a2), 'A1+A2+B1': len(b1)}
        report[k] = r
    (Path(__file__).resolve().parents[1] / 'coverage.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=1))
