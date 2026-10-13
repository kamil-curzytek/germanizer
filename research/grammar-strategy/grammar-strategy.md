# Grammar strategy: research and plan

> **Status (2026-10-07): implemented** for all 42 topics A1–B2 (67 skills, 669 exercises). The daily-load decision (§4.6) was Option A: grammar items are extra to the words-per-day target. See README → *Grammar practice*.

**Question:** How should Lernbrot teach grammar so learners can actually *use* it, not just read about it?

**Short answer.** Today's grammar section is a well-ordered reference book: 28 full A1–A2 lessons and 14 B1–B2 outlines, with no practice, no review and no link to the daily lesson. The evidence points to one change above all: **every rule needs practice that is checked, explained when wrong, and brought back over time, mixed with other rules.** Concretely:
1. Split each lesson into small **grammar skills** (e.g. "dative after *mit/bei/zu*", "verb at the end after *weil*").
2. Give each skill auto-graded exercises with **feedback that names the rule**.
3. Put **2–3 grammar items into each daily lesson**, chosen by the same FSRS scheduler as words, from skills the learner has already studied.
4. Track which **kind of mistake** each learner makes and point them to the matching lesson.

Word order deserves the most attention: in German learner exams, about a third of all errors are words in the wrong place.

---

## 1. Where the app is today

| Part | State |
|---|---|
| Lessons | 42 topics in a sensible order: A1 (16) and A2 (12) fully written (rule, examples, common mistake, everyday phrases, memory tip); B1 (8) and B2 (6) title + summary only |
| Practice | None. Grammar is read, never practised or tested |
| Review | None. A lesson read once is never revisited |
| Link to vocabulary | 74 word → topic links (e.g. *helfen* → dative), shown only on the word card |
| Grammar inside the vocabulary quiz | Article (der/die/das) and plural questions for well-known nouns |

## 2. What the research says

| Finding | Evidence | Implication |
|---|---|---|
| **Explicit instruction works, and better than implicit.** Large gains from focused instruction; explicit beats implicit for simple *and* complex features, also on delayed tests and on spontaneous (implicit) use | Norris & Ortega 2000 (49 studies); Spada & Tomita 2010; Goo et al. 2015 (update with 34 studies to 2011) | Keep the short explicit lessons, and make sure each is followed by practice |
| **Rule knowledge becomes usable only through practice.** Skill acquisition: declarative knowledge → proceduralised through deliberate practice → automatised | DeKeyser (skill acquisition theory; DeKeyser & Criado 2013) | Each lesson needs many practice items: few at first, then spread over weeks |
| **Purely mechanical drills add little**, because they can be done without attending to meaning. Practice should require understanding the sentence | Wong & VanPatten 2003 (*Foreign Language Annals*); the meaningful/mechanical distinction (Paulston 1972) | Exercises use real example sentences with a translation shown. The learner must use the meaning (who does what to whom), not just fill a pattern |
| **Structured input + a short rule helps with German case.** With explicit information, twice as many learners began reading OVS sentences (*Den Hund beißt der Mann*) correctly, and they started sooner | Culman, Henry & VanPatten 2009 (German accusative) | Add "who does what?" interpretation items for the accusative/dative, with a one-line rule first |
| **Spacing helps grammar too, but the best gap varies.** Distributed beat massed practice on long-term tests (Bird 2010); some studies favour shorter gaps (Suzuki 2017); 3.5 vs 7 days made little difference in a classroom study, where individual differences mattered more (Kasprowicz et al. 2019) | as cited | Space grammar reviews and adapt to the learner, which the FSRS scheduler already does. Don't hard-code a single gap |
| **Mixing rules in practice improves long-term retention** (interleaving) | Nakata & Suzuki 2019 (*Modern Language Journal*, grammar exercises); Pan et al. 2019 (Spanish verb tenses: better after a week with interleaving over two sessions, but no gain within a single session) | Introduce a new rule in a short block, then review it **mixed** with other rules in daily sessions |
| **Corrective feedback works**, and output-pushing / metalinguistic feedback is among the most effective types | Li 2010 (33 studies); Lyster & Saito 2010 (15 classroom studies, durable effects) | Every wrong answer shows the correct form **and the rule** ("*mit* always takes the dative → *dem*"), plus a link to the lesson |
| In German CALL specifically, **feedback explaining the error led learners to correct more of their errors** than less detailed feedback | Heift & Rimrott 2008; Heift (longitudinal study of German learners using a sentence-building exercise) | Error-specific messages, not just ✗ |
| **German word order develops in fixed stages.** First adverb fronting, then the verb split (modal/Perfekt participle to the end), then inversion (verb 2nd after a fronted element), then verb-final in subordinate clauses. Teaching works best when the learner is ready for the next stage | ZISA / Processability Theory (Pienemann; teachability hypothesis) | Keep the current order (V2 → separable/modal → *weil/dass*). Unlock subordinate-clause practice after the V2 skills are stable |
| **Word order is the biggest error area in real German learner writing.** In the MERLIN corpus (German exam texts A1–C1), **34 % of errors are words in the wrong position**, 12.1 % of those a misplaced verb, and **95 % of verb-placement errors occur at A2–B2**. In MERLIN, verb-final structures appear in 44 % of B1 texts but in most A2 texts not at all; inversion is still inaccurate at B1 | GermDetect (Michael et al., BEA 2025) using MERLIN (Boyd et al. 2014); Wisniewski 2020 (*Int. J. of Learner Corpus Research*) | Word order is a priority from A1 to B2 |
| **Case, gender and adjective endings are the other big areas.** Case is acquired nominative → accusative → dative and stays hard; in at least one learner error analysis, adjective endings were the most frequent error type, since they depend on article, case and gender (a single small study, so treat it as indicative) | L2 acquisition studies of German case; learner error analyses | Separate small skills for case after prepositions, verbs with the dative, adjective endings |
| **Gender follows probabilistic cues** (semantic, morphological, phonological); a few suffixes are near-deterministic, and reliable cues speed up correct retrieval | Köpcke & Zubin; gender-cue processing studies | Teach the reliable rules as hints; otherwise learn the article with each noun (§3a) |

