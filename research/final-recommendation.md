# Final recommendation: how much German vocabulary, in what order

**Short answer.** For real life in Germany, a learner needs:
- about **750 active items** to get by (Core);
- about **1,650 active items** to function in everyday life (end of A2);
- about **2,100 active + 1,100 receptive** to communicate independently (B1);
- about **2,250 active + 2,250 receptive ≈ 4,500 in total** for B2.

These figures count lexical units (lemmas and constructions) plus a separately reported set of chunks. They agree with the converging research evidence (`vocabulary-size-analysis.md`) and were tested against corpora, the Goethe lists and A1–B2 scenarios (`validation-report.md`).

## 1. The numbers

| Level | Tier(s) | Items in the curriculum (cumulative) | of which **productive** (active + both) | of which receptive | Lexical units / chunks | Research range (receptive, lemma-equivalent) |
|---|---|---:|---:|---:|---|---|
| **Core** (≈A1, survival) | 1 | **761** | **751** | 10 | 700 / 61 | Goethe A1 ≈ 650 entries, ½ active |
| **Everyday** (≈A2) | 1–2 | **1,839** | **1,660** | 179 | 1,707 / 132 | 1,300–2,000 |
| **Independent** (≈B1) | 1–3 | **3,171** | **2,100** | 1,071 | 2,957 / 214 | 2,400–3,200 |
| **B2 breadth & precision** | 1–4 | **4,522** | **2,260** | 2,262 | 4,263 / 259 | 3,250–4,500 |

