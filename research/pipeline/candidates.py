"""Build the scored candidate pool (research/candidates.csv).

Pool = union of:
  * top 7,000 lemmas in each frequency table (subtitles, news, web)
  * every Goethe A1/A2/B1 headword
  * every word already in the app (content/vocabulary.json)
  * FOLK spoken lemmas, if research/sources/folk_lemmas.* is present (added automatically)

Each candidate gets transparent component scores in [0, 1]; see research/methodology.md.
These scores rank and flag candidates; the final selection is a curated, documented decision.
"""
import csv, json, math, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'sources'
POOL_TOP_N = 7000
RANK_CAP = 20000  # rank at which a frequency score reaches 0

def load(name):
    return json.loads((SRC / f'freq_{name}.json').read_text(encoding='utf-8'))

def ranks(freq: dict) -> dict:
    return {w: i for i, w in enumerate(freq, 1)}

def fscore(rank):
    if not rank:
        return 0.0
    return max(0.0, 1 - math.log(rank) / math.log(RANK_CAP))

# Closed-class and interactional vocabulary that must not be crowded out by nouns.
FUNCTION_WORDS = set('''
der ein kein ich du er sie es wir ihr man sich mein dein sein unser euer dieser jener jeder all anderer welcher
viel wenig mehr meist beide einige manche etwas nichts jemand niemand alles
was wer wo wohin woher wann wie warum wieso weshalb welcher wieviel
und oder aber denn sondern doch weil dass ob wenn als wie obwohl damit bevor nachdem während bis seit sobald
falls sodass trotzdem deshalb deswegen daher also außerdem dann danach zuerst schließlich jedoch allerdings sonst
in an auf aus bei mit nach von zu für über unter vor hinter neben zwischen durch gegen ohne um seit ab bis
wegen trotz statt innerhalb außerhalb gegenüber entlang laut
sein haben werden können müssen wollen sollen dürfen mögen möchten lassen
nicht nie immer oft manchmal schon noch erst nur auch sehr ganz ziemlich fast gar etwa ungefähr genau
ja nein doch mal eben halt eigentlich wohl ja bitte danke gern gerne vielleicht bestimmt sicher natürlich klar
hier da dort jetzt heute morgen gestern bald später gleich sofort wieder zusammen
okay ok na ach oh hm äh genau stimmt
'''.split())

def main():
    tables = {k: load(k) for k in ('subtitles_lemma', 'news', 'web')}
    folk_path = next(iter(SRC.glob('folk_lemmas*.json')), None)
    if folk_path:
        tables['folk'] = json.loads(folk_path.read_text(encoding='utf-8'))
    rk = {k: ranks(v) for k, v in tables.items()}

    goethe = json.loads((SRC / 'goethe_headwords.json').read_text(encoding='utf-8'))
    glevel, gmeta = {}, {}
    for lv in ('B1', 'A2', 'A1'):  # lowest level wins
        for w, meta in goethe[lv].items():
            glevel[w.lower()] = lv
            gmeta[w.lower()] = {**gmeta.get(w.lower(), {}), **meta, 'surface': w}

    app = {w['de'].lower().replace('sich ', ''): w for w in json.loads((ROOT.parent / 'content' / 'vocabulary.json').read_text(encoding='utf-8'))['words']}

    pool = set(glevel) | set(app) | FUNCTION_WORDS
    for k, freq in tables.items():
        pool |= set(list(freq)[:POOL_TOP_N])
    pool = {w for w in pool if re.match(r"^[a-zäöüß][a-zäöüß-]*$", w) and len(w) > 1}

    rows = []
    for w in pool:
        r = {k: rk[k].get(w) for k in rk}
        s_sub = fscore(r.get('subtitles_lemma'))
        s_folk = fscore(r.get('folk')) if 'folk' in r else None
        spoken = s_sub if s_folk is None else 0.35 * s_sub + 0.65 * s_folk
        written = (fscore(r.get('news')) + fscore(r.get('web'))) / 2
        g = {'A1': 1.0, 'A2': 0.8, 'B1': 0.6}.get(glevel.get(w), 0.0)
        breadth = sum(1 for k in rk if r.get(k) and r[k] <= 8000) / len(rk)
        func = 1.0 if w in FUNCTION_WORDS else 0.0
        # penalties
        regional = 0.15 if gmeta.get(w, {}).get('regional') else 0.0
        # film/TV skew: frequent in subtitles, rare in everyday written German, not in any Goethe list
        skew = 0.15 if (s_sub > 0.45 and written < 0.25 and not g and not func) else 0.0
        written_only = 0.05 if (written > 0.45 and spoken < 0.15 and not g) else 0.0
        score = (0.35 * spoken + 0.20 * written + 0.25 * g + 0.10 * breadth + 0.10 * func
                 - regional - skew - written_only)
        rows.append({
            'lemma': w, 'score': round(score, 4),
            'spoken': round(spoken, 3), 'written': round(written, 3), 'goethe_level': glevel.get(w, ''),
            'breadth': round(breadth, 2), 'function_word': int(func),
            'rank_subtitles': r.get('subtitles_lemma') or '', 'rank_folk': r.get('folk') or '',
            'rank_news': r.get('news') or '', 'rank_web': r.get('web') or '',
            'article': gmeta.get(w, {}).get('article') or '', 'goethe_surface': gmeta.get(w, {}).get('surface', ''),
            'regional_variant': gmeta.get(w, {}).get('regional') or '',
            'penalties': ';'.join(p for p, v in (('regional', regional), ('film-skew', skew), ('written-only', written_only)) if v),
            'in_app': int(w in app),
        })
    rows.sort(key=lambda x: -x['score'])
    for i, row in enumerate(rows, 1):
        row['priority_rank'] = i
    out = ROOT / 'candidates.csv'
    with out.open('w', encoding='utf-8', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=['priority_rank'] + [k for k in rows[0] if k != 'priority_rank'])
        wr.writeheader()
        wr.writerows(rows)
    print(f'{len(rows)} candidates -> {out}  (FOLK included: {bool(folk_path)})')

if __name__ == '__main__':
    main()
