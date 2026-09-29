import { ArrowRight, BarChart3, FileCheck2, Leaf, Upload } from "lucide-react";
import { Link } from "react-router-dom";

import facilityHero from "../assets/carbontrace-facility-hero.png";

const flow = [
  { icon: Upload, title: "Bring your activity data", text: "Import electricity workbooks and fuel CSVs into the right facility." },
  { icon: BarChart3, title: "Calculate and monitor", text: "Convert activity into Scope 1 and 2 CO2e with traceable factors." },
  { icon: FileCheck2, title: "Report with confidence", text: "Investigate anomalies and export an emissions summary report." },
];

export default function Landing() {
  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <header className="mx-auto flex h-20 max-w-7xl items-center justify-between border-b border-line px-5 md:px-8">
        <Link to="/" className="flex items-center gap-2 font-bold tracking-tight" aria-label="CarbonTrace home">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-leaf-action text-white"><Leaf size={22} /></span>
          CarbonTrace
        </Link>
        <nav className="flex items-center gap-2" aria-label="Public navigation">
          <a href="#workflow" className="hidden rounded-lg px-3 py-2 text-sm font-semibold hover:bg-black/5 sm:block">How it works</a>
          <Link to="/login" className="rounded-lg border border-[#bdc9c0] px-4 py-2 text-sm font-bold hover:border-leaf">Sign in</Link>
        </nav>
      </header>

      <main>
        <section className="mx-auto grid max-w-7xl items-center gap-10 px-5 py-14 md:px-8 lg:grid-cols-[0.95fr_1.05fr] lg:gap-14 lg:py-20">
          <div className="max-w-xl">
            <p className="mb-5 text-sm font-semibold text-leaf-action">For the people running your facilities</p>
            <h1 className="text-5xl font-semibold leading-[1.04] tracking-[-0.045em] sm:text-6xl lg:text-7xl">Understand your carbon footprint.</h1>
            <p className="mt-6 max-w-lg text-lg leading-8 text-body">A shared place for energy records, emissions tracking, and better decisions. From your first electricity bill to your next reduction plan.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/login" className="inline-flex items-center gap-2 rounded-lg bg-leaf-action px-5 py-3 font-bold text-white transition hover:bg-leaf-action-hover active:translate-y-px">Open workspace <ArrowRight size={18} /></Link>
              <a href="#workflow" className="rounded-lg border border-[#bdc9c0] px-5 py-3 font-bold transition hover:border-leaf">View workflow</a>
            </div>
            <div className="mt-10 flex flex-wrap gap-x-6 gap-y-2 border-t border-line pt-5 text-sm text-body"><span>Electricity & fuel</span><span>Facility-level access</span><span>Traceable calculations</span></div>
          </div>

          <figure className="overflow-hidden rounded-2xl bg-[#204B36]">
            <img src={facilityHero} alt="Industrial facility with rooftop solar panels surrounded by forest" className="aspect-[5/4] w-full object-cover" />
            <figcaption className="flex items-center justify-between gap-3 px-6 py-5 text-sm text-white"><span>One workspace. Every facility.</span><Leaf size={20} aria-hidden="true" /></figcaption>
          </figure>
        </section>

        <section id="workflow" className="border-y border-line bg-surface">
          <div className="mx-auto max-w-7xl px-5 py-16 md:px-8">
            <h2 className="max-w-2xl text-3xl font-semibold tracking-tight sm:text-4xl">From records to a clearer picture.</h2>
            <div className="mt-10 grid gap-8 md:grid-cols-3">
              {flow.map(({ icon: Icon, title, text }, index) => (
                <article key={title} className="border-t border-line pt-6">
                  <div className="flex items-center justify-between"><Icon className="text-leaf-action" size={24} aria-hidden="true" /><span className="text-sm text-body">Step {index + 1}</span></div>
                  <h3 className="mt-6 text-xl font-semibold">{title}</h3>
                  <p className="mt-3 max-w-sm leading-7 text-body">{text}</p>
                </article>
              ))}
            </div>
          </div>
        </section>
      </main>

      <footer className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-8 text-sm text-[#68736a] md:flex-row md:items-center md:justify-between md:px-8">
        <span>CarbonTrace</span>
        <span>Scope 1 and 2 accounting for facility teams.</span>
      </footer>
    </div>
  );
}

