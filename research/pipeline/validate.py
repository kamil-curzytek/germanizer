"""Curriculum validation (writes research/validation.json):
1. Goethe cross-check  – share of Goethe A1/A2/B1 headwords (Germany-standard, non-numeral) taught by tier <=1/2/3.
2. Inflation check     – multi-word entries whose content words all have their own entries and that carry
                         neither a why= reason nor the 'pattern' tag (candidates for deletion).
3. Scenario check      – must-know items per A1–B2 scenario (validation/scenarios.json) found at the right tier.
"""
import glob, json, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).parent))
from tier_coverage import item_lemmas, exposure_lemmas, _keys  # noqa: E402

FUNCTION = {'sich', 'etwas', 'jemand', 'jemanden', 'jemandem', 'der', 'die', 'das', 'den', 'dem', 'des', 'ein',
            'eine', 'einen', 'einem', 'einer', 'an', 'auf', 'aus', 'bei', 'für', 'gegen', 'in', 'im', 'ins', 'mit',
            'nach', 'über', 'um', 'unter', 'von', 'vom', 'vor', 'zu', 'zum', 'zur', 'es', 'ich', 'du', 'sie', 'er',
            'wir', 'ihr', 'mir', 'dir', 'mich', 'dich', 'uns', 'ist', 'bin', 'und', 'oder', 'nicht', 'kein', 'keine'}
TIER_FOR = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4}


def norm_phrase(g):
    return re.sub(r'\s+', ' ', g.lower().replace('…', '...').strip(' ?!.,…'))


def known_by_tier(data):
    """tier -> set of lemma keys taught up to that tier (strict + exposure + listed forms)."""
    out, acc = {}, set()
    for t in (1, 2, 3, 4):
        for e in data:
            if e['priorityTier'] == t:
                acc |= item_lemmas(e) | exposure_lemmas(e)
                for f in ((e.get('grammar') or {}).get('forms') or {}).values():
                    acc |= _keys(f.split()[0]) if f else set()
        out[t] = set(acc)
    return out


def goethe_check(known):
    goethe = json.loads((ROOT / 'sources' / 'goethe_headwords.json').read_text(encoding='utf-8'))
    res = {}
    for lvl, tier in (('A1', 1), ('A2', 2), ('B1', 3)):
        words = [w for w, m in goethe[lvl].items()
                 if not m.get('regional') and m.get('pos') != 'numeral' and len(w) > 3 and not w.endswith('-')]
        hit_tier = [w for w in words if _keys(w) & known[tier]]
        hit_any = [w for w in words if _keys(w) & known[4]]
        missing = sorted(w for w in words if not (_keys(w) & known[4]))
        res[lvl] = {'headwords': len(words), f'covered_by_tier<={tier}': round(100 * len(hit_tier) / len(words), 1),
                    'covered_anywhere': round(100 * len(hit_any) / len(words), 1),
                    'missing_count': len(missing), 'missing_sample': missing[:80]}
    return res


def inflation_check(data):
    singles = set()
    for e in data:
        if ' ' not in e['german'].strip():
            singles |= item_lemmas(e)
    flagged = []
    for f in sorted(glob.glob(str(ROOT / 'authoring' / '*.psv'))):
        for i, line in enumerate(open(f, encoding='utf-8'), 1):
            if line.startswith('#') or not line.strip():
                continue
            c = line.rstrip('\n').split('|')
            g = c[0]
            if ' ' not in g.strip() or ',' in g:
                continue
            gram = c[13].lower()
            # exempt: curator reason, pattern frames, valency constructions (they teach the governed preposition/case)
            if 'why=' in line or 'pattern' in gram or 'prep:' in gram or 'refl' in gram or c[0].startswith('sich '):
                continue
            content = [w for w in re.findall(r"[A-Za-zÄÖÜäöüß]+", g) if w.lower() not in FUNCTION]
            if content and all(_keys(w) & singles for w in content):
                flagged.append({'where': f'{Path(f).name}:{i}', 'german': g,
                                'kind': 'pragmatic routine' if c[1] in ('f', 'p') else 'construction'})
    return flagged


