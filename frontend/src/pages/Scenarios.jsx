import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import client from "../api/client";
import { useFacilities, useActivity } from "../api/hooks";

const number = (value) => value.toLocaleString(undefined, { maximumFractionDigits: 2 });
const inputQuantity = (value) => String(Number(value.toPrecision(12)));
const month = (value) => new Date(value).toLocaleDateString(undefined, { month: "short", year: "numeric", timeZone: "UTC" });

export default function Scenarios() {
  const facilities = useFacilities();
  const records = useActivity();
  const [recordId, setRecordId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [result, setResult] = useState(null);
  const record = records.data?.find((item) => item.id === recordId);
  const preview = useMutation({
    mutationFn: (payload) => client.post("/scenarios/preview", payload).then((r) => r.data),
    onSuccess: setResult,
  });
  function changeQuantity(value) {
    setQuantity(value);
    setResult(null);
    preview.reset();
  }
  const valid = quantity.trim() !== "" && Number.isFinite(Number(quantity)) && Number(quantity) >= 0;
  const errorDetail = preview.error?.response?.data?.detail;
  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">What-if scenarios</h1>
        <p className="mt-1 text-sm text-muted">Explore a change in consumption for one confirmed record. Your college records and report totals stay unchanged.</p>
      </div>
      {records.isLoading || facilities.isLoading ? <p role="status">Loading confirmed records...</p> :
        records.isError || facilities.isError ? <p role="alert">Could not load the baseline records. <button className="underline" onClick={() => { records.refetch(); facilities.refetch(); }}>Retry</button></p> :
        !records.data?.length ? <p>No confirmed records yet. <Link className="text-leaf underline" to="/upload">Review activity data first</Link>.</p> : (
          <div className="grid gap-5 lg:grid-cols-2">
            <form className="flex flex-col gap-4 rounded-card border border-line bg-surface p-5" onSubmit={(event) => {
              event.preventDefault();
              if (record && valid) { setResult(null); preview.mutate({ activity_record_id: record.id, quantity: Number(quantity) }); }
            }}>
              <h2 className="font-semibold text-ink">1. Choose your baseline</h2>
              <label htmlFor="scenario-record" className="text-sm font-medium">Confirmed activity record</label>
              <select id="scenario-record" required value={recordId} disabled={preview.isPending}
                onChange={(event) => {
                  setRecordId(event.target.value);
                  const selected = records.data.find((item) => item.id === event.target.value);
                  changeQuantity(selected ? inputQuantity(selected.quantity) : "");
                }} className="w-full rounded-lg border border-line bg-canvas p-3 text-sm">
                <option value="">Choose a facility and month</option>
                {records.data.map((item) => <option key={item.id} value={item.id}>
                  {facilities.data?.find((f) => f.id === item.facility_id)?.name ?? "Facility"} · {month(item.period_start)} · {item.activity_type}
                </option>)}
              </select>
              {record && <>
                <p className="text-sm text-muted">Recorded usage: <strong className="text-ink">{number(record.quantity)} {record.unit}</strong></p>
                <h2 className="mt-2 font-semibold text-ink">2. Change the consumption</h2>
                <label htmlFor="scenario-quantity" className="text-sm font-medium">Proposed quantity ({record.unit})</label>
                <input id="scenario-quantity" type="number" min="0" step="any" required value={quantity}
                  disabled={preview.isPending} onChange={(event) => changeQuantity(event.target.value)}
                  className="w-full rounded-lg border border-line bg-canvas p-3 font-mono" />
                <div className="flex flex-wrap gap-2">
                  {[10, 20, 30].map((reduction) => <button key={reduction} type="button" disabled={preview.isPending}
                    onClick={() => changeQuantity(inputQuantity(record.quantity * (1 - reduction / 100)))}
                    className="rounded-lg border border-line px-3 py-2 text-sm hover:bg-canvas disabled:opacity-60">{reduction}% less</button>)}
                  <button type="button" disabled={preview.isPending} onClick={() => changeQuantity(inputQuantity(record.quantity))}
                    className="rounded-lg border border-line px-3 py-2 text-sm hover:bg-canvas">Reset</button>
                </div>
              </>}
              <button type="submit" disabled={!record || !valid || preview.isPending}
                className="rounded-xl bg-leaf px-4 py-3 font-semibold text-white hover:bg-leaf-hover disabled:opacity-60">
                {preview.isPending ? "Calculating..." : "Compare scenario"}
              </button>
              {preview.isError && <p role="alert" className="text-sm text-rose">{typeof errorDetail === "string" ? errorDetail : "Unable to calculate this scenario. Check the quantity and try again."}</p>}
            </form>
            <section aria-label="Scenario comparison" aria-live="polite" className="rounded-card border border-line bg-surface p-5">
              <h2 className="font-semibold text-ink">3. Compare the outcome</h2>
              {!result ? <p className="mt-4 text-sm text-muted">Choose a record and run a comparison to see its baseline, projected emissions, and change.</p> : <>
                <p className="mt-2 text-xs uppercase tracking-wider text-muted">Hypothetical result · Scope {result.scope}</p>
                <dl className="mt-4 divide-y divide-line">
                  {[['Recorded emissions', result.baseline_co2e_kg], ['Projected emissions', result.projected_co2e_kg],
                    [result.savings_co2e_kg >= 0 ? 'Potential reduction' : 'Potential increase', Math.abs(result.savings_co2e_kg)]].map(([label, value]) => (
                    <div key={label} className="flex flex-wrap justify-between gap-2 py-4"><dt className="text-sm">{label}</dt><dd className="font-mono font-semibold text-ink">{number(value)} kg CO2e</dd></div>
                  ))}
                </dl>
                <p className="mt-3 text-sm font-semibold text-leaf-deep">{result.savings_percent === null ? "Percentage change is unavailable for a zero-emission baseline." : `${number(Math.abs(result.savings_percent))}% ${result.savings_percent >= 0 ? "lower" : "higher"} emissions`}</p>
                <p className="mt-5 text-xs text-muted">Calculation: {number(result.proposed_quantity)} {result.unit} × {number(result.factor_value)} {result.factor_unit}. Uses the baseline record's factor; this is not a forecast of measured performance.</p>
              </>}
              <p className="mt-5 border-t border-line pt-4 text-xs text-muted">Preview only. Nothing is saved to the activity ledger. Current emission factors are demonstration placeholders.</p>
            </section>
          </div>
        )}
    </div>
  );
}
