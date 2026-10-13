"""Can grammar exercises be generated from content we already have? (writes content_analysis.json)

1. Gender cues: how many nouns in the curriculum (data/german-all.json) follow a reliable ending rule,
   and how reliable each rule is on our own nouns.
2. Exercise material: how many example sentences (app seed + curriculum) contain each grammar
   phenomenon an automatic exercise needs. Detection is regex-based (deliberately conservative).
Run from research/grammar-strategy: python content_analysis.py
"""
import json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]

curr = json.loads((ROOT / 'data' / 'german-all.json').read_text(encoding='utf-8'))
app = json.loads((ROOT / 'content' / 'vocabulary.json').read_text(encoding='utf-8'))['words']

# ---------------------------------------------------------------- 1. gender cues
RULES = [  # (ending, article) – textbook rules (Köpcke & Zubin type regularities)
    ('ung', 'die'), ('heit', 'die'), ('keit', 'die'), ('schaft', 'die'), ('ion', 'die'), ('tät', 'die'),
    ('ei', 'die'), ('ie', 'die'), ('ik', 'die'), ('enz', 'die'), ('anz', 'die'), ('ur', 'die'), ('e', 'die'),
    ('chen', 'das'), ('lein', 'das'), ('ment', 'das'), ('um', 'das'), ('nis', 'das'),
    ('ling', 'der'), ('ismus', 'der'), ('or', 'der'), ('ist', 'der'), ('ant', 'der'), ('er', 'der'),
]
nouns = [e for e in curr if e['partOfSpeech'] == 'noun' and e.get('article') in ('der', 'die', 'das')]


def compound_head(word):
    return word.split('-')[-1].lower()


gender = {'nouns': len(nouns), 'rules': []}
matched_any = set()
for end, art in RULES:
    hits = [e for e in nouns if compound_head(e['german']).endswith(end) and e['id'] not in matched_any]
    ok = [e for e in hits if e['article'] == art]
    for e in hits:
        matched_any.add(e['id'])
    gender['rules'].append({'ending': f'-{end}', 'article': art, 'nouns': len(hits),
                            'accuracy': round(100 * len(ok) / len(hits), 1) if hits else None,
                            'exceptions_sample': [e['german'] for e in hits if e['article'] != art][:6]})
covered = [e for e in nouns if e['id'] in matched_any]
gender['covered_by_some_rule_pct'] = round(100 * len(covered) / len(nouns), 1)
reliable = [r for r in gender['rules'] if r['accuracy'] and r['accuracy'] >= 90]
gender['covered_by_rules_90pct_reliable'] = round(100 * sum(r['nouns'] for r in reliable) / len(nouns), 1)
gender['article_distribution'] = Counter(e['article'] for e in nouns)

