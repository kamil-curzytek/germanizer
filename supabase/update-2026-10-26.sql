-- Lernbrot database update (2026-10-26): daily reminders as push notifications.
-- For a project that already ran update-2026-10-17.sql (email reminders). Paste into Supabase SQL Editor
-- and click Run. Safe to run more than once.
-- Then deploy the send-push-reminders Edge Function and add the secrets: see README, "Push notifications".

-- ===== supabase/migrations/20261026000010_push_reminders.sql =====
-- Daily reminders as push notifications (Web Push), next to the reminder emails of 0008.
-- 1. push_subscriptions: one row per device that allowed notifications. Learners read their own rows;
--    writes go through save_push_subscription / delete_push_subscription.
-- 2. due_reminder_profiles(p_now) holds the "who should be reminded now" rule shared by both channels:
--    onboarded, local time >= reminder_hour, today's lesson not completed, active in the last N days.
--    claim_due_reminders (email, same signature as before) now uses it too.
-- 3. claim_due_push_reminders(p_now) returns every device of each due learner and marks the learner as
--    pushed for their local date (profiles.last_push_date), so at most one push per day. It is called
--    by the send-push-reminders Edge Function (service_role), which is triggered hourly (0011).
-- Push and email are independent: a learner can have either, both or neither.

alter table public.profiles add column if not exists last_push_date date;

create table if not exists public.push_subscriptions (
  id           bigint generated always as identity primary key,
  user_id      uuid not null references auth.users (id) on delete cascade,
  endpoint     text not null unique check (endpoint ~ '^https://' and length(endpoint) <= 1000),
  -- base64url without padding: 65-byte P-256 public key, 16-byte auth secret
  p256dh       text not null check (p256dh ~ '^[A-Za-z0-9_-]{87}$'),
  auth_secret  text not null check (auth_secret ~ '^[A-Za-z0-9_-]{22}$'),
  created_at   timestamptz not null default now(),
  last_sent_at timestamptz
);

create index if not exists push_subscriptions_user_idx on public.push_subscriptions (user_id);

alter table public.push_subscriptions enable row level security;
revoke all on public.push_subscriptions from anon, authenticated;
grant select on public.push_subscriptions to authenticated;
-- the Edge Function records deliveries and removes subscriptions the push service reports as gone
grant select, update (last_sent_at), delete on public.push_subscriptions to service_role;

drop policy if exists "own push subscriptions: read" on public.push_subscriptions;
create policy "own push subscriptions: read" on public.push_subscriptions
  for select to authenticated using (user_id = auth.uid());

-- Called by the browser after the learner allowed notifications. The same device signing in with another
-- account takes its subscription along. At most 10 devices per learner (the oldest are dropped).
create or replace function public.save_push_subscription(p_endpoint text, p_p256dh text, p_auth text)
returns void
language plpgsql security definer set search_path = public as $$
begin
  if auth.uid() is null then
    raise exception 'not signed in';
  end if;
  insert into push_subscriptions (user_id, endpoint, p256dh, auth_secret)
  values (auth.uid(), p_endpoint, p_p256dh, p_auth)
  on conflict (endpoint) do update
    set user_id = excluded.user_id, p256dh = excluded.p256dh, auth_secret = excluded.auth_secret, created_at = now();
  delete from push_subscriptions
   where user_id = auth.uid()
     and id not in (select id from push_subscriptions where user_id = auth.uid() order by created_at desc, id desc limit 10);
end;
$$;

create or replace function public.delete_push_subscription(p_endpoint text)
returns void
language sql security definer set search_path = public as $$
  delete from push_subscriptions where endpoint = p_endpoint and user_id = auth.uid()
$$;

create or replace function public.due_reminder_profiles(p_now timestamptz, p_inactive_days int)
returns table (user_id uuid, local_date date, word_count int, grammar_count int)
language sql stable security definer set search_path = public as $$
  select p.id, d.local_date,
         coalesce(s.total_word_count, p.daily_word_target),
         coalesce((select count(*)::int from daily_session_grammar g where g.session_id = s.id), 0)
    from profiles p
    cross join lateral (select (p_now at time zone p.timezone)::date as local_date) d
    left join daily_sessions s on s.user_id = p.id and s.session_date = d.local_date
   where p.onboarded_at is not null
     and extract(hour from p_now at time zone p.timezone) >= p.reminder_hour
     and s.status is distinct from 'completed'
     and greatest(p.onboarded_at, (select max(c.completed_at) from daily_sessions c where c.user_id = p.id))
         >= p_now - make_interval(days => p_inactive_days)