## 3. Our own data

`content_analysis.py`, results in `content_analysis.json`.

### 3a. How far do noun endings predict the article? (2,194 nouns in the curriculum)

| Rule | Nouns | Correct |
|---|---:|---:|
| -ung → die | 229 | 99.6 % (exception: *der Sprung*) |
| -heit, -keit, -schaft, -tät → die | 65 | 100 % |
| -ion → die | 44 | 97.7 % (*das Stadion*) |
| -e → die | 406 | 87.4 % (*das Ende, der Name, das Auge, der Junge, der Kaffee*) |
| -er → der | 199 | 68.3 % (*die Mutter, das Wasser, die Nummer*) |
| -um → das | 21 | 71.4 % (*der Raum, der Baum, der Traum*) |
| -nis → das | 18 | 66.7 % (*die Erlaubnis, die Kenntnis*) |

Rules that are ≥ 90 % reliable cover only **16.7 %** of our nouns; any rule at all covers about half.

**Conclusion:** the article must be learned with each noun (the app already asks article questions). Show the reliable rules as hints: *-ung, -heit, -keit, -schaft, -ion, -tät* → die; *-chen, -ment* → das (mostly); *-ismus* → der. Show *-e* as "usually die". Unreliable rules (*-er*, *-nis*) are not worth teaching.

### 3b. Is there enough material for automatic exercises?

Example sentences that contain each pattern (conservative pattern matching; precision not yet checked by hand):

| Pattern | Curriculum + app sentences | of which in today's app seed |
|---|---:|---:|
| Two-way preposition + article (*in der / in die*) | 300 | 11 |
| Article + adjective + noun (endings) | 312 | 12 |
| Reflexive pronoun | 290 | 22 |
| Negation *nicht / kein* | 282 | 20 |
| Fronted time/place + verb (inversion) | 273 | 16 |
| Modal verb … infinitive at the end | 271 | 43 |
| Verb-first question | 229 | 30 |
| Perfekt (auxiliary … participle at the end) | 167 | 2 |
| Separable verb split (prefix at the end) | 113 | — |
| Dative preposition + article (*mit dem*) | 110 | 12 |
| Accusative preposition + article (*für den*) | 94 | 8 |
| Subordinate clause, verb at the end (*weil/dass/wenn*) | 79 | 6 |
| *zu* + infinitive | 23 | 2 |
| Comparative / superlative | 12 | 1 |
| Verbs with stored forms (3sg, preterite, perfect) | 1,031 | — |
| Nouns with a plural | 1,888 | — |

