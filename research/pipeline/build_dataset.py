"""Build data/*.json from the curated authoring files and validate every entry.

Authoring format: research/authoring/*.psv, one entry per line, "#" starts a comment line.
14 positional columns separated by "|":
  german | type | pos | article | plural | english | cefr | tier | mode | topics | register | example | example_en | grammar
followed by optional LABELLED segments (any order), so a miscounted "|" can never shift data:
  f=forms   c=collocations   r=related items   why=curator note for evidence.selectionReason

  german      lemma / expression ("Termin", "sich erinnern", "Keine Ahnung")
  type        w(ord) | c(onstruction) | f(ixedExpression) | p(functionalPhrase)
  pos         noun verb adj adv prep conj pron det num part intj phrase
  article     der/die/das (nouns)
  plural      plural form | "∅" no plural (singular-only) | "Pl" plural-only noun
  english     meanings separated by ";"
  cefr        A1 A2 B1 B2      tier 1-4      mode a(ctive) | r(eceptive) | b(oth)
  topics      comma-separated  register comma-separated (empty = neutral)
  grammar     tags + notes, ";"-separated. Tags: sep, insep, refl, +Akk, +Dat, +Gen, aux:sein, aux:haben, irreg,
              pattern, prep:<p>, var:<variant>. Anything else is kept as a note.
  f=          verbs "3sg, preterite, perfect" (fährt, fuhr, ist gefahren); adjectives "comparative, superlative"
  c=, r=      ";"-separated lists
"""
import csv, json, re, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
import simplemma

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'sources'
AUTH = ROOT / 'authoring'
OUT = ROOT.parent / 'data'
COLS = ['german', 'type', 'pos', 'article', 'plural', 'english', 'cefr', 'tier', 'mode', 'topics', 'register',
        'example', 'example_en', 'grammar', 'forms', 'collocations', 'related', 'reason']
TYPES = {'w': 'word', 'c': 'construction', 'f': 'fixedExpression', 'p': 'functionalPhrase'}
POS = {'noun', 'verb', 'adj', 'adv', 'prep', 'conj', 'pron', 'det', 'num', 'part', 'intj', 'phrase'}
POS_NAME = {'adj': 'adjective', 'adv': 'adverb', 'prep': 'preposition', 'conj': 'conjunction', 'pron': 'pronoun',
            'det': 'determiner', 'num': 'numeral', 'part': 'particle', 'intj': 'interjection'}
MODES = {'a': 'active', 'r': 'receptive', 'b': 'both'}
GENDER = {'der': 'masculine', 'die': 'feminine', 'das': 'neuter'}
SEP_PREFIXES = ('ab', 'an', 'auf', 'aus', 'bei', 'dabei', 'dar', 'durch', 'ein', 'fern', 'fest', 'fort', 'her', 'heraus',
                'herein', 'herum', 'hin', 'hinaus', 'hinein', 'kennen', 'los', 'mit', 'nach', 'statt', 'teil', 'um', 'vor',
                'vorbei', 'weg', 'weiter', 'zu', 'zurück', 'zusammen', 'spazieren', 'stehen', 'statt', 'sauber', 'frei',
                'kaputt', 'leid', 'wieder', 'hoch', 'runter', 'rein', 'raus')

def slug(s: str) -> str:
    s = s.lower().replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue').replace('ß', 'ss')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

def load_candidates():
    with open(ROOT / 'candidates.csv', encoding='utf-8') as f:
        return {r['lemma']: r for r in csv.DictReader(f)}

def load_forms():
    forms = set()
    for name in ('deu_news_2023_300K', 'deu-de_web_2021_300K'):
        with open(SRC / name / f'{name}-words.txt', encoding='utf-8') as f:
            for line in f:
                p = line.rstrip('\n').split('\t')
                if len(p) >= 3 and int(p[2]) >= 2:
                    forms.add(p[1].lower())
    with open(SRC / 'SUBTLEX_DE.csv', encoding='utf-8', errors='replace') as f:
        for row in csv.reader(f):
            forms.add(row[0].lower())
    return forms

def tokens(s):
    return re.findall(r"[A-Za-zÄÖÜäöüß]+", s)

def lemmas_of(sentence):
    toks = tokens(sentence)
    out = set()
    for t in toks:
        out.add(t.lower())
        out.add(simplemma.lemmatize(t, lang='de').lower())
        out.add(simplemma.lemmatize(t.lower(), lang='de').lower())
        out.add(simplemma.lemmatize(t.capitalize(), lang='de').lower())
    return out, [t.lower() for t in toks]

