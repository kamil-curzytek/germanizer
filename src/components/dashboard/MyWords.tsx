import { useApp } from '../../AppContext';
import { useAsync } from '../../hooks/useAsync';
import { displayGerman } from '../../lib/quiz';
import { daysBetween, localDate } from '../../lib/time';
import { getWordsByIds } from '../../services/vocabularyService';
import type { VocabularyProgress } from '../../types';
import { StatusPill } from '../vocabulary/StatusPill';

export type WordListKind = 'known' | 'toReview';

/** The learner's own words: the ones they know, or the ones coming back for review. */
export function MyWords({ kind, rows, onClose }: { kind: WordListKind; rows: VocabularyProgress[]; onClose: () => void }) {
  const tz = useApp().profile.timezone;
  const words = useAsync(() => getWordsByIds(rows.map((r) => r.word_id)), [rows]);
  const today = localDate(tz);

  const when = (p: VocabularyProgress) => {
    if (!p.next_review_at) return 'today';
    const d = daysBetween(today, localDate(tz, new Date(p.next_review_at)));
    return d <= 0 ? 'today' : d === 1 ? 'tomorrow' : `in ${d} days`;
  };

  return (
    <section className="card">
      <div className="row">
        <h2 style={{ margin: 0 }}>{kind === 'known' ? `Words you know (${rows.length})` : `Words to review (${rows.length})`}</h2>
        <span className="spacer" />
        <button className="link-btn" onClick={onClose}>close</button>
      </div>
      <p className="muted small">
        {kind === 'known'
          ? 'Answered right last time. Each one comes back once it is about to slip.'
          : 'Answered wrong last time, or due again. They are added to your daily lesson automatically.'}
      </p>
      {words.loading && <div className="loading">Loading words…</div>}
      {words.error && <div className="alert">Could not load words: {words.error}</div>}
      {words.data && (
        <ul className="list">
          {rows.map((p) => {
            const w = words.data!.get(p.word_id);
            if (!w) return null;
            return (
              <li key={p.word_id} className="row">
                <strong lang="de">{displayGerman(w)}</strong>
                <span className="muted">{w.english}</span>
                <span className="spacer" />
                <span className="muted small">{when(p)}</span>
                <StatusPill status={p.status} />
              </li>
            );
          })}
          {rows.length === 0 && <li className="muted">Nothing here yet.</li>}
        </ul>
      )}
    </section>
  );
}
