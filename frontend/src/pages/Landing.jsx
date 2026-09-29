import { ArrowRight, BarChart3, FileCheck2, Leaf, Upload, Building2, Users, SlidersHorizontal, Zap, Fuel, Check } from "lucide-react";
import { Link } from "react-router-dom";

import facilityHero from "../assets/carbontrace-facility-hero.png";

const flow = [
  { icon: Upload, title: "Bring your activity data", text: "Import electricity workbooks and fuel CSVs into the right facility." },
  { icon: BarChart3, title: "Calculate and monitor", text: "Convert activity into Scope 1 and 2 CO2e with traceable factors." },
  { icon: FileCheck2, title: "Report with confidence", text: "Investigate anomalies and export an emissions summary report." },
];

const audiences = [
  { icon: Building2, title: "Facility managers", need: "Keep your site's records in order.", text: "Upload bills and fuel records to your assigned facility, check extracted values, and confirm what belongs in the ledger.", result: "A focused workspace for the site you manage." },
  { icon: Users, title: "Administrators", need: "See the whole organization.", text: "Manage facilities and user access, switch between sites, and review records across the organization from one place.", result: "Local responsibility with organization-wide visibility." },
  { icon: FileCheck2, title: "Sustainability & reporting teams", need: "Explain the numbers behind a report.", text: "Use period comparisons, calculation factors, and emissions summaries to prepare internal reviews with facility managers and decision-makers.", result: "A traceable starting point for reporting discussions." },
];

