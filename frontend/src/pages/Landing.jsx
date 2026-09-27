import { ArrowRight, BarChart3, FileCheck2, Leaf, Upload } from "lucide-react";
import { Link } from "react-router-dom";

import facilityHero from "../assets/carbontrace-facility-hero.png";

const flow = [
  { icon: Upload, title: "Bring your activity data", text: "Upload electricity, fuel, and LPG records from CSV or Excel." },
  { icon: BarChart3, title: "Calculate and monitor", text: "Convert activity into Scope 1 and 2 CO2e with traceable factors." },
  { icon: FileCheck2, title: "Report with confidence", text: "Investigate anomalies and export a BRSR-ready ESG report." },
];

export default function Landing() {
  return (
    <div className="min-h-[100dvh] bg-[#f3f5f0] text-[#1d2922] dark:bg-[#111713] dark:text-[#edf3ee]">
      <header className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 md:px-8">
        <Link to="/" className="flex items-center gap-2 font-bold tracking-tight" aria-label="CarbonTrace home">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-leaf text-white"><Leaf size={19} /></span>
          CarbonTrace
        </Link>
        <nav className="flex items-center gap-2" aria-label="Public navigation">
          <a href="#workflow" className="hidden rounded-lg px-3 py-2 text-sm font-semibold hover:bg-black/5 dark:hover:bg-white/10 sm:block">How it works</a>
          <Link to="/login" className="rounded-lg border border-[#bdc9c0] px-4 py-2 text-sm font-bold hover:border-leaf dark:border-[#435248]">Sign in</Link>
        </nav>
      </header>

      <main>
        <section className="mx-auto grid min-h-[calc(100dvh-4rem)] max-w-7xl items-center gap-10 px-5 py-10 md:px-8 lg:grid-cols-[0.85fr_1.15fr] lg:py-14">
          <div className="max-w-xl">
            <p className="mb-5 text-xs font-bold uppercase tracking-[0.18em] text-leaf">Carbon accounting for operations</p>
            <h1 className="text-5xl font-bold leading-[0.98] tracking-[-0.05em] sm:text-6xl lg:text-7xl">Measure what your facilities emit.</h1>
            <p className="mt-6 max-w-lg text-lg leading-8 text-[#56635a] dark:text-[#aebbb1]">Turn energy records into audit-ready emissions data, anomaly alerts, and ESG reports.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/login" className="inline-flex items-center gap-2 rounded-lg bg-leaf-action px-5 py-3 font-bold text-white transition hover:bg-leaf-action-hover active:translate-y-px">Open workspace <ArrowRight size={18} /></Link>
              <a href="#workflow" className="rounded-lg border border-[#bdc9c0] px-5 py-3 font-bold transition hover:border-leaf dark:border-[#435248]">View workflow</a>
            </div>
          </div>

          <figure className="overflow-hidden rounded-2xl bg-[#dce5dd]">
            <img src={facilityHero} alt="Industrial facility with rooftop solar panels surrounded by forest" className="aspect-[4/3] h-full w-full object-cover" />
          </figure>
        </section>

        <section id="workflow" className="border-y border-[#d8dfd9] bg-[#e8ede8] dark:border-[#2b362e] dark:bg-[#171f19]">
          <div className="mx-auto max-w-7xl px-5 py-20 md:px-8">
            <h2 className="max-w-2xl text-3xl font-bold tracking-tight sm:text-4xl">One accountable flow from activity to report.</h2>
            <div className="mt-12 grid gap-px overflow-hidden rounded-xl bg-[#cbd5cd] dark:bg-[#364139] md:grid-cols-[1.15fr_0.85fr]">
              {flow.map(({ icon: Icon, title, text }, index) => (
                <article key={title} className={`bg-[#f3f5f0] p-7 dark:bg-[#111713] ${index === 0 ? "md:row-span-2 md:p-10" : ""}`}>
                  <Icon className="text-leaf" size={24} aria-hidden="true" />
                  <h3 className={`${index === 0 ? "mt-16 text-2xl md:mt-24" : "mt-8 text-lg"} font-bold`}>{title}</h3>
                  <p className="mt-2 leading-7 text-[#5d695f] dark:text-[#aebbb1]">{text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-8 text-sm text-[#68736a] md:flex-row md:items-center md:justify-between md:px-8 dark:text-[#92a096]">
        <span>CarbonTrace</span>
        <span>Scope 1 and 2 accounting for facility teams.</span>
      </footer>
    </div>
  );
}