**Conclusion:**
- Once the 4,500-entry curriculum is in the app, there is ample material for most skills. Verb forms and plurals are covered by the forms already stored.
- Today's 266-word seed is too thin, so A1 practice needs a set of written-for-purpose items (~15–20 per skill) in the meantime.
- Thin areas (comparatives, *zu* + infinitive, subordinate clauses) need written items in any case.

## 4. Recommended design

### 4.1 Skills instead of whole topics
Each lesson splits into 1–4 **skills**, each small enough that one question tests one decision. Examples:
- *Accusative*: "article form den/einen" and "accusative after *für/ohne/gegen/durch/um*".
- *Word order*: "verb 2nd after a fronted time/place".
- *Perfekt*: "haben or sein" and "form the participle".

About 30 skills at A1, 25 at A2. Each skill has its own FSRS memory state per learner, like a word.

### 4.2 Exercise types (deterministic, one defensible answer, auto-graded)

| Type | Example | Skills | Source |
|---|---|---|---|
| **Form in context** (choice) | *Ich fahre mit ___ Bus.* der / den / **dem** (translation shown) | case after prepositions, articles, possessives, adjective endings | generated from example sentences + validated |
| **Typed form** | *du ___ (fahren)* → **fährst**; *Ich habe das Buch ___ (kaufen)* → **gekauft** | conjugation, participles, plural, comparative | stored verb/noun forms |
| **Build the sentence** (tap the chunks in order) | [weil] [ich] [müde] [bin] | V2, inversion, verb split, verb-final | example sentences split into chunks; graded on **verb position**, since German allows several orders for the rest |
| **Who does what?** (structured input) | *Den Hund beißt der Mann.* Who bites? → the man | accusative/dative markers, OVS order | written items (Culman et al. 2009 design) |
| **Find the mistake** (later) | *Ich habe nach Berlin gefahren.* → *bin* | haben/sein, word order | written items |

Every item passes a validator like the vocabulary one: exactly one correct option, the translation disambiguates, nothing outside the learner's studied skills.

### 4.3 Learning flow
1. **Read** the lesson (as today, about 2 minutes).
2. **Practise right away:** 5–8 items for that skill, blocked (one rule), repeated until 3 are correct, unscored. This is successive relearning, as in the vocabulary quiz.
3. **Review in the daily lesson:** 2–3 grammar items from studied skills, chosen by FSRS (lowest predicted recall first) and **mixed** across skills.
4. **Unlock order** follows the developmental stages: subordinate-clause word order opens once the V2 and verb-split skills are stable (e.g. strong in FSRS terms).

### 4.4 Feedback
- **Wrong:** correct answer + the rule in one line + a typical mistake if relevant, with a link to the lesson. For example: "*mit* always takes the dative: *dem Bus*. → Lesson: Dative basics".
- Article questions in the vocabulary quiz also show the reliable ending rule where one applies: "*-ung* words are always *die*".

### 4.5 Weak spots
- Every grammar answer and every article/plural answer is tagged with an **error category**: gender, case, verb position, verb form, adjective ending, preposition.
- *Progress* shows the 2–3 weakest categories, with a "practise this" button that starts a short mixed set.

### 4.6 Daily load (needs a decision)
- **Option A (recommended):** grammar items are **extra**, a fixed 2–3 per day, so they don't push out vocabulary.
- **Option B:** they count inside "words per day".

## 5. Implementation plan

| Phase | Work | Files / data | Tests |
|---|---|---|---|
| **G1 A1 skills + items** | Define ~30 A1 skills. Generator from example sentences + written items (~15–20 per skill). Validator (uniqueness, translation shown, uses only studied vocabulary where possible) | `content/grammar-skills.json`, `scripts/build-grammar-items.mjs` → seed | Content tests like the vocabulary ones (every item has exactly one answer) |
| **G2 Practice after a lesson** | "Practise" button on each A1 lesson: blocked items to criterion, unscored | `GrammarTopic.tsx`, `src/lib/grammar/` (exercise builders + grading, pure) | Unit tests for each exercise type and its grading |
| **G3 Grammar in the daily lesson** | `grammar_progress` table (FSRS state per user × skill), `daily_session_grammar` (2–3 items). Selection in `create_daily_session_for` (studied skills, lowest predicted recall, mixed). Grading via `submit_quiz` (extended) | migration 0007, quiz page | PGlite DB tests (RLS, selection, mixing, idempotency); simulation update |
| **G4 Feedback and weak spots** | Error categories on answers, rule lines, *Progress* weak-spot panel | `quiz_answers.error_category`, Progress UI | Unit + DB tests |
| **G5 A2 skills, then finish the B1/B2 lessons** | As G1 for A2; write the 14 B1/B2 lessons | content | as above |
| **Later** | "Who does what?" listening items, find-the-mistake, sentence production with flexible grading | — | — |

