import { useWorkspace } from "../context/WorkspaceContext";

export default function DateRange() {
  const { dates, setDates } = useWorkspace();
  return <div className="flex flex-wrap items-end gap-3">
    {[['start_date', 'From'], ['end_date', 'Through']].map(([key, label]) => <label key={key} className="text-sm text-body">{label}
      <input type="date" aria-label={label} value={dates[key]} min={key === 'end_date' ? dates.start_date : undefined} max={key === 'start_date' ? dates.end_date : undefined}
        onChange={(e) => setDates((previous) => ({ ...previous, [key]: e.target.value }))}
        className="ml-2 rounded-lg border border-line bg-surface px-3 py-2 text-ink" />
    </label>)}
    <button onClick={() => setDates({ start_date: "", end_date: "" })} className="rounded-lg border border-line px-3 py-2 text-sm">All dates</button>
    <p className="w-full text-xs text-muted">Filters use each record's reporting-period start date (UTC). Monthly totals are not daily or hourly readings.</p>
  </div>;
}
