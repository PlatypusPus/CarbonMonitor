import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';
import { accountError } from './Signup';

export default function AccountLink({join = false}) {
  const location = useLocation();
  const {user,loading,logout} = useAuth();
  const [token] = useState(() => new URLSearchParams(location.hash.slice(1)).get('token') || '');
  const [busy,setBusy] = useState(false);
  const [message,setMessage] = useState('');
  const [error,setError] = useState('');
  const [invitation,setInvitation] = useState(null);
  useEffect(() => {
    if (!join || !user || !token) return;
    let active = true;
    client.post('/account/invitations/preview',{token}).then(({data}) => {if(active) setInvitation(data);})
      .catch(error => {if(active) setError(accountError(error));});
    return () => {active = false;};
  },[join,user,token]);
  async function confirm() {
    setBusy(true); setError('');
    try { const {data} = await client.post(join?'/account/join':'/account/verify-email',{token});
      if(join) await logout();
      setMessage(data.message); window.history.replaceState(null,'',location.pathname);
    } catch(error) {setError(accountError(error));} finally {setBusy(false);}
  }
  return <main className="grid min-h-screen place-items-center bg-canvas p-5"><section className="w-full max-w-lg rounded-2xl border border-line bg-surface p-8">
    <Link to="/" className="font-bold text-leaf-action">CarbonTrace</Link><h1 className="mt-7 text-2xl font-semibold text-ink">{join?'Join an organization':'Verify your email'}</h1>
    {message ? <><p role="status" className="mt-5 text-sm text-leaf-action">{message}</p><Link to="/login" className="account-primary mt-6 inline-flex">Sign in</Link></> : <>
      <p className="my-5 text-sm leading-7 text-body">{join?'Accepting this invitation moves your account to the invited organization as a facility manager. Your previous organization’s records stay there. Sign in using the email that received the invitation.':'Confirm your email address to unlock your private workspace.'}</p>
      {invitation && <dl className="mb-5 rounded-lg bg-canvas p-4 text-sm"><dt className="text-body">Organization</dt><dd className="mt-1 font-semibold">{invitation.organization}</dd><dt className="mt-3 text-body">Assigned facility</dt><dd className="mt-1 font-semibold">{invitation.facility}</dd></dl>}
      {!token ? <p role="alert">Open the full link from your email.</p> : join && !user ? <div className="flex flex-wrap gap-4"><Link to="/login" state={{returnTo:location.pathname+location.hash}} className="account-primary">Sign in to accept</Link><Link to="/signup" className="button-secondary">Create account</Link><p className="text-xs text-body">After creating and verifying an account, reopen this invitation.</p></div> : <button disabled={busy || loading || (join && !invitation)} onClick={confirm} className="account-primary">{busy?'Working...':join?'Accept invitation':'Verify email'}</button>}
    </>}{error && <p role="alert" className="mt-5 text-sm text-[#A62F38]">{error}</p>}
  </section></main>;
}
