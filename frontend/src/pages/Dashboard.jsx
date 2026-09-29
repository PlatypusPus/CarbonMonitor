import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useState } from "react";
import DateRange from "../components/DateRange";
import Dropdown from "../components/Dropdown";
import { formatNumber as fmt } from "../lib/trends";

import { useAnomalies, useLatest, useSummary, useTimeseries } from "../api/hooks";

const time = (ts) => new Date(ts).toLocaleDateString([], { year: "numeric", month: "short", timeZone: "UTC" });

function LivePill() {
  return (
    <span className="inline-flex items-center gap-2 rounded-pill border border-mint bg-[#E8F3EC] px-3 py-1 text-xs font-semibold text-leaf">
      <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-leaf" />
      CONFIRMED DATA
    </span>
  );
}

function StatCard({ label, value, unit, accent = "mint" }) {
  const border = accent === "peach" ? "border-l-peach" : "border-l-mint";
  return (
    <div className={`rounded-card border border-line border-l-4 ${border} bg-surface p-4`}>
      <div className="text-xs text-muted">{label}</div>
      <div className="mt-1 font-mono text-2xl text-ink">
        {value}
        {unit && <span className="ml-1 text-xs text-muted">{unit}</span>}
      </div>
    </div>
  );
}

function ChartCard({ series }) {
  const points = (series.data ?? []).map((p) => ({ t: time(p.timestamp), value: p.value }));
  return (
    <div className="rounded-card border border-line bg-surface p-5">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-sm font-semibold text-ink">CO₂ trend</span>
        <span className="font-mono text-xs text-muted">kg CO₂e</span>
      </div>
      {series.isLoading ? (
        <div className="h-56 animate-pulse rounded-lg bg-canvas" />
      ) : points.length === 0 ? (
        <div className="grid h-56 place-items-center rounded-lg border border-dashed border-line text-sm text-muted">
          No data for this range
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={224}>
          <AreaChart data={points} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="co2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#2E9E6B" stopOpacity={0.22} />
                <stop offset="100%" stopColor="#2E9E6B" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#ECF1EE" vertical={false} />
            <XAxis dataKey="t" tick={{ fontSize: 11, fill: "#A8A89F" }} tickLine={false} axisLine={false} />
            <YAxis tickFormatter={fmt} tick={{ fontSize: 11, fill: "#55554F" }} tickLine={false} axisLine={false} width={92} />
            <Tooltip formatter={(value) => [fmt(value), "kg CO₂e"]} />
            <Area type="monotone" dataKey="value" stroke="#2E9E6B" strokeWidth={2.5} fill="url(#co2)" />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

function SensorFeed({ feed }) {
  const rows = feed.data ?? [];
  return (
    <div className="rounded-card border border-line bg-surface p-5">
      <div className="mb-3 text-sm font-semibold text-ink">Recent activity records</div>
      <div className="flex max-h-72 flex-col gap-1 overflow-auto">
        {rows.length === 0 && <div className="text-sm text-muted">No recent readings.</div>}
        {rows.map((r, i) => (
          <div key={i} className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-canvas">
            <span className="h-2 w-2 flex-none rounded-full bg-leaf" />
            <div className="min-w-0 flex-1">
              <div className="truncate text-sm text-ink">{r.facility_name ?? r.region ?? r.source}</div>
              <div className="font-mono text-xs text-muted">
                {r.metric} · {time(r.timestamp)}
              </div>
            </div>
            <div className="font-mono text-sm text-ink">
              {fmt(r.value)} <span className="text-xs text-muted">{r.unit}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const summary = useSummary();
  const [metric, setMetric] = useState("electricity");
  const anomalies = useAnomalies({ limit: 200 });
  // metric matches ActivityRecord.activity_type (electricity/diesel/...)
  const defaultMetric = metric;
  const series = useTimeseries({ metric: defaultMetric, interval: "1mo" });
  const feed = useLatest({ metric: defaultMetric, limit: 200 });

  const metrics = (summary.data ?? []).slice(0, 3);

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink">Emissions overview</h1>
          <p className="text-sm text-muted">Confirmed activity records and monthly emissions</p>
        </div>
        <LivePill />
      </div>

      <DateRange />
      <div className="max-w-xs"><p className="mb-2 text-xs font-semibold text-body">Chart and activity type</p><Dropdown label="Chart and activity type" value={metric} onChange={setMetric} options={['electricity', 'diesel', 'petrol', 'lpg'].map((type) => ({value:type,label:`${type} (Scope ${type === 'electricity' ? '2' : '1'})`}))} /></div>
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label={`Total ${defaultMetric} emissions`} value={series.data ? fmt(series.data.reduce((total, row) => total + (row.value ?? 0), 0)) : "-"} unit="kg CO2e" />
        {metrics.map((m) => (
          <StatCard key={m.metric} label={`Latest ${m.metric} record`} value={fmt(m.latest_value)} unit={m.unit} />
        ))}
        <StatCard label="Confirmed records" value={summary.data ? summary.data.reduce((total, item) => total + item.count, 0) : "-"} />
        <StatCard
          label="Flagged records (all dates)"
          value={anomalies.data?.length ?? "-"}
          unit="flags"
          accent="peach"
        />
      </div>

      {[summary, anomalies, series, feed].some((query) => query.isError) && (
        <p role="alert" className="text-sm text-rose">Some emissions data could not be loaded. <button className="underline" onClick={() => [summary, anomalies, series, feed].forEach((query) => query.refetch())}>Retry</button></p>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ChartCard series={series} />
        </div>
        <SensorFeed feed={feed} />
      </div>
    </div>
  );
}
