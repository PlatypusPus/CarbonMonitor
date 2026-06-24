import { useAnomalies } from "../api/hooks";

const fmt = (n, d = 2) =>
  typeof n === "number" ? n.toLocaleString(undefined, { maximumFractionDigits: d }) : "–";
const ts = (t) =>
  new Date(t).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

function ScoreBadge({ score }) {
  const high = score < -0.1;
  return (
    <span
      className={`inline-flex items-center rounded-pill px-2.5 py-1 text-xs font-semibold ${
        high ? "bg-rose/10 text-rose" : "bg-peach/10 text-peach"
      }`}
    >
      {high ? "High" : "Medium"} · {fmt(score)}
    </span>
  );
}

export default function Anomalies() {
  const { data, isLoading } = useAnomalies({ limit: 100 });
  const rows = data ?? [];

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">Anomaly Log</h1>
        <p className="text-sm text-muted">
          Isolation Forest–flagged emission spikes (last 7 days)
        </p>
      </div>

      <div className="overflow-hidden rounded-card border border-line bg-surface">
        {isLoading ? (
          <div className="h-48 animate-pulse bg-canvas" />
        ) : rows.length === 0 ? (
          <div className="grid h-48 place-items-center text-sm text-muted">
            No anomalies detected
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line bg-canvas text-left">
                <th className="px-4 py-3 font-semibold text-ink">Time</th>
                <th className="px-4 py-3 font-semibold text-ink">Metric</th>
                <th className="px-4 py-3 font-semibold text-ink">Facility / Source</th>
                <th className="px-4 py-3 font-semibold text-ink">Value</th>
                <th className="px-4 py-3 font-semibold text-ink">Expected</th>
                <th className="px-4 py-3 font-semibold text-ink">Score</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-line last:border-0 hover:bg-canvas">
                  <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-muted">
                    {r.timestamp ? ts(r.timestamp) : "–"}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-ink">{r.metric ?? "–"}</td>
                  <td className="px-4 py-3 text-ink">
                    {r.facility_name ?? r.source ?? r.region ?? "–"}
                  </td>
                  <td className="px-4 py-3 font-mono text-ink">
                    {fmt(r.value)}{" "}
                    <span className="text-xs text-muted">{r.unit}</span>
                  </td>
                  <td className="px-4 py-3 font-mono text-muted">{fmt(r.expected_value)}</td>
                  <td className="px-4 py-3">
                    {r.anomaly_score != null ? <ScoreBadge score={r.anomaly_score} /> : "–"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
