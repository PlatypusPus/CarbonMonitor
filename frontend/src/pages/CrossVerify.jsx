import { useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { useCrossVerify, useSummary } from "../api/hooks";

const INTERVALS = [
  { label: "1 hr", value: "1h" },
  { label: "6 hr", value: "6h" },
  { label: "1 day", value: "1d" },
];

const fmt = (n, d = 1) =>
  typeof n === "number" ? n.toLocaleString(undefined, { maximumFractionDigits: d }) : "–";
const date = (ts) =>
  new Date(ts).toLocaleDateString([], { month: "short", day: "numeric" });

export default function CrossVerify() {
  const summary = useSummary();
  const metrics = summary.data ?? [];

  const [metric, setMetric] = useState("co2_kg_per_hour");
  const [interval, setInterval] = useState("1d");

  const { data, isLoading } = useCrossVerify({ metric, interval });
  const rows = data ?? [];
  const points = rows.map((r) => ({
    t: date(r.timestamp),
    live: r.live_value,
    upload: r.upload_value,
  }));

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">Cross-Verification</h1>
        <p className="text-sm text-muted">
          Live sensor data vs uploaded CSV — alignment check
        </p>
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
        <div className="mb-3 text-sm font-semibold text-ink">Live vs Uploaded</div>
        {isLoading ? (
          <div className="h-56 animate-pulse rounded-lg bg-canvas" />
        ) : points.length === 0 ? (
          <div className="grid h-56 place-items-center rounded-lg border border-dashed border-line text-sm text-muted">
            No cross-verify data — upload a CSV to compare
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={224}>
            <LineChart data={points} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
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
              <Legend />
              <Line
                type="monotone"
                dataKey="live"
                stroke="#2E9E6B"
                strokeWidth={2}
                dot={false}
                name="Live"
              />
              <Line
                type="monotone"
                dataKey="upload"
                stroke="#4A9ECC"
                strokeWidth={2}
                dot={false}
                name="Uploaded"
                strokeDasharray="5 3"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>

      {rows.length > 0 && (
        <div className="overflow-hidden rounded-card border border-line bg-surface">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-canvas text-left">
                <th className="px-4 py-3 font-semibold text-ink">Period</th>
                <th className="px-4 py-3 font-semibold text-ink">Live</th>
                <th className="px-4 py-3 font-semibold text-ink">Uploaded</th>
                <th className="px-4 py-3 font-semibold text-ink">Discrepancy</th>
              </tr>
            </thead>
            <tbody>
              {[...rows].reverse().slice(0, 20).map((r, i) => {
                const disc = r.discrepancy_pct;
                const bad = disc != null && Math.abs(disc) > 10;
                return (
                  <tr key={i} className="border-b border-line last:border-0 hover:bg-canvas">
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-muted">
                      {date(r.timestamp)}
                    </td>
                    <td className="px-4 py-3 font-mono text-ink">{fmt(r.live_value)}</td>
                    <td className="px-4 py-3 font-mono text-ink">{fmt(r.upload_value)}</td>
                    <td
                      className={`px-4 py-3 font-mono font-semibold ${
                        disc == null ? "text-muted" : bad ? "text-rose" : "text-leaf"
                      }`}
                    >
                      {disc != null ? `${disc > 0 ? "+" : ""}${fmt(disc, 2)}%` : "–"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
