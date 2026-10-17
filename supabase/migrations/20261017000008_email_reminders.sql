-- Daily email reminders.
-- 1. profiles get email_reminders (on by default, the learner can switch it off), reminder_hour (local
--    hour 0..23 from which the reminder may go out, default 18) and last_reminder_date (local date of
--    the last reminder, so at most one per day).
-- 2. claim_due_reminders(p_now) picks everyone who should get a reminder now and marks them as
--    reminded for their local date. It has no side effects outside the database, so it is testable;
--    the actual sending (pg_net -> Resend) and its hourly schedule live in 0009_reminder_cron.
-- 3. Every reminder carries a one-click unsubscribe link with the profile's reminder_token, handled by
--    unsubscribe_reminders(token), which works signed out (anon).
-- Who gets one: onboarded, reminders on, has an email, local time >= reminder_hour, not reminded today,
-- today's lesson not completed yet, and active in the last 14 days (completed a lesson or onboarded),
-- so people who stopped using the app aren't emailed forever.

alter table public.profiles
  add column if not exists email_reminders    boolean not null default true,
  add column if not exists reminder_hour      int     not null default 18 check (reminder_hour between 0 and 23),
  add column if not exists last_reminder_date date,
  add column if not exists reminder_token     uuid    not null default gen_random_uuid();

create unique index if not exists profiles_reminder_token_idx on public.profiles (reminder_token);

grant update (email_reminders, reminder_hour) on public.profiles to authenticated;

create or replace function public.claim_due_reminders(
  p_now          timestamptz default now(),
  p_inactive_days int default 14)
returns table (user_id uuid, email text, local_date date, word_count int, grammar_count int, reminder_token uuid)
language plpgsql security definer set search_path = public as $$
begin
  return query
  with due as (
    select p.id, u.email::text as email, (p_now at time zone p.timezone)::date as d, p.daily_word_target, p.reminder_token as token
      from profiles p
      join auth.users u on u.id = p.id
     where p.onboarded_at is not null
       and p.email_reminders
       and coalesce(u.email, '') <> ''
       and extract(hour from p_now at time zone p.timezone) >= p.reminder_hour
       and p.last_reminder_date is distinct from (p_now at time zone p.timezone)::date
       and not exists (select 1 from daily_sessions s
                        where s.user_id = p.id and s.session_date = (p_now at time zone p.timezone)::date
                          and s.status = 'completed')
       and greatest(p.onboarded_at,
                    (select max(s.completed_at) from daily_sessions s where s.user_id = p.id))
           >= p_now - make_interval(days => p_inactive_days)
     for update of p skip locked
  ),
  claimed as (
    update profiles p set last_reminder_date = due.d
      from due where p.id = due.id
    returning p.id
  )
  select due.id, due.email, due.d,
         coalesce(s.total_word_count, due.daily_word_target),
         coalesce((select count(*)::int from daily_session_grammar g where g.session_id = s.id), 0),
         due.token
    from due
    join claimed c on c.id = due.id
    left join daily_sessions s on s.user_id = due.id and s.session_date = due.d
   order by due.id;
end;
$$;

-- One-click unsubscribe from the link in the email; the token is the only credential.
create or replace function public.unsubscribe_reminders(p_token uuid)
returns boolean
language sql security definer set search_path = public as $$
  with u as (update profiles set email_reminders = false where reminder_token = p_token returning 1)
  select exists (select 1 from u)
$$;

revoke execute on function public.claim_due_reminders(timestamptz, int) from public, anon, authenticated;
revoke execute on function public.unsubscribe_reminders(uuid) from public;
grant  execute on function public.unsubscribe_reminders(uuid) to anon, authenticated;

-- make the API see the new columns and functions immediately
notify pgrst, 'reload schema';
