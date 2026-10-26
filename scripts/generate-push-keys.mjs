// Generates the secrets for push notifications and writes them, with the exact setup commands, to
// supabase/push-secrets.local.md (git-ignored). Run once; running again creates NEW keys, after which
// every device has to turn notifications on again (the app re-subscribes automatically when it can).
//   node scripts/generate-push-keys.mjs
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const root = join(import.meta.dirname, '..');
const target = join(root, 'supabase', 'push-secrets.local.md');
if (existsSync(target) && !process.argv.includes('--force')) {
  console.error(`${target} already exists. Use --force to create new keys.`);
  process.exit(1);
}

const b64url = (bytes) => Buffer.from(bytes).toString('base64url');
const pair = await crypto.subtle.generateKey({ name: 'ECDSA', namedCurve: 'P-256' }, true, ['sign', 'verify']);
const publicKey = b64url(new Uint8Array(await crypto.subtle.exportKey('raw', pair.publicKey)));
const privateKey = (await crypto.subtle.exportKey('jwk', pair.privateKey)).d;
const cronSecret = b64url(crypto.getRandomValues(new Uint8Array(32)));

const url = readFileSync(join(root, '.env.production'), 'utf8').match(/VITE_SUPABASE_URL=(\S+)/)?.[1] ?? 'https://<project-ref>.supabase.co';
const ref = new URL(url).hostname.split('.')[0];

writeFileSync(
  target,
  `# Push notification secrets (generated ${new Date().toISOString().slice(0, 10)}). Do not commit or share.

VAPID_PUBLIC_KEY=${publicKey}
VAPID_PRIVATE_KEY=${privateKey}
VAPID_SUBJECT=https://kamil-curzytek.github.io/lernbrot/
CRON_SECRET=${cronSecret}

## 1. Edge Function secrets
\`\`\`bash
npx supabase secrets set --project-ref ${ref} VAPID_PUBLIC_KEY=${publicKey} VAPID_PRIVATE_KEY=${privateKey} VAPID_SUBJECT=https://kamil-curzytek.github.io/lernbrot/ CRON_SECRET=${cronSecret}
\`\`\`
(or Dashboard -> Edge Functions -> Secrets, one per line above)

## 2. Vault secrets for the hourly trigger (SQL Editor)
\`\`\`sql
select vault.create_secret('${url}/functions/v1/send-push-reminders', 'push_function_url');
select vault.create_secret('${cronSecret}', 'push_cron_secret');
\`\`\`
`,
);
console.log(`Wrote ${target}`);
console.log(`Public key (goes in .env.production as VITE_VAPID_PUBLIC_KEY): ${publicKey}`);
