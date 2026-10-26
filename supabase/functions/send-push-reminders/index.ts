// send-push-reminders: delivers the daily reminder as a push notification.
//
// Two ways in:
// - hourly from pg_cron (migration 0011) with header x-cron-secret = CRON_SECRET: claims everyone due
//   (claim_due_push_reminders) and pushes to each of their devices;
// - from the app with the learner's own access token and {"test": true}: pushes a test notification
//   to that learner's devices only.
// Deploy with JWT verification off (the function checks both itself), see README "Push notifications".
//
// Secrets: VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, VAPID_SUBJECT, CRON_SECRET.
// SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are provided by Supabase.

import { createClient } from 'npm:@supabase/supabase-js@2';
import { sendWebPush, type PushTarget, type Vapid } from './webpush.ts';

const cors = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { ...cors, 'Content-Type': 'application/json' } });

interface Message {
  subscriptionId: number;
  target: PushTarget;
  payload: { title: string; body: string; tag: string };
}

function plural(n: number, one: string, many: string) {
  return `${n} ${n === 1 ? one : many}`;
}

function reminder(words: number, grammar: number): Message['payload'] {
  const what = plural(words, 'word', 'words') + (grammar > 0 ? ` and ${plural(grammar, 'grammar exercise', 'grammar exercises')}` : '');
  return { title: 'Your German lesson is ready', body: `${what} waiting. It only takes a few minutes.`, tag: 'daily-reminder' };
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: cors });
  if (req.method !== 'POST') return json({ error: 'POST only' }, 405);

  const env = (k: string) => Deno.env.get(k) ?? '';
  const vapid: Vapid = { publicKey: env('VAPID_PUBLIC_KEY'), privateKey: env('VAPID_PRIVATE_KEY'), subject: env('VAPID_SUBJECT') };
  if (!vapid.publicKey || !vapid.privateKey || !vapid.subject) return json({ error: 'VAPID secrets are not set' }, 500);

  const admin = createClient(env('SUPABASE_URL'), env('SUPABASE_SERVICE_ROLE_KEY'), { auth: { persistSession: false } });
  const cronSecret = env('CRON_SECRET');
  let messages: Message[];

  if (cronSecret && req.headers.get('x-cron-secret') === cronSecret) {
    const { data, error } = await admin.rpc('claim_due_push_reminders');
    if (error) return json({ error: error.message }, 500);
    messages = (data ?? []).map((r: { subscription_id: number; endpoint: string; p256dh: string; auth_secret: string; word_count: number; grammar_count: number }) => ({
      subscriptionId: r.subscription_id,
      target: { endpoint: r.endpoint, p256dh: r.p256dh, auth: r.auth_secret },
      payload: reminder(r.word_count, r.grammar_count),
    }));
  } else {
    const token = (req.headers.get('Authorization') ?? '').replace(/^Bearer\s+/i, '');
    const { data: auth } = token ? await admin.auth.getUser(token) : { data: { user: null } };
    if (!auth.user) return json({ error: 'not signed in' }, 401);
    const { data, error } = await admin.from('push_subscriptions').select('id, endpoint, p256dh, auth_secret').eq('user_id', auth.user.id);
    if (error) return json({ error: error.message }, 500);
    messages = (data ?? []).map((r) => ({
      subscriptionId: r.id,
      target: { endpoint: r.endpoint, p256dh: r.p256dh, auth: r.auth_secret },
      payload: { title: 'Notifications are working 🎉', body: 'Your daily lesson reminder will show up here.', tag: 'test' },
    }));
  }

  const sent: number[] = [];
  const gone: number[] = [];
  const failed: { id: number; status: number; error: string }[] = [];
  await Promise.all(
    messages.map(async (m) => {
      try {
        const res = await sendWebPush(m.target, JSON.stringify(m.payload), vapid);
        if (res.ok) sent.push(m.subscriptionId);
        else if (res.status === 404 || res.status === 410) gone.push(m.subscriptionId);
        else failed.push({ id: m.subscriptionId, status: res.status, error: (await res.text()).slice(0, 200) });
      } catch (e) {
        failed.push({ id: m.subscriptionId, status: 0, error: String(e).slice(0, 200) });
      }
    }),
  );

  if (sent.length) await admin.from('push_subscriptions').update({ last_sent_at: new Date().toISOString() }).in('id', sent);
  // the browser unsubscribed or the app was removed: stop trying that device
  if (gone.length) await admin.from('push_subscriptions').delete().in('id', gone);
  if (failed.length) console.error('push failures', failed);

  return json({ sent: sent.length, gone: gone.length, failed });
});
