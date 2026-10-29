// Question builders. Each returns null when it cannot produce a question with
// exactly one defensible answer; the generator then tries another type.

import { CEFR_LEVELS, type Article, type VocabularyWord } from '../../types';
import { shuffle, type Rng } from './random';
import {
  blankOut,
  coreForm,
  displayGerman,
  findInSentence,
  glossesConflict,
  normalizeAnswer,
  primaryGloss,
} from './text';

export type QuestionType =
  | 'de_en'        // L1: German -> English, multiple choice
  | 'en_de'        // L2: English -> German, multiple choice
  | 'context'      // L2: which word fits the sentence? multiple choice
  | 'fill_blank'   // L3: type the missing word in the sentence
  | 'en_de_typed'  // L3: type the German for an English word
  | 'article'      // L4: der / die / das
  | 'plural';      // L4: type the plural

export type QuestionLevel = 1 | 2 | 3 | 4;

export const QUESTION_LEVEL: Record<QuestionType, QuestionLevel> = {
  de_en: 1,
  en_de: 2,
  context: 2,
  fill_blank: 3,
  en_de_typed: 3,
  article: 4,
  plural: 4,
};

export const QUESTION_TYPES = Object.keys(QUESTION_LEVEL) as QuestionType[];

export interface QuizQuestion {
  id: string;
  wordId: number;
  type: QuestionType;
  level: QuestionLevel;
  format: 'choice' | 'typed';
  instruction: string;
  prompt: string;
  helper?: string;
  options?: string[];
  /** Normalized accepted answers (typed) or the exact correct option (choice). */
  accepted: string[];
  correctAnswer: string;
  /** Extra feedback after a wrong answer, e.g. a reliable gender rule. */
  hint?: string;
}

const OPTION_COUNT = 4;

// Candidate distractors per pool, part of speech, level and level gap; built once per pool
// so a question looks only at a few candidates instead of scanning thousands of words.
const candidateCache = new WeakMap<readonly VocabularyWord[], Map<string, VocabularyWord[]>>();

function candidatesFor(pool: readonly VocabularyWord[], word: VocabularyWord, gap: number): VocabularyWord[] {
  let byKey = candidateCache.get(pool);
  if (!byKey) candidateCache.set(pool, (byKey = new Map()));
  const key = `${word.part_of_speech}|${word.cefr_level}|${gap}`;
  let list = byKey.get(key);
  if (!list) {
    const level = CEFR_LEVELS.indexOf(word.cefr_level);
    list = pool.filter(
      (d) => d.part_of_speech === word.part_of_speech && Math.abs(CEFR_LEVELS.indexOf(d.cefr_level) - level) === gap,
    );
    byKey.set(key, list);
  }
  return list;
}

function pickDistractors(
  word: VocabularyWord,
  pool: readonly VocabularyWord[],
  rng: Rng,
  extraFilter: (d: VocabularyWord) => boolean,
  label: (d: VocabularyWord) => string,
): string[] | null {
  const correctLabel = normalizeAnswer(label(word));
  const seen = new Set([correctLabel]);
  const out: string[] = [];
  // Prefer distractors from the word's own level, so beginners aren't shown B2 words.
  for (let gap = 0; gap < CEFR_LEVELS.length; gap++) {
    // Lazy Fisher-Yates: draw random candidates until enough of them pass the filters.
    const list = candidatesFor(pool, word, gap).slice();
    for (let n = list.length; n > 0; n--) {
      const j = Math.floor(rng() * n);
      const d = list[j];
      list[j] = list[n - 1];
      if (d.id === word.id || glossesConflict(d.english, word.english) || !extraFilter(d)) continue;
      const l = label(d);
      const key = normalizeAnswer(l);
      if (seen.has(key)) continue;
      seen.add(key);
      out.push(l);
      if (out.length === OPTION_COUNT - 1) return out;
    }
  }
  return null;
}

function choice(
  word: VocabularyWord,
  type: QuestionType,
  instruction: string,
  prompt: string,
  correct: string,
  distractors: string[],
  rng: Rng,
  helper?: string,
): QuizQuestion {
  return {
    id: `${word.id}:${type}`,
    wordId: word.id,
    type,
    level: QUESTION_LEVEL[type],
    format: 'choice',
    instruction,
    prompt,
    helper,
    options: shuffle([correct, ...distractors], rng),
    accepted: [correct],
    correctAnswer: correct,
  };
}

function typed(
  word: VocabularyWord,
  type: QuestionType,
  instruction: string,
  prompt: string,
  correct: string,
  accepted: string[],
  helper?: string,
): QuizQuestion {
  return {
    id: `${word.id}:${type}`,
    wordId: word.id,
    type,
    level: QUESTION_LEVEL[type],
    format: 'typed',
    instruction,
    prompt,
    helper,
    accepted: [...new Set(accepted.map(normalizeAnswer))],
    correctAnswer: correct,
  };
}

export function buildDeEn(word: VocabularyWord, pool: readonly VocabularyWord[], rng: Rng): QuizQuestion | null {
  const d = pickDistractors(word, pool, rng, () => true, (x) => x.english);
  if (!d) return null;
  return choice(word, 'de_en', 'What does this mean?', displayGerman(word), word.english, d, rng);
}

