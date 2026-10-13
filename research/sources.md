# Sources

Every source below was either **used as data** (downloaded and processed by `research/pipeline/`) or **read** for its findings. Third-party data files are stored in `research/sources/`, which is excluded from git because several licences don't allow redistribution. Re-download them with the URLs below.

## Data used in the pipeline

| Source | What it is | Unit | Size | Used for | Licence / access |
|---|---|---|---|---|---|
| **SUBTLEX-DE**, Brysbaert, Buchmeier, Conrad, Jacobs, Bölte & Böhl (2011), *Experimental Psychology* 58(5) | Word frequencies from German film/TV subtitles | Word forms + lemma file (`SUBTLEXDE_LemmasJV.csv`) | 25.4 M tokens, 4,610 films/series | **Spoken-language proxy** (lemma level) | Free for education/research (CC BY-NC-ND 3.0). Mirror: OSF project `479um` → FrequencyCorpora |
| **OpenSubtitles 2018** frequency list (hermitdave/FrequencyWords) | Word-form frequencies from German subtitles | Lower-cased word forms | ~151 M tokens (top 50k forms) | Secondary spoken proxy, **form level only** (lower-casing breaks noun lemmatization) | CC BY-SA 4.0, github.com/hermitdave/FrequencyWords |
| **Leipzig Corpora Collection** `deu_news_2023_300K` | German news, 2023 | Word forms (case-sensitive), lemmatized here | 300 k sentences, ~4.5 M word tokens | **Written frequency (news)** | CC BY, downloads.wortschatz-leipzig.de |
| **Leipzig Corpora Collection** `deu-de_web_2021_300K` | Web text from the `.de` domain, 2021 | Word forms, lemmatized here | 300 k sentences, ~4.5 M word tokens | **Written frequency (everyday web, Germany)** | CC BY |
| **Goethe-Zertifikat A1 (Start Deutsch 1) Wortliste** | Exam vocabulary inventory | ~650 entries | — | CEFR evidence, **not copied** | goethe.de (PDF) |
| **Goethe-Zertifikat A2 Wortliste** (2016) | Exam vocabulary inventory | ~1,300 lexical units | — | CEFR evidence, **not copied** | goethe.de (PDF) |
| **Goethe-Zertifikat B1 Wortliste** (2016) | Exam vocabulary inventory (Goethe-Institut, Universität Freiburg/Schweiz, ÖSD) | ~2,400 lexical units | — | CEFR evidence + **regional-variant flags (A/CH)**, **not copied** | goethe.de (PDF) |
| **simplemma 2.0** (Barbaresi) | Lemmatizer | — | — | Normalizing word forms → lemmas | MIT, PyPI |
| **FOLK** (Forschungs- und Lehrkorpus Gesprochenes Deutsch), IDS Mannheim, via DGD | Recorded natural spoken interaction | Lemma frequency list | ~3.7 M transcribed tokens (v2.26) | **Pending.** The pipeline picks it up automatically when `research/sources/folk_lemmas*.json` is added | Free registration at dgd.ids-mannheim.de |

## Literature read

| Reference | Finding used |
|---|---|
| Council of Europe (2020). *CEFR Companion Volume*. Strasbourg. | Competence descriptors per level (vocabulary range, spoken interaction, etc.). The CEFR gives **no word counts**. |
| Goethe-Institut, prefaces of the A1/A2/B1 Wortlisten (read in full) | A1: ~650 entries, *"etwa die Hälfte"* should be active. A2 ~1,300 and B1 ~2,400 lexical units, to be mastered *"zumindest rezeptiv"*. Predictable derivatives and compounds are **not** counted. A2 is based on the **German** standard variety. B1 is **pluricentric** (A/CH variants are separate entries). |
| Tschirner, Hacking & Rubio, *Vocabulary Size as a Screener for Reading Proficiency* (ILR presentation; read in full) | German n = 97, Russian n = 48, Spanish n = 52. Vocabulary Levels Test with 5 frequency bands of the 5,000 most frequent words. Predicted bands: 1k ≈ ILR 1, 2k ≈ 1+, 3k ≈ 2, 4k ≈ 2+, 5k ≈ 3. **For German the relationship was weak** (R² = .392, ρ = .57), against .80/.87 for Spanish/Russian. |
| Tschirner et al. (2019), as reported in secondary sources (not accessed directly) | Reading-proficiency mapping for German: A2 ≈ 1,600, B1.1 ≈ 2,400, B1.2 ≈ 3,200, B2 ≈ 4,000, C1.1 ≈ 5,000 (receptive lemmas). Treated as **reported, not verified**. |
| Milton, J. (2010). The development of vocabulary breadth across the CEFR levels. In Bartning, Martin & Vedder (eds.), *EUROSLA Monographs* 1, 211–232. Read via Milton (2011), *EUROSLA Monographs* 2, Table 3 | EFL learners in Greece (>10,000), X_Lex recognition of the 5,000 most frequent **lemmas**: A1 < 1,500, A2 1,500–2,500, B1 2,500–3,250, B2 3,250–3,750, C1 3,750–4,500, C2 4,500–5,000 |
| Milton, J. (2009). *Measuring Second Language Vocabulary Acquisition*, p. 58 (via Milton 2011) | BNC (English): the 2,000 most frequent lemmas ≈ **90 % of spoken** and ≈ **70 % of written** text. **Origin of the "2,000 words" claim.** |
| Nation, I. S. P. (2006). How large a vocabulary is needed for reading and listening? *Canadian Modern Language Review* 63(1) | 98 % coverage needs 8–9k word families (reading), 6–7k (listening). English, word families |
| Laufer, B. & Ravenhorst-Kalovski, G. (2010). *Reading in a Foreign Language* 22(1) | 95 % coverage = "minimally acceptable" comprehension, 98 % = optimal. 4–5k families give ~95 % (English) |
| van Zeeland, H. & Schmitt, N. (2013). *Applied Linguistics* 34(4) | Listening: ~95 % coverage can be enough. Reached with 2–3k word families in English spoken narratives |
| Adolphs, S. & Schmitt, N. (2003). Lexical coverage of spoken discourse. *Applied Linguistics* 24(4) | Spoken discourse needs more vocabulary than older estimates suggested (cited via Milton 2011) |
| Jones, R. & Tschirner, E. (2006). *A Frequency Dictionary of German*. Routledge | 4,034 most frequent lemmas from a 4.2 M-word corpus split evenly between spoken, fiction and non-fiction. Basis of the German vocabulary tests above (not accessed: commercial) |
| Schmidt, T. (2014 ff.) papers on FOLK / LeGeDe (IDS Mannheim) | FOLK design: lemmatized and POS-tagged with STTS adapted to conversation. LeGeDe = lexical resource for spoken German (discourse markers, interaction) |

## Deliberately not used

- **Copied word lists** (Goethe or others): used only as membership evidence. No Goethe example sentence or entry text is reproduced in `data/`.
- **Generic "top 1000/2000 words" web lists**: no traceable corpus or unit definition.
- **Popular coverage figures** such as "1,000 words = 80 % of texts" with no primary source: replaced by our own measurements (`coverage-analysis.md`).
