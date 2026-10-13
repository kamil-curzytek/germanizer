# Review strategy: research and plan

**Questions:** How should repetitions work? Should there be a big weekly quiz? What happens to words that weren't answered? Should random old words come back in later weeks so they aren't forgotten?

**Short answers**

| Question | Recommendation |
|---|---|
| Big weekly quiz on everything from the last 7 days? | **No, not as a fixed big test.** In simulation it costs ~65 % more answers for ~2 % more words remembered. Instead, an optional **short weekly review** (≈15 items) that picks the words you're most likely to be forgetting. |
| Words that were not answered (lesson left unfinished, day skipped)? | Mostly handled already: unanswered review words stay due, and unquizzed new words are picked again first. Two fixes: record that the card was seen, and stop treating a late review like an on-time one. |
| Random old words in later weeks? | **Not random. Scheduled.** Random resurfacing was less efficient per answer than any of the scheduler changes. The real fix is to remove the **60-day cap**, so a known word comes back at growing gaps (2, 4, 8 months…), timed to when it's likely to be fading. |
| The biggest finding (not asked) | The fixed schedule over-reviews. With 10 words/day, a learner **never reaches the 761-word Core**, because every known word costs ~6 reviews a year forever. A memory-model scheduler (FSRS) at the same effort lets a learner know **~40–75 % more words** after a year. |

Everything below is reproducible: `python simulate.py`, `python sensitivity.py` (results in `results.txt`, `results.json`, `sensitivity.json`, `new_plus_due.json`).

---

## 1. How the app works today

| Behaviour | Where | Consequence |
|---|---|---|
| One quiz answer per word per day, right/wrong | `submit_quiz`, `src/lib/spacedRepetition` | No "hard/easy" signal |
| Fixed gaps 1, 2, 4, 7, 14, 30, 60 days, then **60 forever** | `config.ts`, `intervalForStreak` | A known word costs 6 reviews/year indefinitely |
| A correct multiple-choice answer counts the same as typed recall | quiz levels 1–2 are multiple choice | Recognising or guessing (25 % chance) advances the word as much as truly remembering it |
| A late review (e.g. after a holiday) answered correctly gets the normal next gap | `applyAnswer` uses the streak only | Memory that survived a long gap isn't credited, so the extra reviews are wasted |
| Wrong → back tomorrow, streak halved | `applyAnswer` | Reasonable |
| "10 words/day" = 10 quiz answers including reviews; new words shrink when reviews pile up | migration 0005 | Protects the learner from overload, but caps how many words can ever be kept |
| Lesson left after the cards: new words have no progress row and are re-offered first; review words stay due | `create_daily_session_for` | Works, but the card exposure isn't recorded |
| No weekly quiz, no resurfacing, no retry of missed words within the quiz | — | — |

## 2. What the research says

| Finding | Evidence | Implication for Lernbrot |
|---|---|---|
| **Spacing beats massing, and the best gap grows with how long you want to remember.** It falls from ~20–40 % of the retention interval (1 week) to ~5–10 % (1 year). Too short a gap hurts more than too long | Cepeda et al. 2008, >1,350 learners | Gaps must keep growing for long-term retention; a fixed 60-day ceiling is too short for remembering for years |
| **Long gaps for maintaining foreign vocabulary**: 13 sessions 56 days apart ≈ 26 sessions 14 days apart, after up to 5 years | Bahrick et al. 1993, 9-year study | Half the reviews at wider spacing keep the same knowledge, so remove the cap |
| **Expanding vs. equal spacing** makes little difference for L2 vocabulary; spacing itself matters most | Nakata 2015 (128 learners); Karpicke & Roediger 2007 | Don't over-engineer the shape. Use a model that times reviews to the forgetting curve |
| **Retrieval, not re-study, builds memory.** Dropping items from *testing* once known hurt recall a week later; dropping them from study didn't | Karpicke & Roediger 2008, *Science* (Swahili–English) | Keep testing known words (spaced). Studying cards alone doesn't count as a review |
| **Harder retrieval with feedback (short answer) beats multiple choice** for later retention | Kang, McDermott & Roediger 2007 | Typed recall should be needed to "promote" a word. Multiple choice is for first contact |
| For L2 flashcards, recall formats help spelling/form; recognition is easier during learning | Nakata 2013 (thesis) | Mix formats, but don't let a multiple-choice success move a word as far as recall |
| **Successive relearning**: get each item right during practice, then relearn it at spaced sessions. 1-week recall rose from ~20 % to ~80 % | Rawson & Dunlosky (series of studies) | Re-ask missed words at the end of the same quiz until correct (not scored) |
| **Cumulative tests** improve retention, partly because learners *expect* to be retested | Szpunar, McDermott & Roediger 2007; classroom studies | A weekly review can help motivation, but the memory effect comes from retrieval at good spacing, which the scheduler already provides |
| **Personalised, model-based review** beat one-size-fits-all spacing by 10 % (and massed study by 16.5 %) over a semester, with ~30 min/week | Lindsey, Shroyer, Pashler & Mozer 2014 (school foreign-language course) | Use a memory model to pick *which* words to review |
| **Memory-model schedulers** predict recall better than fixed rules. FSRS is reported to need 20–30 % fewer reviews than SM-2 for the same retention; Duolingo's half-life regression cut prediction error by 45 % and raised engagement 12 % | FSRS (open-spaced-repetition, fitted on large Anki datasets); Settles & Meeder 2016 (13 M Duolingo traces) | Replace the fixed gaps with FSRS, which is open-source and has a TypeScript implementation |

