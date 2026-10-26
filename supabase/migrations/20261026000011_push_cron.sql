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
