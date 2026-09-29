import { Building2, LogOut, ShieldCheck } from "lucide-react";

import { useAuth } from "../context/AuthContext";
import { useWorkspace } from "../context/WorkspaceContext";
import { useFacilities } from "../api/hooks";
import Dropdown from "./Dropdown";

export default function TopBar() {
  const { user, logout } = useAuth();
  const { facilityId, setFacilityId } = useWorkspace();
  const facilities = useFacilities();
  const isAdmin = user?.role === "admin";
  const initial = user?.email?.[0]?.toUpperCase() ?? "?";

  return (
    <header className="flex shrink-0 flex-wrap items-center justify-between gap-4 border-b border-line bg-surface px-4 py-4 md:px-6">
      <div className="flex items-center gap-2">
        <div className="grid h-8 w-8 place-items-center rounded-lg bg-leaf text-sm font-bold text-white">
          C
        </div>
        <span className="font-bold text-ink">CarbonTrace</span>
      </div>
      <div className="flex min-w-0 flex-wrap items-center gap-3">
        <div className="flex min-w-0 items-center gap-2 text-sm">
          <Building2 size={16} className="shrink-0 text-leaf" />
          {isAdmin ? <Dropdown label="Workspace facility" value={facilityId} onChange={setFacilityId} className="w-[220px]" options={[{value:'',label:'All facilities'}, ...(facilities.data ?? []).map((f) => ({value:f.id,label:f.name}))]} /> : <span>{facilities.data?.find((f) => f.id === facilityId)?.name ?? 'No facility assigned'}</span>}
        </div>
        <div className="hidden text-right text-xs sm:block"><p className="font-semibold text-ink">{user?.full_name || user?.email}</p><p className="mt-1 flex items-center justify-end gap-1 text-muted"><ShieldCheck size={12} />{isAdmin ? "Administrator" : "Facility manager"}</p></div>
        <div className="grid h-9 w-9 place-items-center rounded-full bg-mint text-sm font-semibold text-leaf-deep">
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
    </header>
  );
}
