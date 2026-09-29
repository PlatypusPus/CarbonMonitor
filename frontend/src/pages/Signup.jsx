import { useState } from "react";
import { Link } from "react-router-dom";
import { Leaf, MailCheck } from "lucide-react";
import client from "../api/client";

export const accountError = (error) => {
  const detail = error?.response?.data?.detail;
  return typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((item) => item.msg).join('. ') : 'The request could not be completed. Please try again.';
};

export default function Signup() {
  const [form, setForm] = useState({full_name:'',email:'',organization_name:'',password:''});
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  async function submit(event, resend = false) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('');
    try {
      const {data} = await client.post(resend ? '/account/resend-verification' : '/account/signup', resend ? {email:form.email} : form);
      setSent(true); setMessage(data.message); setForm((previous) => ({...previous,password:''}));
    } catch(error) { setError(accountError(error)); } finally { setBusy(false); }
  }
  return <main className="grid min-h-screen place-items-center bg-canvas px-5 py-10"><section className="w-full max-w-lg rounded-2xl border border-line bg-surface p-6 sm:p-9">
    <Link to="/" className="mb-8 flex items-center gap-2 font-bold text-ink"><Leaf className="text-leaf-action" />CarbonTrace</Link>
    <h1 className="text-3xl font-semibold tracking-tight text-ink">{sent ? 'Check your email' : 'Create your workspace'}</h1>
    <p className="mt-3 text-sm leading-6 text-body">{sent ? 'Verify your email, then sign in. Verification links expire after 24 hours.' : 'Start with a private organization and an empty facility. An administrator can invite you to another organization later.'}</p>
    {sent ? <div className="mt-7"><MailCheck className="mb-4 text-leaf-action" size={32} /><p className="break-all font-semibold">{form.email}</p><button disabled={busy} onClick={(event) => submit(event, true)} className="button-secondary mt-5">{busy ? 'Sending...' : 'Resend verification'}</button></div>
      : <form onSubmit={submit} className="mt-7 grid gap-4"><fieldset disabled={busy} className="grid gap-4">
        {[["full_name","Full name","text","name"],["email","Email address","email","email"],["organization_name","Organization name","text","organization"],["password","Password","password","new-password"]].map(([key,label,type,autoComplete]) => <label key={key} className="text-sm font-medium text-ink">{label}<input required type={type} autoComplete={autoComplete} minLength={key==='password'?10:1} maxLength={key==='password'?72:255} value={form[key]} onChange={(event)=>setForm({...form,[key]:event.target.value})} className="account-input" /></label>)}
        <p className="text-xs text-body">Use at least 10 characters for your password.</p>
        <button className="account-primary" type="submit">{busy ? 'Creating account...' : 'Create account'}</button>
      </fieldset></form>}
    {message && <p role="status" className="mt-5 text-sm text-leaf-action">{message}</p>}{error && <p role="alert" className="mt-5 text-sm text-[#A62F38]">{error}</p>}
    <p className="mt-7 text-sm text-body">Already have an account? <Link to="/login" className="font-semibold text-leaf-action underline">Sign in</Link></p>
  </section></main>;
}