export default function Landing() {
  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <header className="mx-auto flex min-h-20 max-w-7xl flex-wrap items-center justify-between gap-3 border-b border-line px-5 py-4 md:px-8">
        <Link to="/" className="flex items-center gap-2 font-bold tracking-tight" aria-label="CarbonTrace home">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-leaf-action text-white"><Leaf size={22} /></span>
          CarbonTrace
        </Link>
        <nav className="flex flex-wrap items-center gap-2" aria-label="Public navigation">
          <a href="#why-carbontrace" className="rounded-lg px-2 py-2 text-sm font-semibold hover:bg-black/5">Why CarbonTrace</a>
          <a href="#who-its-for" className="rounded-lg px-2 py-2 text-sm font-semibold hover:bg-black/5">Who it's for</a>
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

        <section id="why-carbontrace" className="scroll-mt-6 bg-[#204B36] text-white">
          <div className="mx-auto grid max-w-7xl gap-12 px-5 py-16 md:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:py-20">
            <div><h2 className="max-w-lg text-3xl font-semibold leading-tight tracking-tight sm:text-4xl">Bills tell you what you used.<br />CarbonTrace helps you see what it means.</h2>
              <p className="mt-6 max-w-lg leading-7 text-white/80">Electricity spreadsheets, fuel logs, and reporting files often live in different places. CarbonTrace brings those records into a common process so teams can connect consumption with emissions and decide what to investigate next.</p>
              <a href="#workflow" className="mt-7 inline-flex min-h-11 items-center gap-2 font-semibold text-white underline underline-offset-4">See the workflow <ArrowRight size={17} /></a>
            </div>
            <div className="space-y-7">
              {[
                [Upload, 'Spend less time reconciling scattered files', 'Bring records into a facility ledger, review them before confirmation, and keep the source attached to the workflow.'],
                [BarChart3, 'Understand changes across reporting periods', 'Compare monthly, quarterly, and yearly emissions to spot changes worth discussing with your operations team.'],
                [SlidersHorizontal, 'Explore a reduction before making a change', 'Use what-if scenarios to see how a different activity quantity changes calculated emissions without altering original records.'],
              ].map(([Icon,title,text]) => <article key={title} className="flex gap-4 border-b border-white/20 pb-7 last:border-0 last:pb-0"><Icon size={24} className="mt-1 shrink-0 text-[#A8DBBF]" aria-hidden="true" /><div><h3 className="text-lg font-semibold">{title}</h3><p className="mt-2 text-sm leading-7 text-white/80">{text}</p></div></article>)}
            </div>
          </div>
        </section>

        <section id="who-its-for" className="mx-auto max-w-7xl scroll-mt-6 px-5 py-16 md:px-8 lg:py-20">
          <div className="flex flex-wrap items-end justify-between gap-5"><h2 className="max-w-xl text-3xl font-semibold tracking-tight sm:text-4xl">Built for the people behind each facility.</h2><p className="max-w-sm text-sm leading-7 text-body">Useful for campus teams and organizations tracking electricity and fuel across multiple sites.</p></div>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {audiences.map(({icon:Icon,title,need,text,result}) => <article key={title} className="flex flex-col rounded-xl border border-line bg-surface p-6 lg:p-7"><div className="mb-6 flex items-center gap-3"><Icon size={23} className="text-leaf-action" aria-hidden="true" /><h3 className="font-semibold">{title}</h3></div><p className="text-xl font-semibold leading-snug">{need}</p><p className="mb-7 mt-3 text-sm leading-7 text-body">{text}</p><p className="mt-auto flex items-start gap-2 border-t border-line pt-4 text-sm text-leaf-action"><Check size={17} className="mt-1 shrink-0" aria-hidden="true" />{result}</p></article>)}
          </div>
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

        <section className="mx-auto grid max-w-7xl gap-10 px-5 py-16 md:px-8 lg:grid-cols-2">
          <div><h2 className="text-3xl font-semibold tracking-tight">Start with the energy you can measure.</h2><p className="mt-5 max-w-lg leading-7 text-body">CarbonTrace currently covers Scope 1 and Scope 2. Keep fuel and purchased electricity distinct, then bring them together for an emissions overview.</p>
            <div className="mt-7 grid gap-4 sm:grid-cols-2">{[[Fuel,'Scope 1','Diesel, petrol and LPG','Direct emissions from recorded fuel use.'],[Zap,'Scope 2','Purchased electricity','Indirect emissions calculated from electricity consumption.']].map(([Icon,scope,title,text]) => <div key={scope} className="border-l-2 border-mint pl-4"><Icon size={22} className="mb-3 text-leaf-action" /><p className="text-sm font-semibold text-leaf-action">{scope}</p><h3 className="mt-1 font-semibold">{title}</h3><p className="mt-2 text-sm leading-6 text-body">{text}</p></div>)}</div>
          </div>
          <div className="rounded-xl border border-line bg-surface p-6 sm:p-8"><h2 className="mb-4 text-xl font-semibold">Before you get started</h2>
            {[
              ['What records can I upload?', 'Import the supported electricity workbook format or activity CSVs. The intake workflow also supports scanned documents for review before confirmation.'],
              ['Can each manager see only their facility?', 'Yes. Managers work within their assigned facility. Administrators control access and can review all facilities. Assigning an existing facility shares its historical records.'],
              ['Does this replace verified sustainability reporting?', 'No. Calculations depend on the records and emission factors you use. Check completeness, units and applicable factors before using results for external reporting. Scope 3 is not currently included.'],
            ].map(([question,answer]) => <details key={question} className="border-t border-line py-4"><summary className="cursor-pointer text-sm font-semibold text-ink">{question}</summary><p className="mt-3 text-sm leading-7 text-body">{answer}</p></details>)}
          </div>
        </section>
        <section className="mx-auto max-w-7xl px-5 pb-16 md:px-8"><div className="flex flex-wrap items-center justify-between gap-6 rounded-2xl bg-[#E2EFE7] p-8 sm:p-10"><div><h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Put your facility records to work.</h2><p className="mt-3 text-sm text-body">Sign in to your assigned workspace. New accounts are created by your administrator.</p></div><Link to="/login" className="inline-flex items-center gap-2 rounded-lg bg-leaf-action px-5 py-3 font-semibold text-white hover:bg-leaf-action-hover">Open workspace <ArrowRight size={18} /></Link></div></section>
      </main>

      <footer className="mx-auto flex max-w-7xl flex-col gap-3 px-5 py-8 text-sm text-[#68736a] md:flex-row md:items-center md:justify-between md:px-8">
        <span>CarbonTrace</span>
        <span>Scope 1 and 2 accounting for facility teams.</span>
      </footer>
    </div>
  );
}

