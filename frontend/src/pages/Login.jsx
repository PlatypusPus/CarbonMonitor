import { ArrowLeft, Eye, EyeOff, Leaf } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import client from "../api/client";
import { accountError } from "./Signup";

import { useAuth } from "../context/AuthContext";
import facilityHero from "../assets/carbontrace-facility-hero.png";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [notice, setNotice] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await login(email, password);
      const destination = location.state?.returnTo;
      navigate(destination?.startsWith('/join-organization#') ? destination : "/onboarding", { replace: true });
    } catch (error) {
      setError(accountError(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden flex-col overflow-hidden bg-[#204B36] p-12 text-white lg:flex xl:p-16">
        <div className="relative flex w-fit items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl border border-white/30 bg-white/20">
            <Leaf size={26} />
          </div>
          <span className="text-2xl font-bold tracking-tight">CarbonTrace</span>
        </div>
        <div className="relative mb-8 mt-16 max-w-lg">
          <h2 className="text-4xl font-semibold leading-[1.12] tracking-tight xl:text-5xl">
            A clearer view of your facility's footprint.
          </h2>
          <p className="mt-5 max-w-md text-base leading-7 text-white/80">
            Bring electricity and fuel records together. Review emissions, compare periods, and plan your next reduction.
          </p>
        </div>
        <figure className="mt-auto overflow-hidden rounded-xl"><img src={facilityHero} alt="Solar panels on a facility surrounded by trees" className="aspect-[16/9] w-full object-cover" /></figure>
        <p className="mt-5 text-xs text-white/70">Scope 1 and 2 accounting for facility teams.</p>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center bg-surface px-6 py-10 sm:px-12">
        <div className="w-full max-w-md">
          <div className="mb-10 flex items-center gap-2 font-bold text-ink lg:hidden"><Leaf className="text-leaf-action" size={24} />CarbonTrace</div>
          <Link to="/" className="mb-8 inline-flex items-center gap-2 text-sm font-semibold text-body hover:text-leaf"><ArrowLeft size={16} /> Back to home</Link>
          <h1 className="text-4xl font-semibold tracking-tight text-ink">Welcome back.</h1>
          <p className="mb-9 mt-3 text-base text-body">Sign in to manage your facility's emissions.</p>

          <form onSubmit={handleSubmit} className="flex flex-col">
            <label htmlFor="email" className="mb-2 text-sm font-semibold text-ink">Work email</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@facility.com"
              className="mb-5 rounded-xl border-[1.5px] border-line bg-[#FBFCFB] px-4 py-3.5 text-ink outline-none focus:border-leaf focus:bg-white"
            />

            <label htmlFor="password" className="mb-2 text-sm font-semibold text-ink">Password</label>
            <div className="relative mb-6">
              <input
                id="password"
                type={showPw ? "text" : "password"}
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="••••••••••"
                className="w-full rounded-xl border-[1.5px] border-line bg-[#FBFCFB] px-4 py-3.5 pr-12 text-ink outline-none focus:border-leaf focus:bg-white"
              />
              <button
                type="button"
                onClick={() => setShowPw((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-leaf"
                aria-label={showPw ? "Hide password" : "Show password"}
              >
                {showPw ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>

            {error && <p role="alert" className="mb-4 rounded-lg border border-rose/30 bg-rose/5 p-3 text-sm text-[#A62F38]">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="rounded-xl bg-leaf-action py-4 text-lg font-bold text-white shadow-card transition-colors hover:bg-leaf-action-hover disabled:opacity-60"
            >
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <p className="mt-6 text-center text-sm leading-6 text-body">New to CarbonTrace? <Link to="/signup" className="font-semibold text-leaf-action underline">Create an account</Link></p>
          <button type="button" disabled={submitting || !email} className="mt-4 text-sm text-leaf-action underline disabled:opacity-50" onClick={async () => {
            setSubmitting(true); setError(''); setNotice('');
            try {const {data} = await client.post('/account/resend-verification', {email}); setNotice(data.message);}
            catch(error) {setError(accountError(error));} finally {setSubmitting(false);}
          }}>Resend email verification</button>
          {notice && <p role="status" className="mt-3 text-sm text-leaf-action">{notice}</p>}
        </div>
      </div>
    </div>
  );
}
