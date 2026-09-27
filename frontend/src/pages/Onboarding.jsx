import { ArrowRight, BarChart3, Building2, FileUp, Leaf, Radio } from "lucide-react";
import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";
import { getOnboarding, saveOnboarding } from "../lib/onboarding";

const focuses = [
  { value: "overview", label: "Facility overview", icon: Building2 },
  { value: "trends", label: "Emissions trends", icon: BarChart3 },
  { value: "anomalies", label: "Anomaly review", icon: Radio },
];

const sources = [
  { value: "upload", label: "Upload or scan records", detail: "Review CSV, Excel, PDF, or image records before confirming", icon: FileUp },
  { value: "review", label: "Review existing data", detail: "Open your selected view without uploading a file", icon: BarChart3 },
];

export default function Onboarding() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [focus, setFocus] = useState("overview");
  const [source, setSource] = useState("upload");

  if (getOnboarding(user?.id)) return <Navigate to="/dashboard" replace />;

  function complete() {
    saveOnboarding(user.id, { focus, source, completedAt: new Date().toISOString() });
    const focusPath = { overview: "/dashboard", trends: "/trends", anomalies: "/anomalies" }[focus];
    navigate(source === "upload" ? "/upload" : focusPath, { replace: true });
  }

  return (
    <main className="min-h-[100dvh] bg-canvas px-5 py-8 text-ink md:px-8">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center gap-2 font-bold"><span className="grid h-9 w-9 place-items-center rounded-lg bg-leaf text-white"><Leaf size={18} /></span>CarbonTrace</div>

        <div className="mt-12 grid gap-10 lg:grid-cols-[0.7fr_1.3fr]">
          <section>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-leaf">Workspace setup</p>
            <h1 className="mt-4 text-4xl font-bold tracking-tight">Start with the work that matters.</h1>
            <p className="mt-4 leading-7 text-body">Choose your first view and how you plan to add facility activity data. You can change course anytime.</p>
            <dl className="mt-8 space-y-4 text-sm">
              <div><dt className="font-semibold text-ink">Signed in as</dt><dd className="mt-1 text-body">{user?.full_name || user?.email}</dd></div>
              <div><dt className="font-semibold text-ink">Facility access</dt><dd className="mt-1 text-body">{user?.facility_id ? "Facility assigned" : "No facility assigned. Ask an administrator before uploading."}</dd></div>
            </dl>
          </section>

          <section className="rounded-2xl border border-line bg-surface p-6 shadow-card md:p-8" aria-labelledby="setup-options">
            <h2 id="setup-options" className="text-xl font-bold">Personalize your starting point</h2>

            <fieldset className="mt-7">
              <legend className="text-sm font-semibold">What do you want to review first?</legend>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                {focuses.map(({ value, label, icon: Icon }) => (
                  <label key={value} className={`cursor-pointer rounded-xl border p-4 transition ${focus === value ? "border-leaf bg-[#edf6f0]" : "border-line hover:border-mint"}`}>
                    <input className="sr-only" type="radio" name="focus" value={value} checked={focus === value} onChange={() => setFocus(value)} />
                    <Icon size={20} className="text-leaf" /><span className="mt-3 block text-sm font-semibold">{label}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <fieldset className="mt-8">
              <legend className="text-sm font-semibold">How will you add your first records?</legend>
              <div className="mt-3 grid gap-3">
                {sources.map(({ value, label, detail, icon: Icon }) => (
                  <label key={value} className={`flex cursor-pointer items-start gap-4 rounded-xl border p-4 transition ${source === value ? "border-leaf bg-[#edf6f0]" : "border-line hover:border-mint"}`}>
                    <input className="mt-1 accent-leaf" type="radio" name="source" value={value} checked={source === value} onChange={() => setSource(value)} />
                    <Icon size={20} className="mt-0.5 text-leaf" /><span><span className="block font-semibold">{label}</span><span className="mt-1 block text-sm text-body">{detail}</span></span>
                  </label>
                ))}
              </div>
            </fieldset>

            <button onClick={complete} className="mt-8 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-leaf-action px-5 py-3.5 font-bold text-white transition hover:bg-leaf-action-hover active:translate-y-px">Finish setup <ArrowRight size={18} /></button>
          </section>
        </div>
      </div>
    </main>
  );
}
