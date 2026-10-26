// Web Push crypto used by the send-push-reminders Edge Function. Payloads are decrypted with
// http_ece (the reference implementation behind the `web-push` npm package), so this checks the
// wire format against an independent implementation, not just against itself.
import { createECDH, randomBytes } from 'node:crypto';
// @ts-expect-error http_ece ships no types
import ece from 'http_ece';
import { describe, expect, it } from 'vitest';
import {
  b64urlDecode,
  b64urlEncode,
  encryptPayload,
  generateVapidKeys,
  vapidAuthorization,
} from '../supabase/functions/send-push-reminders/webpush';

/** A browser's side of a push subscription. */
function fakeBrowser() {
  const ecdh = createECDH('prime256v1');
  ecdh.generateKeys();
  const auth = randomBytes(16);
  return { ecdh, p256dh: b64urlEncode(ecdh.getPublicKey()), auth: b64urlEncode(auth) };
}

describe('web push payload encryption (RFC 8291, aes128gcm)', () => {
  it('the reference implementation decrypts what we send', async () => {
    const browser = fakeBrowser();
    const message = JSON.stringify({ title: 'Your German lesson is ready', body: '10 words – los geht’s! 🇩🇪' });
    const body = await encryptPayload(new TextEncoder().encode(message), b64urlDecode(browser.p256dh), b64urlDecode(browser.auth));

    const plain = ece.decrypt(Buffer.from(body), { version: 'aes128gcm', privateKey: browser.ecdh, authSecret: browser.auth });
    expect(plain.toString('utf8')).toBe(message);
  });

  it('writes the aes128gcm header: random salt, 4096 record size, server public key as key id', async () => {
    const browser = fakeBrowser();
    const a = await encryptPayload(new Uint8Array([1, 2, 3]), b64urlDecode(browser.p256dh), b64urlDecode(browser.auth));
    const b = await encryptPayload(new Uint8Array([1, 2, 3]), b64urlDecode(browser.p256dh), b64urlDecode(browser.auth));
    const view = new DataView(a.buffer);
    expect(view.getUint32(16)).toBe(4096);
    expect(a[20]).toBe(65);
    expect(a[21]).toBe(0x04); // uncompressed point
    expect(a.length).toBe(21 + 65 + 3 + 1 + 16); // header + key id + payload + delimiter + GCM tag
    expect(b64urlEncode(a.slice(0, 16))).not.toBe(b64urlEncode(b.slice(0, 16))); // fresh salt
    expect(b64urlEncode(a.slice(21, 86))).not.toBe(b64urlEncode(b.slice(21, 86))); // fresh server key
  });

  it('a different browser cannot decrypt it', async () => {
    const browser = fakeBrowser();
    const other = fakeBrowser();
    const body = await encryptPayload(new TextEncoder().encode('hi'), b64urlDecode(browser.p256dh), b64urlDecode(browser.auth));
    expect(() => ece.decrypt(Buffer.from(body), { version: 'aes128gcm', privateKey: other.ecdh, authSecret: other.auth })).toThrow();
  });

  it('refuses payloads that do not fit one record', async () => {
    const browser = fakeBrowser();
    await expect(encryptPayload(new Uint8Array(4080), b64urlDecode(browser.p256dh), b64urlDecode(browser.auth))).rejects.toThrow(/too large/);
  });
});

describe('VAPID (RFC 8292)', () => {
  it('signs a JWT for the push service origin that verifies with the public key', async () => {
    const keys = await generateVapidKeys();
    expect(b64urlDecode(keys.publicKey)).toHaveLength(65);
    expect(b64urlDecode(keys.privateKey)).toHaveLength(32);

    const now = Date.UTC(2026, 9, 26, 12);
    const header = await vapidAuthorization('https://fcm.googleapis.com/fcm/send/abc:def', { ...keys, subject: 'https://example.org/' }, now);
    const m = header.match(/^vapid t=([\w-]+)\.([\w-]+)\.([\w-]+), k=([\w-]+)$/);
    expect(m).not.toBeNull();
    const [, h, c, sig, k] = m!;
    expect(k).toBe(keys.publicKey);
    expect(JSON.parse(new TextDecoder().decode(b64urlDecode(h)))).toEqual({ typ: 'JWT', alg: 'ES256' });
    expect(JSON.parse(new TextDecoder().decode(b64urlDecode(c)))).toEqual({
      aud: 'https://fcm.googleapis.com',
      exp: now / 1000 + 1800,
      sub: 'https://example.org/',
    });

    const pub = await crypto.subtle.importKey('raw', b64urlDecode(keys.publicKey), { name: 'ECDSA', namedCurve: 'P-256' }, false, ['verify']);
    const ok = await crypto.subtle.verify({ name: 'ECDSA', hash: 'SHA-256' }, pub, b64urlDecode(sig), new TextEncoder().encode(`${h}.${c}`));
    expect(ok).toBe(true);
  });
});
