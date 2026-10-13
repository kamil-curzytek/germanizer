"""Compare review strategies for Lernbrot with a simulated learner.

Memory model: FSRS-6 (open-spaced-repetition) with its published default parameters, used as the
"true" memory of a simulated learner. Each word gets a random difficulty multiplier, so some words
are much harder than the model's average. The app's scheduler never sees the true memory state;
it only sees right/wrong answers, as in production.

What is simulated (mirrors the app):
- daily target N words; session = due reviews (wrong-first, most overdue) + new words, with the
  adaptive minimum-new rule of migration 0005 (20 % / 10 % / 0 % new by backlog)
- day 1 of a word: study card (first exposure) + same-day quiz
- quiz format by streak: streak 0-1 multiple choice (4 options), 2-3 typed recall, 4+ typed
- multiple choice can be passed by recognition or guessing without recall; that counts as
  "correct" for the scheduler but strengthens memory less (assumption, see FORMAT_GAIN)
- optional: the learner skips some days entirely, or abandons a session after the cards

Outputs per strategy: words introduced, mean true recall probability of all introduced words
at the end, share "forgotten" (R < 0.7), total quiz answers, answers per day.
Run: python simulate.py   (seeded; ~1 min)
"""
import json, math, random, statistics, sys
from dataclasses import dataclass, field
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# FSRS-6 default parameters (awesome-fsrs wiki, "The Algorithm")
W = [0.212, 1.2931, 2.3065, 8.2956, 6.4133, 0.8334, 3.0194, 0.001, 1.8722, 0.1666, 0.796,
     1.4835, 0.0614, 0.2629, 1.6483, 0.6014, 1.8729, 0.5425, 0.0912, 0.0658, 0.1542]
DECAY = W[20]
FACTOR = 0.9 ** (-1 / DECAY) - 1

# Assumptions (stated in the report): typed recall = full FSRS gain; recognition/MC success = 60 %
# of that gain; a lucky guess (recall failed) = treated by memory as a failed retrieval with feedback.
FORMAT_GAIN = {'mc': 0.6, 'typed': 1.0}
MC_OPTIONS = 4
RECOGNITION_BOOST = 0.5   # recognition succeeds on R**0.5: easier than free recall


def retrievability(t, s):
    return (1 + FACTOR * t / s) ** (-DECAY)


def d0(g):
    return min(10, max(1, W[4] - math.exp(W[5] * (g - 1)) + 1))


def next_d(d, g):
    dd = -W[6] * (g - 3)
    d2 = d + dd * (10 - d) / 9
    return min(10, max(1, W[7] * d0(4) + (1 - W[7]) * d2))


def s_recall(d, s, r, g=3):
    hard = W[15] if g == 2 else 1
    easy = W[16] if g == 4 else 1
    return s * (math.exp(W[8]) * (11 - d) * s ** (-W[9]) * (math.exp(W[10] * (1 - r)) - 1) * hard * easy + 1)


def s_forget(d, s, r):
    sf = W[11] * d ** (-W[12]) * ((s + 1) ** W[13] - 1) * math.exp(W[14] * (1 - r))
    return min(sf, s / math.exp(W[17] * W[18]))


def s_same_day(s, g):
    return s * math.exp(W[17] * (g - 3 + W[18])) * s ** (-W[19])


@dataclass
class Memory:            # true state (hidden from the app)
    s: float
    d: float
    last: int
    hardness: float      # >1 = harder word: stability effectively divided by this

    def r(self, day):
        return retrievability(max(0, day - self.last), self.s / self.hardness)


@dataclass
class Sched:             # what the app stores (vocabulary_progress)
    streak: int = 0
    due: int = 0
    correct: int = 0
    incorrect: int = 0
    interval: int = 0
    last_seen: int = 0
    est_s: float = 0.0                       # the app's own FSRS estimate (default parameters, no hidden hardness)
    est_d: float = 0.0


@dataclass
class Strategy:
    name: str
    intervals: list = field(default_factory=lambda: [1, 2, 4, 7, 14, 30, 60])
    growth_after_last: float = 1.0          # >1: keep growing beyond the last interval
    weekly_quiz: bool = False               # weekly cumulative quiz on words studied in the last 7 days
    weekly_counts: bool = True              # weekly answers update the schedule
    resurface_per_day: int = 0              # random "strong" words added to each session
    overdue_bonus: bool = False             # correct after a late review: interval from actual gap
    typed_for_promotion: bool = False       # streak 2+ requires typed recall; MC success only re-schedules short
    carry_unquizzed: bool = False           # new words seen on cards but not quizzed come back first next day
    fsrs_retention: float = 0.0             # >0: interval = FSRS-estimated time until recall falls to this
    note: str = ''


def interval_for(strat, streak):
    iv = strat.intervals
    if streak <= len(iv):
        return iv[streak - 1]
    return round(iv[-1] * strat.growth_after_last ** (streak - len(iv)))


