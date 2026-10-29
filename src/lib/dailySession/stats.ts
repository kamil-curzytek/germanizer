// Dashboard numbers, derived deterministically from rows in Supabase.
// Session *selection* lives in SQL (create_daily_session_for) so the cloud job
// and the app share one implementation.

import type { ProgressStatus, VocabularyProgress } from '../../types';
import { addDays } from '../time';

/** Consecutive days with a completed session, ending today (or yesterday, if today isn't done yet). */
export function currentStreak(completedDates: readonly string[], today: string): number {
  const done = new Set(completedDates);
  let day = done.has(today) ? today : addDays(today, -1);
  let streak = 0;
  while (done.has(day)) {
    streak++;
    day = addDays(day, -1);
  }
  return streak;
}

export interface ProgressSummary {
  /** Words answered correctly at least once. */
  learned: number;
  /** Words whose next review is due now. */
  due: number;
  byStatus: Record<ProgressStatus, number>;
}

export function summarizeProgress(rows: readonly VocabularyProgress[], now: Date = new Date()): ProgressSummary {
  const byStatus: Record<ProgressStatus, number> = { new: 0, learning: 0, familiar: 0, strong: 0, review: 0 };
  let learned = 0;
  let due = 0;
  for (const r of rows) {
    byStatus[r.status]++;
    if (r.times_correct > 0) learned++;
    if (r.next_review_at && Date.parse(r.next_review_at) <= now.getTime()) due++;
  }
  return { learned, due, byStatus };
}

/**
 * Every word the learner has met, split in two: "known" (last answer right and not due yet) and
 * "to review" (last answer wrong, never answered right, or due now). Each list is soonest-due first.
 */
export function splitStudiedWords<T extends Pick<VocabularyProgress, 'streak' | 'next_review_at'>>(
  rows: readonly T[],
  now: Date = new Date(),
): { known: T[]; toReview: T[] } {
  const known: T[] = [];
  const toReview: T[] = [];
  for (const r of rows) {
    const due = !r.next_review_at || Date.parse(r.next_review_at) <= now.getTime();
    (r.streak === 0 || due ? toReview : known).push(r);
  }
  const bySoonest = (a: T, b: T) => (a.next_review_at ?? '').localeCompare(b.next_review_at ?? '');
  return { known: known.sort(bySoonest), toReview: toReview.sort(bySoonest) };
}

export function greeting(hour: number): string {
  if (hour < 5) return 'Good evening.';
  if (hour < 12) return 'Good morning.';
  if (hour < 18) return 'Good afternoon.';
  return 'Good evening.';
}