# ---------------------------------------------------------------- 2. exercise material
sentences = [(e['example']['german'], 'curriculum', e) for e in curr] + [(w['ex'], 'app', w) for w in app]
DET = r'(?:der|die|das|den|dem|des|ein|eine|einen|einem|einer|eines|kein|keine|keinen|keinem|keiner|mein|meine|meinen|meinem|meiner|dein|deine|deinen|deinem|deiner|sein|seine|seinen|seinem|seiner|ihr|ihre|ihren|ihrem|ihrer|unser|unsere|unseren|unserem|unserer)'
DAT_PREP = r'(?:mit|bei|nach|von|zu|aus|seit|gegenüber)'
ACC_PREP = r'(?:für|ohne|gegen|durch|um)'
WAY_PREP = r'(?:in|an|auf|über|unter|vor|hinter|neben|zwischen)'
PATTERNS = {
    'case after dative preposition (mit dem, bei der …)': rf'\b{DAT_PREP}\s+{DET}\s+[A-ZÄÖÜ]',
    'case after accusative preposition (für den …)': rf'\b{ACC_PREP}\s+{DET}\s+[A-ZÄÖÜ]',
    'two-way preposition + article (in der / in die …)': rf'\b{WAY_PREP}\s+{DET}\s+[A-ZÄÖÜ]',
    'article + adjective + noun (adjective ending)': rf'\b{DET}\s+[a-zäöüß]+(?:e|en|er|es|em)\s+[A-ZÄÖÜ][a-zäöüß]+',
    'Perfekt (haben/sein … participle at the end)': r'\b(?:habe|hast|hat|haben|habt|bin|bist|ist|sind|seid)\b.*\bge[a-zäöüß]+(?:t|en)[.!?]$',
    'modal verb … infinitive at the end': r'\b(?:kann|kannst|können|muss|musst|müssen|will|willst|wollen|möchte|möchtest|möchten|darf|darfst|dürfen|soll|sollst|sollen)\b.*\b[a-zäöüß]+en[.!?]$',
    'subordinate clause: verb to the end (weil, dass, wenn, ob …)': r'\b(?:weil|dass|wenn|ob|obwohl|als|damit|bevor|nachdem|während)\b[^,.!?]*\b[a-zäöüß]+[.!?]$',
    'inversion: sentence starts with time/place, then the verb': r'^(?:Heute|Morgen|Gestern|Jetzt|Dann|Danach|Am|Im|Um|Nach|Vor|Seit|Leider|Zum|Hier|Dort|Abends|Morgens|Montags)\b',
    'question with verb first (Kommst du …?)': r'^[A-ZÄÖÜ][a-zäöüß]+(?:st|t|en)\s+(?:du|ihr|Sie|wir|er|sie|es)\b.*\?$',
    'negation with nicht / kein': r'\b(?:nicht|kein|keine|keinen|keinem|keiner)\b',
    'reflexive pronoun (mich, dich, sich …)': r'\b(?:mich|dich|sich|uns|euch)\b',
    'zu + infinitive': r'\bzu\s+[a-zäöüß]+en[.!?,]',
    'comparative / superlative': r'\b(?:[a-zäöüß]+er\s+als|am\s+[a-zäöüß]+sten)\b',
}
material = {}
for name, pat in PATTERNS.items():
    rx = re.compile(pat)
    hits = [(s, src) for s, src, _ in sentences if rx.search(s)]
    material[name] = {'sentences': len(hits), 'app_seed': sum(1 for _, src in hits if src == 'app'),
                      'examples': [s for s, _ in hits[:3]]}

# separable verbs: tagged in the curriculum, prefix stands alone at the end of the example
sep = [e for e in curr if (e.get('grammar') or {}).get('separable') is True and e['partOfSpeech'] == 'verb']
split = [e for e in sep if re.search(r'\b(an|auf|aus|ein|mit|vor|zu|ab|zurück|weg|los|fest|teil|statt|fern|nach|her|hin|um|durch)[.!?]$', e['example']['german'])]
material['separable verb split (prefix at the end)'] = {'sentences': len(split), 'tagged_separable_verbs': len(sep),
                                                       'examples': [e['example']['german'] for e in split[:3]]}
# verbs with forms: conjugation drill material
forms = [e for e in curr if e['partOfSpeech'] == 'verb' and ((e.get('grammar') or {}).get('forms') or {}).get('present3sg')]
material['verbs with stored forms (3sg, preterite, perfect)'] = {'sentences': len(forms)}
plural = [e for e in curr if e['partOfSpeech'] == 'noun' and e.get('plural') not in (None, '', '∅')]
material['nouns with a plural (plural drill)'] = {'sentences': len(plural)}

out = {'gender_cues': gender, 'exercise_material': material, 'sentences_scanned': len(sentences)}
Path(__file__).with_name('content_analysis.json').write_text(json.dumps(out, ensure_ascii=False, indent=1, default=dict), encoding='utf-8')

print(f"nouns: {gender['nouns']}  articles: {dict(gender['article_distribution'])}")
print(f"covered by any ending rule: {gender['covered_by_some_rule_pct']} %   by rules ≥90 % reliable: {gender['covered_by_rules_90pct_reliable']} %")
for r in gender['rules']:
    if r['nouns']:
        print(f"  {r['ending']:>7} → {r['article']}: {r['nouns']:>4} nouns, {r['accuracy']:>5} % correct   exceptions: {', '.join(r['exceptions_sample'])}")
print(f'\nsentences scanned: {len(sentences)}')
for k, v in material.items():
    print(f"  {v['sentences']:>5}  {k}" + (f"   (app seed: {v['app_seed']})" if 'app_seed' in v else ''))