def answer(mem, day, fmt, rng):
    """Returns (recorded_correct, true_recall) and updates true memory."""
    r = mem.r(day)
    recalled = rng.random() < r
    if fmt == 'mc':
        recognised = recalled or rng.random() < (r ** RECOGNITION_BOOST - r) / max(1e-9, 1 - r)
        correct = recognised or rng.random() < 1 / MC_OPTIONS
    else:
        correct = recalled
    same_day = day == mem.last
    if same_day:
        g = 3 if recalled else 1
        mem.s = s_same_day(mem.s, g)
    elif recalled or (fmt == 'mc' and correct):
        gain = FORMAT_GAIN[fmt] if recalled else FORMAT_GAIN['mc'] * 0.5
        new_s = s_recall(mem.d, mem.s, r, 3)
        mem.s = mem.s + gain * (new_s - mem.s)
        mem.d = next_d(mem.d, 3)
    else:
        mem.s = s_forget(mem.d, mem.s, r)
        mem.d = next_d(mem.d, 1)
    mem.last = day
    return correct, recalled


def fmt_for(strat, streak):
    if strat.typed_for_promotion:
        return 'mc' if streak == 0 else 'typed'   # recall is required from the second success on
    return 'mc' if streak <= 1 else 'typed'


def fsrs_interval(stability, retention):
    return max(1, round(stability / FACTOR * (retention ** (-1 / DECAY) - 1)))


def update_sched(strat, sc, correct, fmt, day):
    if strat.fsrs_retention:
        if sc.est_s == 0:
            sc.est_s, sc.est_d = (W[2], d0(3)) if correct else (W[0], d0(1))
        elif day == sc.last_seen:
            sc.est_s = s_same_day(sc.est_s, 3 if correct else 1)
        else:
            r = retrievability(day - sc.last_seen, sc.est_s)
            if correct:
                sc.est_s, sc.est_d = s_recall(sc.est_d, sc.est_s, r, 3), next_d(sc.est_d, 3)
            else:
                sc.est_s, sc.est_d = s_forget(sc.est_d, sc.est_s, r), next_d(sc.est_d, 1)
        if correct:
            sc.streak += 1; sc.correct += 1
        else:
            sc.streak //= 2; sc.incorrect += 1
        sc.interval = 1 if not correct else fsrs_interval(sc.est_s, strat.fsrs_retention)
        sc.due = day + sc.interval
        sc.last_seen = day
        return
    if correct:
        if strat.typed_for_promotion and fmt == 'mc' and sc.streak >= 1:
            sc.due = day + 1                     # recognised but not recalled: check again soon, typed
            sc.correct += 1
        else:
            sc.streak += 1
            iv = interval_for(strat, sc.streak)
            if strat.overdue_bonus and sc.interval and day - sc.last_seen > sc.interval:
                iv = max(iv, round((day - sc.last_seen) * 1.5))
            sc.interval = iv
            sc.due = day + iv
            sc.correct += 1
    else:
        sc.streak = sc.streak // 2
        sc.interval = 1
        sc.due = day + 1
        sc.incorrect += 1
    sc.last_seen = day