def example_contains(entry, example):
    """Does the example actually use the item? Lemma match, separable verbs and multi-word items handled."""
    lem, toks = lemmas_of(example)
    words = [w for w in tokens(entry['german']) if w.lower() not in ('sich', 'etwas', 'jemandem', 'jemanden', 'jdm', 'jdn', 'etw')]
    if not words:
        return True
    if ', ' in entry['german'] and entry['unitType'] == 'word':  # 'der, die, das' / 'mein, meine': any listed form counts
        return any(w.lower() in lem for w in words)
    if entry['unitType'] in ('fixedExpression', 'functionalPhrase'):
        ex = ' '.join(toks)
        key = ' '.join(w.lower() for w in words)
        # inflected words inside expressions count (in den Gelben Sack, in der Europäischen Union)
        return key in ex or all(w.lower() in lem or any(t.startswith(w.lower()[:max(4, len(w) - 2)]) for t in toks) for w in words)
    # inflected forms listed in the entry (e.g. 'weiß, wusste, hat gewusst') count as the item
    listed = {t.lower() for t in tokens(entry.get('_forms') or '')} - {'hat', 'ist', 'sich'}
    if listed and listed & set(toks) or any(t.startswith(f if len(f) < 6 else f[:5]) for f in listed if len(f) >= 4 for t in toks):
        return True
    ok = []
    for w in words:
        wl = w.lower()
        if wl in lem or any(t.startswith(wl[:max(4, len(wl) - 3)]) for t in toks):
            ok.append(True)
            continue
        # separable verb: prefix appears separately and the stem's lemma appears
        hit = False
        for p in sorted(SEP_PREFIXES, key=len, reverse=True):
            if wl.startswith(p) and len(wl) > len(p) + 2:
                stem = wl[len(p):]
                if p in toks and (stem in lem or any(t.startswith(stem[:max(3, len(stem) - 3)]) for t in toks)):
                    hit = True
                    break
                if any(t.startswith(p) and t.endswith(stem[-3:]) for t in toks):  # zu-infinitive / participle: anzurufen, angerufen
                    hit = True
                    break
        ok.append(hit)
    return all(ok)

def parse_grammar(text):
    g = {'notes': None}
    notes = []
    for part in [p.strip() for p in (text or '').split(';') if p.strip()]:
        low = part.lower()
        if low == 'sep':
            g['separable'] = True
        elif low == 'insep':
            g['separable'] = False
        elif low == 'refl':
            g['reflexive'] = True
        elif low in ('+akk', '+dat', '+gen'):
            g.setdefault('case', []).append({'+akk': 'Akkusativ', '+dat': 'Dativ', '+gen': 'Genitiv'}[low])
        elif low.startswith('aux:'):
            g['auxiliary'] = low[4:]
        elif low == 'irreg':
            g['irregular'] = True
        elif low == 'pattern':
            g['pattern'] = True  # entry teaches a pattern; the example shows one instance
        elif low.startswith('prep:'):
            g['preposition'] = part[5:].strip()
        elif low.startswith('var:'):
            g.setdefault('variants', []).append(part[4:].strip())
        else:
            notes.append(part)
    if notes:
        g['notes'] = ' '.join(notes)
    return g

FUNCTION_TOKENS = {'sich', 'etwas', 'jemandem', 'jemanden', 'jemand', 'der', 'die', 'das', 'den', 'dem', 'des',
                   'ein', 'eine', 'einen', 'einem', 'einer', 'an', 'auf', 'aus', 'bei', 'für', 'gegen', 'in', 'im',
                   'ins', 'mit', 'nach', 'über', 'um', 'ums', 'unter', 'von', 'vom', 'vor', 'zu', 'zum', 'zur'}

def evidence_head(entry, cands):
    """Lemma whose corpus evidence describes the entry. Single words: the word itself. Constructions: the rarest
    content word (the noun of a noun-verb construction, the verb of 'sich freuen auf'), never a function word."""
    content = [w.lower() for w in tokens(entry['german']) if w.lower() not in FUNCTION_TOKENS]
    if not content:
        return None
    if entry['unitType'] == 'word' or len(content) == 1:
        return content[0]
    known = [w for w in content if w in cands]
    if not known:
        return None
    rank = lambda w: min(int(x) for x in (cands[w]['rank_subtitles'], cands[w]['rank_news'], cands[w]['rank_web']) if x)         if any((cands[w]['rank_subtitles'], cands[w]['rank_news'], cands[w]['rank_web'])) else 10**9
    return max(known, key=rank)