*Productive* = `learningMode` `active` or `both` (shown receptively first, produced once the learner reaches the item's level). *Chunks* = fixed expressions and functional phrases (*Keine Ahnung*, *Wie bitte?*, *Sehr geehrte Damen und Herren*). They are taught as wholes and **not** counted as vocabulary size.

### What each number means

- **750 core items** are the smallest set with the highest return: all function words, the high-frequency verbs with their forms, numbers and time, ~300 everyday nouns, and the survival routines for shops, doctors, transport and offices. They give **74 % token coverage of speech** (subtitles) and ~59 % of written text. That's enough for predictable, supported interactions, not for following native-speaker conversation.
- **~1,650 active by the end of A2.** Tier 2 adds the domains of life in Germany: housing (*Kaution, Nebenkosten*), offices (*Anmeldung, Bescheid*), health (*Krankenkasse, Überweisung*), work (*Probezeit, Schicht*). Coverage only rises to 79 % (speech) / 65 % (writing), because these words are rare in text but indispensable in life. **This is the most important level for an app aimed at people living in Germany.**
- **B1: about 2,100 active plus 1,100 receptive.** From here, breadth grows mainly receptively. Tier 3 is 33 % productive: explaining, giving reasons, experiences, workplace and services. Coverage: 83 % speech, 73 % writing.
- **B2: about 4,500 in total, half of them receptive.** Tier 4 is ~88 % receptive: formal written German (*sowie, zudem, gemäß*), argumentation frames, abstract nouns, media and law, colloquial speech for listening. Coverage: **85 % speech, 77–78 % writing**. A pure frequency list reaches the same with ~1,500 lemmas (speech) or ~2,150 (web text). The difference is the price of about 2,200 entries chosen for usefulness rather than frequency.

## 2. Why these numbers and not others

1. **The CEFR sets no word counts.** All published figures are estimates tied to a test, an exam list or a corpus. Their apparent disagreement (Goethe B1 ≈ 2,400 vs. research B1 ≈ 3,200) mostly comes from **units**: Goethe excludes predictable compounds and derivatives. Our B1 total (3,171 items, 3,002 lemma keys) sits at the top of that range because we keep important compounds that can't be predicted from their parts (*Nebenkostenabrechnung, Aufenthaltserlaubnis*) as their own entries.
2. **Return per word collapses after ~750–1,000 lemmas** (`coverage-analysis.md`): the top 750 lemmas give 80 % of speech; the next 1,250 add only 7 points. A small frequency-led core is justified; after it, **usefulness must outrank frequency.**
3. **The "2,000 words" claim** holds roughly for **speech coverage** (87 % in German subtitles), not for reading (76–78 %) and not for comprehension (which needs ≈95 %). It is a good A2/B1 milestone for listening, not an end point.
4. **Receptive breadth beats more memorisation.** In written German, about **a third of everything beyond the 4,000 most frequent lemmas** is a compound of a known word. B2 reading is reached through compound heads and word families (`relatedItems`, `collocations`), not by drilling 10,000 items.

## 3. How the app should use the dataset

| File | Entries | Use |
|---|---:|---|
| `data/german-core.json` | 761 | Start here: the default pool for "Today's words" |
| `data/german-a1.json` | 873 | Grouping by CEFR label (lesson topics, level badges) |
| `data/german-a2.json` | 769 | |
| `data/german-b1.json` | 1,537 | |
| `data/german-b2.json` | 1,343 | |
| `data/german-all.json` | 4,522 | Everything, with evidence |

Recommendations for integration (a later step, after your review):

1. **Daily new words only from productive items, in tier order** (Tier 1 → 2 → 3 `active/both` → 4 `both`). That gives about 2,260 items for the spaced-repetition loop. At 10 new words a day, the Core takes about 2½ months and the A2 active set about 5½ months (longer in practice, since the adaptive rule holds back new words when reviews pile up).
2. **Receptive items do not enter the daily production loop.** Show them in reading/listening exercises and recognition quizzes (German → English). Promote them to active only when the learner asks.
3. **Use `cefr` for lesson topics and level labels, `priorityTier` for order.** The held-out test showed tier and CEFR label can disagree for topic words (*Winter* is A1 by topic but was Tier 2 by priority). Ordering by tier while labelling by CEFR keeps both.
4. **Teach chunks as phrases** (whole-phrase cards with situation context), separate from word cards.
5. **Use `relatedItems` and compound heads** for "word family" extensions instead of new cards.

## 4. Confidence and what's still open

| Claim | Confidence | Basis |
|---|---|---|
| Core ≈ 750, A2 active ≈ 1,650 | **High** for the order of magnitude | Goethe prefaces; coverage curve; scenario tests |
| B1 ≈ 3,200, B2 ≈ 4,500 in total | **Medium** | Converging receptive research (Milton; Tschirner et al.), but the German size–proficiency link is weak (R² = .39) |
| Item-level choices | **Medium** | Held-out scenarios before fixes: **82 % A1, 71 % A2, 88 % B1, 95 % B2** of must-know items available in time. A1–A2 is the weakest area |
| Spoken figures | **Provisional** | Subtitles stand in for speech. **FOLK** (real conversation) is still to be added |

### Open items
1. **FOLK lemma list.** When you place it at `research/sources/folk_lemmas*.json`, rerun `candidates.py → build_dataset.py → tier_coverage.py → validate.py`. Spoken weights switch to 35 % subtitles + 65 % FOLK automatically. Expect discourse particles and spoken forms to rise and film vocabulary to fall.
2. **Native-speaker review** of examples, glosses and register labels. Everything was machine-checked, not human-proofread.
3. **A fresh held-out scenario set**, ideally written by someone else, before further tuning. The weak spots are A1/A2 domains not covered by Goethe topics (parcels, online shopping, apps).
4. **105 pragmatic routines** are kept as chunks without a written reason. A reviewer could thin them further.

## 5. Reproducing everything

```bash
python pipeline/goethe.py
python pipeline/frequencies.py
python pipeline/candidates.py
python pipeline/build_dataset.py
python pipeline/tier_coverage.py
python pipeline/validate.py
```

The source corpora live in `research/sources/` (git-ignored for licensing; download instructions in `sources.md`). The curated entries are in `research/authoring/*.psv`, one file per tier and topic.
