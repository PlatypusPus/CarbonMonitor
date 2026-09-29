import { Building2, LogOut, ShieldCheck, Leaf } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { useWorkspace } from "../context/WorkspaceContext";
import { useFacilities } from "../api/hooks";
import Dropdown from "./Dropdown";
import { Link } from "react-router-dom";

export default function TopBar() {
  const { user, logout } = useAuth();
  const { facilityId, setFacilityId } = useWorkspace();
  const facilities = useFacilities();
  const isAdmin = user?.role === "admin";
  const initial = user?.email?.[0]?.toUpperCase() ?? "?";

  return (
    <header className="workspace-header relative z-30 flex shrink-0 flex-wrap items-stretch border-b border-line bg-surface">
      <a href="#main-content" className="skip-link">Skip to content</a>
      <Link to="/dashboard" aria-label="CarbonTrace overview" className="flex min-h-20 w-full shrink-0 items-center gap-2 px-5 md:w-[232px] md:border-r md:border-line">
        <div className="grid h-10 w-10 place-items-center rounded-xl bg-leaf-action text-white">
          <Leaf size={22} aria-hidden="true" />
        </div>
        <div><span className="text-lg font-bold tracking-tight text-ink">CarbonTrace</span><p className="text-xs text-body">Emissions workspace</p></div>
      </Link>
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-3 px-4 pb-4 md:px-7 md:py-3">
        <div className="flex min-w-0 items-center gap-2 text-sm">
          <Building2 size={16} className="shrink-0 text-leaf" />
          {isAdmin ? <Dropdown label="Workspace facility" value={facilityId} onChange={setFacilityId} className="w-[180px] sm:w-[220px]" options={[{value:'',label:'All facilities'}, ...(facilities.data ?? []).map((f) => ({value:f.id,label:f.name}))]} /> : <span>{facilities.data?.find((f) => f.id === facilityId)?.name ?? 'No facility assigned'}</span>}
        </div>
        <div className="ml-auto flex items-center gap-3">
        <div className="hidden max-w-[160px] text-right text-xs lg:block"><p className="truncate font-semibold text-ink">{user?.full_name || user?.email}</p><p className="mt-1 flex items-center justify-end gap-1 text-muted"><ShieldCheck size={12} />{isAdmin ? "Administrator" : "Facility manager"}</p></div>
        <div aria-hidden="true" className="hidden h-9 w-9 place-items-center rounded-full bg-mint text-sm font-semibold text-leaf-deep sm:grid">
          {initial}
        </div>
        <button
          onClick={logout}
          className="rounded-lg border border-line p-2 text-body transition-colors hover:bg-canvas"
          title="Log out"
          aria-label="Log out"
        >
          <LogOut size={18} />
        </button>
        </div>
      </div>
    </header>
  );
}
