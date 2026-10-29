-- Lernbrot database update (2026-10-29, second): about a quarter of new words come from lower levels.
-- For a project that already ran update-2026-10-29.sql. Paste into Supabase SQL Editor and click Run.
-- Safe to run more than once.

-- ===== supabase/migrations/20261029000013_lower_level_new_words.sql =====
-- New words from lower levels too: about a quarter of the new words a learner meets come from the levels
-- below theirs (nearest first, most frequent first), so gaps in A1/A2 show up early instead of only after
-- the learner's whole level is used up. The share counts every word met so far, so a learner who came up
-- from a lower level (and already met many such words) gets few or none.
-- create_daily_session_for is otherwise unchanged from 0012.

create or replace function public.create_daily_session_for(p_user_id uuid, p_session_date date)
returns public.daily_sessions
language plpgsql security definer set search_path = public as $$
declare
  v_profile    public.profiles;
  v_session    public.daily_sessions;
  v_target     int;
  v_min_new    int;
  v_day_start  timestamptz;
  v_day_end    timestamptz;
  v_user_rank  int;
  v_new_avail  int;
  v_due_count  int;
  v_review_cap int;
  v_due        int[];
  v_struggling int[];
  v_reviews    int[];
  v_new        int[];
  v_lower      int[];
  v_new_room   int;
  v_lower_want int;
  v_fill       int[];
