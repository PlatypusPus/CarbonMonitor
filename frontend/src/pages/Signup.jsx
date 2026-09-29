import { useState } from 'react';
import { Link } from 'react-router-dom';
import { MailCheck } from 'lucide-react';
import client from '../api/client';
import AuthLayout, { AuthPassword } from '../components/AuthLayout';

export const accountError = (error) => {
  const detail = error?.response?.data?.detail;
  return typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((item) => item.msg).join('. ') : 'The request could not be completed. Please try again.';
};

export default function Signup() {
  const [form, setForm] = useState({ full_name: '', email: '', organization_name: '', password: '' });
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  async function submit(event, resend = false) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('');
    try {
      const { data } = await client.post(resend ? '/account/resend-verification' : '/account/signup', resend ? { email: form.email } : form);
      setSent(true); setMessage(data.message); setForm(previous => ({ ...previous, password: '' }));
    } catch (error) { setError(accountError(error)); } finally { setBusy(false); }
  }

  return <AuthLayout title={sent ? 'Check your email.' : 'Create your account.'} description={sent ? 'Verify your email to open your new workspace.' : 'Start tracking your facility with a private organization.'}>
    {sent ? <div>
      <div className="rounded-xl border border-line bg-canvas p-5">
        <MailCheck className="mb-4 text-leaf-action" size={28} aria-hidden="true" />
        <p className="text-sm text-body">Verification sent to</p>
        <p className="mt-1 break-all font-semibold">{form.email}</p>
        <p className="mt-4 text-sm leading-6 text-body">Open the link in your email, then return to sign in. The link expires after 24 hours.</p>
      </div>
      {message && <p role="status" className="mt-4 text-sm text-leaf-action">{message}</p>}
      {error && <p role="alert" className="auth-error mt-4">{error}</p>}
      <Link to="/login" className="account-primary mt-6 block w-full">Continue to sign in</Link>
      <button disabled={busy} onClick={event => submit(event, true)} className="auth-link mt-3 min-h-11 w-full disabled:opacity-50">{busy ? 'Sending verification...' : 'Resend verification email'}</button>
    </div> : <>
      <form onSubmit={submit}>
        <fieldset disabled={busy} className="grid gap-5">
          {[['full_name','Full name','text','name'],['email','Email address','email','email'],['organization_name','Organization name','text','organization']].map(([key,label,type,autoComplete]) => <label key={key} className="text-sm font-semibold">{label}<input required type={type} autoComplete={autoComplete} maxLength={255} value={form[key]} onChange={event => setForm({ ...form, [key]: event.target.value })} className="account-input" /></label>)}
          <AuthPassword id="signup-password" required minLength={10} maxLength={72} autoComplete="new-password" hint="Use at least 10 characters." value={form.password} onChange={event => setForm({ ...form, password: event.target.value })} />
          {error && <p role="alert" className="auth-error">{error}</p>}
          <button className="account-primary w-full" type="submit">{busy ? 'Creating account...' : 'Create account'}</button>
        </fieldset>
      </form>
      <p className="mt-6 text-center text-sm text-body">Already have an account? <Link to="/login" className="auth-link">Sign in</Link></p>
      <p className="mt-8 border-t border-line pt-5 text-sm leading-6 text-body">Joining an existing team? Create and verify your account, then open the invitation from your administrator.</p>
    </>}
  </AuthLayout>;
}
