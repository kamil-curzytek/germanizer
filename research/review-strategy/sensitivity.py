"""Robustness of the simulate.py ranking to its assumptions, and days needed to reach milestones.
Run: python sensitivity.py  (writes sensitivity.json)"""
import json, math, random, statistics, sys
from pathlib import Path
import simulate as sim

sys.stdout.reconfigure(encoding='utf-8')
PICK = {s.name: s for s in sim.STRATEGIES}
NAMES = ['A current', 'B + weekly cumulative quiz', 'C + 2 random strong words/day', 'G = D + E + F',
         'H FSRS scheduler, 90 % target', 'I FSRS scheduler, 85 % target']


def mean_run(strat, **kw):
    runs = [sim.run(strat, seed=s, **kw) for s in range(1, 4)]
    return {k: round(statistics.mean(r[k] for r in runs), 1) for k in ('words_introduced', 'mean_recall_end', 'known_words_end', 'known_per_100_answers', 'answers_total')}


def with_assumptions(spread, mc_gain, recog):
    """Re-run with a different word-difficulty spread / multiple-choice gain / recognition ease."""
    old = (sim.FORMAT_GAIN['mc'], sim.RECOGNITION_BOOST)
    sim.FORMAT_GAIN['mc'], sim.RECOGNITION_BOOST = mc_gain, recog
    orig_gauss = random.Random.gauss
    random.Random.gauss = lambda self, mu, sigma: orig_gauss(self, mu, spread)
    try:
        return {n: mean_run(PICK[n]) for n in NAMES}
    finally:
        random.Random.gauss = orig_gauss
        sim.FORMAT_GAIN['mc'], sim.RECOGNITION_BOOST = old


def days_to(strat, words, target=10, limit=1500):
    """First day on which `words` words have been introduced (single long run)."""
    lo, hi = 1, limit
    if sim.run(strat, days=hi, target=target, seed=1)['words_introduced'] < words:
        return None
    while lo < hi:
        mid = (lo + hi) // 2
        if sim.run(strat, days=mid, target=target, seed=1)['words_introduced'] >= words:
            hi = mid
        else:
            lo = mid + 1
    return lo


def main():
    out = {'sensitivity': {}, 'milestones': {}}
    grid = {
        'baseline (spread 0.6, MC gain 0.6, recognition 0.5)': (0.6, 0.6, 0.5),
        'words more alike (spread 0.3)': (0.3, 0.6, 0.5),
        'words very unequal (spread 1.0)': (1.0, 0.6, 0.5),
        'multiple choice nearly as good as recall (0.9)': (0.6, 0.9, 0.5),
        'multiple choice weak (0.3), recognition easy (0.3)': (0.6, 0.3, 0.3),
    }
    for label, args in grid.items():
        res = with_assumptions(*args)
        out['sensitivity'][label] = res
        print(f'\n## {label}')
        for n, r in res.items():
            print(f"  {n:34} words {r['words_introduced']:>6}  recall {r['mean_recall_end']:>5}%  known {r['known_words_end']:>6}  known/100 answers {r['known_per_100_answers']:>5}")
    print('\n## days to reach a vocabulary milestone (words introduced)')
    for target in (10, 20):
        for n in ('A current', 'G = D + E + F', 'H FSRS scheduler, 90 % target', 'I FSRS scheduler, 85 % target'):
            row = {m: days_to(PICK[n], m, target=target) for m in (761, 1839)}
            out['milestones'][f'{n} @ {target}/day'] = row
            print(f'  {target}/day  {n:34} core 761: {row[761]} days   A2 1,839: {row[1839]} days')
    Path(__file__).with_name('sensitivity.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
