// Merges the research dataset (data/german-all.json) into content/vocabulary.json.
// Hand-curated words (id < 10001) keep their content but take the dataset's CEFR level;
// dataset entries that duplicate one of them are not imported again. Every other entry is imported with id >= 10001, remembered
// by its dataset id in `src`, so re-running keeps ids stable (ids are never reused).
// Within each level, words are ordered active-first, then by tier and priority score.
// Usage: node scripts/import-vocabulary.mjs   (then npm test && npm run seed:build)
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const vocabPath = join(root, 'content/vocabulary.json');
const vocab = JSON.parse(readFileSync(vocabPath, 'utf8'));
const dataset = JSON.parse(readFileSync(join(root, 'data/german-all.json'), 'utf8'));

const FIRST_IMPORTED_ID = 10001;

// The app's part-of-speech set is smaller; small classes join the closest larger one
// so multiple-choice questions still find distractors of the same kind.
const POS = {
  noun: 'noun', verb: 'verb', adjective: 'adjective', adverb: 'adverb', preposition: 'preposition',
  conjunction: 'conjunction', pronoun: 'pronoun', phrase: 'phrase',
  determiner: 'pronoun', numeral: 'adjective', particle: 'adverb', interjection: 'phrase',
};

// Hand-curated words whose dataset entry is spelled differently (dataset german -> app de).
const ALIASES = {
  'sich erinnern an': 'sich erinnern',
  'sich kümmern um': 'sich kümmern',
  'sich entscheiden für': 'sich entscheiden',
  'sich verlassen auf': 'sich verlassen',
  'sich gewöhnen an': 'sich gewöhnen',
  'auseinandersetzen': 'sich auseinandersetzen',
  'Es lässt sich nicht leugnen, dass ...': 'Es lässt sich nicht leugnen',
};

// The dataset's ~45 topics folded into the app's 11. create_daily_session_for interleaves new
// words round-robin by topic, so many small topics would pull their top words ahead of more useful ones.
const TOPICS = {
  people: 'people', family: 'people', feelings: 'people', social: 'people', body: 'people', description: 'people',
  communication: 'communication', grammar: 'communication', discourse: 'communication', opinions: 'communication',
  media: 'communication', politics: 'communication', society: 'communication', history: 'communication',
  everyday: 'everyday', numbers: 'everyday', weather: 'everyday', nature: 'everyday', environment: 'everyday',
  place: 'everyday', places: 'everyday', events: 'everyday',
  time: 'time',
  home: 'home', housing: 'home',
  work: 'work', education: 'work', economy: 'work', technology: 'work',
  food: 'food',
  transport: 'transport', city: 'transport',
  shopping: 'shopping', money: 'shopping', clothing: 'shopping', services: 'shopping',
  travel: 'travel', leisure: 'travel',
  appointments: 'appointments', healthcare: 'appointments', health: 'appointments', bureaucracy: 'appointments',
  law: 'appointments', emergency: 'appointments',
};

const MODAL_VERBS = new Set(['können', 'müssen', 'dürfen', 'sollen', 'wollen', 'mögen', 'möchten']);

const key = (s) => s.toLowerCase().replace(/[.,!?…]/g, '').replace(/\s+/g, ' ').trim();

function grammarLinks(e, pos) {
  const g = e.grammar;
  const out = new Set();
  if (g.separable) out.add('separable-verbs');
  if (g.reflexive) out.add('reflexive-verbs');
  if (g.preposition && pos === 'verb') out.add('verbs-with-prepositions');
  if (g.case?.includes('Dativ') && pos === 'verb') out.add('dative-verbs');
  if (g.case?.includes('Genitiv')) out.add('genitive');
  if (g.auxiliary === 'sein') out.add('perfekt-sein');
  if (pos === 'preposition') out.add('prepositions');
  if (g.forms?.comparative) out.add('comparative-superlative');
  if (MODAL_VERBS.has(e.german)) out.add('modal-verbs');
  return [...out];
}

function note(e) {
  const parts = [];
  const reg = e.register.filter((r) => r !== 'neutral');
  if (reg.length) parts.push(`Register: ${reg.join(', ')}.`);
  if (e.grammar.notes) parts.push(e.grammar.notes.trim().replace(/([^.!?])$/, '$1.'));
  const forms = Object.values(e.grammar.forms ?? {});
  if (forms.length && !forms.every((f) => e.grammar.notes?.includes(f))) parts.push(`Forms: ${forms.join(', ')}.`);
  if (e.learningMode === 'receptive') parts.push('Mainly to understand when reading or listening.');
  return parts.length ? parts.join(' ') : undefined;
}

const sentence = (s) => (/[.!?]$/.test(s) ? s : `${s.replace(/\s*…$/, '')}.`);

