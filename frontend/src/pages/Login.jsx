import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

function LeafMark({ size = 26 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.85"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M5 18 C5 9 12 4 20 4 C20 12 15 19 6 19 Z" />
      <path d="M5 19 C8 14 12 11 16 9" />
    </svg>
  );
}

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
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
      navigate("/", { replace: true });
    } catch {
      setError("Incorrect email or password");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      {/* Brand panel */}
      <div className="relative hidden flex-col overflow-hidden bg-gradient-to-br from-[#23895A] via-leaf to-[#3FB079] p-14 text-white lg:flex">
        <div className="absolute -right-20 -top-24 h-80 w-80 rounded-full bg-white/[0.08]" />
        <div className="absolute -bottom-32 -left-24 h-96 w-96 rounded-full bg-white/[0.06]" />
        <div className="relative flex w-fit items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl border border-white/30 bg-white/20">
            <LeafMark />
          </div>
          <span className="text-2xl font-bold tracking-tight">CarbonTrace</span>
        </div>
        <div className="relative my-auto max-w-lg">
          <h2 className="text-5xl font-bold leading-tight tracking-tight">
            Every emission, accounted for.
          </h2>
          <p className="mt-6 text-xl leading-relaxed text-white/90">
            Log in to monitor live facility data, investigate anomalies, and generate
            audit-ready compliance reports.
          </p>
        </div>
      </div>

      {/* Form panel */}
      <div className="flex items-center justify-center bg-surface px-10 py-12">
        <div className="w-full max-w-sm">
          <h1 className="text-3xl font-bold tracking-tight text-ink">Welcome back</h1>
          <p className="mb-9 mt-2 text-lg text-body">Sign in to your CarbonTrace workspace.</p>

          <form onSubmit={handleSubmit} className="flex flex-col">
            <label className="mb-2 text-sm font-semibold text-ink">Work email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@facility.com"
              className="mb-5 rounded-xl border-[1.5px] border-line bg-[#FBFCFB] px-4 py-3.5 text-ink outline-none focus:border-leaf focus:bg-white"
            />

            <label className="mb-2 text-sm font-semibold text-ink">Password</label>
            <div className="relative mb-6">
              <input
                type={showPw ? "text" : "password"}
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

            {error && <p className="mb-4 text-sm text-rose">{error}</p>}

            <button
              type="submit"
              disabled={submitting}
              className="rounded-xl bg-leaf py-4 text-lg font-bold text-white shadow-card transition-colors hover:bg-leaf-hover disabled:opacity-60"
            >
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
