import { useEffect, useState } from 'react';
import { disablePush, enablePush, getPushState, sendTestPush, type PushState } from '../../services/pushService';

/** Settings row: daily reminder as a push notification on this device. */
export function PushReminders() {
  const [state, setState] = useState<PushState | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    getPushState().then(setState, () => setState('unsupported'));
  }, []);

  async function run(action: () => Promise<string | null>) {
    setBusy(true);
    setMessage(null);
    try {
      setMessage(await action());
    } catch (e) {
      setMessage(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const toggle = (on: boolean) =>
    run(async () => {
      const next = on ? await enablePush() : await disablePush();
      setState(next);
      if (on && next === 'denied') return 'Notifications are blocked. Allow them for this site in your browser settings, then reload.';
      if (on && next === 'off') return 'Notifications were not allowed.';
      return null;
    });

  const test = () =>
    run(async () => {
      const r = await sendTestPush();
      return r.sent > 0 ? 'Test sent. It should appear in a few seconds.' : 'Could not send the test notification. Try turning notifications off and on again.';
    });

  if (state === null) return null;

  return (
    <div className="stack" style={{ gap: 6 }}>
      {state === 'unsupported' && <p className="small muted" style={{ margin: 0 }}>This browser can't show notifications from Lernbrot.</p>}
      {state === 'needs-install' && (
        <p className="small muted" style={{ margin: 0 }}>
          For notifications on iPhone or iPad: tap <strong>Share → Add to Home Screen</strong>, then open Lernbrot from your home screen and turn them on there.
        </p>
      )}
      {state === 'denied' && (
        <p className="small muted" style={{ margin: 0 }}>
          Notifications are blocked for this site. Allow them in your browser's site settings, then reload the page.
        </p>
      )}
      {(state === 'on' || state === 'off') && (
        <label className="row small">
          <input type="checkbox" checked={state === 'on'} disabled={busy} onChange={(e) => toggle(e.target.checked)} />
          <span>Notify me on this device if I haven't done my lesson</span>
          {state === 'on' && (
            <button type="button" className="btn btn-ghost small" style={{ padding: '2px 6px', marginLeft: 'auto' }} disabled={busy} onClick={test}>
              Send test
            </button>
          )}
        </label>
      )}
      {message && <div className="notice">{message}</div>}
    </div>
  );
}
