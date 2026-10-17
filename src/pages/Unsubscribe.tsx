import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { unsubscribeReminders } from '../services/profileService';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

// Opened from the "Turn off reminders" link in a reminder email; works signed in and signed out.
export default function Unsubscribe() {
  const { token = '' } = useParams();
  const [state, setState] = useState<'working' | 'done' | 'invalid' | 'error'>('working');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!UUID.test(token)) {
      setState('invalid');
      return;
    }
    unsubscribeReminders(token).then(
      (ok) => setState(ok ? 'done' : 'invalid'),
      (e: Error) => {
        setError(e.message);
        setState('error');
      },
    );
  }, [token]);

  return (
    <div className="main narrow stack">
      <h1>Email reminders</h1>
      {state === 'working' && <p className="muted">Turning off reminders…</p>}
      {state === 'done' && (
        <p>Done. You won't get daily reminder emails any more. You can turn them back on under Progress → Settings.</p>
      )}
      {state === 'invalid' && <div className="alert">This link is not valid. You can turn reminders off under Progress → Settings.</div>}
      {state === 'error' && <div className="alert">Could not turn off reminders: {error}</div>}
      <p>
        <Link to="/">Go to Lernbrot</Link>
      </p>
    </div>
  );
}