G1–G3 deliver the core change: grammar that is practised and reviewed. G4 makes it personal.

## 6. Limitations
- **The research base is mostly classroom studies, often with English as the target language.** German-specific evidence covers word-order development (ZISA, MERLIN), case processing and gender cues, and CALL feedback (Heift).
- **Spacing studies on grammar disagree on the best gap**, hence the adaptive scheduler rather than a fixed gap.
- **The MERLIN numbers describe written exam texts**, not speech.
- **The §3b pattern counts are conservative heuristics.** Generated items still need the validator and spot checks.
- **Sentence building is graded on verb position only.** German word order is partly free, and a fully flexible grader is a later project.

## Sources
- Norris & Ortega (2000), Spada & Tomita (2010): https://www.eas.utoronto.ca/node/790 · Goo, Granena, Yilmaz & Novella (2015): https://www.degruyterbrill.com/document/doi/10.1075/sibil.48.18goo/html
- DeKeyser & Criado (2013), automatization and skill acquisition: https://digitum.um.es/digitum/bitstream/10201/142072/1/DeKeyser%20and%20Criado_Automatization_Skill%20Acquisition%20and%20Practice%20in%20Second%20Language%20Acquisition_2013.pdf
- Wong & VanPatten (2003), "The evidence is IN: drills are OUT": https://web.pdx.edu/~fischerw/courses/advanced/methods_docs/pdf_doc/wbf_collection/0351_0400/0385_FLA_Wong_DrillsAreOUT.pdf
- Culman, Henry & VanPatten (2009), explicit information in processing instruction, German accusative: https://resolve.cambridge.org/core/journals/studies-in-second-language-acquisition/article/abs/more-on-the-effects-of-explicit-information-in-instructed-sla/F30D4BC87BEA0FE953CD680A341EE151
- Bird (2010): https://research.uaeu.ac.ae/en/publications/effects-of-distributed-practice-on-the-acquisition-of-second-lang/ · Suzuki on spacing in grammar: https://www.benjamins.com/catalog/bct.116.02suz · Kasprowicz, Marsden & Sephton (2019): https://eprints.whiterose.ac.uk/141710/
- Nakata & Suzuki (2019), mixing grammar exercises: https://www.jbe-platform.com/content/journals/10.1075/jsls.00047.buh (citation context) · Pan, Tajran, Lovelett, Osuna & Rickard (2019), interleaving and foreign-language learning: https://discovery-imamu.kwaretech.com/EdsRecord/edsbas,edsbas.988BAC9D
- Li (2010) and Lyster & Saito (2010), corrective-feedback meta-analyses: https://researchspace.auckland.ac.nz/handle/2292/24985?show=full · https://resolve.cambridge.org/core/journals/studies-in-second-language-acquisition/article/oral-feedback-in-classroom-sla/4999EE1C8379B2BF026B148EAF373CA1
- Heift, metalinguistic feedback in German CALL: https://www.jbe-platform.com/content/journals/10.1075/itl.19009.hei · https://journal.equinoxpub.com/Calico/article/view/17072
- Processability theory / ZISA: https://en.wikipedia.org/wiki/Processability_theory · https://www.geisteswissenschaften.fu-berlin.de/izeus/forschung/veranstaltungen/dahlemlectureslinguistics/downloads/Processability__Theory_FU_Berlin.pdf
- Michael et al. (2025), GermDetect (MERLIN error statistics, quoted from the paper): https://aclanthology.org/2025.bea-1.59.pdf · Wisniewski (2020), inversion and verb-end in MERLIN A2/B1: https://benjamins.com/catalog/ijlcr.18008.wis · MERLIN corpus: http://www.lrec-conf.org/proceedings/lrec2014/pdf/606_Paper.pdf
- German case acquisition order: https://www.degruyterbrill.com/document/doi/10.1515/zgl.2011.003/html · gender cues (Köpcke & Zubin; cue reliability): https://www.cambridge.org/core/journals/applied-psycholinguistics/article/accessing-grammatical-gender-in-german-the-impact-of-gendermarking-regularities/B3A722F50B583D26AA0DFD10C6BEF4B2