begin
  select * into v_session from daily_sessions
   where user_id = p_user_id and session_date = p_session_date;
  if found then
    return v_session;
  end if;

  select * into v_profile from profiles where id = p_user_id;
  if not found then
    raise exception 'profile % not found', p_user_id;
  end if;

  v_target    := v_profile.daily_word_target;
  v_day_start := p_session_date::timestamp at time zone v_profile.timezone;
  v_day_end   := (p_session_date + 1)::timestamp at time zone v_profile.timezone;
  v_user_rank := cefr_rank(v_profile.current_cefr_level);

  -- How many new words to keep, depending on the review backlog:
  --   up to the target due      -> at least 20% new (10 -> 2)
  --   more than the target due  -> at least 10% new (10 -> 1), so there is something new every day
  select count(*) into v_due_count
    from vocabulary_progress p
   where p.user_id = p_user_id and p.next_review_at < v_day_end;
  v_min_new := case
                 when v_due_count <= v_target then ceil(v_target * 0.2)::int
                 else ceil(v_target * 0.1)::int
               end;

  select count(*) into v_new_avail
    from vocabulary_words w
   where not exists (select 1 from vocabulary_progress p
                      where p.user_id = p_user_id and p.word_id = w.id);

  v_review_cap := v_target - least(v_min_new, v_new_avail);

  -- 1. Words due for review by the end of the learner's local day.
  --    Frequently-wrong words first, then the ones most likely forgotten (lowest predicted recall).
  v_due := array(
    select p.word_id
      from vocabulary_progress p
     where p.user_id = p_user_id
       and p.next_review_at < v_day_end
     order by (p.times_incorrect > p.times_correct) desc,
              fsrs_retrievability(p.stability, coalesce(p.last_review_at, p.last_seen_at), v_day_start),
              p.next_review_at, p.word_id
     limit v_review_cap);

  -- 2. Up to two frequently-wrong words that are not due yet (not seen today).
  v_struggling := array(
    select p.word_id
      from vocabulary_progress p
     where p.user_id = p_user_id
       and p.next_review_at >= v_day_end
       and p.times_incorrect >= 2
       and p.times_incorrect >= p.times_correct
       and p.last_seen_at < v_day_start
     order by p.times_incorrect - p.times_correct desc, p.difficulty desc, p.word_id
     limit least(2, v_review_cap - cardinality(v_due)));

  v_reviews := v_due || v_struggling;

  -- 3. New words. About a quarter come from levels below the learner's (nearest level first), to fill
  --    gaps in the most frequent words; the share is kept over everything met so far, so with 2 new
  --    words a day that is one lower-level word every other day. The rest: learner's level first,
  --    then lower levels, then higher ones. Within a level, interleave topics by frequency for variety.
  v_new_room := v_target - cardinality(v_reviews);
  select greatest(0, least(v_new_room,
           floor(0.25 * (count(*) + v_new_room))::int
           - count(*) filter (where cefr_rank(w.cefr_level) < v_user_rank)))
    into v_lower_want
    from vocabulary_progress p join vocabulary_words w on w.id = p.word_id
   where p.user_id = p_user_id;

  v_lower := array(
    select c.id
      from (
        select w.id, w.frequency_rank, v_user_rank - cefr_rank(w.cefr_level) as distance, w.topic
          from vocabulary_words w
         where cefr_rank(w.cefr_level) < v_user_rank
           and not exists (select 1 from vocabulary_progress p
                            where p.user_id = p_user_id and p.word_id = w.id)
      ) c
     order by c.distance,
              row_number() over (partition by c.distance, c.topic order by c.frequency_rank, c.id),
              c.frequency_rank,
              c.id
     limit v_lower_want);

  v_new := v_lower || array(
    select c.id
      from (
        select w.id,
               w.frequency_rank,
               case
                 when cefr_rank(w.cefr_level) = v_user_rank then 0
                 when cefr_rank(w.cefr_level) < v_user_rank then v_user_rank - cefr_rank(w.cefr_level)
                 else 3 + cefr_rank(w.cefr_level) - v_user_rank
               end as level_priority,
               w.topic
          from vocabulary_words w
         where not exists (select 1 from vocabulary_progress p
                            where p.user_id = p_user_id and p.word_id = w.id)
           and w.id <> all (v_lower)
      ) c
     order by c.level_priority,
              row_number() over (partition by c.level_priority, c.topic order by c.frequency_rank, c.id),
              c.frequency_rank,
              c.id
     limit v_new_room - cardinality(v_lower));

  -- 4. Out of new words: top up with the earliest upcoming reviews.
  if cardinality(v_reviews) + cardinality(v_new) < v_target then
    v_fill := array(
      select p.word_id
        from vocabulary_progress p
       where p.user_id = p_user_id
         and p.word_id <> all (v_reviews)
       order by p.next_review_at nulls first, p.word_id
       limit v_target - cardinality(v_reviews) - cardinality(v_new));
    v_reviews := v_reviews || v_fill;
  end if;

  insert into daily_sessions (user_id, session_date, new_word_count, review_word_count, total_word_count)
  values (p_user_id, p_session_date, cardinality(v_new), cardinality(v_reviews),
          cardinality(v_new) + cardinality(v_reviews))
  on conflict (user_id, session_date) do nothing
  returning * into v_session;

  if not found then
    -- a concurrent call created it first
    select * into v_session from daily_sessions
     where user_id = p_user_id and session_date = p_session_date;
    return v_session;
  end if;

  insert into daily_session_words (session_id, word_id, position, kind)
  select v_session.id, x.word_id, x.ord::int, 'new'
    from unnest(v_new) with ordinality as x(word_id, ord);

  insert into daily_session_words (session_id, word_id, position, kind)
  select v_session.id, x.word_id, cardinality(v_new) + x.ord::int, 'review'
    from unnest(v_reviews) with ordinality as x(word_id, ord);

  update vocabulary_progress
     set status = 'review'
   where user_id = p_user_id and word_id = any (v_reviews);

  -- 5. Grammar: up to 3 studied skills that are due, the one most likely forgotten first.
  --    Mixed practice: one skill per lesson topic before a second skill from the same topic.
  insert into daily_session_grammar (session_id, skill_id, position)
  select v_session.id, g.skill_id, row_number() over (order by g.second_of_topic, g.recall, g.skill_id)
    from (
      select gp.skill_id,
             fsrs_retrievability(gp.stability, gp.last_review_at, v_day_start) as recall,
             row_number() over (partition by gs.topic_id
                                order by fsrs_retrievability(gp.stability, gp.last_review_at, v_day_start), gp.skill_id) > 1
               as second_of_topic
        from grammar_progress gp
        join grammar_skills gs on gs.id = gp.skill_id
       where gp.user_id = p_user_id
         and gp.next_review_at < v_day_end
    ) g
   order by g.second_of_topic, g.recall, g.skill_id
   limit 3;

  return v_session;
end;
$$;

revoke execute on function public.create_daily_session_for(uuid, date) from public, anon, authenticated;
