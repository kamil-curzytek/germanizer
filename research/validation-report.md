# Validation report

Everything here is reproducible with `python pipeline/build_dataset.py && python pipeline/tier_coverage.py && python pipeline/validate.py`. Raw results: `build-report.json`, `tier-coverage.json`, `topN-inclusion.json`, `validation.json`, plus the two pre-fix snapshots `validation-before-fixes.json` and `validation-heldout-before-fixes.json`.

Final dataset: **4,522 entries** (Tier 1: 761 · Tier 2: 1,078 · Tier 3: 1,332 · Tier 4: 1,351).

## 1. Automatic checks (`build_dataset.py`)

Every build checks every entry. The final build has **0 problems**. The remaining warnings are listed in `build-report.json` and are all of one kind: plural forms of rare compounds that don't occur in the 300k-sentence corpora (*Brückentage, Einbürgerungstests*); these were checked by hand. The checks:

| Check | Rule | Errors it caught during authoring |
|---|---|---|
| Schema / columns | 14 positional columns + labelled `f= c= r= why=` segments; valid POS, CEFR, tier, mode | column shifts (fixed with `fix_columns.py` and the switch to labelled segments); long POS names (`adverb` → `adv`) |
| Duplicates | single words: same form + POS + article (case- and gender-sensitive: *Sie/sie, der/die Leiter*); phrases: case- and punctuation-insensitive | dozens of duplicates across tiers (e.g. *Krieg, Kumpel, Nachtisch, überweisen, beantragen, Na und?, Mit freundlichen Grüßen*) |
| Near-duplicates (`check_heads.py`) | same head word after removing *sich*/placeholders/prepositions | same-sense repeats such as *bewerben / sich bewerben*, *erholen / sich erholen*; remaining collisions are deliberate (*warten / warten auf*, *trennen* waste vs *sich trennen* break up, homonym *Leiter*) |
| Example contains the item | lemma, separated prefix, listed forms, inflected forms inside expressions (`pattern` tag exempts frames) | dozens of examples that used only a compound (*Uniklinik* for *Klinik*, *Rentenreform* for *Reform*) |
| Article agreement with Goethe | our article must match Goethe's where Goethe lists one | *Eingang* (die → der). Two justified disagreements kept and noted: *das Virus*, *das Terminal* (Duden standard; Goethe gives *der*) |
| Plural in corpus | warning only | singular-only nouns set to `∅` (*Grippe, Durchführung, Opposition*) |
| Evidence attribution | multi-word entries take corpus evidence from their rarest content word, recorded as `evidence.evidenceHead` | **bug found and fixed:** constructions had inherited the stats of their first token (*in Anspruch nehmen* showed the rank of *in*) |

## 2. Anti-inflation check (`validate.py`)

**Rule:** a multi-word entry made entirely of words that already have their own entries must either carry a `why=` reason (idiomatic, verb choice not predictable, fixed formula), teach a pattern/valency (`pattern`, `prep:`, `refl`), or be removed.

| Result | Count |
|---|---:|
| Constructions without a reason, first run | 12 |
| …given a documented reason (e.g. *Es gibt*: geben ≠ give; *Kinder bekommen*; *Anzeige erstatten*) | 9 |
| …deleted as compositional (*sauber machen, Unterlagen einreichen, in Kontakt bleiben*) | 3 |
| **Constructions without a reason, final** | **0** |
| Pragmatic routines built from known words (*Wie bitte?, Zusammen oder getrennt?, Kann ich Ihnen helfen?*) | 105 |

The 105 routines are kept: they are memorised as wholes for speaking and listening, as the brief allows for functional phrases. To keep the counts honest, **all 259 chunks (fixed expressions + functional phrases) are reported separately from the 4,263 lexical units** in `final-recommendation.md`. Many more candidate phrases were removed during authoring as plain collocations (*Pause machen, Termin bestätigen, Rechnung bezahlen*); the collocations live inside the head word's `collocations` field instead.

## 3. Independent cross-check against the Goethe lists

Goethe headwords, excluding regional (A/CH) items, numerals and extraction fragments:

| Goethe list | Headwords | Taught by the matching tier (A1→T1, A2→T≤2, B1→T≤3) | Anywhere in the curriculum |
|---|---:|---:|---:|
| A1 | 631 | 69.4 % | **98.3 %** |
| A2 | 1,081 | 90.9 % | **96.4 %** |
| B1 | 2,788 | 81.9 % | **88.0 %** |

- **A1 at 69 % by Tier 1 is by design.** Tier 1 is the ~750 highest-return items, and Goethe itself expects only about half of A1 to be active. The other A1 words are in Tier 2.
- **What's still missing** (`validation.json → goethe.*.missing_sample`): mostly female forms covered by a note on the male entry (*Studentin, Kundin, Nachbarin*), Austrian/Swiss variants the regional filter missed (*Abwart, Ammann, Bancomat, Matura*), dated items (*Fotoapparat, Diskothek*), and extraction fragments (*gung, tung, dium*). Real A2 gaps found here (weekday adverbs *montags…*, *vorgestern, windig, bewölkt, leidtun, Flohmarkt, Stockwerk*) were added.

## 4. Scenario validation

Scenarios follow CEFR Companion Volume domains, Goethe/telc exam task types and the integration-course framework (*Rahmencurriculum*). Each lists the items a learner must know. An item passes only if it exists **at or below the scenario's tier**. Too late or missing both count as failures.

### 4a. Development set: 24 scenarios (`validation/scenarios.json`)

