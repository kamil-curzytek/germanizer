# Vocabulary size analysis

**Question:** how many words does a learner need at A1, A2, B1 and B2, and why do published figures disagree?

## 1. Three things that are often confused

| Concept | Meaning | In this curriculum |
|---|---|---|
| **Core / extended active vocabulary** | Items the learner can retrieve and use in speech or writing | Drawn into the daily review (Today's 10) |
| **Receptive vocabulary** | Items recognised in listening/reading, not necessarily produced | Shown in context, quizzed by recognition only |
| **Curriculum size** | Every item in the dataset, active and receptive | `data/german-all.json` |

Research consistently finds receptive vocabulary well ahead of productive vocabulary. Goethe states it directly: of ~650 A1 entries, *"etwa die Hälfte"* (about half) should be active. From A2 on, its lists are to be mastered *"zumindest rezeptiv"* (at least receptively). **A B2 word count is not a list to memorise.**

## 2. The CEFR gives no word counts

The CEFR Companion Volume (2020) describes vocabulary **qualitatively**. Range runs from a basic repertoire of words and phrases for concrete needs (A1), through everyday situations and familiar topics (A2–B1), to a broad range for most general topics (B2). Vocabulary *control* is described separately. There is no official "A1 = X words". Every number below is an **empirical estimate** linked to the CEFR by a test, exam or corpus.

## 3. What the evidence says

| Source | Language | Unit | Kind | A1 | A2 | B1 | B2 |
|---|---|---|---|---:|---:|---:|---:|
| Goethe Wortlisten | German | **lexical units / entries**, without predictable derivatives & compounds | Exam syllabus | ~650 (½ active) | ~1,300 (rec.) | ~2,400 (rec.) | — |
| Milton 2010 (X_Lex, >10,000 EFL learners in Greece) | English | **lemmas**, top 5,000 only | Receptive recognition | < 1,500 | 1,500–2,500 | 2,500–3,250 | 3,250–3,750 |
| Tschirner, Hacking & Rubio (VLT, 97 German learners) | German | **lemmas**, 5 bands of 1,000 | Receptive, linked to reading | ~1,000 (ILR 1) | ~2,000 (ILR 1+) | ~3,000 (ILR 2) | ~4,000 (ILR 2+) |
| Tschirner et al. 2019 (reported, not verified) | German | lemmas | Receptive, reading | (A1.2 ≈ 800) | ~1,600 | 2,400 (B1.1) – 3,200 (B1.2) | ~4,000 |
| This project, coverage | German | lemmas | Corpus coverage | 750 → 80 % spoken | 2,000 → 87 % | 3,000 → 90 % | 4,500 → 92 % |

### Why the numbers differ

1. **Different units.** "2,400 lexical units" (Goethe B1) leaves out predictable derivatives and compounds and counts some multi-word units as one. "3,200 lemmas" (B1.2 research) counts every lemma in a frequency band. Word-family counts would be smaller still. The same knowledge can be "2,400", "3,200" or "~2,000 families".
2. **Receptive vs. productive.** All research figures here are **receptive** (recognition tests). Goethe's lists are receptive targets from A2 up. Productive vocabulary at the same level is considerably smaller.
3. **Syllabus vs. frequency.** An exam list is a topic-based selection of what tasks may require. A test band is the top N of a frequency list. They overlap but are not the same set (see the Goethe coverage table in `coverage-analysis.md`).
4. **Skill.** The Tschirner and Milton figures are tied to **reading**. Speech needs fewer distinct words for the same coverage: our data shows ~10 points more coverage in subtitles than in news at any N.
5. **Population and precision.** For German specifically, the link between vocabulary size and reading level was **weak** (R² = .39, n = 97, mostly lower levels), much weaker than for Spanish and Russian. The German thresholds are **rough guides, not cut-offs**.
6. **Language.** Milton's figures are for English. German compounding and inflection change how many lemmas a learner meets.

**So the "2,400 vs 3,200" puzzle mostly disappears.** Goethe's ~2,400 B1 *exam* units sit inside a ~3,000-lemma *receptive* range once derivatives and compounds are counted as separate lemmas. Both describe "B1", measured with different units and purposes.

## 4. The "2,000 words" claim

| Question | Answer |
|---|---|
| Where does it come from? | Mainly **English** corpus work. In the BNC, the 2,000 most frequent **lemmas** give ~90 % coverage of spoken and ~70 % of written text (Milton 2009, p. 58). Older word-family studies (e.g. Schonell et al.) reported similar figures for speech. |
| What is a "word" there? | Lemmas (Milton) or word families (older studies). Not word forms. |
| What kind of speech? | Conversation (BNC demographic) and formal speech (lectures, courts). |
| Does it hold for German? | **Roughly, for speech.** In our German subtitle data, 2,000 lemmas give **87.2 %**. In German news and web text, **76–78 %**. |
| Comprehension or production? | **Neither, directly.** It is token coverage: at 87 % about 1 word in 8 is unknown, well below the ~95 % associated with minimally acceptable listening comprehension. |
| Enough for everyday communication? | **For routine, predictable interactions, mostly yes,** if the 2,000 include the right functional phrases and survival vocabulary (which pure frequency doesn't guarantee). For following natural conversation between native speakers, media or forms, no. |
| Where does it stop being enough? | Reading anything written (76–78 % coverage). Reaching 95 % spoken coverage needs ~10,000 lemmas in subtitles. That is only feasible receptively, through word-family and compound knowledge, not by memorising more items. |

## 5. Conclusions that drive the curriculum

1. A **small, frequency-led core** is justified: return per word collapses after about 750–1,000 lemmas.
2. After the core, **usefulness must outrank frequency**, so Germany-life vocabulary (housing, bureaucracy, health, work) enters on practical grounds, as in the Goethe lists.
3. From B1, the curriculum should split **active** and **receptive** items. Receptive breadth grows faster and is supported by word-family and compound teaching, not by more memorisation.
4. Totals per level should land within the convergent evidence: **~1,300–2,000 by A2**, **~2,400–3,200 by B1**, **~4,000–4,500 by B2** (receptive, lemma-equivalent). The active subsets are much smaller.

The concrete numbers are in `final-recommendation.md`.