def evidence(entry, cands, goethe_level):
    key = evidence_head(entry, cands)
    c = cands.get(key) if key and entry['unitType'] in ('word', 'construction') else None
    ev = {'sources': [], 'frequency': None, 'goetheLevel': None, 'priorityScore': None, 'selectionReason': ''}
    multi = c is not None and ' ' in entry['german'].strip()
    if multi:
        ev['evidenceHead'] = key  # corpus figures below describe this head word, not the whole construction
    if c:
        ev['frequency'] = {k: (int(c[f'rank_{k}']) if c[f'rank_{k}'] else None) for k in ('subtitles', 'news', 'web', 'folk')}
        ev['goetheLevel'] = c['goethe_level'] or None
        ev['priorityScore'] = float(c['score'])
        ev['sources'] = [s for s, k in (('SUBTLEX-DE', 'subtitles'), ('Leipzig news 2023', 'news'), ('Leipzig web .de 2021', 'web'), ('FOLK', 'folk')) if ev['frequency'][k]]
        if ev['goetheLevel']:
            ev['sources'].append(f"Goethe {ev['goetheLevel']} Wortliste")
    reasons = []
    if c and c['rank_subtitles'] and int(c['rank_subtitles']) <= 1000:
        reasons.append(f"very frequent in speech (subtitle rank {c['rank_subtitles']})")
    elif c and c['rank_subtitles'] and int(c['rank_subtitles']) <= 5000:
        reasons.append(f"frequent in speech (subtitle rank {c['rank_subtitles']})")
    if c and (c['rank_news'] or c['rank_web']):
        wr = min(int(x) for x in (c['rank_news'], c['rank_web']) if x)
        if wr <= 3000:
            reasons.append(f'common in written German (rank {wr})')
    if ev['goetheLevel']:
        reasons.append(f"in the Goethe {ev['goetheLevel']} list")
    if multi and reasons:
        reasons = [f"head word '{key}': " + '; '.join(reasons)]
    if entry['unitType'] in ('fixedExpression', 'functionalPhrase'):
        reasons.append('high-value chunk for spoken interaction')
    if entry.get('_reason'):
        reasons.append(entry['_reason'])
    if not reasons:
        reasons.append('needed for real-life scenarios in Germany (low corpus frequency, high practical value)')
    ev['selectionReason'] = '; '.join(reasons)
    return ev

