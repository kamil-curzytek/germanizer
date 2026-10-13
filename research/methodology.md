# Methodology

Goal: choose the vocabulary that maximises **real-world communicative value per unit of learning effort** for someone living in Germany, from complete beginner to B2. The order of work was research → candidate pool → normalization → scoring → curation → validation. No list was written from memory first.

## 1. Pipeline (reproducible)

| Step | Script | Output |
|---|---|---|
| Goethe A1/A2/B1 headword extraction (evidence only) | `pipeline/goethe.py` | `sources/goethe_headwords.json` |
| Lemma frequency per genre + coverage | `pipeline/frequencies.py` | `sources/freq_*.json`, `coverage.json` |
| Compound/derivative share of the long tail | `pipeline/compounds.py` | `compounds.json` |
| Candidate pool + component scores | `pipeline/candidates.py` | `candidates.csv` (≈12,900 candidates) |
| Curated entries (expert authoring, one file per tier/topic) | `authoring/*.psv` | — |
| Build, validate, attach evidence | `pipeline/build_dataset.py` | `data/*.json`, `build-report.json` |
| Near-duplicate check (same head word) | `pipeline/check_heads.py` | console report |
| Which candidate words are still missing | `pipeline/missing.py` | console report |
| Coverage per tier (strict + inclusive) | `pipeline/tier_coverage.py` | `tier-coverage.json` |
| Goethe cross-check, anti-inflation, scenarios | `pipeline/validate.py` | `validation.json` → `validation-report.md` |

Run them in this order: `goethe.py → frequencies.py → candidates.py → build_dataset.py → tier_coverage.py → validate.py`. FOLK data is used automatically once `sources/folk_lemmas*.json` exists.

## 2. Units: what counts as one item

| Unit type | Definition | Example | Counted as its own item? |
|---|---|---|---|
| `word` | One lemma with its forms as metadata | *gehen* (geht, ging, ist gegangen) | yes |
| `construction` | A word plus required preposition/case/reflexive with independent learning value | *warten auf + Akk*, *sich erinnern an + Akk* | yes, **only** when the pattern is not predictable from the base verb |
| `collocation` | Frequent word combination | *einen Termin vereinbaren*, *Rechnung bezahlen* | **no**, stored inside the head word's `collocations`. Exception: noun-verb constructions whose verb choice or meaning is not predictable (*eine Entscheidung treffen*, *in Anspruch nehmen*) become `construction` entries **with a written `why=` reason** |
| `fixedExpression` | Conventionalised chunk, not built word by word | *Keine Ahnung.*, *Das kommt darauf an.*, *Mal sehen.* | yes |
| `functionalPhrase` | Formula that performs a speech act | *Können Sie das wiederholen?*, *Wie bitte?* | yes, but only when it can't be assembled from known words (see below) |

**Anti-inflation rules:**
- *Ich möchte einen Kaffee / einen Termin / bezahlen* = **one** item (*möchten*) with pattern examples.
- Predictable derivatives (*Lehrer → Lehrerin*, *zahlen → Zahlung*) are recorded under `relatedItems` and treated as receptive. They become their own entry only when meaning or use is not predictable or they are very frequent (*bezahlen* vs *zahlen*).
- Every multi-word entry built only from words that have their own entries must carry a `why=` reason, a `pattern` tag or a valency tag (`prep:`, `refl`); `validate.py` flags the rest. Chunks are reported separately from lexical units in all counts.
- Predictable compounds (*Kinderbett*) are not entries. Compounds become entries only if (a) common in everyday life **and** (b) not reliably inferable, **or** important in Germany (*Krankenkasse*, *Nebenkosten*, *Anmeldung*, *Führerschein*). Productive compound heads are taught through `relatedItems`.

## 3. Candidate pool

Union of the top 7,000 lemmas per genre (subtitles, news, web), all Goethe A1–B1 headwords, the app's existing words, and the closed-class/interaction list in `candidates.py`. FOLK is added when available. Forms are normalized to lemmas with simplemma. Contractions become prepositions, and determiner/pronoun forms collapse to one lemma.

## 4. Priority model (transparent, not "scientific")

Each candidate gets component scores in [0, 1]. A frequency score is `1 − ln(rank)/ln(20,000)`, i.e. log-scaled and 0 beyond rank 20,000.

```
score = 0.35 · spoken        (subtitles; with FOLK: 0.35·subtitles + 0.65·FOLK)
      + 0.20 · written       (mean of news and .de web)
      + 0.25 · cefr_evidence (Goethe A1 = 1.0, A2 = 0.8, B1 = 0.6, none = 0)
      + 0.10 · breadth       (share of genres where rank ≤ 8,000)
      + 0.10 · function_word (closed-class & interactional vocabulary is protected)
      − 0.15 · regional      (Goethe marks it as Austrian/Swiss)
      − 0.15 · film_skew     (frequent in subtitles, rare in written German, no CEFR evidence: töten, Waffe, sir)
      − 0.05 · written_only  (frequent in writing, rare in speech, no CEFR evidence)
```

