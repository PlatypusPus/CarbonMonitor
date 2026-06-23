import { useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { useSummary, useTimeseries } from "../api/hooks";

const INTERVALS = [
  { label: "15 min", value: "15m" },
  { label: "1 hr", value: "1h" },
  { label: "6 hr", value: "6h" },
  { label: "1 day", value: "1d" },
];

const fmt = (n, d = 1) =>
  typeof n === "number" ? n.toLocaleString(undefined, { maximumFractionDigits: d }) : "–";
const time = (ts) =>
  new Date(ts).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

export default function Trends() {
  const summary = useSummary();
  const metrics = summary.data ?? [];

  const [metric, setMetric] = useState("co2_kg_per_hour");
  const [interval, setInterval] = useState("1h");

  const series = useTimeseries({ metric, interval });
  const points = (series.data ?? []).map((p) => ({ t: time(p.timestamp), value: p.value }));
  const unitLabel = metrics.find((m) => m.metric === metric)?.unit ?? "";

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">Trends & Analytics</h1>
        <p className="text-sm text-muted">Historical emission patterns by metric and interval</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select
          value={metric}
          onChange={(e) => setMetric(e.target.value)}
          className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-leaf"
        >
          {metrics.map((m) => (
            <option key={m.metric} value={m.metric}>
              {m.metric}
            </option>
          ))}
        </select>

        <div className="flex overflow-hidden rounded-lg border border-line bg-surface">
          {INTERVALS.map((iv) => (
            <button
              key={iv.value}
              onClick={() => setInterval(iv.value)}
              className={`px-3 py-2 text-sm font-medium transition-colors ${
                interval === iv.value ? "bg-leaf text-white" : "text-body hover:bg-canvas"
              }`}
            >
              {iv.label}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-card border border-line bg-surface p-5">
        <div className="mb-3 flex items-center justify-between">
          <span className="text-sm font-semibold text-ink">{metric}</span>
          <span className="font-mono text-xs text-muted">{unitLabel}</span>
        </div>
        {series.isLoading ? (
          <div className="h-64 animate-pulse rounded-lg bg-canvas" />
        ) : points.length === 0 ? (
          <div className="grid h-64 place-items-center rounded-lg border border-dashed border-line text-sm text-muted">
            No data for this range
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={256}>
            <AreaChart data={points} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="trend" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#2E9E6B" stopOpacity={0.22} />
                  <stop offset="100%" stopColor="#2E9E6B" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#ECF1EE" vertical={false} />
              <XAxis
                dataKey="t"
                tick={{ fontSize: 11, fill: "#A8A89F" }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#A8A89F" }}
                tickLine={false}
                axisLine={false}
                width={44}
              />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#2E9E6B"
                strokeWidth={2.5}
                fill="url(#trend)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      {metrics.length > 0 && (
        <div className="overflow-hidden rounded-card border border-line bg-surface">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-canvas text-left">
                <th className="px-4 py-3 font-semibold text-ink">Metric</th>
                <th className="px-4 py-3 font-semibold text-ink">Latest</th>
                <th className="px-4 py-3 font-semibold text-ink">Avg</th>
                <th className="px-4 py-3 font-semibold text-ink">Readings</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((m) => (
                <tr
                  key={m.metric}
                  className="cursor-pointer border-b border-line last:border-0 hover:bg-canvas"
                  onClick={() => setMetric(m.metric)}
                >
                  <td
                    className={`px-4 py-3 font-mono text-xs ${
                      m.metric === metric ? "font-semibold text-leaf" : "text-ink"
                    }`}
                  >
                    {m.metric}
                  </td>
                  <td className="px-4 py-3 font-mono text-ink">
                    {fmt(m.latest_value)}{" "}
                    <span className="text-xs text-muted">{m.unit}</span>
                  </td>
                  <td className="px-4 py-3 font-mono text-muted">{fmt(m.avg_value)}</td>
                  <td className="px-4 py-3 text-muted">{m.count.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
