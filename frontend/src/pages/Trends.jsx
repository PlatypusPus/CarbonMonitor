import { useState } from "react";
import { UploadCloud } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useTimeseries } from "../api/hooks";
import DateRange from "../components/DateRange";
import Dropdown from "../components/Dropdown";
import { groupPeriods, formatNumber as fmt } from "../lib/trends";

const activities = ['electricity', 'diesel', 'petrol', 'lpg'].map((type) => ({value:type,label:`${type.toUpperCase()} · Scope ${type === 'electricity' ? 2 : 1}`}));
const periods = [{value:'month',label:'Monthly'}, {value:'quarter',label:'Quarterly'}, {value:'year',label:'Yearly'}];

export default function Trends() {
  const navigate = useNavigate();
  const [metric, setMetric] = useState('electricity');
  const [interval, setInterval] = useState('month');
  const series = useTimeseries({ metric, interval: '1mo' });
  const points = groupPeriods(series.data ?? [], interval);
  const years = [...new Set(points.map((point) => point.year))];
  const panels = interval === 'year' ? [{title:'Annual comparison', points}] : years.map((year) => ({title:String(year), points:points.filter((point) => point.year === year)}));
  const total = points.reduce((sum, point) => sum + point.value, 0);
  const scope = metric === 'electricity' ? 2 : 1;
  const color = scope === 2 ? '#236F4B' : '#AD6228';
  return <div className="flex flex-col gap-6">
    <header className="flex flex-wrap items-start justify-between gap-3">
      <div><h1 className="text-2xl font-bold text-ink">Trends & Analytics</h1><p className="mt-1 text-sm text-body">Compare emissions across reporting periods.</p></div>
      <button onClick={() => navigate('/upload')} className="inline-flex items-center gap-2 rounded-lg bg-leaf-action px-4 py-3 text-sm font-semibold text-white hover:bg-leaf-action-hover"><UploadCloud size={16} />Upload data</button>
    </header>
    <DateRange />
    <div className="flex flex-wrap items-end gap-5">
      <div className="w-full sm:w-64"><p className="mb-2 text-xs font-semibold text-body">Emission source</p><Dropdown label="Emission source" value={metric} onChange={setMetric} options={activities} /></div>
      <div><p className="mb-2 text-xs font-semibold text-body">Reporting groups</p><div className="interval-control" role="group" aria-label="Reporting groups">
        {periods.map((period) => <button key={period.value} aria-pressed={interval === period.value} onClick={() => setInterval(period.value)}>{period.label}</button>)}
      </div></div>
    </div>
    {series.isError ? <p role="alert" className="rounded-xl border border-rose p-4 text-sm">Unable to load trends. <button className="underline" onClick={() => series.refetch()}>Retry</button></p>
      : series.isLoading ? <div className="h-64 animate-pulse rounded-xl bg-canvas" />
      : !points.length ? <div className="rounded-xl border border-dashed border-line bg-surface p-10 text-center"><h2 className="font-semibold text-ink">No {metric} records in this range</h2><p className="mt-2 text-sm text-body">Choose another facility or date range, or upload records for Scope {scope}.</p></div>
      : <>
        <div className="grid gap-3 sm:grid-cols-3">
          {[[`${metric} total (Scope ${scope})`,`${fmt(total)} kg CO₂e`],['Average per displayed period',`${fmt(total / points.length)} kg CO₂e`],['Reporting coverage',`${points.length} ${interval === 'month' ? 'months' : interval === 'quarter' ? 'quarters' : 'years'}`]].map(([label,value]) => <div key={label} className="rounded-xl border border-line bg-surface p-4"><p className="text-xs text-body">{label}</p><p className="mt-2 font-mono text-lg font-semibold text-ink">{value}</p></div>)}
        </div>
        <p className="text-xs text-body">Groups include only records within the selected dates. Partial quarters and years are not annualized; missing periods are not treated as zero.</p>
        <div className="grid gap-5 xl:grid-cols-2">
          {panels.map((panel) => <section key={panel.title} className={`min-w-0 rounded-xl border border-line bg-surface p-4 sm:p-5 ${panels.length === 1 ? 'xl:col-span-2' : ''}`} aria-label={`${panel.title} emissions`}>
            <div className="mb-5 flex items-center justify-between gap-3"><div><h2 className="text-lg font-semibold text-ink">{panel.title}</h2><p className="text-xs text-body">{activities.find((item) => item.value === metric).label}</p></div><p className="text-right font-mono text-sm text-ink">{fmt(panel.points.reduce((sum, point) => sum + point.value, 0))}<span className="block text-xs text-body">kg CO₂e</span></p></div>
            <ResponsiveContainer width="100%" height={260}><BarChart data={panel.points} margin={{top:8,right:8,left:0,bottom:0}}>
              <CartesianGrid stroke="#E6E6E0" vertical={false} /><XAxis dataKey="label" tick={{fontSize:11,fill:'#55554F'}} tickLine={false} axisLine={false} />
              <YAxis domain={[0, Math.max(1, ...points.map((point) => point.value)) * 1.1]} tickFormatter={fmt} width={94} tick={{fontSize:10,fill:'#55554F'}} tickLine={false} axisLine={false} />
              <Tooltip formatter={(value) => [fmt(value), 'kg CO₂e']} labelFormatter={(label) => interval === 'year' ? label : `${label} ${panel.title}`} contentStyle={{borderRadius:12,borderColor:'#CBD8D0'}} cursor={{fill:'#F4F7F5'}} />
              <Bar dataKey="value" fill={color} radius={[4,4,0,0]} maxBarSize={48} />
            </BarChart></ResponsiveContainer>
            <details className="mt-4 border-t border-line pt-3"><summary className="cursor-pointer text-sm font-semibold text-leaf-action">View period values</summary>
              <table className="mt-3 w-full text-left text-sm"><thead><tr className="text-body"><th className="py-2">Period</th><th className="text-right">kg CO₂e</th><th className="text-right">Records</th></tr></thead><tbody>{panel.points.map((point) => <tr key={point.key} className="border-t border-line"><td className="py-2">{point.label}</td><td className="text-right font-mono">{fmt(point.value)}</td><td className="text-right">{point.count}</td></tr>)}</tbody></table>
            </details>
          </section>)}
        </div>
      </>}
  </div>;
}