**Weights.** Spoken outweighs written because the app is for communication. CEFR evidence carries real weight because exam lists encode practical, topic-based needs that frequency misses (`coverage-analysis.md`). Function words get a protected bonus so concrete nouns can't crowd them out. These weights are judgment, stated openly; the score ranks candidates for review and decides nothing on its own.

## 5. Curation (where judgment enters)

Candidates were reviewed in score order and each decision recorded with these rules:

1. **Include** if the item is needed for a validation scenario (§7) or ranks highly and is standard, Germany-wide and contemporary.
2. **Promote** low-frequency, high-value Germany items: housing (*Kaution, Nebenkosten*), bureaucracy (*Anmeldung, Aufenthaltstitel, Bescheid*), health (*Krankenkasse, Überweisung*), work (*Gehalt, Probezeit*).
3. **Demote / exclude:** proper names, subtitle artefacts (*sir, okay* duplicates), film vocabulary, Austrian/Swiss-only variants (recorded in `grammar.variants` when useful), strong regionalisms, slang that isn't broadly understood, specialist terms.
4. **Communicative productivity.** High-productivity verbs (*machen, nehmen, bringen, lassen, stellen, legen, halten, bekommen*) are kept only when the corpus confirms them and they get collocation lists, because their value lies in combinations.
5. **CEFR assignment = recommended point of deliberate acquisition**, not first encounter. Goethe level, frequency band and scenario need are combined. Disagreements (e.g. frequent but abstract words that Goethe places late) are decided case by case and noted in `evidence.selectionReason`.
6. **Register:** `neutral` is the default; `spoken`, `informal`, `formal`, `written` and `colloquial` are marked. The core prefers contemporary, Germany-wide standard German.

## 6. Tiers and learning modes

| Tier | Name | Role | Entries | Productive share |
|---|---|---|---:|---:|
| 1 | Core German for Germany | Smallest set with the highest communicative return | 761 | 99 % |
| 2 | Everyday Germany | Functioning comfortably in ordinary life | 1,078 | 84 % |
| 3 | Independent communication (≈B1) | Explaining, giving reasons, experiences, opinions, workplace and services | 1,332 | 33 % |
| 4 | B2 breadth & precision | Nuance, argument, abstract topics, formal writing, media, colloquial listening | 1,351 | 12 % |

The planned productive shares (Core 100 %, Everyday ~90 %, B1 ~60 %, B2 ~35 %) ended lower for Tiers 3–4. During authoring, most B1/B2 breadth items (formal connectors, abstract and media nouns) were judged recognition targets. The resulting totals (≈2,260 productive, ≈2,260 receptive) match the research finding that receptive vocabulary runs well ahead of productive.

`learningMode`: `active` (daily review, production questions), `receptive` (recognition only), `both` (active once the learner reaches the item's level; recognition before that).

## 7. Validation

1. **Automatic** (`build_dataset.py`): unique ids; schema; nouns carry article, gender and plural (or an explicit singular-only/plural-only flag); the example contains the item (lemma-matched, including separated verb prefixes); every Goethe-listed article agrees with ours; plural forms occur in at least one corpus.
2. **Anti-inflation check** (`validate.py`): multi-word entries composed only of known words need a documented reason (§2).
3. **Independent cross-check** against the Goethe A1/A2/B1 headwords: share taught by the matching tier and anywhere.
4. **Scenario validation:** 24 development scenarios (CEFR Companion Volume domains, Goethe/telc tasks, *Rahmencurriculum*) list the items each needs; every item must exist at or below the scenario's tier. Gaps were fixed. Then **12 held-out scenarios**, written after those fixes, were scored *before* any further change. That score is the honest quality estimate.
5. **Coverage validation:** coverage per tier is recomputed on all genres (plus FOLK when available), alongside inclusion of the top-N frequency lemmas.

All results and the before/after numbers are in `validation-report.md`.

## 8. Known limitations

- **Spoken evidence is a proxy** (subtitles) until FOLK is added. Subtitles over-represent drama vocabulary and under-represent discourse particles of natural conversation.
- **Lemmatization errors** (simplemma) affect a small share of ranks, e.g. *heißen ↔ heiß*. Curation corrects them for selected items.
- **Corpus samples** (300k sentences each) are enough for ranks up to ~10k but noisy beyond.
- **Dataset and scenarios share an author.** The held-out set reduces but doesn't remove this bias; an external reviewer should write the next set.
- **Evidence for multi-word entries** describes their rarest content word (`evidence.evidenceHead`), not the whole construction; no phrase-frequency data was used.
- **Examples and glosses were written for this project** and checked automatically, but they are not native-speaker reviewed. A native-speaker review pass is recommended before publishing widely.
