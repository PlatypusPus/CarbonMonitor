import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link } from "react-router-dom";
import DateRange from "../components/DateRange";
import { compactNumber, formatEmissions, formatNumber as fmt, mergeMonthly } from "../lib/trends";

import { useAnomalies, useLatest, useTimeseries } from "../api/hooks";

const FUEL = ["diesel", "petrol", "lpg"];
const month = (ts) => new Date(ts).toLocaleDateString([], { year: "numeric", month: "short", timeZone: "UTC" });
const sum = (rows) => (rows ?? []).reduce((total, row) => total + (row.value ?? 0), 0);

function Stat({ label, kg, note, loading, to }) {
  const { value, unit } = formatEmissions(kg);
  const body = (
    <>
      <div className="text-xs font-semibold text-body">{label}</div>
      {loading ? (
        <div className="mt-3 h-8 w-32 animate-pulse rounded bg-canvas" />
      ) : (
        <div className="mt-2 text-2xl font-semibold tabular-nums text-ink">
          {value}
          <span className="ml-1 text-xs font-normal text-muted">{unit}</span>
        </div>
      )}
      {note && !loading && <div className="mt-1 text-xs text-muted">{note}</div>}
    </>
  );
  const cls = "rounded-card border border-line bg-surface p-5";
  return to ? <Link to={to} className={`${cls} block hover:border-leaf`}>{body}</Link> : <div className={cls}>{body}</div>;
}

function Change({ months, loading }) {
  const last = months.at(-1);
  const prev = months.at(-2);
  const total = (m) => (m?.scope1 ?? 0) + (m?.scope2 ?? 0);
  let note = "Needs at least two months of data";
  let text = "-";
  if (!loading && last && prev && total(prev) > 0) {
    const pct = ((total(last) - total(prev)) / total(prev)) * 100;
    text = `${pct >= 0 ? "+" : "-"}${Math.abs(pct).toFixed(1)}%`;
    note = `${last.label} vs ${prev.label}`;
  }
  return (
    <div className="rounded-card border border-line bg-surface p-5">
      <div className="text-xs font-semibold text-body">Latest month vs previous</div>
      {loading ? <div className="mt-3 h-8 w-24 animate-pulse rounded bg-canvas" /> : <div className="mt-2 text-2xl font-semibold tabular-nums text-ink">{text}</div>}
      {!loading && <div className="mt-1 text-xs text-muted">{note}</div>}
    </div>
  );
}

function MonthlyChart({ months, loading }) {
  return (
    <section className="rounded-card border border-line bg-surface p-5" aria-label="Monthly emissions by scope">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h2 className="text-sm font-semibold text-ink">Monthly emissions by scope</h2>
        <span className="text-xs text-muted">kg CO₂e</span>
      </div>
      {loading ? (
        <div className="h-60 animate-pulse rounded-lg bg-canvas" />
      ) : (
        <>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={months} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#E6E6E0" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: "#55554F" }} tickLine={false} axisLine={false} />
              <YAxis tickFormatter={compactNumber} tick={{ fontSize: 12, fill: "#55554F" }} tickLine={false} axisLine={false} width={48} />
              <Tooltip formatter={(value, name) => [fmt(value), name]} contentStyle={{ borderRadius: 12, borderColor: "#CBD8D0" }} cursor={{ fill: "#F4F7F5" }} />
              <Legend iconType="square" wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="scope2" name="Scope 2 (electricity)" stackId="co2" fill="#236F4B" maxBarSize={48} />
              <Bar dataKey="scope1" name="Scope 1 (fuel)" stackId="co2" fill="#AD6228" radius={[4, 4, 0, 0]} maxBarSize={48} />
            </BarChart>
          </ResponsiveContainer>
          <details className="mt-3 border-t border-line pt-3">
            <summary className="cursor-pointer text-sm font-semibold text-leaf-action">View monthly values</summary>
            <table className="mt-3 w-full text-left text-sm">
              <thead><tr className="text-body"><th className="py-2">Month</th><th className="text-right">Scope 1</th><th className="text-right">Scope 2</th></tr></thead>
              <tbody>{months.map((m) => <tr key={m.key} className="border-t border-line"><td className="py-2">{m.label}</td><td className="text-right tabular-nums">{m.scope1 === undefined ? "-" : fmt(m.scope1)}</td><td className="text-right tabular-nums">{m.scope2 === undefined ? "-" : fmt(m.scope2)}</td></tr>)}</tbody>
            </table>
          </details>
        </>
      )}
    </section>
  );
}

