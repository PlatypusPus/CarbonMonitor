import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import client from '../api/client';
import { accountError } from './Signup';
import AuthLayout, { AuthPassword } from '../components/AuthLayout';

export default function ResetPassword() {
  const location = useLocation();
  const [token] = useState(() => new URLSearchParams(location.hash.slice(1)).get('token') || '');
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  async function submit(event) {
    event.preventDefault();
    setBusy(true); setError(''); setMessage('');
    try {
      const { data } = token
        ? await client.post('/account/reset-password', { token, new_password: value })
        : await client.post('/account/forgot-password', { email: value });
      setMessage(data.message);
      if (token) window.history.replaceState(null, '', location.pathname);
    } catch (error) { setError(accountError(error)); }
    finally { setBusy(false); }
  }

  return <AuthLayout title={token ? 'Choose a new password.' : 'Reset your password.'}
    description={token ? 'Your new password signs out every existing session.' : "Enter your account email and we'll send you a reset link."}>
    {message && token ? <p role="status" className="text-sm text-leaf-action">{message}</p> : <form onSubmit={submit}>
      <fieldset disabled={busy} className="grid gap-5">
        {token
          ? <AuthPassword id="new-password" label="New password" required minLength={10} maxLength={72} autoComplete="new-password" hint="At least 10 characters." value={value} onChange={event => setValue(event.target.value)} />
          : <label className="text-sm font-semibold">Email address<input type="email" autoComplete="email" required value={value} onChange={event => setValue(event.target.value)} placeholder="you@organization.com" className="account-input" /></label>}
        {error && <p role="alert" className="auth-error">{error}</p>}
        {message && <p role="status" className="text-sm text-leaf-action">{message}</p>}
        <button type="submit" className="account-primary w-full">{busy ? 'Working...' : token ? 'Change password' : 'Send reset link'}</button>
      </fieldset>
    </form>}
    <p className="mt-6 text-center text-sm text-body"><Link to="/login" className="auth-link">Back to sign in</Link></p>
  </AuthLayout>;
}
