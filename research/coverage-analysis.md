# Coverage analysis

**Question:** how much running German does a learner recognise if they know the *N* most frequent lemmas, and how does that differ between speech and writing?

All figures were **measured in this project** (`pipeline/frequencies.py`, `coverage.json`), not taken from popular sources.

## Method

- **Unit = lemma**, not word form and not word family. *gehen, geht, ging, gegangen* = 1 lemma. *Zahl* and *bezahlen* = 2 lemmas.
- **Genres are kept separate:** subtitles (SUBTLEX-DE lemma file, 21 M word tokens), news (Leipzig 2023, 4.5 M), web `.de` (Leipzig 2021, 4.5 M).
- **Normalization:** contractions count as their preposition (*im → in*, *zum → zu*). Determiner forms share one lemma (*die/das/den → der*, *eine → ein*). Lemmas are lower-cased (*essen/Essen* merge).
- **Tokens:** only alphabetic tokens count. Numbers and punctuation are excluded. **Proper names are included**, which lowers coverage, especially in news.
- **Caveat on subtitles:** subtitles stand in for speech. They are scripted, partly translated from English, and over-represent drama vocabulary (*töten, Waffe*). Natural conversation (FOLK) is usually *more* repetitive, so subtitle figures likely **understate** spoken coverage. FOLK will be added when available.

## Coverage of the most frequent N lemmas (% of word tokens)

| N lemmas | Subtitles (spoken proxy) | Web (.de) | News |
|---:|---:|---:|---:|
| 100 | 60.4 | 49.8 | 50.0 |
| 250 | 70.4 | 57.6 | 57.7 |
| 500 | 77.0 | 64.0 | 63.7 |
| 750 | 80.2 | 68.1 | 67.2 |
| 1,000 | 82.4 | 71.0 | 69.8 |
| 1,500 | 85.3 | 75.0 | 73.4 |
| **2,000** | **87.2** | **77.6** | **76.0** |
| 3,000 | 89.7 | 81.1 | 79.4 |
| 4,000 | 91.3 | 83.3 | 81.7 |
| 5,000 | 92.4 | 84.8 | 83.3 |
| 8,000 | 94.5 | 87.7 | 86.4 |
| 10,000 | 95.4 | 88.9 | 87.7 |

## Diminishing returns (coverage gained per 100 extra lemmas)

| Range | Subtitles | Web | News |
|---|---:|---:|---:|
| 100 → 250 | 6.7 | 5.2 | 5.1 |
| 250 → 500 | 2.6 | 2.6 | 2.4 |
| 500 → 1,000 | 1.1 | 1.4 | 1.2 |
| 1,000 → 2,000 | 0.48 | 0.66 | 0.62 |
| 2,000 → 3,000 | 0.25 | 0.35 | 0.34 |
| 3,000 → 4,000 | 0.16 | 0.22 | 0.23 |
| 4,000 → 5,000 | 0.11 | 0.15 | 0.16 |
| 5,000 → 10,000 | 0.06 | 0.08 | 0.09 |

**Reading:** the return per word collapses after about 500–1,000 lemmas. Spoken coverage drops below 1 point per 100 words at around **1,000**, and below half a point at around **2,000**. In writing, the same vocabulary always gives about 10 points less coverage. This is the empirical basis for a **small, frequency-led core** followed by layers chosen increasingly by **usefulness** rather than frequency.

## How do the Goethe exam lists compare?

| Goethe list (cumulative) | Lemmas (our extraction, + articles/pronouns) | Subtitles | Web | News |
|---|---:|---:|---:|---:|
| A1 | 734 | 66.8 | 53.7 | 54.9 |
| A1 + A2 | 1,351 | 74.8 | 60.3 | 61.6 |
| A1 + A2 + B1 | 3,138 | 81.1 | 70.1 | 70.6 |

The Goethe lists cover **much less** text than a frequency list of the same size: 734 Goethe A1 words cover 67 % of subtitles, the top 750 lemmas cover 80 %. This is not a flaw, because the lists are built differently:

- They are **topic-led**: practical words such as *Anmeldung*, *Formular*, *Apotheke* are rare in corpora but essential in life.
- They **exclude** discourse markers and interjections (*okay, na, ach, hey*), proper names, and many high-frequency but abstract words.
- They leave out predictable compounds and derivatives, which would otherwise add coverage.

**Implication:** neither source alone is right. A curriculum built only on frequency misses survival vocabulary. One built only on exam lists under-serves real conversation. This motivates the combined scoring model (`methodology.md`).

## Compounds and derivatives in the long tail

For lemmas beyond rank K, the share of tail tokens whose final component is an already-known lemma (`pipeline/compounds.py`):

| Corpus | Known K | Tail share of all tokens | Tail that is a compound of a known word | Tail that is a derivative of a known stem |
|---|---:|---:|---:|---:|
| Subtitles | 2,000 | 12.8 % | 16.7 % | 2.5 % |
| Subtitles | 4,000 | 8.7 % | 22.3 % | 2.8 % |
| Web | 2,000 | 22.4 % | 29.1 % | 3.0 % |
| Web | 4,000 | 16.7 % | 38.8 % | 2.7 % |
| News | 2,000 | 24.0 % | 24.3 % | 3.0 % |
| News | 4,000 | 18.3 % | 33.0 % | 2.7 % |

The heuristic is rough. It also counts prefix verbs (*verstehen* ends in *stehen*) and misses compounds with linking elements. Still, the scale is clear. In **written** German, roughly **a third of everything beyond the 4,000 most frequent lemmas** is a compound of a word the learner already knows. So teaching compound **heads and patterns** (*-vertrag, -karte, -zeit, -amt*), rather than memorising every compound, has a large receptive payoff. It is also why Goethe excludes predictable compounds from its counts.

## What these numbers do not show

- **Coverage is not comprehension.** 95 % coverage means about 1 unknown word in 20, which research associates with *minimally acceptable* understanding; 98 % with comfortable understanding (Laufer & Ravenhorst-Kalovski 2010; van Zeeland & Schmitt 2013, for listening).
- **Recognising a word is not being able to use it.** These are receptive figures.
- **Lemmas ≠ word families.** Family-based counts (common in English research) give higher coverage per "word". German compounding makes the difference larger.
- We report **no precise comprehension percentage** for any curriculum layer; coverage is a proxy.

## Coverage of the finished curriculum

Cumulative token coverage of the dataset itself (strict lemma matching, `tier-coverage.json`):

| Up to tier | Entries | Subtitles | Web .de | News | Frequency list with the same speech coverage |
|---|---:|---:|---:|---:|---|
| 1 Core | 761 | 74.2 % | 57.9 % | 59.8 % | ≈ top 370 lemmas |
| 2 Everyday | 1,839 | 78.8 % | 65.1 % | 66.1 % | ≈ top 620 |
| 3 Independent | 3,171 | 83.1 % | 72.7 % | 72.8 % | ≈ top 1,100 |
| 4 B2 | 4,522 | 85.4 % | 78.3 % | 77.0 % | ≈ top 1,500 (writing: ≈ top 2,150) |

The gap between the curriculum and a pure frequency list of the same size is the deliberate cost of including Germany-life domain words, constructions and phrases. Details and the top-N inclusion check are in `validation-report.md` §5.
