import { db, unwrap } from '../lib/supabase/client';

// Public half of the VAPID key pair (the private half is a secret of the send-push-reminders function).
const VAPID_PUBLIC_KEY = (import.meta.env.VITE_VAPID_PUBLIC_KEY as string | undefined) ?? '';

/**
 * Push notifications on this device:
 * - needs-install: iPhone/iPad Safari, where push only works once Lernbrot is added to the home screen
 * - denied: the learner blocked notifications for this site (only the browser settings can undo that)
 */
export type PushState = 'unsupported' | 'needs-install' | 'denied' | 'off' | 'on';

function isIos(): boolean {
  return /iPad|iPhone|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
}

function isStandalone(): boolean {
  return matchMedia('(display-mode: standalone)').matches || (navigator as Navigator & { standalone?: boolean }).standalone === true;
}

function pushSupported(): boolean {
  return Boolean(VAPID_PUBLIC_KEY) && 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
}

function keyBytes(b64url: string): Uint8Array<ArrayBuffer> {
  const b64 = b64url.replace(/-/g, '+').replace(/_/g, '/');
  const bin = atob(b64 + '='.repeat((4 - (b64.length % 4)) % 4));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

function sameKey(a: ArrayBuffer | null | undefined, b: Uint8Array): boolean {
  if (!a || a.byteLength !== b.length) return false;
  const x = new Uint8Array(a);
  return x.every((v, i) => v === b[i]);
}

async function registration(): Promise<ServiceWorkerRegistration> {
  await navigator.serviceWorker.register('./sw.js');
  return navigator.serviceWorker.ready;
}

async function save(sub: PushSubscription): Promise<void> {
  const { endpoint, keys } = sub.toJSON();
  const strip = (s = '') => s.replace(/=+$/, '');
  unwrap(await db().rpc('save_push_subscription', { p_endpoint: endpoint, p_p256dh: strip(keys?.p256dh), p_auth: strip(keys?.auth) }));
}

/** The device's subscription for the current key; an old one made with a different key is replaced. */
async function currentSubscription(reg: ServiceWorkerRegistration, create: boolean): Promise<PushSubscription | null> {
  const key = keyBytes(VAPID_PUBLIC_KEY);
  let sub = await reg.pushManager.getSubscription();
  if (sub && !sameKey(sub.options.applicationServerKey, key)) {
    await sub.unsubscribe();
    sub = null;
    create = true;
  }
  if (!sub && create) sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: key });
  return sub;
}

export async function getPushState(): Promise<PushState> {
  if (!pushSupported()) return isIos() && !isStandalone() ? 'needs-install' : 'unsupported';
  if (Notification.permission === 'denied') return 'denied';
  if (Notification.permission !== 'granted') return 'off';
  const reg = await navigator.serviceWorker.getRegistration();
  return (await reg?.pushManager.getSubscription()) ? 'on' : 'off';
}

/** Asks for permission (call straight from a click) and saves this device for the signed-in learner. */
export async function enablePush(): Promise<PushState> {
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') return permission === 'denied' ? 'denied' : 'off';
  const sub = await currentSubscription(await registration(), true);
  await save(sub!);
  return 'on';
}

export async function disablePush(): Promise<PushState> {
  const reg = await navigator.serviceWorker.getRegistration();
  const sub = await reg?.pushManager.getSubscription();
  if (sub) {
    unwrap(await db().rpc('delete_push_subscription', { p_endpoint: sub.endpoint }));
    await sub.unsubscribe();
  }
  return 'off';
}

/**
 * On app start: re-saves this device's subscription for whoever is signed in (browsers rotate
 * subscriptions, and the same device may now be used by another account). Never prompts.
 */
export async function syncPushSubscription(): Promise<void> {
  if (!pushSupported() || Notification.permission !== 'granted') return;
  const reg = await navigator.serviceWorker.getRegistration();
  if (!reg) return;
  const sub = await currentSubscription(reg, false);
  if (sub) await save(sub);
}

/** Pushes a test notification to all of the learner's devices. */
export async function sendTestPush(): Promise<{ sent: number; failed: unknown[] }> {
  const { data, error } = await db().functions.invoke('send-push-reminders', { body: { test: true } });
  if (error) throw new Error(error.message);
  return data as { sent: number; failed: unknown[] };
}