## 3. Simulation

**Set-up** (`simulate.py`):
- A simulated learner whose true memory follows **FSRS-6 with its published default parameters**. Each word also gets a random difficulty, which the app can't see.
- The app sees only right/wrong answers, exactly as in production.
- Simulated: card + same-day quiz for new words; multiple choice at streaks 0–1, then typed; the adaptive new-word rule; 1 year; 3–5 seeds per cell.
- Assumptions: multiple-choice success = 60 % of a recall's memory gain; recognition is easier than recall; 25 % guessing chance.

### 3a. One year, 10 words/day, every day

| Strategy | Words met | Recall at end | Recall after a further 3-month break | Answers | **Known words per 100 answers** |
|---|---:|---:|---:|---:|---:|
| A today (fixed, cap 60) | 355 | 97.9 % | 92.7 % | 3,650 | 9.5 |
| B + weekly cumulative quiz | 364 | 98.4 % | 93.5 % | 6,023 | **6.0** |
| C + 2 random strong words/day | 393 | 97.9 % | 92.7 % | 4,364 | 8.8 |
| D gaps keep growing after 60 days | 399 | 96.9 % | 91.2 % | 3,650 | 10.6 |
| E typed recall needed from 2nd success | 350 | 97.7 % | 92.3 % | 3,650 | 9.4 |
| F late-but-correct credited | 378 | 97.6 % | 92.1 % | 3,650 | 10.1 |
| G = D + E + F | 397 | 96.8 % | 91.1 % | 3,650 | 10.5 |
| **H FSRS, 90 % target** | **528** | 95.0 % | 88.5 % | 3,650 | **13.8** |
| I FSRS, 85 % target | 649 | 92.6 % | 85.5 % | 3,650 | 16.4 |
| J = H + weekly quiz | 566 | 96.0 % | 90.0 % | 5,969 | 9.1 |

The same ranking holds at 20 words/day, when the learner skips 20 % of days, and when 15 % of lessons are abandoned after the cards (`results.txt`).

### 3b. Is the ranking an artefact of my assumptions? (`sensitivity.py`)

FSRS ranks first and the weekly quiz last in every variant:
- word difficulty spread 0.3 / 0.6 / 1.0;
- multiple-choice gain 0.3–0.9;
- recognition ease 0.3–0.5.

FSRS-90 % gives +42–47 % more known words than today in every case (FSRS-85 %: +71–82 %).

### 3c. How long to reach the curriculum milestones (words met)

| Scheduler | 10/day → Core (761) | 20/day → Core | 20/day → A2 (1,839) |
|---|---:|---:|---:|
| Today | **never** (still < 761 after 1,500 days) | 403 days | never |
| G (fixed, improved) | 845 days | 344 days | 1,109 days |
| FSRS 90 % | 648 days | 205 days | 806 days |
| FSRS 85 % | 465 days | 151 days | 613 days |