export function buildEnDe(word: VocabularyWord, pool: readonly VocabularyWord[], rng: Rng): QuizQuestion | null {
  const d = pickDistractors(
    word, pool, rng,
    (x) => normalizeAnswer(coreForm(x)) !== normalizeAnswer(coreForm(word)),
    displayGerman,
  );
  if (!d) return null;
  return choice(word, 'en_de', 'How do you say this in German?', word.english, displayGerman(word), d, rng);
}

function sentenceBlank(word: VocabularyWord) {
  const match = findInSentence(word.example_sentence, coreForm(word));
  return match ? { match, blanked: blankOut(word.example_sentence, match) } : null;
}

export function buildContext(word: VocabularyWord, pool: readonly VocabularyWord[], rng: Rng): QuizQuestion | null {
  const s = sentenceBlank(word);
  if (!s) return null;
  // Distractors come from other topics and must not already appear in the sentence;
  // the translation is shown, so only one option matches the meaning.
  const d = pickDistractors(
    word, pool, rng,
    (x) =>
      x.topic !== word.topic &&
      findInSentence(word.example_sentence, coreForm(x)) === null &&
      normalizeAnswer(coreForm(x)) !== normalizeAnswer(s.match.text),
    coreForm,
  );
  if (!d) return null;
  return choice(word, 'context', 'Which word fits the sentence?', s.blanked, s.match.text, d, rng, word.example_translation);
}

export function buildFillBlank(word: VocabularyWord): QuizQuestion | null {
  const s = sentenceBlank(word);
  if (!s) return null;
  const answer = s.match.text;
  const hint = `${word.example_translation}  ·  starts with “${answer[0]}”, ${answer.replace(/\s/g, '').length} letters`;
  return typed(word, 'fill_blank', 'Type the missing word.', s.blanked, answer, [answer], hint);
}

const glossCountCache = new WeakMap<readonly VocabularyWord[], Map<string, number>>();

/** How many words in the pool have each main English meaning. */
function glossCounts(pool: readonly VocabularyWord[]): Map<string, number> {
  let counts = glossCountCache.get(pool);
  if (!counts) {
    counts = new Map();
    for (const x of pool) counts.set(primaryGloss(x.english), (counts.get(primaryGloss(x.english)) ?? 0) + 1);
    glossCountCache.set(pool, counts);
  }
  return counts;
}

export function buildEnDeTyped(word: VocabularyWord, pool: readonly VocabularyWord[]): QuizQuestion | null {
  // Typed recall is only fair when no other word shares the same main meaning.
  if ((glossCounts(pool).get(primaryGloss(word.english)) ?? 0) > 1) return null;
  // Nouns are only right together with their article.
  if (word.article) {
    const q = typed(word, 'en_de_typed', 'Type the German word.', word.english, displayGerman(word), [displayGerman(word)],
      'Noun: include der / die / das.');
    return { ...q, hint: genderHint(word) };
  }
  return typed(word, 'en_de_typed', 'Type the German word.', word.english, word.german, [coreForm(word), word.german]);
}

// Endings that predict the article almost without exception (99–100 % on the curriculum's 2,194 nouns;
// research/grammar-strategy). Less reliable rules (-e, -er, -um, -nis) are deliberately not shown.
const GENDER_RULES: [RegExp, string, Article][] = [
  [/ung$/, '-ung', 'die'], [/heit$/, '-heit', 'die'], [/keit$/, '-keit', 'die'], [/schaft$/, '-schaft', 'die'],
  [/tät$/, '-tät', 'die'], [/ion$/, '-ion', 'die'], [/ismus$/, '-ismus', 'der'],
];

/** "Words ending in -ung are always die." when a reliable rule fits the noun (and agrees with it). */
export function genderHint(word: Pick<VocabularyWord, 'german' | 'article'>): string | undefined {
  const head = word.german.toLowerCase().split(/[\s-]/).pop() ?? '';
  for (const [rx, ending, article] of GENDER_RULES) {
    if (rx.test(head) && word.article === article) return `Tip: nouns ending in ${ending} are ${article}.`;
  }
  return undefined;
}

export function buildArticle(word: VocabularyWord): QuizQuestion | null {
  if (word.part_of_speech !== 'noun' || !word.article) return null;
  return {
    id: `${word.id}:article`,
    wordId: word.id,
    type: 'article',
    level: QUESTION_LEVEL.article,
    format: 'choice',
    instruction: 'Choose the article.',
    prompt: `___ ${word.german}`,
    helper: word.english,
    options: ['der', 'die', 'das'],
    accepted: [word.article],
    correctAnswer: word.article,
    hint: genderHint(word),
  };
}

export function buildPlural(word: VocabularyWord): QuizQuestion | null {
  if (word.part_of_speech !== 'noun' || !word.article || !word.plural) return null;
  return typed(
    word, 'plural', 'Type the plural with its article.', `${displayGerman(word)} → ?`,
    `die ${word.plural}`, [`die ${word.plural}`], word.english,
  );
}

export function buildQuestion(
  type: QuestionType,
  word: VocabularyWord,
  pool: readonly VocabularyWord[],
  rng: Rng,
): QuizQuestion | null {
  switch (type) {
    case 'de_en': return buildDeEn(word, pool, rng);
    case 'en_de': return buildEnDe(word, pool, rng);
    case 'context': return buildContext(word, pool, rng);
    case 'fill_blank': return buildFillBlank(word);
    case 'en_de_typed': return buildEnDeTyped(word, pool);
    case 'article': return buildArticle(word);
    case 'plural': return buildPlural(word);
  }
}
