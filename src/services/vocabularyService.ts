import { db, unwrap } from '../lib/supabase/client';
import type { VocabularyWord } from '../types';

// PostgREST returns at most 1,000 rows per request, so the word list is read in pages.
const PAGE_SIZE = 1000;

let cache: Promise<VocabularyWord[]> | null = null;

/** All shared vocabulary (a few thousand rows), cached for the page lifetime. */
export function listWords(): Promise<VocabularyWord[]> {
  cache ??= (async () => {
    const all: VocabularyWord[] = [];
    for (let from = 0; ; from += PAGE_SIZE) {
      const page = unwrap(
        await db()
          .from('vocabulary_words')
          .select('*')
          .order('cefr_level')
          .order('frequency_rank')
          .order('id')
          .range(from, from + PAGE_SIZE - 1),
      ) as VocabularyWord[];
      all.push(...page);
      if (page.length < PAGE_SIZE) return all;
    }
  })();
  cache.catch(() => (cache = null));
  return cache;
}

export async function getWordsByIds(ids: readonly number[]): Promise<Map<number, VocabularyWord>> {
  const all = await listWords();
  const wanted = new Set(ids);
  return new Map(all.filter((w) => wanted.has(w.id)).map((w) => [w.id, w]));
}