### 3d. If "words per day" meant *new* words, plus all reviews that are due (Anki-style)

| New words/day | Scheduler | Answers/day, month 1 | Month 6 | Month 12 |
|---:|---|---:|---:|---:|
| 5 | Today | 22 | 48 | 64 |
| 5 | FSRS 90 % | 15 | 31 | 43 |
| 10 | Today | 44 | 93 | 132 |
| 10 | FSRS 90 % | 29 | 60 | 87 |

So there are two honest options. **Fix the daily effort** (today's model): progress then depends on how efficient the scheduler is. **Fix the new words**: the effort then grows over time. FSRS makes either option about a third cheaper.

### Caveats on the simulation
- **It favours FSRS by construction.** The simulated learner's memory *is* an FSRS model, and the FSRS scheduler uses the same formulas (though not the hidden per-word difficulty). Real-world gains will be smaller. The independent benchmark figure of **20–30 % fewer reviews** is the safer expectation. The *direction* (cap removal and model-based timing win; a fixed weekly quiz and random resurfacing lose on efficiency) agrees with the human studies in §2.
- Not modelled: motivation (streaks, feeling of progress, which may favour a weekly review), within-quiz relearning, and exposure outside the app.
- "Recall at end" is the model's predicted probability, not a measured test score.

## 4. Recommended design

### 4.1 Scheduler: FSRS instead of fixed gaps
- **FSRS-6 with default parameters**, desired retention **90 %** (configurable later; 85 % = more words, a little more forgetting).
- **Ratings from what the app already knows:**

  | Answer | Rating |
  |---|---|
  | Wrong | *Again* |
  | Correct multiple choice (recognition) | *Hard* |
  | Correct typed answer | *Good* |
  | Correct typed and fast (optional, later) | *Easy* |

- **No cap:** gaps grow as long as the word keeps being recalled.
- **Late reviews handled naturally:** FSRS uses the real elapsed time, so a correct answer after a holiday earns a long next gap. Missed days don't count as failures.
- **Selection order for reviews:** lowest predicted recall first, replacing "most overdue first". Keep "often wrong" words near the top.

### 4.2 Question format
- Multiple choice only for brand-new words and right after a lapse.
- From the second success on, the word needs **typed recall** (German → English typed, English → German typed, gap fill), plus article/plural for nouns once strong.

### 4.3 Within-quiz relearning (successive relearning)
- Words answered wrong come back at the **end of the same quiz** until answered correctly (max 2 retries).
- Only the first answer is scored and scheduled.

### 4.4 Unanswered words
- **Unfinished lesson:** the study position is already saved. Add a `seen_at` marker on new words viewed on cards, so they come back first next time and can be quizzed without re-teaching (today they look brand-new).
- **Skipped days:** reviews stay due and are ordered by predicted recall. No penalty, no catch-up flood: the adaptive new-word rule stays.
- **Review words shown but not answered:** stay due (as today).

### 4.5 Weekly review (optional, motivational)
- Offered once a week, e.g. "Wochenrückblick": **~15 items**.
  - The week's missed words.
  - The words with the lowest predicted recall that aren't due yet.
  - A few long-unseen strong words for variety.
- Answers **count** in the scheduler.
- Optional, so it never adds a big mandatory load. It gives the feeling of "my week's words are still there", which the cumulative-test research links to better study habits.

### 4.6 Daily target: decision needed
- **Option A (recommended, keeps today's model):** "words per day" = total answers per day. New words fill the space FSRS frees up. Effort is predictable, and progress becomes ~40 % faster (simulation; expect less in reality).
- **Option B:** "new words per day" + all due reviews. Fastest progress, but the daily load grows to 40–90 answers within a year.
- Either way, show the learner both numbers ("today: 7 reviews + 3 new"), and suggest 15–20/day for anyone aiming at A2 within a year (§3c).

## 5. Implementation plan

| Phase | Change | Files | Tests |
|---|---|---|---|
| **1. FSRS scheduler** | Add `stability`, `fsrs_difficulty`, `last_review_at` to `vocabulary_progress`. Convert existing rows (stability ≈ current interval, difficulty from times wrong/right). Implement FSRS-6 (own code in `src/lib/spacedRepetition`, or the MIT-licensed `ts-fsrs` package). Ratings from §4.1. `submit_quiz` validates the new fields within bounds | migration `…0006_fsrs.sql`, `spacedRepetition/*`, `submit_quiz` | Unit tests against reference values from the FSRS implementation; PGlite migration test; update the 60-day simulation (backlog and load bounds) |
| **2. Selection by predicted recall** | `create_daily_session_for` orders due words by recall computed from stability and elapsed days; keeps wrong-first and the adaptive new-word rule | same migration | Existing session tests + a test that the lowest-recall word comes first |
| **3. Format rule + within-quiz retry** | Quiz generator: multiple choice only at streak 0 / after a lapse; missed words repeated at the end, unscored | `src/lib/quiz/generate.ts`, `Quiz.tsx` | Quiz unit tests; check that retries don't change the score |
| **4. Seen-but-unquizzed tracking** | `daily_session_words.seen_at` or a progress row with `status='seen'`; selection puts them first | migration, `save_session_progress` | DB test: abandon after cards → next day the same words come first |
| **5. Weekly review** | New optional session type (`daily_sessions.kind = 'weekly'`), offered on the learner's chosen day; 15 items as in §4.5 | migration, Dashboard card, Quiz reuse | DB + UI tests |
| **6. Daily-target meaning + display** | Depends on the §4.6 decision. Show "reviews + new" on the home screen | Dashboard, About page | — |
| **Later** | Fit FSRS parameters to Lernbrot's own review data once there are enough reviews (thousands across users); per-user retention setting | offline script | Compare prediction error before/after |

Phases 1–3 carry almost all the benefit. Phase 5 is a product/motivation feature.

## Sources
- Cepeda, Vul, Rohrer, Wixted & Pashler (2008). Spacing effects in learning: a temporal ridgeline of optimal retention. *Psychological Science* 19(11). https://pubmed.ncbi.nlm.nih.gov/19076480/ · PDF: https://www.evullab.org/pdf/CepedaVulRohrerWixtedPashler-PS-2008.pdf
- Bahrick, Bahrick, Bahrick & Bahrick (1993). Maintenance of foreign language vocabulary and the spacing effect. *Psychological Science*. https://digitalcommons.fiu.edu/psychology_fac/50 · PDF: https://www.Gwern.net/doc/psychology/spaced-repetition/1993-bahrick.pdf
- Nakata (2015). Effects of expanding and equal spacing on second language vocabulary learning (summary of findings via citing work): https://pressto.amu.edu.pl/index.php/ssllt/article/download/49487/44378/139556 · Nakata (2013) thesis, *Optimising second language vocabulary learning from flashcards*: https://linguistlist.org/issues/24/3797
- Karpicke & Roediger (2008). The critical importance of retrieval for learning. *Science*. https://www.brucehayes.org/Teaching/papers/2008_Roediger_Karpicke_Science.pdf · https://profiles.wustl.edu/en/publications/the-critical-importance-of-retrieval-for-learning/
- Kang, McDermott & Roediger (2007). Test format and corrective feedback modify the effect of testing on long-term retention. https://www.gwern.net/docs/spaced-repetition/2007-kang.pdf
- Rawson & Dunlosky: successive relearning, overview: https://psychologicalscience.org/?p=193451 · review: https://link.springer.com/article/10.1007/s10648-023-09809-2
- Szpunar, McDermott & Roediger (2007) and cumulative testing: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8062001/ · https://journals.sagepub.com/doi/abs/10.1177/0098628313487458
- Lindsey, Shroyer, Pashler & Mozer (2014). Improving students' long-term knowledge retention through personalized review. *Psychological Science* 25. https://home.cs.colorado.edu/~mozer/Research/Selected%20Publications/reprints/LindseyShroyerPashlerMozer2014.pdf
- Settles & Meeder (2016). A trainable spaced repetition model for language learning. ACL. https://preview.aclanthology.org/landing_page/P16-1174 · https://blog.duolingo.com/how-we-learn-how-you-learn
- FSRS algorithm and default parameters: https://github.com/open-spaced-repetition/awesome-fsrs/wiki/The-Algorithm · overview: https://help.remnote.com/en/articles/9124137-the-fsrs-spaced-repetition-algorithm · https://domenic.me/fsrs/
