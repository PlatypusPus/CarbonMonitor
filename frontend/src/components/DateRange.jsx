import { useWorkspace } from "../context/WorkspaceContext";

export default function DateRange() {
  const { dates, setDates } = useWorkspace();
  return <div className="flex flex-wrap items-end gap-3 rounded-xl border border-line bg-surface p-4">
    {[['start_date', 'From'], ['end_date', 'Through']].map(([key, label]) => <label key={key} className="flex min-w-0 flex-1 flex-col gap-2 text-xs font-semibold text-body sm:flex-none">{label}
      <input type="date" aria-label={label} value={dates[key]} min={key === 'end_date' ? dates.start_date : undefined} max={key === 'start_date' ? dates.end_date : undefined}
        onChange={(e) => setDates((previous) => ({ ...previous, [key]: e.target.value }))}
        className="w-full min-w-0 sm:w-44" />
    </label>)}
    <button onClick={() => setDates({ start_date: "", end_date: "" })} className="button-secondary">All dates</button>
    <p className="w-full text-xs text-body">Filters use each record's reporting-period start date (UTC). Monthly totals are not daily or hourly readings.</p>
  </div>;
}