def run(strat, days=365, target=10, n_words=4500, seed=1, skip_rate=0.0, abandon_rate=0.0):
    rng = random.Random(seed)
    hardness = [math.exp(rng.gauss(0, 0.6)) for _ in range(n_words)]   # word difficulty spread
    mem, sch = {}, {}
    next_new = 0
    pending_new = []          # seen on cards, never quizzed
    answers = 0
    recent = {}               # word -> last day studied (for weekly quiz)
    for day in range(days):
        if rng.random() < skip_rate:
            continue
        due = sorted((w for w, s in sch.items() if s.due <= day),
                     key=lambda w: (not (sch[w].incorrect > sch[w].correct), sch[w].due))
        n_due = len(due)
        min_new = math.ceil(0.2 * target) if n_due <= target else (math.ceil(0.1 * target) if n_due < 2 * target else 0)
        reviews = due[:target - min_new]
        extra = []
        if strat.resurface_per_day:
            pool = [w for w, s in sch.items() if s.streak >= 4 and w not in reviews and s.due > day]
            extra = rng.sample(pool, min(strat.resurface_per_day, len(pool)))
        new = list(pending_new[:target - len(reviews)])
        while len(reviews) + len(new) < target and next_new < n_words:
            new.append(next_new)
            next_new += 1
        abandoned = rng.random() < abandon_rate
        # study cards: first exposure of brand-new words
        for w in new:
            if w not in mem:
                mem[w] = Memory(s=W[2], d=d0(3), last=day, hardness=hardness[w])
            else:
                mem[w].r(day)  # re-exposure of a carried word
                mem[w].s = max(mem[w].s, s_same_day(mem[w].s, 3)) if mem[w].last == day else s_recall(mem[w].d, mem[w].s, mem[w].r(day))
                mem[w].last = day
        if abandoned:
            # app today: unquizzed new words are forgotten by the app and become "new" again later
            # the app has no progress row for them, so the selection query picks the same words again
            # at the next new-word slot (ordering by frequency rank); only the exposure is untracked
            pending_new = [w for w in new if w not in sch] + [w for w in pending_new if w not in new]
            continue
        pending_new = [w for w in pending_new if w not in new]
        for w in new + reviews + extra:
            sc = sch.setdefault(w, Sched())
            fmt = fmt_for(strat, sc.streak)
            correct, _ = answer(mem[w], day, fmt, rng)
            update_sched(strat, sc, correct, fmt, day)
            answers += 1
            recent[w] = day
        if strat.weekly_quiz and day % 7 == 6:
            week = [w for w, d in recent.items() if day - 6 <= d < day]
            for w in week:
                sc = sch[w]
                fmt = 'typed'
                correct, _ = answer(mem[w], day, fmt, rng)
                if strat.weekly_counts:
                    if not correct:
                        update_sched(strat, sc, False, fmt, day)
                answers += 1
    end = days
    rs = [mem[w].r(end) for w in sch]
    rs_later = [mem[w].r(end + 90) for w in sch]   # 3 months without any study
    return {
        'strategy': strat.name, 'note': strat.note,
        'words_introduced': len(sch),
        'mean_recall_end': round(100 * statistics.mean(rs), 1),
        'forgotten_share_end': round(100 * sum(r < 0.7 for r in rs) / len(rs), 1),
        'mean_recall_after_90d_break': round(100 * statistics.mean(rs_later), 1),
        'answers_total': answers,
        'answers_per_study_day': round(answers / max(1, days * (1 - skip_rate)), 1),
        'known_words_end': round(sum(rs)),
        'known_per_100_answers': round(100 * sum(rs) / answers, 1),
    }


STRATEGIES = [
    Strategy('A current', note='fixed 1-2-4-7-14-30-60, cap 60, any correct promotes'),
    Strategy('B + weekly cumulative quiz', weekly_quiz=True, note='typed quiz on all words studied that week; wrong answers reschedule'),
    Strategy('C + 2 random strong words/day', resurface_per_day=2, note='random resurfacing of mastered words'),
    Strategy('D intervals keep growing', growth_after_last=2.0, note='after 60: 120, 240 … days'),
    Strategy('E typed recall from 2nd success', typed_for_promotion=True, note='multiple choice only for brand-new words'),
    Strategy('F overdue-aware', overdue_bonus=True, note='late but correct: next gap from the real gap'),
    Strategy('G = D + E + F', growth_after_last=2.0, typed_for_promotion=True, overdue_bonus=True,
             note='combined fixed-interval improvements'),
    Strategy('H FSRS scheduler, 90 % target', typed_for_promotion=True, fsrs_retention=0.90,
             note='interval = estimated time until recall drops to 90 %'),
    Strategy('I FSRS scheduler, 85 % target', typed_for_promotion=True, fsrs_retention=0.85,
             note='same, accepts slightly more forgetting'),
    Strategy('J = H + weekly quiz', typed_for_promotion=True, fsrs_retention=0.90, weekly_quiz=True,
             note='FSRS 90 % plus weekly cumulative quiz'),
]


def main():
    out = {}
    scenarios = {
        '10 words/day, every day': dict(),
        '20 words/day, every day': dict(target=20),
        '10 words/day, skips 20 % of days': dict(skip_rate=0.2),
        '10 words/day, abandons 15 % of sessions after the cards': dict(abandon_rate=0.15),
    }
    for sc_name, kw in scenarios.items():
        rows = []
        for st in STRATEGIES:
            runs = [run(st, seed=s, **kw) for s in range(1, 6)]
            agg = {k: (round(statistics.mean(r[k] for r in runs), 1) if isinstance(runs[0][k], (int, float)) else runs[0][k])
                   for k in runs[0]}
            rows.append(agg)
        out[sc_name] = rows
        print(f'\n## {sc_name}')
        print(f"{'strategy':34} {'words':>6} {'recall%':>8} {'forgot%':>8} {'+90d%':>6} {'answers':>8} {'/day':>5} {'known':>6} {'known/100ans':>12}")
        for r in rows:
            print(f"{r['strategy']:34} {r['words_introduced']:>6} {r['mean_recall_end']:>8} {r['forgotten_share_end']:>8} "
                  f"{r['mean_recall_after_90d_break']:>6} {r['answers_total']:>8} {r['answers_per_study_day']:>5} "
                  f"{r['known_words_end']:>6} {r['known_per_100_answers']:>12}")
    Path(__file__).with_name('results.json').write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding='utf-8')


if __name__ == '__main__':
    main()
