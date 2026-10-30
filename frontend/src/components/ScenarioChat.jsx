import { useEffect, useRef, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import client from "../api/client";

const number = (value) => value.toLocaleString(undefined, { maximumFractionDigits: 0 });
const kg = (value) => `${number(value)} kg CO2e`;
const monthLabel = (value) => new Date(`${value}-01T00:00:00Z`).toLocaleDateString(undefined, { month: "short", year: "2-digit", timeZone: "UTC" });
const change = (before, after) => {
  const diff = after - before;
  const percent = before ? ` (${Math.abs(diff / before * 100).toFixed(1)}%)` : "";
  return `${diff <= 0 ? "−" : "+"}${kg(Math.abs(diff))}${percent}`;
};
const EXAMPLES = [
  "What if we cut electricity by 15% from next month?",
  "Which month used the most diesel?",
  "What if we switch half our LPG use to electric cooking?",
];

function Result({ answer }) {
  const forecastBase = answer.forecast.reduce((sum, m) => sum + m.baseline_co2e_kg, 0);
  const forecastNew = answer.forecast.reduce((sum, m) => sum + m.projected_co2e_kg, 0);
  const hasFuture = answer.future_changes.length > 0;
  return (
    <div className="mt-3 flex flex-col gap-4 rounded-xl border border-line bg-canvas p-4 text-sm">
      {answer.changes.length > 0 && <div>
        <h3 className="font-semibold text-ink">Past records</h3>
        <ul className="mt-2 divide-y divide-line">
          {answer.changes.map((c, i) => <li key={c.activity_record_id} className="flex flex-wrap justify-between gap-2 py-2">
            <span>{answer.reasons[i]}</span>
            <span className="tabular-nums text-muted">{number(c.baseline_quantity)} → {number(c.proposed_quantity)} {c.unit}</span>
          </li>)}
        </ul>
        <p className="mt-2 tabular-nums">Those months: {kg(answer.baseline_co2e_kg)} → {kg(answer.projected_co2e_kg)}</p>
        <p className="tabular-nums font-semibold text-leaf-deep">Whole recorded footprint: {kg(answer.footprint_co2e_kg)} → {kg(answer.footprint_co2e_kg - answer.savings_co2e_kg)} · {change(answer.footprint_co2e_kg, answer.footprint_co2e_kg - answer.savings_co2e_kg)}</p>
      </div>}
      {answer.forecast.length > 0 && <div>
        <h3 className="font-semibold text-ink">Next 12 months forecast</h3>
        {hasFuture && <p className="mt-1 text-muted">{answer.future_changes.map((f) => `${f.activity_type} ${f.change_percent > 0 ? "+" : ""}${f.change_percent}%${f.start_month ? ` from ${monthLabel(f.start_month)}` : ""}`).join(" · ")}</p>}
        <p className="mt-1 tabular-nums font-semibold text-leaf-deep">
          {hasFuture ? `${kg(forecastBase)} → ${kg(forecastNew)} · ${change(forecastBase, forecastNew)}` : `${kg(forecastBase)} expected if nothing changes`}
        </p>
        <div className="mt-2 h-56">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={answer.forecast.map((m) => ({ ...m, label: monthLabel(m.month) }))} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#E6E6E0" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: "#55554F" }} tickLine={false} axisLine={false} />
              <YAxis tickFormatter={number} width={64} tick={{ fontSize: 10, fill: "#55554F" }} tickLine={false} axisLine={false} />
              <Tooltip formatter={(value, name) => [kg(value), name]} contentStyle={{ borderRadius: 12, borderColor: "#CBD8D0" }} />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="baseline_co2e_kg" name="If nothing changes" stroke="#65766B" strokeDasharray="5 4" dot={false} />
              {hasFuture && <Line type="monotone" dataKey="projected_co2e_kg" name="With this scenario" stroke="#2E9E6B" strokeWidth={2} dot={false} />}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>}
      {answer.skipped.length > 0 && <p className="text-xs text-muted">Skipped: {answer.skipped.join("; ")}</p>}
    </div>
  );
}

export default function ScenarioChat() {
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const end = useRef(null);
  const ask = useMutation({
    mutationFn: (history) => client.post("/scenarios/ask", {
      // ponytail: last 10 turns only, the backend caps history at 20
      messages: history.slice(-10).map(({ role, text }) => ({ role, text })),
    }).then((r) => r.data),
    onSuccess: (answer) => setMessages((list) => [...list, { role: "model", text: answer.reply, answer }]),
    // Drop the unanswered question so the history keeps alternating; put it back in the box.
    onError: (_error, history) => { setMessages(history.slice(0, -1)); setDraft(history.at(-1).text); },
  });
  useEffect(() => { end.current?.scrollIntoView({ block: "nearest" }); }, [messages, ask.isPending]);
  function send(text) {
    const question = text.trim();
    if (question.length < 1 || ask.isPending) return;
    const history = [...messages, { role: "user", text: question.slice(0, 1000) }];
    setMessages(history);
    setDraft("");
    ask.mutate(history);
  }
  const detail = ask.error?.response?.data?.detail;
  return (
    <section className="flex flex-col rounded-card border border-line bg-surface p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-semibold text-ink">Scenario assistant</h2>
        {messages.length > 0 && <button type="button" onClick={() => { setMessages([]); ask.reset(); }} className="text-sm text-muted underline">New chat</button>}
      </div>
      <div className="mt-3 flex max-h-[36rem] flex-col gap-3 overflow-y-auto" aria-live="polite">
        {messages.length === 0 && <div className="text-sm text-muted">
          <p>Ask a what-if in plain language. Follow up to adjust it, for example "make it 25% instead".</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {EXAMPLES.map((e) => <button key={e} type="button" onClick={() => send(e)} className="rounded-full border border-line px-3 py-1.5 text-left hover:bg-canvas">{e}</button>)}
          </div>
        </div>}
        {messages.map((m, i) => m.role === "user"
          ? <p key={i} className="max-w-[85%] self-end whitespace-pre-wrap rounded-2xl rounded-br-sm bg-leaf px-4 py-2 text-sm text-white">{m.text}</p>
          : <div key={i} className="max-w-full self-start">
              <p className="whitespace-pre-wrap rounded-2xl rounded-bl-sm bg-canvas px-4 py-2 text-sm text-ink">{m.text}</p>
              {(m.answer.changes.length > 0 || m.answer.future_changes.length > 0) && <Result answer={m.answer} />}
            </div>)}
        {ask.isPending && <p role="status" className="self-start rounded-2xl bg-canvas px-4 py-2 text-sm text-muted">Thinking...</p>}
        {ask.isError && <p role="alert" className="text-sm text-rose">{typeof detail === "string" ? detail : "Could not answer that. Try again."}</p>}
        <div ref={end} />
      </div>
      <form className="mt-4 flex gap-2" onSubmit={(event) => { event.preventDefault(); send(draft); }}>
        <label htmlFor="scenario-chat" className="sr-only">Message</label>
        <textarea id="scenario-chat" rows={1} maxLength={1000} value={draft} placeholder="Ask a what-if..."
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(draft); } }}
          className="min-h-11 flex-1 resize-y rounded-lg border border-line bg-canvas p-3 text-sm" />
        <button type="submit" disabled={ask.isPending || !draft.trim()}
          className="rounded-xl bg-leaf px-4 py-2 font-semibold text-white hover:bg-leaf-hover disabled:opacity-60">Send</button>
      </form>
      <p className="mt-3 text-xs text-muted">Gemini suggests the changes; CarbonTrace calculates every number from your records and emission factors. The forecast repeats last year's pattern (or the recent average) and is an estimate. Nothing is saved.</p>
    </section>
  );
}
