import { Link } from "react-router-dom";

// Illustrative rows only. They use the same formula the app applies: kg CO2e = quantity x factor.
const FACTOR = 0.82;
const sample = [
  ["Jan 2026", 41200],
  ["Feb 2026", 38650],
  ["Mar 2026", 44900],
].map(([month, kwh]) => ({ month, kwh, kg: kwh * FACTOR }));
const n = (value) => Math.round(value).toLocaleString("en");

const steps = [
  ["Upload", "A Mescom electricity workbook (.xlsx), a fuel CSV, or a scanned bill. Each one is read into draft rows for the facility you pick."],
  ["Review", "Drafts are listed with their source file and row. Nothing is counted yet, and rows you reject never reach a report."],
  ["Confirm", "Confirming a row applies the emission factor valid for that period and stores the result with the factor that was used."],
  ["Report", "Dashboard, trends, what-if scenarios and the PDF read only confirmed rows. Anomaly detection runs when you trigger it."],
];

const roles = [
  ["Administrator", "Creates facilities and accounts, switches between facilities, reviews everything in the organization."],
  ["Facility manager", "Uploads, reviews and confirms records for their own facility, and edits that facility's details."],
  ["Auditor", "Read access to dashboards and reports. Cannot create or confirm records."],
];

const faq = [
  ["Which files can I upload?", "The supported electricity workbook layout, CSVs with timestamp, metric, value and unit columns, and scanned bills or PDFs that go through the same review step."],
  ["Where do emission factors come from?", "A table in the database, matched by activity type, region and validity dates. The seeded values are placeholders. Replace them with your approved factors before using any number externally."],
  ["Is this a verified disclosure?", "No. It calculates from the records you confirm. Check units, completeness and factors first. Scope 3 is not included."],
];