def main():
    cands = load_candidates()
    forms = load_forms()
    goethe = json.loads((SRC / 'goethe_headwords.json').read_text(encoding='utf-8'))
    g_article = {}
    for lv in ('B1', 'A2', 'A1'):
        for w, m in goethe[lv].items():
            if m.get('article') and not m.get('pluralOnly'):  # 'die Lebensmittel (Pl.)' says nothing about the singular
                g_article[w] = m['article']

    entries, problems, warnings = [], [], []
    ids = Counter()
    seen_lemma = {}
    for path in sorted(AUTH.glob('*.psv')):
        for n, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
                if not line.strip() or line.lstrip().startswith('#'):
                    continue
                cols = [c.strip() for c in line.split('|')]
                head, tail = cols[:14], cols[14:]
                r = dict(zip(COLS[:14], head + [''] * (14 - len(head))))
                r.update({'forms': '', 'collocations': '', 'related': '', 'reason': ''})
                for seg in tail:
                    m = re.match(r'^(f|c|r|why)=(.*)$', seg)
                    if not seg:
                        continue
                    if not m:
                        problems.append(f'{path.name}:{n}: unlabelled trailing field {seg!r}')
                        continue
                    r[{'f': 'forms', 'c': 'collocations', 'r': 'related', 'why': 'reason'}[m.group(1)]] = m.group(2).strip()
                where = f'{path.name}:{n} "{r["german"]}"'
                t = TYPES.get(r['type'])
                if not t:
                    problems.append(f'{where}: bad type {r["type"]!r}')
                    continue
                if r['pos'] not in POS:
                    problems.append(f'{where}: bad pos {r["pos"]!r}')
                if r['cefr'] not in ('A1', 'A2', 'B1', 'B2'):
                    problems.append(f'{where}: bad cefr {r["cefr"]!r}')
                if r['tier'] not in ('1', '2', '3', '4'):
                    problems.append(f'{where}: bad tier {r["tier"]!r}')
                if r['mode'] not in MODES:
                    problems.append(f'{where}: bad mode {r["mode"]!r}')
                if not r['english']:
                    problems.append(f'{where}: missing english')
                if not r['example'] or not r['example_en']:
                    problems.append(f'{where}: missing example')
                elif not re.search(r'[.!?…"“”]$', r['example']):
                    problems.append(f'{where}: example should end with punctuation')

                base = slug(r['german'])
                g = r['german'].strip('?!.,… ')
                # single words: case- and gender-sensitive (Sie/sie, der/die Leiter); phrases: case-insensitive, any POS
                key = (g, r['pos'], r['article']) if (' ' not in g or ',' in g) else (g.lower(), 'multi', '')
                if key in seen_lemma:
                    problems.append(f'{where}: duplicate of {seen_lemma[key]} (same word and part of speech)')
                seen_lemma.setdefault(key, where)
                eid = base if not ids[base] else (f"{base}-{r['article']}" if r['pos'] == 'noun' and ids.get(f"{base}-{r['pos']}") else f"{base}-{r['pos']}")
                if ids[eid]:
                    problems.append(f'{where}: duplicate id {eid}')
                ids[base] += 1
                ids[eid] += 1

                e = {
                    'id': eid,
                    'german': r['german'],
                    'unitType': t,
                    'partOfSpeech': POS_NAME.get(r['pos'], r['pos']),
                    'english': [x.strip() for x in r['english'].split(';') if x.strip()],
                    'article': None, 'gender': None, 'plural': None,
                    'cefr': r['cefr'],
                    'priorityTier': int(r['tier']) if r['tier'].isdigit() else None,
                    'learningMode': MODES.get(r['mode']),
                    'topics': [x.strip() for x in r['topics'].split(',') if x.strip()],
                    'register': [x.strip() for x in r['register'].split(',') if x.strip()] or ['neutral'],
                    'example': {'german': r['example'], 'english': r['example_en']},
                    'grammar': parse_grammar(r['grammar']),
                    'collocations': [x.strip() for x in r['collocations'].split(';') if x.strip()],
                    'relatedItems': [x.strip() for x in r['related'].split(';') if x.strip()],
                    '_reason': r['reason'],
                    '_forms': r['forms'],
                }
                if r['pos'] == 'noun':
                    if r['article'] not in GENDER:
                        problems.append(f'{where}: noun needs der/die/das')
                    else:
                        e['article'], e['gender'] = r['article'], GENDER[r['article']]
                    if r['plural'] == '∅':
                        e['plural'] = None
                        e['grammar']['singularOnly'] = True
                    elif r['plural'] == 'Pl':
                        e['plural'] = r['german']
                        e['grammar']['pluralOnly'] = True
                    elif r['plural']:
                        e['plural'] = r['plural']
                        if r['plural'].lower() not in forms:
                            warnings.append(f'{where}: plural "{r["plural"]}" not found in any corpus')
                    else:
                        problems.append(f'{where}: noun needs a plural, ∅ or Pl')
                    ga = g_article.get(r['german'])
                    if ga and ga != r['article'] and r['plural'] != 'Pl':
                        warnings.append(f'{where}: article {r["article"]} but Goethe lists {ga}')
                if r['forms']:
                    p = [x.strip() for x in r['forms'].split(',')]
                    keys = ('comparative', 'superlative') if r['pos'] in ('adj', 'adv') else ('present3sg', 'preterite', 'perfect')
                    e['grammar']['forms'] = dict(zip(keys, p))
                if r['example'] and not e['grammar'].get('pattern') and not example_contains(e, r['example']):
                    warnings.append(f'{where}: example may not contain the item: {r["example"]}')
                e['evidence'] = evidence(e, cands, None)
                del e['_reason'], e['_forms']
                entries.append(e)

    OUT.mkdir(exist_ok=True)
    order = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4}
    entries.sort(key=lambda e: (e['priorityTier'] or 9, order.get(e['cefr'], 9), -(e['evidence']['priorityScore'] or 0)))
    def write(name, items):
        (OUT / name).write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding='utf-8')
    write('german-all.json', entries)
    write('german-core.json', [e for e in entries if e['priorityTier'] == 1])
    for lv in ('A1', 'A2', 'B1', 'B2'):
        write(f'german-{lv.lower()}.json', [e for e in entries if e['cefr'] == lv])

    stats = defaultdict(Counter)
    for e in entries:
        stats['tier'][e['priorityTier']] += 1
        stats['cefr'][e['cefr']] += 1
        stats['mode'][e['learningMode']] += 1
        stats['unitType'][e['unitType']] += 1
        stats['pos'][e['partOfSpeech']] += 1
    report = {'entries': len(entries), **{k: dict(sorted(v.items(), key=lambda x: str(x[0]))) for k, v in stats.items()},
              'problems': len(problems), 'warnings': len(warnings)}
    (ROOT / 'build-report.json').write_text(json.dumps({'summary': report, 'problems': problems, 'warnings': warnings},
                                                       ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))
    for p in problems[:40]:
        print('PROBLEM', p)
    for w in warnings[:60]:
        print('warn', w)
    if problems:
        sys.exit(1)

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
