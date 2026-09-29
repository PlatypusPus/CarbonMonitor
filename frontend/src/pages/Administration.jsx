import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Users, Plus, Pencil, ShieldCheck } from "lucide-react";
import client from "../api/client";
import { useFacilities } from "../api/hooks";
import { useAuth } from "../context/AuthContext";

const input = "mt-1 w-full rounded-lg border border-line bg-canvas px-3 py-2.5 text-sm text-ink";
const action = "inline-flex items-center justify-center gap-2 rounded-lg bg-leaf-action px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-50 hover:bg-leaf-action-hover";
const blankUser = { full_name: "", email: "", password: "", role: "facility_manager", facility_id: "", is_active: true };
const errorMessage = (error) => {
  const detail = error?.response?.data?.detail;
  return typeof detail === "string" ? detail : Array.isArray(detail) ? detail.map((item) => item.msg).join(". ") : "The change could not be saved. Please try again.";
};

export default function Administration() {
  const { user } = useAuth();
  const isAdmin = user.role === "admin";
  const cache = useQueryClient();
  const facilities = useFacilities();
  const users = useQuery({ queryKey: ["users"], queryFn: () => client.get("/users").then((r) => r.data), enabled: isAdmin });
  const [section, setSection] = useState("facilities");
  const [editor, setEditor] = useState(null);
  const [form, setForm] = useState({});
  const [notice, setNotice] = useState("");
  const save = useMutation({
    mutationFn: () => {
      const isUser = editor.kind === "users";
      const payload = isUser ? {
        full_name: form.full_name, role: form.role, facility_id: form.facility_id || null,
        ...(editor.id ? { is_active: form.is_active } : { email: form.email, password: form.password }),
      } : { ...form, facility_type: form.facility_type || null };
      return editor.id ? client.patch(`/${editor.kind}/${editor.id}`, payload) : client.post(`/${editor.kind}`, payload);
    },
    onSuccess: () => {
      setNotice(editor.id ? "Changes saved." : editor.kind === "users" ? "Account created. Share the sign-in details privately with the user." : "Facility created. You can now assign its managers.");
      setEditor(null);
      setForm({});
      cache.invalidateQueries();
    },
  });
  function open(kind, item) {
    setNotice("");
    save.reset();
    setEditor({ kind, id: item?.id });
    setForm(kind === "users" ? { ...blankUser, ...item, facility_id: item?.facility_id ?? "" } : {
      name: item?.name ?? "", location: item?.location ?? "", region_code: item?.region_code ?? "", facility_type: item?.facility_type ?? "",
    });
  }
  const set = (key, value) => setForm((previous) => ({ ...previous, [key]: value }));
  const rows = facilities.data ?? [];
  const accounts = users.data ?? [];
  const ownAccount = editor?.id === user.id;
  return <div className="flex flex-col gap-6">
    <header className="flex flex-wrap items-start justify-between gap-4">
      <div><p className="mb-2 text-xs font-semibold uppercase tracking-widest text-leaf">{isAdmin ? "Organization administration" : "Your workspace"}</p>
        <h1 className="text-3xl font-bold tracking-tight text-ink">{isAdmin ? "Facilities & users" : "My facility"}</h1>
        <p className="mt-2 max-w-2xl text-sm text-body">{isAdmin ? "Create facilities, assign managers, and control who has access. Each manager works within their assigned facility." : "Keep your facility details up to date. Your uploads, reports, and scenarios are limited to this facility."}</p>
      </div>
      {isAdmin && <button className={action} disabled={save.isPending} onClick={() => open(section)}><Plus size={16} />{section === "users" ? "Add user" : "Add facility"}</button>}
    </header>
    {isAdmin && <div className="grid gap-3 sm:grid-cols-3">
      {[["Facilities", rows.length, Building2], ["Active users", accounts.filter((u) => u.is_active).length, Users], ["Facility managers", accounts.filter((u) => u.role === "facility_manager" && u.is_active).length, ShieldCheck]].map(([label, count, Icon]) => <div key={label} className="flex items-center gap-4 rounded-xl border border-line bg-surface p-4"><Icon size={21} className="text-leaf" /><div><p className="text-xs text-muted">{label}</p><p className="mt-1 font-mono text-2xl text-ink">{facilities.isLoading || users.isLoading ? "..." : count}</p></div></div>)}
    </div>}
    {isAdmin && <nav aria-label="Administration sections" className="flex gap-2 border-b border-line pb-3">
      {[['facilities', 'Facilities'], ['users', 'Users & access']].map(([key, label]) => <button key={key} aria-pressed={section === key} disabled={save.isPending} onClick={() => { setSection(key); setEditor(null); setForm({}); save.reset(); setNotice(""); }} className={`rounded-lg px-4 py-2 text-sm font-semibold ${section === key ? "bg-mint text-leaf-deep" : "text-body hover:bg-canvas"}`}>{label}</button>)}
    </nav>}
    {notice && <p role="status" className="rounded-lg border border-mint bg-[#edf6f0] p-3 text-sm text-leaf-deep">{notice}</p>}
    {(facilities.isError || (isAdmin && users.isError)) && <p role="alert">Unable to load workspace details. <button className="underline" onClick={() => { facilities.refetch(); if (isAdmin) users.refetch(); }}>Retry</button></p>}
    {editor && <form onSubmit={(e) => { e.preventDefault(); save.mutate(); }} className="rounded-xl border border-line bg-surface p-5 md:p-6">
      <h2 className="mb-5 text-lg font-semibold text-ink">{editor.id ? "Edit" : "New"} {editor.kind === "users" ? "user" : "facility"}</h2>
      <fieldset disabled={save.isPending} className="grid gap-4 sm:grid-cols-2">
        {editor.kind === "users" ? <>
          <label className="text-sm">Full name<input autoFocus required maxLength={255} className={input} value={form.full_name} onChange={(e) => set("full_name", e.target.value)} /></label>
          <label className="text-sm">Email<input required type="email" disabled={!!editor.id} className={input} value={form.email} onChange={(e) => set("email", e.target.value)} autoComplete="off" /></label>
          {!editor.id && <label className="text-sm">Initial password<input required type="password" minLength={10} maxLength={72} className={input} value={form.password} onChange={(e) => set("password", e.target.value)} autoComplete="new-password" /><span className="mt-1 block text-xs text-muted">At least 10 characters. Share privately with this user.</span></label>}
          <label className="text-sm">Role<select disabled={ownAccount} className={input} value={form.role} onChange={(e) => set("role", e.target.value)}><option value="facility_manager">Facility manager</option><option value="admin">Administrator</option></select></label>
          <label className="text-sm">Assigned facility<select required={form.role !== "admin"} className={input} value={form.facility_id} onChange={(e) => set("facility_id", e.target.value)}><option value="">{form.role === "admin" ? "All facilities (administrator)" : "Select a facility"}</option>{rows.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}</select></label>
          {editor.id && <label className="flex items-center gap-2 text-sm"><input type="checkbox" disabled={ownAccount} checked={form.is_active} onChange={(e) => set("is_active", e.target.checked)} />Account active</label>}
          <p className="text-xs text-muted sm:col-span-2">Administrators have access to all facilities. Managers can upload and review data only for their assigned facility. Deactivation blocks sign-in and API access.</p>
        </> : <>
          <label className="text-sm">Facility name<input autoFocus required maxLength={255} className={input} value={form.name} onChange={(e) => set("name", e.target.value)} /></label>
          <label className="text-sm">Location<input className={input} maxLength={255} value={form.location} onChange={(e) => set("location", e.target.value)} /></label>
          <label className="text-sm">Region code<input className={input} maxLength={50} value={form.region_code} onChange={(e) => set("region_code", e.target.value)} /><span className="mt-1 block text-xs text-muted">Used to select a regional emission factor when available.</span></label>
          <label className="text-sm">Facility type<select className={input} value={form.facility_type} onChange={(e) => set("facility_type", e.target.value)}><option value="">Not specified</option>{['office', 'warehouse', 'data_center', 'manufacturing'].map((type) => <option key={type} value={type}>{type.replace('_', ' ')}</option>)}</select></label>
        </>}
        <div className="flex gap-3 sm:col-span-2"><button className={action} type="submit">{save.isPending ? "Saving..." : "Save changes"}</button><button type="button" className="rounded-lg border border-line px-4 py-2 text-sm" onClick={() => { setEditor(null); setForm({}); save.reset(); }}>Cancel</button></div>
      </fieldset>
      {save.isError && <p role="alert" className="mt-4 text-sm text-rose">{errorMessage(save.error)}</p>}
    </form>}
    {section === "facilities" ? <section aria-label="Facilities" className="grid gap-4 lg:grid-cols-2">
      {rows.map((facility) => <article key={facility.id} className="rounded-xl border border-line bg-surface p-5">
        <div className="flex items-start justify-between gap-3"><div className="grid h-11 w-11 place-items-center rounded-lg bg-[#edf6f0] text-leaf"><Building2 size={23} /></div><button disabled={save.isPending} aria-label={`Edit ${facility.name}`} onClick={() => open("facilities", facility)} className="inline-flex items-center gap-1 rounded-lg border border-line px-3 py-2 text-xs font-semibold"><Pencil size={13} />Edit</button></div>
        <h2 className="mt-4 text-lg font-semibold text-ink">{facility.name}</h2><p className="mt-1 text-sm text-muted">{facility.location || "Location not set"}</p>
        <div className="mt-4 flex flex-wrap gap-2 text-xs text-body"><span className="rounded-md bg-canvas px-2 py-1">{facility.facility_type?.replace('_', ' ') || "Type not specified"}</span><span className="rounded-md bg-canvas px-2 py-1">{facility.region_code || "Global factor fallback"}</span></div>
        {isAdmin && <p className="mt-4 border-t border-line pt-3 text-xs text-muted">{accounts.filter((account) => account.facility_id === facility.id && account.role === "facility_manager" && account.is_active).length} active facility managers</p>}
      </article>)}
      {!facilities.isLoading && !facilities.isError && !rows.length && <p className="rounded-xl border border-dashed border-line p-8 text-sm">{isAdmin ? "Add your first facility, then assign a manager." : "No facility is assigned to your account. Ask your administrator for access."}</p>}
    </section> : <section aria-label="User directory" className="overflow-x-auto rounded-xl border border-line bg-surface">
      <table className="w-full text-left text-sm"><thead className="border-b border-line bg-canvas"><tr>{['User', 'Access', 'Facility', 'Status', 'Actions'].map((title) => <th key={title} className="px-5 py-3 font-semibold text-ink">{title}</th>)}</tr></thead><tbody>
        {accounts.map((account) => <tr key={account.id} className="border-b border-line last:border-0"><td className="px-5 py-4"><p className="font-medium text-ink">{account.full_name || account.email}{account.id === user.id ? " (you)" : ""}</p><p className="mt-1 text-xs text-muted">{account.email}</p></td><td className="px-5 py-4">{account.role === "admin" ? "Administrator" : "Facility manager"}</td><td className="px-5 py-4">{account.role === "admin" ? "All facilities" : rows.find((f) => f.id === account.facility_id)?.name || "Unassigned"}</td><td className="px-5 py-4"><span className={`rounded-full px-2 py-1 text-xs ${account.is_active ? "bg-mint text-leaf-deep" : "bg-canvas text-muted"}`}>{account.is_active ? "Active" : "Inactive"}</span></td><td className="px-5 py-4"><button disabled={save.isPending} className="rounded-lg border border-line px-3 py-2 text-xs font-semibold" aria-label={`Edit user ${account.email}`} onClick={() => open("users", account)}>Edit</button></td></tr>)}
      </tbody></table>
    </section>}
  </div>;
}
