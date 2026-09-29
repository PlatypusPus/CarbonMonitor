import { ArrowLeft, Eye, EyeOff, Leaf } from 'lucide-react';
import { useState } from 'react';
import { Link, NavLink } from 'react-router-dom';
import facilityHero from '../assets/carbontrace-facility-hero.png';

export default function AuthLayout({ title, description, children }) {
  return <main className="auth-layout min-h-screen bg-surface text-ink lg:grid lg:grid-cols-2">
    <aside className="hidden bg-[#204B36] text-white lg:flex lg:flex-col lg:px-12 lg:py-10 xl:px-16">
      <Link to="/" className="flex w-fit items-center gap-3 text-xl font-semibold tracking-tight"><Leaf size={28} aria-hidden="true" />CarbonTrace</Link>
      <div className="my-12 max-w-lg xl:my-16">
        <h2 className="text-4xl font-semibold leading-[1.12] tracking-tight xl:text-5xl">A clearer view of your facility’s footprint.</h2>
        <p className="mt-5 max-w-md leading-7 text-white/80">Bring electricity and fuel records together. Understand your emissions and plan your next reduction.</p>
      </div>
      <figure className="mt-auto max-w-xl">
        <img src={facilityHero} alt="Solar panels on a facility surrounded by trees" className="aspect-[16/9] w-full rounded-xl object-cover" />
        <figcaption className="mt-5 border-t border-white/20 pt-5 text-sm text-white/80">Scope 1 and 2 accounting for facility teams.</figcaption>
      </figure>
    </aside>
    <section className="px-6 py-8 sm:px-12 lg:px-10 lg:py-10 xl:px-16" aria-labelledby="auth-title">
      <div className="mx-auto w-full max-w-md">
        <div className="mb-8 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2 font-semibold lg:hidden"><Leaf size={24} className="text-leaf-action" aria-hidden="true" />CarbonTrace</Link>
          <Link to="/" className="ml-auto inline-flex min-h-11 items-center gap-2 text-sm font-medium text-body hover:text-leaf-action"><ArrowLeft size={16} aria-hidden="true" />Back to home</Link>
        </div>
        <nav aria-label="Account access" className="mb-8 grid grid-cols-2 border-b border-line">
          {[['/login','Sign in'],['/signup','Create account']].map(([to,label]) => <NavLink key={to} to={to} className={({isActive}) => `border-b-2 px-3 py-3 text-center text-sm font-semibold ${isActive ? 'border-leaf-action text-leaf-action' : 'border-transparent text-body hover:text-ink'}`}>{label}</NavLink>)}
        </nav>
        <h1 id="auth-title" className="text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h1>
        <p className="mb-7 mt-3 text-sm leading-6 text-body">{description}</p>
        {children}
      </div>
    </section>
  </main>;
}

export function AuthPassword({ id, hint, ...props }) {
  const [visible, setVisible] = useState(false);
  return <div>
    <label htmlFor={id} className="text-sm font-semibold">Password</label>
    <div className="relative">
      <input {...props} id={id} type={visible ? 'text' : 'password'} aria-describedby={hint ? `${id}-hint` : undefined} className="account-input" style={{ paddingRight: '3.5rem' }} />
      <button type="button" onClick={() => setVisible(!visible)} aria-label={visible ? 'Hide password' : 'Show password'} aria-pressed={visible} className="absolute inset-y-0 right-0 grid w-12 place-items-center rounded-r-lg text-body hover:text-leaf-action">
        {visible ? <EyeOff size={18} /> : <Eye size={18} />}
      </button>
    </div>
    {hint && <p id={`${id}-hint`} className="mt-2 text-xs leading-5 text-body">{hint}</p>}
  </div>;
}
