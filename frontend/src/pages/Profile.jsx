import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';
import { useFacilities } from '../api/hooks';
import { accountError } from './Signup';

export default function Profile() {
  const {user,logout,reloadUser} = useAuth();
  const navigate = useNavigate();
  const profile = useQuery({queryKey:['profile',user.id],queryFn:()=>client.get('/account/profile').then(r=>r.data)});
  const facilities = useFacilities();
  const [name,setName] = useState(user.full_name || '');
  const [password,setPassword] = useState({current_password:'',new_password:''});
  const [invite,setInvite] = useState({email:'',facility_id:''});
  const [deletion,setDeletion] = useState({password:'',confirmation:''});
  const [busy,setBusy] = useState('');
  const [feedback,setFeedback] = useState(null);
  async function save(event,kind) {
    event.preventDefault(); setBusy(kind); setFeedback(null);
    try {
      if(kind==='name') {await client.patch('/account/profile',{full_name:name}); await reloadUser(); await profile.refetch();}
      if(kind==='password') await client.post('/account/password',password);
      if(kind==='invite') {await client.post('/account/invitations',invite);setInvite({...invite,email:''});}
      if(kind==='delete') await client.delete('/account/profile',{data:deletion});
      if(['password','delete'].includes(kind)) {await logout(); navigate('/login',{replace:true});return;}
      setFeedback({kind,text:kind==='invite'?'Invitation sent. It expires in 7 days.':'Profile saved.'});
    } catch(error) {setFeedback({kind,error:true,text:accountError(error)});} finally {setBusy('');}
  }
  const notice = (kind) => feedback?.kind===kind && <p role={feedback.error?'alert':'status'} className={`mt-4 text-sm ${feedback.error?'text-[#A62F38]':'text-leaf-action'}`}>{feedback.text}</p>;
  const date = (value) => value?new Date(value).toLocaleString():'Not available';
  return <div className="mx-auto flex max-w-4xl flex-col gap-6">
    <header><h1 className="font-semibold text-ink">Your account</h1><p className="mt-2 text-sm text-body">Manage your profile, security, and organization access.</p></header>
    <section className="account-section"><h2 className="text-lg font-semibold text-ink">Profile</h2><form onSubmit={(e)=>save(e,'name')} className="mt-5"><fieldset disabled={!!busy} className="grid gap-4 sm:grid-cols-2"><label className="text-sm">Full name<input required maxLength={255} value={name} onChange={e=>setName(e.target.value)} className="account-input" /></label><div className="text-sm"><p>Email address</p><p className="mt-3 break-all font-semibold">{user.email}</p><span className="text-xs text-leaf-action">Verified email</span></div><button className="account-primary w-fit" type="submit">{busy==='name'?'Saving...':'Save profile'}</button></fieldset>{notice('name')}</form></section>
    <section className="account-section"><h2 className="text-lg font-semibold text-ink">Account activity</h2>{profile.isError?<p role="alert" className="mt-4 text-sm">Could not load account activity. <button onClick={()=>profile.refetch()} className="underline">Retry</button></p>:<dl className="mt-5 grid gap-5 text-sm sm:grid-cols-2">{[['Organization',user.organization_name || 'Not assigned'],['Access',user.role==='admin'?'Organization administrator':'Facility manager'],['Joined',date(profile.data?.created_at)],['Last sign-in',date(profile.data?.last_login_at)],['Your uploads',profile.data?.uploads ?? '...'],['Active sessions',profile.data?.active_sessions ?? '...']].map(([label,value])=><div key={label}><dt className="text-body">{label}</dt><dd className="mt-1 font-medium text-ink">{value}</dd></div>)}</dl>}</section>
    <section className="account-section"><h2 className="text-lg font-semibold text-ink">Change password</h2><p className="mt-2 text-sm text-body">Changing your password signs out all sessions.</p><form onSubmit={e=>save(e,'password')} className="mt-5"><fieldset disabled={!!busy} className="grid gap-4 sm:grid-cols-2">{[['current_password','Current password'],['new_password','New password']].map(([key,label])=><label key={key} className="text-sm">{label}<input type="password" required minLength={key==='new_password'?10:1} maxLength={72} autoComplete={key==='new_password'?'new-password':'current-password'} value={password[key]} onChange={e=>setPassword({...password,[key]:e.target.value})} className="account-input" /></label>)}<button type="submit" className="account-primary w-fit">{busy==='password'?'Updating...':'Update password'}</button></fieldset>{notice('password')}</form></section>
    <section className="account-section"><h2 className="text-lg font-semibold text-ink">Organization access</h2><p className="mt-2 text-sm leading-7 text-body">To join another organization, ask its administrator to invite your verified email. Accept the link in that email. Your account belongs to one organization at a time; previous facility records stay with their organization.</p>
      {user.role==='admin' && <form onSubmit={e=>save(e,'invite')} className="mt-5 border-t border-line pt-5"><h3 className="mb-4 font-semibold">Invite a facility manager</h3><fieldset disabled={!!busy} className="grid gap-4 sm:grid-cols-2"><label className="text-sm">Recipient email<input type="email" required value={invite.email} onChange={e=>setInvite({...invite,email:e.target.value})} className="account-input" /></label><label className="text-sm">Assigned facility<select required value={invite.facility_id} onChange={e=>setInvite({...invite,facility_id:e.target.value})} className="account-input"><option value="">Choose a facility</option>{(facilities.data??[]).map(f=><option key={f.id} value={f.id}>{f.name}</option>)}</select></label><button type="submit" className="account-primary w-fit">{busy==='invite'?'Sending...':'Send invitation'}</button></fieldset>{notice('invite')}</form>}
    </section>
    <section className="account-section border-[#D9B5B9]"><h2 className="text-lg font-semibold text-[#A62F38]">Delete account</h2><p className="mt-2 text-sm leading-7 text-body">This permanently removes your sign-in access and anonymizes your profile. Shared facility records and upload attribution remain for the organization's history. If you are the last administrator of an organization with members or records, assign another administrator first.</p><details className="mt-4"><summary className="cursor-pointer text-sm font-semibold text-[#A62F38]">Delete my account</summary><form onSubmit={e=>save(e,'delete')} className="mt-4"><fieldset disabled={!!busy} className="grid gap-4 sm:grid-cols-2"><label className="text-sm">Current password<input required type="password" autoComplete="current-password" maxLength={72} value={deletion.password} onChange={e=>setDeletion({...deletion,password:e.target.value})} className="account-input" /></label><label className="text-sm">Type DELETE to confirm<input required pattern="DELETE" value={deletion.confirmation} onChange={e=>setDeletion({...deletion,confirmation:e.target.value})} className="account-input" /></label><button type="submit" className="w-fit rounded-lg bg-[#A62F38] px-4 py-3 text-sm font-semibold text-white">{busy==='delete'?'Deleting...':'Permanently delete account'}</button></fieldset>{notice('delete')}</form></details></section>
  </div>;
}
