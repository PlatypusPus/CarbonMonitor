import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import client from '../api/client';
import { accountError } from './Signup';
import { useAuth } from '../context/AuthContext';
import AuthLayout, { AuthPassword } from '../components/AuthLayout';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState('');

  async function submit(event, resend = false) {
    event.preventDefault();
    setError(''); setNotice(''); setBusy(resend ? 'resend' : 'login');
    try {
      if (resend) {
        const { data } = await client.post('/account/resend-verification', { email });
        setNotice(data.message);
      } else {
        await login(email, password);
        const destination = location.state?.returnTo;
        navigate(destination?.startsWith('/join-organization#') ? destination : '/onboarding', { replace: true });
      }
    } catch (error) { setError(accountError(error)); }
    finally { setBusy(''); }
  }

  return <AuthLayout title="Welcome back." description="Sign in to your CarbonTrace workspace.">
    <form onSubmit={submit}>
      <fieldset disabled={!!busy} className="grid gap-5">
        <label className="text-sm font-semibold">Email address<input type="email" autoComplete="email" required value={email} onChange={event => setEmail(event.target.value)} placeholder="you@organization.com" className="account-input" /></label>
        <AuthPassword id="login-password" required autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} />
        {error && <p role="alert" className="auth-error">{error}</p>}
        <button type="submit" className="account-primary w-full">{busy === 'login' ? 'Signing in...' : 'Sign in'}</button>
      </fieldset>
    </form>
    <p className="mt-6 text-center text-sm text-body">New to CarbonTrace? <Link to="/signup" className="auth-link">Create an account</Link></p>
    <div className="mt-8 border-t border-line pt-5 text-sm leading-6 text-body">
      <p>Still waiting to verify your email?</p>
      <button type="button" disabled={!!busy || !email} onClick={event => submit(event, true)} className="auth-link mt-1 min-h-11 disabled:opacity-50">{busy === 'resend' ? 'Sending verification...' : 'Resend verification email'}</button>
      {notice && <p role="status" className="mt-3 text-leaf-action">{notice}</p>}
    </div>
  </AuthLayout>;
}
