// Quality gates for the seed content and for every question the engine can generate from it.
import { describe, expect, it } from 'vitest';
import { loadContent } from '../scripts/build-seed.mjs';
import { buildQuestion, QUESTION_TYPES, type QuizQuestion } from '../src/lib/quiz';
import { createRng } from '../src/lib/quiz/random';
import { coreForm, findInSentence, glossesConflict, normalizeAnswer, primaryGloss } from '../src/lib/quiz/text';
import type { VocabularyWord } from '../src/types';

const { words, topics } = loadContent() as unknown as { words: (VocabularyWord & { grammar: string[] })[]; topics: any[] };

describe('vocabulary seed', () => {
  it('has the research curriculum with the planned level spread', () => {
    const by = (l: string) => words.filter((w) => w.cefr_level === l).length;
    expect(words.length).toBeGreaterThanOrEqual(4500);
    expect(by('A1')).toBeGreaterThanOrEqual(800);
    expect(by('A2')).toBeGreaterThanOrEqual(700);
    expect(by('B1')).toBeGreaterThanOrEqual(1400);
    expect(by('B2')).toBeGreaterThanOrEqual(1200);
  });

  it('has unique ids and unique German entries', () => {
    expect(new Set(words.map((w) => w.id)).size).toBe(words.length);
    // the article separates homonyms (der/die Leiter)
    expect(new Set(words.map((w) => `${w.german}|${w.part_of_speech}|${w.article}`)).size).toBe(words.length);
  });

  it('gives every noun an article, and only nouns', () => {
    for (const w of words) {
      if (w.part_of_speech === 'noun') expect(w.article, w.german).toMatch(/^(der|die|das)$/);
      else expect(w.article, w.german).toBeNull();
      if (w.part_of_speech === 'noun') expect(w.german[0], w.german).toBe(w.german[0].toUpperCase());
    }
  });

  it('gives every word a complete example with translation', () => {
    for (const w of words) {
      expect(w.example_sentence.length, w.german).toBeGreaterThan(5);
      expect(w.example_translation.length, w.german).toBeGreaterThan(3);
      expect(w.example_sentence, w.german).toMatch(/[.!?]$/);
    }
  });

  it('covers the required everyday topics and parts of speech', () => {
    const t = new Set(words.map((w) => w.topic));
    for (const topic of ['home', 'work', 'food', 'shopping', 'transport', 'appointments', 'communication', 'people', 'time', 'everyday', 'travel']) {
      expect(t.has(topic), topic).toBe(true);
    }
    const pos = new Set<string>(words.map((w) => w.part_of_speech));
    for (const p of ['noun', 'verb', 'adjective', 'adverb', 'preposition', 'phrase']) expect(pos.has(p), p).toBe(true);
  });

  it('gives most words a main English meaning of their own (shared ones get no typed English->German recall)', () => {
    const count = new Map<string, number>();
    for (const w of words) count.set(primaryGloss(w.english), (count.get(primaryGloss(w.english)) ?? 0) + 1);
    const shared = words.filter((w) => count.get(primaryGloss(w.english))! > 1);
    expect(shared.length / words.length).toBeLessThan(0.3);
  });

  it('most words can be blanked in their own example sentence', () => {
    const ok = words.filter((w) => findInSentence(w.example_sentence, coreForm(w)));
    expect(ok.length / words.length).toBeGreaterThan(0.75);
  });
});

describe('grammar seed', () => {
  it('has 15-20 A1 lessons, 10-15 A2 lessons, and a complete lesson for every topic up to B2', () => {
    const lv = (l: string) => topics.filter((t) => t.cefr_level === l);
    expect(lv('A1').length).toBeGreaterThanOrEqual(15);
    expect(lv('A1').length).toBeLessThanOrEqual(20);
    expect(lv('A2').length).toBeGreaterThanOrEqual(10);
    expect(lv('A2').length).toBeLessThanOrEqual(15);
    expect(lv('B1').length).toBeGreaterThanOrEqual(6);
    expect(lv('B2').length).toBeGreaterThanOrEqual(5);
    for (const t of topics) {
      for (const k of ['what', 'rule', 'examples', 'mistake', 'everyday', 'remember']) expect(t.content?.[k], `${t.slug}.${k}`).toBeTruthy();
      expect(t.content.examples.length, t.slug).toBeGreaterThanOrEqual(2);
    }
  });

  it('links vocabulary to grammar (e.g. helfen -> Dative)', () => {
    const helfen = words.find((w) => w.german === 'helfen')!;
    expect(helfen.grammar).toContain('dative');
  });
});

describe('every generated question is unambiguous', () => {
  const all: QuizQuestion[] = [];
  for (const w of words) {
    for (const type of QUESTION_TYPES) {
      for (const seed of ['a', 'b', 'c']) {
        const q = buildQuestion(type, w, words, createRng(`${w.id}${type}${seed}`));
        if (q) all.push(q);
      }
    }
  }
  const byId = new Map(words.map((w) => [w.id, w]));
  const byEnglish = new Map(words.map((w) => [w.english, w]));
  const byGerman = new Map<string, (typeof words)[number]>();
  for (const w of words) {
    byGerman.set(w.article ? `${w.article} ${w.german}` : w.german, w);
    byGerman.set(coreForm(w), w);
  }

  it('generates many questions of every type', () => {
    for (const t of QUESTION_TYPES) expect(all.filter((q) => q.type === t).length, t).toBeGreaterThan(20);
  });

  it('choice questions: correct answer present once, distinct options, no overlapping meaning', () => {
    for (const q of all.filter((x) => x.format === 'choice')) {
      const opts = q.options!;
      expect(opts.filter((o) => o === q.correctAnswer).length, q.id).toBe(1);
      expect(new Set(opts.map(normalizeAnswer)).size, q.id).toBe(opts.length);
      if (q.type === 'article') continue;
      const target = byId.get(q.wordId)!;
      const others = opts.filter((o) => o !== q.correctAnswer);
      for (const o of others) {
        const w = q.type === 'de_en' ? byEnglish.get(o) : byGerman.get(o);
        expect(w, `${q.id}: option ${o}`).toBeDefined();
        expect(glossesConflict(w!.english, target.english), `${q.id}: ${o} overlaps ${target.english}`).toBe(false);
      }
    }
  });

  it('sentence questions blank exactly one occurrence and no option already appears in the sentence', () => {
    for (const q of all.filter((x) => x.type === 'context' || x.type === 'fill_blank')) {
      expect(q.prompt.split('_____').length, q.id).toBe(2);
      expect(q.helper, q.id).toBeTruthy(); // translation shown -> one meaning fits
      for (const o of q.options ?? []) {
        if (o === q.correctAnswer) continue;
        expect(findInSentence(q.prompt, o), `${q.id}: ${o}`).toBeNull();
      }
    }
  });

  it('typed questions accept their own correct answer', () => {
    for (const q of all.filter((x) => x.format === 'typed')) {
      expect(q.accepted, q.id).toContain(normalizeAnswer(q.correctAnswer));
    }
  });
});
