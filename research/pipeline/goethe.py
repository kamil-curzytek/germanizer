"""Extract headwords from the Goethe A1/A2/B1 word lists (used only as CEFR evidence).

The PDFs are multi-column (headword | examples, sometimes two such pairs per page).
We split each line on runs of 2+ spaces and keep segments that look like entries:
  nouns:  'der Termin, -e'            -> Termin (+ article)
  others: 'bezahlen', 'ab·fahren, ...' -> bezahlen / abfahren
then drop inflected forms with the lemmatizer (e.g. 'isst' from 'essen, isst, ...').
"""
import json, re, sys
from pathlib import Path
import simplemma

SRC = Path(__file__).resolve().parents[1] / 'sources'
NOUN = re.compile(r'^(der|die|das)\s+([A-ZÄÖÜ][A-Za-zÄÖÜäöüß-]+)(?:\s*,\s*([^\s(]*)|\s*\((Pl\.|Sg\.)\)|\s*$|\s+\(|\s*/)')
OTHER = re.compile(r'^([a-zäöüß][a-zäöüß·|\-]+)(?:\s*,|\s*$|\s+\(|\s+sich\b|\s*/)')
SICH = re.compile(r'^sich\s+([a-zäöüß][a-zäöüß·|\-]+)')
SKIP_START = {'hat', 'ist', 'war', 'hatte', 'wird', 'wurde', 'z', 'siehe'}

def sections(text: str, level: str) -> str:
    # skip the foreword; keep the topic word groups (time, numbers, ...) and the alphabetical list
    marker = {'A1': 'Inventare', 'A2': 'WORTGRUPPEN', 'B1': '1 Wortgruppen'}[level]
    idx = [m.start() for m in re.finditer(marker, text)]
    return text[idx[1] if level == 'B1' and len(idx) > 1 else idx[0]:] if idx else text

def extract(level: str, path: Path):
    text = sections(path.read_text(encoding='utf-8'), level)
    out = {}
    for line in text.splitlines():
        for seg in re.split(r'\s{2,}|\t', line.strip()):
            seg = seg.strip()
            if not seg:
                continue
            # a segment that clearly starts with an entry ('der X,' / 'word,') may have an example glued on
            starts_entry = bool(NOUN.match(seg)) or bool(re.match(r'^(sich\s+)?[a-zäöüß][a-zäöüß·|\-]+,', seg))
            if not starts_entry and (len(seg.split()) > 7 or re.search(r'[.!?]$', seg)):
                continue
            region = 'A' if re.search(r'\(A\)', seg) else 'CH' if re.search(r'\(CH\)', seg) else None
            m = re.match(r'^\d+\s*=\s*([a-zäöüß]+)$', seg)
            if m:  # number words: '2 = zwei'
                out.setdefault(m.group(1), {'article': None, 'regional': None, 'pos': 'numeral'})
                continue
            m = NOUN.match(seg)
            if m:
                lemma, art = m.group(2), m.group(1)
                out.setdefault(lemma, {'article': art, 'regional': region, 'pos': 'noun', 'pluralOnly': m.group(4) == 'Pl.'})
                continue
            m = SICH.match(seg) or OTHER.match(seg)
            if m:
                tok = m.group(1).replace('·', '').replace('|', '').strip('-')
                if len(tok) < 2 or tok in SKIP_START:
                    continue
                # drop inflected forms such as 'isst', 'fährt', 'hieß' (infinitives/adjectives are kept)
                if (simplemma.lemmatize(tok, lang='de') != tok
                        and not tok.endswith(('en', 'ern', 'eln', 'lich', 'ig', 'bar', 'isch', 'los', 'sam'))):
                    continue
                out.setdefault(tok, {'article': None, 'regional': region, 'pos': None, 'reflexive': seg.startswith('sich ')})
    return out

if __name__ == '__main__':
    result = {}
    for level, f in [('A1', 'goethe_A1_SD1_Wortliste.txt'), ('A2', 'goethe_A2_Wortliste.txt'), ('B1', 'goethe_B1_Wortliste.txt')]:
        entries = extract(level, SRC / f)
        result[level] = entries
        print(level, len(entries), 'nouns', sum(1 for e in entries.values() if e['pos'] == 'noun'),
              'regional', sum(1 for e in entries.values() if e['regional']))
    (SRC / 'goethe_headwords.json').write_text(json.dumps(result, ensure_ascii=False, indent=0), encoding='utf-8')