| Level | First run (before fixes) | After fixes |
|---|---:|---:|
| A1 | 90.0 % | 100 % |
| A2 | 91.1 % | 100 % |
| B1 | 90.4 % | 100 % |
| B2 | 92.1 % | 100 % |

*(The very first run showed lower A1–A2 scores, but that was a matching bug for phrases with "…" and "?". It was fixed before the numbers above.)*

The fixes were:
- **14 items moved to an earlier tier.** For A1: *Kilo, Gramm, Schlafzimmer, Balkon, Schrank, Praxis, Tablette*. For A2: *reklamieren, Ausfall*. For B1: *Kompromiss, Argument, Nebenkostenabrechnung, Elternabend, Betreuung*.
- **17 items added**, e.g. *Uhrzeit, wehtun, Reisepass, Wohnungsgeberbestätigung, Schienenersatzverkehr, Mieterhöhung, Tagesordnung, Aktenzeichen, Lohnfortzahlung*.

100 % here is circular (we fixed exactly what these scenarios asked for), so the real test is the held-out set.

### 4b. Held-out set: 12 new scenarios (`validation/scenarios-heldout.json`)

Written after the development fixes. The table shows them scored **before** any held-out fixes:

| Level | By tier | By CEFR label | Main failures |
|---|---:|---:|---|
| A1 | **81.6 %** | 86.2 % | items only in Tier 2: *Kellner, Trinkgeld, Winter, Sommer, Schnee, Grad, abends* |
| A2 | **71.1 %** | 65.6 % | post-office vocabulary missing (*Päckchen, Packstation, Sendungsnummer, zustellen*); *Krankmeldung, Vorgesetzte, Training* labelled too late |
| B1 | **87.7 %** | 87.7 % | *Wanderung, stornieren* missing; *Diagnose, Vorsorge* too late |
| B2 | **95.3 %** | 95.3 % | *Prognose, Missverständnis* missing |

**This is the honest quality estimate:** roughly **4 in 5 must-know items at A1–A2, ~9 in 10 at B1, ~19 in 20 at B2** were available at the right time before this test was run. B1–B2 is strongest because Tiers 3–4 are broad. A1–A2 is weakest because:
- the small Tier 1 holds some A1 topic words back;
- whole everyday domains (post and parcels) were missed by both frequency and the Goethe topics used.

The held-out failures were then fixed (15 items re-tiered, 10 added). Post-fix: 97.8 / 100 / 97.6 / 100 % by tier. These post-fix numbers are no longer an independent measure.

**Lesson for the next round:** a new held-out scenario set (other domains: banking app, ordering online, hairdresser, police report, car rental, gym contract…) should be written **before** further changes, ideally by someone who didn't author the dataset.

## 5. Coverage validation (`tier_coverage.py`)

Token coverage by lemma, cumulative per tier. *Strict* counts what each item teaches as a unit; *inclusive* also counts every word inside multi-word items.

| Up to tier | Entries | Lemma keys | Subtitles (speech proxy) | Web .de | News |
|---|---:|---:|---:|---:|---:|
| 1 | 761 | 744 | 74.2 % (74.8) | 57.9 % (58.1) | 59.8 % (59.9) |
| 2 | 1,839 | 1,753 | 78.8 % (79.6) | 65.1 % (65.4) | 66.1 % (66.4) |
| 3 | 3,171 | 3,002 | 83.1 % (83.7) | 72.7 % (73.0) | 72.8 % (73.0) |
| 4 | 4,522 | 4,294 | **85.4 % (86.0)** | **78.3 % (78.6)** | **77.0 % (77.3)** |

**Compared with frequency-optimal lists** (`coverage-analysis.md`): the full curriculum covers as much speech as the top **~1,500** frequency lemmas and as much web text as the top **~2,150**. Tier 1 equals the top ~370 lemmas in speech. That is the measured price of choosing for usefulness. About 2,200 entries are domain vocabulary (housing, offices, health, work), constructions and phrases, which are rare in corpora but needed in life. Tier 1 covers about 3 points less speech than the top 500 lemmas, because it trades frequency for survival items and routines.

**Inclusion of the top-N lemmas** (`topN-inclusion.json`):

| Corpus | Top 500 | Top 1,000 | Top 2,000 | Top 3,000 |
|---|---:|---:|---:|---:|
| Subtitles | 92.6 % | 85.2 % | 73.5 % | 66.3 % |
| Web | 96.4 % | 91.9 % | 80.9 % | 70.4 % |
| News | 96.2 % | 90.4 % | 81.8 % | 72.5 % |

The excluded top-1,000 lemmas were inspected:
- names, English words and OCR errors (*lch, lhr*);
- imperatives the lemmatizer failed to reduce (*lass, warte, sieh*), which are covered by their verbs;
- place and party names (*Bayern, SPD*);
- film vocabulary (*Captain, Sheriff*).

A last batch of genuine words (*Präsident, Angriff, betroffen, Hochschule, Nutzer, erstmals…*) was added as `t4-l-frequency-residuals.psv`.

## 6. Limitations of this validation

- **The same author wrote the dataset and both scenario sets.** The held-out set reduces but doesn't remove that bias.
- **Speech evidence is subtitles.** FOLK (real conversation) is not yet integrated. When `sources/folk_lemmas*.json` is added, `candidates.py`, `build_dataset.py` and `tier_coverage.py` pick it up automatically and the spoken figures should be re-read.
- **Coverage is not comprehension** (see `coverage-analysis.md`), and scenario pass rates measure availability of items, not whether learners acquire them.
- **Not native-speaker reviewed.** Examples, glosses, plurals and register labels were machine-checked, but a native-speaker review is still recommended before publishing.
