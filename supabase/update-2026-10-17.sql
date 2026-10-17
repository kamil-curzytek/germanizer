-- Lernbrot database update (2026-10-17): daily reminder emails.
-- For a project that already ran setup.sql (and the earlier update files) before this date.
-- Paste into Supabase SQL Editor and click Run. Safe to run more than once.
-- Then add the two Vault secrets described in the 0009 section below, or no emails are sent.
-- If pg_net or pg_cron can't be created from SQL, enable them under Database -> Extensions first.

-- ===== supabase/migrations/20261017000008_email_reminders.sql =====
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

-- ===== supabase/migrations/20261017000009_reminder_cron.sql =====
-- Sends the daily reminder emails (picked by claim_due_reminders, 0008) through Resend's HTTP API,
-- using pg_net, scheduled hourly by pg_cron. Everything stays inside Supabase: no Edge Function.
--
-- One-time setup (SQL Editor), with an API key from resend.com and a sender on a domain verified there:
--   select vault.create_secret('re_...', 'resend_api_key');
--   select vault.create_secret('Lernbrot <reminders@your-domain.com>', 'reminder_from');
-- Without these secrets the job does nothing (and marks nobody as reminded).
--
-- pg_net is asynchronous: a learner is marked as reminded when the request is queued, so a failed send
-- is not retried that day (at most one email per day). Check results with:
--   select r.*, h.status_code, h.content from public.reminder_emails r
--     left join net._http_response h on h.id = r.request_id order by r.created_at desc limit 20;
-- (pg_net keeps responses for about 6 hours.)

create extension if not exists pg_net;

create table if not exists public.reminder_emails (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users (id) on delete cascade,
  local_date date not null,
  request_id bigint,
  created_at timestamptz not null default now()
);
-- RLS on, no policies -> invisible to anon/authenticated.
alter table public.reminder_emails enable row level security;
revoke all on public.reminder_emails from anon, authenticated;

create or replace function public.send_daily_reminders(p_now timestamptz default now())
returns int
language plpgsql security definer set search_path = public as $$
declare
  c_app_url constant text := 'https://kamil-curzytek.github.io/lernbrot/';
  v_key     text;
  v_from    text;
  r         record;
  v_unsub   text;
  v_what    text;
  v_html    text;
  v_text    text;
  v_req     bigint;
  v_sent    int := 0;
begin
  select decrypted_secret into v_key  from vault.decrypted_secrets where name = 'resend_api_key';
  select decrypted_secret into v_from from vault.decrypted_secrets where name = 'reminder_from';
  if coalesce(v_key, '') = '' or coalesce(v_from, '') = '' then
    raise notice 'daily reminders: vault secrets resend_api_key / reminder_from are not set';
    return 0;
  end if;

  for r in select * from claim_due_reminders(p_now) loop
    v_unsub := c_app_url || '#/unsubscribe/' || r.reminder_token;
    v_what := r.word_count || case when r.word_count = 1 then ' word' else ' words' end
      || case when r.grammar_count > 0
              then ' and ' || r.grammar_count || ' grammar ' || case when r.grammar_count = 1 then 'exercise' else 'exercises' end
              else '' end;
    v_text := format(E'Hallo!\n\nYour German lesson for today is waiting: %s.\nIt only takes a few minutes.\n\nStart now: %s\n\n--\nDon''t want these reminders? Turn them off: %s\n',
                     v_what, c_app_url, v_unsub);
    v_html := format(
      '<div style="font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:480px;margin:0 auto;padding:24px;color:#222">'
      || '<h1 style="font-size:22px;margin:0 0 12px">Hallo! 👋</h1>'
      || '<p style="font-size:16px;line-height:1.5;margin:0 0 20px">Your German lesson for today is waiting: <strong>%s</strong>. It only takes a few minutes.</p>'
      || '<p style="margin:0 0 28px"><a href="%s" style="display:inline-block;background:#2f6f4f;color:#fff;text-decoration:none;padding:12px 20px;border-radius:8px;font-weight:600">Start today''s lesson</a></p>'
      || '<p style="font-size:12px;color:#888;margin:0">You get this because daily reminders are on in Lernbrot. '
      || '<a href="%s" style="color:#888">Turn off reminders</a> or change the time under Progress → Settings.</p>'
      || '</div>',
      v_what, c_app_url, v_unsub);

    begin
      select net.http_post(
        url     := 'https://api.resend.com/emails',
        headers := jsonb_build_object('Authorization', 'Bearer ' || v_key, 'Content-Type', 'application/json'),
        body    := jsonb_build_object(
          'from', v_from,
          'to', jsonb_build_array(r.email),
          'subject', 'Your German lesson is ready (' || v_what || ')',
          'html', v_html,
          'text', v_text,
          'headers', jsonb_build_object('List-Unsubscribe', '<' || v_unsub || '>'))
      ) into v_req;
      insert into reminder_emails (user_id, local_date, request_id) values (r.user_id, r.local_date, v_req);
      v_sent := v_sent + 1;
    exception when others then
      -- one bad address must not stop everyone else's reminder
      raise warning 'reminder for % failed: %', r.user_id, sqlerrm;
    end;
  end loop;
  return v_sent;
end;
$$;

revoke execute on function public.send_daily_reminders(timestamptz) from public, anon, authenticated;

-- Minute 20 of every hour (after the daily job at :05 has prepared sessions). The local-hour gate in
-- claim_due_reminders makes hourly runs serve every timezone. Same job name = replaced (safe to re-run).
select cron.schedule(
  'lernbrot-daily-reminders',
  '20 * * * *',
  $$select public.send_daily_reminders()$$
);