export default function Landing() {
  return (
    <div className="min-h-[100dvh] bg-canvas text-ink">
      <header className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-5 py-5 md:px-8">
        <Link to="/" className="text-lg font-bold tracking-tight" aria-label="CarbonTrace home">CarbonTrace</Link>
        <nav className="flex items-center gap-2" aria-label="Public navigation">
          <a href="#how-it-works" className="hidden rounded-lg px-3 py-2 text-sm font-semibold hover:bg-black/5 sm:block">How it works</a>
          <a href="#scope" className="hidden rounded-lg px-3 py-2 text-sm font-semibold hover:bg-black/5 sm:block">What it covers</a>
          <Link to="/login" className="rounded-lg border border-line bg-surface px-4 py-2 text-sm font-semibold hover:border-leaf">Sign in</Link>
        </nav>
      </header>

      <main>
        <section className="mx-auto grid max-w-6xl items-center gap-10 px-5 pb-16 pt-8 md:px-8 lg:grid-cols-2 lg:gap-14 lg:pb-24 lg:pt-14">
          <div>
            <h1 className="text-4xl font-semibold leading-[1.08] tracking-tight sm:text-5xl">Monthly electricity and fuel records in. Scope 1 and 2 emissions out.</h1>
            <p className="mt-6 max-w-lg text-lg leading-8 text-body">Upload a workbook or CSV, review every row, then confirm it. Only confirmed rows reach the dashboard and the PDF report, so the numbers always trace back to a source file.</p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/signup" className="rounded-lg bg-leaf-action px-5 py-3 font-semibold text-white hover:bg-leaf-action-hover">Create account</Link>
              <Link to="/login" className="rounded-lg border border-line bg-surface px-5 py-3 font-semibold hover:border-leaf">Sign in</Link>
            </div>
          </div>

          <figure className="rounded-xl border border-line bg-surface p-5 sm:p-6" aria-label="Sample confirmed ledger">
            <figcaption className="mb-4 flex items-baseline justify-between gap-3 text-sm">
              <span className="font-semibold">Confirmed electricity records</span>
              <span className="text-xs text-muted">Sample data</span>
            </figcaption>
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-line text-xs text-body">
                  <th className="pb-2 font-semibold">Month</th>
                  <th className="pb-2 text-right font-semibold">Quantity (kWh)</th>
                  <th className="pb-2 text-right font-semibold">Factor</th>
                  <th className="pb-2 text-right font-semibold">kg CO₂e</th>
                </tr>
              </thead>
              <tbody className="tabular-nums">
                {sample.map((row) => (
                  <tr key={row.month} className="border-b border-line last:border-0">
                    <td className="py-3">{row.month}</td>
                    <td className="py-3 text-right">{n(row.kwh)}</td>
                    <td className="py-3 text-right text-body">{FACTOR}</td>
                    <td className="py-3 text-right font-semibold">{n(row.kg)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-4 border-t border-line pt-4 text-xs leading-6 text-body">kg CO₂e = quantity × emission factor. The factor shown is a demonstration value.</p>
          </figure>
        </section>

        <section id="how-it-works" className="scroll-mt-6 border-y border-line bg-surface">
          <div className="mx-auto max-w-6xl px-5 py-16 md:px-8">
            <h2 className="max-w-2xl text-2xl font-semibold tracking-tight sm:text-3xl">How a row becomes a reported number</h2>
            <ol className="mt-8 divide-y divide-line border-y border-line">
              {steps.map(([title, text], index) => (
                <li key={title} className="grid gap-2 py-5 sm:grid-cols-[3rem_9rem_1fr] sm:gap-6">
                  <span className="text-sm text-muted">{index + 1}</span>
                  <h3 className="font-semibold">{title}</h3>
                  <p className="max-w-2xl text-sm leading-7 text-body">{text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="scope" className="mx-auto grid max-w-6xl scroll-mt-6 gap-10 px-5 py-16 md:px-8 lg:grid-cols-2">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">What it covers</h2>
            <dl className="mt-6 divide-y divide-line border-y border-line text-sm">
              <div className="grid gap-1 py-4 sm:grid-cols-[9rem_1fr]"><dt className="font-semibold">Scope 2</dt><dd className="text-body">Purchased electricity, in kWh.</dd></div>
              <div className="grid gap-1 py-4 sm:grid-cols-[9rem_1fr]"><dt className="font-semibold">Scope 1</dt><dd className="text-body">Diesel and petrol in litres, LPG in kg.</dd></div>
              <div className="grid gap-1 py-4 sm:grid-cols-[9rem_1fr]"><dt className="font-semibold">Analysis</dt><dd className="text-body">Monthly, quarterly and yearly trends, what-if scenarios on a single record, anomaly flags.</dd></div>
              <div className="grid gap-1 py-4 sm:grid-cols-[9rem_1fr]"><dt className="font-semibold">Not covered</dt><dd className="text-body">Scope 3, solar offsets and exports (they are not deducted), and third-party verification.</dd></div>
            </dl>
          </div>
          <div>
            <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">Who can do what</h2>
            <dl className="mt-6 divide-y divide-line border-y border-line text-sm">
              {roles.map(([role, text]) => (
                <div key={role} className="grid gap-1 py-4 sm:grid-cols-[9rem_1fr]"><dt className="font-semibold">{role}</dt><dd className="text-body">{text}</dd></div>
              ))}
            </dl>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-5 pb-16 md:px-8"><div className="max-w-3xl">
          <h2 className="text-2xl font-semibold tracking-tight">Questions</h2>
          <div className="mt-4">
            {faq.map(([question, answer]) => (
              <details key={question} className="border-t border-line py-4 last:border-b">
                <summary className="cursor-pointer text-sm font-semibold">{question}</summary>
                <p className="mt-3 text-sm leading-7 text-body">{answer}</p>
              </details>
            ))}
          </div>
          <p className="mt-10 text-sm text-body">Ready to try it with a real workbook? <Link to="/signup" className="font-semibold text-leaf-action underline underline-offset-4">Create an account</Link> or <Link to="/login" className="font-semibold text-leaf-action underline underline-offset-4">sign in</Link>.</p>
        </div></section>
      </main>

      <footer className="mx-auto max-w-6xl px-5 py-8 text-sm text-body md:px-8">CarbonTrace · Scope 1 and 2 accounting for facility teams</footer>
    </div>
  );
}