function convert(e, id) {
  const pos = POS[e.partOfSpeech];
  if (!pos) throw new Error(`unknown part of speech "${e.partOfSpeech}" for ${e.id}`);
  const topic = TOPICS[e.topics[0]];
  if (!topic) throw new Error(`unknown topic "${e.topics[0]}" for ${e.id}`);
  const isNoun = pos === 'noun';
  const w = {
    id,
    de: e.german,
    ...(isNoun ? { art: e.article } : {}),
    ...(isNoun && e.plural && !e.grammar.pluralOnly && !e.grammar.singularOnly ? { pl: e.plural } : {}),
    en: e.english.join(', '),
    pos,
    lvl: e.cefr,
    topic,
    ex: sentence(e.example.german),
    exEn: sentence(e.example.english),
  };
  const n = note(e);
  if (n) w.note = n;
  const links = grammarLinks(e, pos);
  if (links.length) w.grammar = links;
  w.src = e.id;
  return w;
}

const handCurated = vocab.words.filter((w) => w.id < FIRST_IMPORTED_ID);
const importedBySrc = new Map(vocab.words.filter((w) => w.src && w.id >= FIRST_IMPORTED_ID).map((w) => [w.src, w]));
const handByKey = new Map(handCurated.map((w) => [`${key(w.de)}|${w.pos}|${w.art ?? ''}`, w]));

let nextId = Math.max(FIRST_IMPORTED_ID - 1, ...vocab.words.map((w) => w.id)) + 1;
const sortKey = new Map(); // word id -> [receptive, tier, -score]
const imported = [];
let skipped = 0;

for (const e of dataset) {
  const de = ALIASES[e.german] ?? e.german;
  const hand = handByKey.get(`${key(de)}|${POS[e.partOfSpeech]}|${e.partOfSpeech === 'noun' ? e.article : ''}`);
  const order = [e.learningMode === 'receptive' ? 1 : 0, e.priorityTier, -e.evidence.priorityScore];
  if (hand) {
    hand.src = e.id;
    hand.lvl = e.cefr;
    sortKey.set(hand.id, order);
    skipped++;
    continue;
  }
  const w = convert(e, importedBySrc.get(e.id)?.id ?? nextId++);
  sortKey.set(w.id, order);
  imported.push(w);
}

// Imported words that left the dataset stay (their ids may have user progress).
const kept = new Set(imported.map((w) => w.src));
const orphans = [...importedBySrc.values()].filter((w) => !kept.has(w.src));
for (const w of orphans) console.warn(`warn: ${w.src} is no longer in the dataset, keeping id ${w.id}`);

const LEVELS = ['A1', 'A2', 'B1', 'B2'];
const handPosition = new Map(handCurated.map((w, i) => [w.id, i]));
const rank = (w) => sortKey.get(w.id) ?? [0, 2, 0]; // unmatched hand-curated words: early tier 2
const cmp = (a, b) => {
  const ka = rank(a), kb = rank(b);
  for (let i = 0; i < ka.length; i++) if (ka[i] !== kb[i]) return ka[i] - kb[i];
  return (handPosition.get(a.id) ?? Infinity) - (handPosition.get(b.id) ?? Infinity) || a.id - b.id;
};
const words = [...handCurated, ...imported, ...orphans]
  .sort((a, b) => LEVELS.indexOf(a.lvl) - LEVELS.indexOf(b.lvl) || cmp(a, b));

// Typed English->German recall is skipped for words that share their main (first) English meaning.
// When an imported word's first meaning is already taken by an earlier word, lead with another of
// its meanings that is still free ("appointment, date" -> "date, appointment").
const primary = (en) => en.split(/[,;]/)[0].trim().toLowerCase();
const claimed = new Set(handCurated.map((w) => primary(w.en)));
let reordered = 0;
for (const w of words) {
  if (w.id < FIRST_IMPORTED_ID) continue;
  const glosses = w.en.split(', ');
  const free = glosses.findIndex((g) => !claimed.has(primary(g)));
  if (free > 0) {
    w.en = [glosses[free], ...glosses.filter((_, i) => i !== free)].join(', ');
    reordered++;
  }
  claimed.add(primary(w.en));
}
console.log(`reordered the English meanings of ${reordered} imported words to avoid a shared main meaning`);

vocab._format =
  'One object per word. id: stable, never reuse. Hand-curated words: A1 1-999, A2 1001-1999, B1 2001-2999, B2 3001-3999. ' +
  'Words imported from data/german-all.json by scripts/import-vocabulary.mjs: id >= 10001, any level; src = dataset id (keeps ids stable on re-import). ' +
  'Order within a level = frequency_rank (most useful first; set by the import script). ' +
  'de: German without article (nouns) - article goes in art, plural in pl (without \'die\'). grammar: slugs from content/grammar.json.';
vocab.words = words;
// One word per line keeps the file (and its diffs) readable.
writeFileSync(
  vocabPath,
  `{\n  "_format": ${JSON.stringify(vocab._format)},\n  "words": [\n` +
    words.map((w) => `    ${JSON.stringify(w)}`).join(',\n') +
    '\n  ]\n}\n',
);

const by = Object.fromEntries(LEVELS.map((l) => [l, words.filter((w) => w.lvl === l).length]));
console.log(`wrote ${vocabPath}: ${words.length} words (${handCurated.length} hand-curated, ${imported.length} imported, ${skipped} dataset entries matched hand-curated words)`, by);