function RecentRecords({ feed }) {
  const rows = feed.data ?? [];
  return (
    <section className="rounded-card border border-line bg-surface p-5" aria-label="Recent confirmed records">
      <h2 className="mb-3 text-sm font-semibold text-ink">Recent confirmed records</h2>
      {feed.isLoading ? (
        <div className="h-48 animate-pulse rounded-lg bg-canvas" />
      ) : rows.length === 0 ? (
        <p className="text-sm text-muted">No confirmed records in this range.</p>
      ) : (
        <ul className="flex flex-col divide-y divide-line">
          {rows.map((r, i) => (
            <li key={i} className="flex items-center justify-between gap-3 py-2.5">
              <div className="min-w-0">
                <div className="truncate text-sm text-ink">{r.facility_name ?? "Facility"}</div>
                <div className="text-xs capitalize text-muted">{r.metric} · {month(r.timestamp)}</div>
              </div>
              <div className="text-right text-sm tabular-nums text-ink">{fmt(r.value)} <span className="text-xs text-muted">kg CO₂e</span></div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function Dashboard() {
  const electricity = useTimeseries({ metric: "electricity", interval: "1mo" });
  const diesel = useTimeseries({ metric: "diesel", interval: "1mo" });
  const petrol = useTimeseries({ metric: "petrol", interval: "1mo" });
  const lpg = useTimeseries({ metric: "lpg", interval: "1mo" });
  const feed = useLatest({ limit: 8 });
  const anomalies = useAnomalies({ limit: 200 });

  const queries = [electricity, diesel, petrol, lpg];
  const loading = queries.some((q) => q.isLoading);
  const failed = [...queries, feed, anomalies].filter((q) => q.isError);
  const scope2 = sum(electricity.data);
  const scope1 = sum(diesel.data) + sum(petrol.data) + sum(lpg.data);
  const total = scope1 + scope2;
  const months = mergeMonthly({
    scope2: electricity.data,
    scope1: [...(diesel.data ?? []), ...(petrol.data ?? []), ...(lpg.data ?? [])],
  });
  const empty = !loading && !failed.length && months.length === 0;
  const flags = anomalies.data?.length ?? 0;
  const share = (part) => (total > 0 ? `${((part / total) * 100).toFixed(0)}% of total` : undefined);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-ink">Emissions overview</h1>
          <p className="text-sm text-muted">Confirmed monthly activity, Scope 1 and Scope 2</p>
        </div>
        <Link to="/upload" className="rounded-lg bg-leaf-action px-4 py-3 text-sm font-semibold text-white hover:bg-leaf-action-hover">Add activity</Link>
      </div>

      <DateRange />

      {failed.length > 0 && (
        <p role="alert" className="text-sm text-rose">Some emissions data could not be loaded. <button className="underline" onClick={() => failed.forEach((q) => q.refetch())}>Retry</button></p>
      )}

      {flags > 0 && (
        <Link to="/anomalies" className="rounded-lg border border-peach bg-surface px-4 py-3 text-sm text-ink hover:bg-canvas">
          <strong>{flags >= 200 ? "200+" : flags} flagged {flags === 1 ? "record" : "records"}</strong> may need a second look. Review anomalies →
        </Link>
      )}

      {empty ? (
        <div className="rounded-card border border-dashed border-line bg-surface p-10 text-center">
          <h2 className="font-semibold text-ink">No confirmed records yet</h2>
          <p className="mx-auto mt-2 max-w-md text-sm text-body">Upload an electricity workbook or fuel CSV, review the rows, and confirm them. Only confirmed rows appear here.</p>
          <Link to="/upload" className="mt-5 inline-block rounded-lg bg-leaf-action px-4 py-3 text-sm font-semibold text-white hover:bg-leaf-action-hover">Go to data intake</Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Stat label="Total emissions" kg={total} loading={loading} />
            <Stat label="Scope 1 · fuel" kg={scope1} note={share(scope1)} loading={loading} />
            <Stat label="Scope 2 · electricity" kg={scope2} note={share(scope2)} loading={loading} />
            <Change months={months} loading={loading} />
          </div>
          <div className="grid gap-4 lg:grid-cols-3">
            <div className="min-w-0 lg:col-span-2"><MonthlyChart months={months} loading={loading} /></div>
            <RecentRecords feed={feed} />
          </div>
        </>
      )}
    </div>
  );
}
