import { describe, expect, it } from 'vitest';
import { splitStudiedWords } from '../src/lib/dailySession/stats';

describe('splitStudiedWords', () => {
  const now = new Date('2026-10-29T12:00:00Z');
  const row = (word_id: number, streak: number, next_review_at: string | null) => ({ word_id, streak, next_review_at });

  it('known = last answer right and not due; everything else is to review', () => {
    const { known, toReview } = splitStudiedWords([
      row(1, 2, '2026-11-05T00:00:00Z'), // known
      row(2, 0, '2026-10-30T00:00:00Z'), // answered wrong
      row(3, 3, '2026-10-28T00:00:00Z'), // due
      row(4, 0, null),                   // seen, never scored
      row(5, 1, '2026-10-31T00:00:00Z'), // known, sooner
    ], now);
    expect(known.map((r) => r.word_id)).toEqual([5, 1]);
    expect(toReview.map((r) => r.word_id).sort()).toEqual([2, 3, 4]);
  });
});