LEVELS = ['A1', 'A2', 'B1', 'B2']


def known_by_cefr(data):
    out, acc = {}, set()
    for i, lvl in enumerate(LEVELS, 1):
        for e in data:
            if e['cefr'] == lvl:
                acc |= item_lemmas(e) | exposure_lemmas(e)
        out[i] = set(acc)
    return out


def scenario_check(data, known, name='scenarios.json'):
    sc = json.loads((ROOT / 'validation' / name).read_text(encoding='utf-8'))
    heads = {}
    for e in data:
        heads.setdefault(norm_phrase(e['german']), e['priorityTier'])
    out = []
    for s in sc:
        tier = TIER_FOR[s['level']]
        late, missing = [], []
        for item in s['items']:
            k = norm_phrase(item)
            if ' ' in k:  # multi-word must-know: exact entry
                t = heads.get(k)
                ok_any, ok_tier = t is not None, t is not None and t <= tier
            else:
                ok_any, ok_tier = bool(_keys(item) & known[4]), bool(_keys(item) & known[tier])
            if not ok_any:
                missing.append(item)
            elif not ok_tier:
                late.append(item)
        n = len(s['items'])
        out.append({'scenario': s['name'], 'level': s['level'], 'items': n,
                    'available_in_time': round(100 * (n - len(late) - len(missing)) / n, 1),
                    'too_late': late, 'missing': missing})
    return out


def main():
    data = json.loads((ROOT.parent / 'data' / 'german-all.json').read_text(encoding='utf-8'))
    known = known_by_tier(data)
    report = {'goethe': goethe_check(known), 'inflation_flags': inflation_check(data),
              'scenarios': scenario_check(data, known)}
    held = scenario_check(data, known, 'scenarios-heldout.json')
    held_cefr = scenario_check(data, known_by_cefr(data), 'scenarios-heldout.json')
    report['heldout_summary_by_cefr_label'] = {lvl: round(sum(x['available_in_time'] for x in held_cefr if x['level'] == lvl) /
                                                          max(1, sum(1 for x in held_cefr if x['level'] == lvl)), 1) for lvl in LEVELS}
    report['heldout_scenarios'] = held
    report['heldout_summary'] = {lvl: round(sum(x['available_in_time'] for x in held if x['level'] == lvl) /
                                            max(1, sum(1 for x in held if x['level'] == lvl)), 1) for lvl in ('A1', 'A2', 'B1', 'B2')}
    sc = report['scenarios']
    report['scenario_summary'] = {
        lvl: round(sum(x['available_in_time'] for x in sc if x['level'] == lvl) / max(1, sum(1 for x in sc if x['level'] == lvl)), 1)
        for lvl in ('A1', 'A2', 'B1', 'B2')}
    for lvl, r in report['goethe'].items():
        print('goethe', lvl, {k: v for k, v in r.items() if k != 'missing_sample'})
    fl = report['inflation_flags']
    report['inflation_summary'] = {'pragmatic_routines_without_reason': sum(1 for x in fl if x['kind'] == 'pragmatic routine'),
                                   'constructions_without_reason': [x['german'] for x in fl if x['kind'] == 'construction']}
    print('inflation:', report['inflation_summary'])
    print('scenario summary:', report['scenario_summary'])
    print('HELD-OUT summary:', report['heldout_summary'])
    print('HELD-OUT by CEFR label:', report['heldout_summary_by_cefr_label'])
    for x in held:
        if x['too_late'] or x['missing']:
            print(f"  heldout {x['level']} {x['scenario']}: late={x['too_late']} missing={x['missing']}")
    (ROOT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    for x in sc:
        if x['too_late'] or x['missing']:
            print(f"  {x['level']} {x['scenario']}: late={x['too_late']} missing={x['missing']}")


if __name__ == '__main__':
    main()