$$;

-- Email channel (0008), now on the shared rule. The update's WHERE re-checks last_reminder_date under the
-- row lock, so overlapping runs can't remind anyone twice.
create or replace function public.claim_due_reminders(
  p_now          timestamptz default now(),
  p_inactive_days int default 14)
returns table (user_id uuid, email text, local_date date, word_count int, grammar_count int, reminder_token uuid)
language plpgsql security definer set search_path = public as $$
begin
  return query
  with claimed as (
    update profiles p set last_reminder_date = d.local_date
      from due_reminder_profiles(p_now, p_inactive_days) d, auth.users u
     where p.id = d.user_id and u.id = p.id
       and p.email_reminders
       and coalesce(u.email, '') <> ''
       and p.last_reminder_date is distinct from d.local_date
    returning p.id, u.email::text as email, d.local_date, d.word_count, d.grammar_count, p.reminder_token
  )
  select c.id, c.email, c.local_date, c.word_count, c.grammar_count, c.reminder_token from claimed c order by c.id;
end;
$$;

create or replace function public.claim_due_push_reminders(
  p_now          timestamptz default now(),
  p_inactive_days int default 14)
returns table (subscription_id bigint, endpoint text, p256dh text, auth_secret text, word_count int, grammar_count int)
language plpgsql security definer set search_path = public as $$
begin
  return query
  with claimed as (
    update profiles p set last_push_date = d.local_date
      from due_reminder_profiles(p_now, p_inactive_days) d
     where p.id = d.user_id
       and p.last_push_date is distinct from d.local_date
       and exists (select 1 from push_subscriptions ps where ps.user_id = p.id)
    returning p.id, d.word_count, d.grammar_count
  )
  select ps.id, ps.endpoint, ps.p256dh, ps.auth_secret, c.word_count, c.grammar_count
    from claimed c
    join push_subscriptions ps on ps.user_id = c.id
   order by ps.id;
end;
$$;

revoke execute on function public.due_reminder_profiles(timestamptz, int) from public, anon, authenticated;
revoke execute on function public.claim_due_reminders(timestamptz, int) from public, anon, authenticated;
revoke execute on function public.claim_due_push_reminders(timestamptz, int) from public, anon, authenticated;
grant  execute on function public.claim_due_push_reminders(timestamptz, int) to service_role;
revoke execute on function public.save_push_subscription(text, text, text) from public, anon;
revoke execute on function public.delete_push_subscription(text) from public, anon;
grant  execute on function public.save_push_subscription(text, text, text) to authenticated;
grant  execute on function public.delete_push_subscription(text) to authenticated;

-- make the API see the new table and functions immediately
notify pgrst, 'reload schema';

-- ===== supabase/migrations/20261026000011_push_cron.sql =====
-- Triggers the send-push-reminders Edge Function every hour (minute :20) with pg_net. The function
-- claims who is due (claim_due_push_reminders, 0010) and sends the notifications.
--
-- One-time setup (SQL Editor): the function's URL and the same random secret you set as the
-- function's CRON_SECRET (see README, "Push notifications"):
--   select vault.create_secret('https://<project-ref>.supabase.co/functions/v1/send-push-reminders', 'push_function_url');
--   select vault.create_secret('<CRON_SECRET>', 'push_cron_secret');
-- Without these secrets the job does nothing. Check recent calls with:
--   select id, status_code, content, created from net._http_response order by created desc limit 5;

create extension if not exists pg_net;

create or replace function public.trigger_push_reminders()
returns bigint
language plpgsql security definer set search_path = public as $$
declare
  v_url    text;
  v_secret text;
begin
  select decrypted_secret into v_url    from vault.decrypted_secrets where name = 'push_function_url';
  select decrypted_secret into v_secret from vault.decrypted_secrets where name = 'push_cron_secret';
  if coalesce(v_url, '') = '' or coalesce(v_secret, '') = '' then
    raise notice 'push reminders: vault secrets push_function_url / push_cron_secret are not set';
    return null;
  end if;
  return net.http_post(
    url     := v_url,
    body    := '{}'::jsonb,
    headers := jsonb_build_object('Content-Type', 'application/json', 'x-cron-secret', v_secret),
    timeout_milliseconds := 60000
  );
end;
$$;

revoke execute on function public.trigger_push_reminders() from public, anon, authenticated;

-- Same job name = replaced (safe to re-run).
select cron.schedule(
  'lernbrot-push-reminders',
  '20 * * * *',
  $$select public.trigger_push_reminders()$$
);
