import { Activity, AlertTriangle, BarChart3, FileText, UploadCloud, SlidersHorizontal, Building2 } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const links = [
  { to: "/dashboard", label: "Overview", icon: Activity, end: true },
  { to: "/upload", label: "Data intake", icon: UploadCloud },
  { to: "/trends", label: "Trends & analytics", icon: BarChart3 },
  { to: "/scenarios", label: "What-if scenarios", icon: SlidersHorizontal },
  { to: "/anomalies", label: "Anomaly review", icon: AlertTriangle },
  { to: "/esg-report", label: "Emissions report", icon: FileText },
];

export default function Sidebar() {
  const { user } = useAuth();
  const navigation = [...links, { to: "/administration", label: user?.role === "admin" ? "Facilities & users" : "My facility", icon: Building2 }];
  return (
    <aside className="workspace-sidebar hidden w-[232px] shrink-0 flex-col border-r border-line p-4 md:flex">
      <p className="px-3 pb-4 pt-3 text-xs font-semibold text-body">
        Your workspace
      </p>
      <nav aria-label="Workspace navigation" className="flex flex-col gap-1.5">
        {navigation.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `workspace-nav-link ${isActive ? "is-active" : ""}`
            }
          >
            <span className="grid w-5 shrink-0 place-items-center">
              <Icon size={18} />
            </span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto px-3 pb-3 pt-12 text-xs leading-6 text-body"><div className="border-t border-line pt-4"><p className="font-semibold text-ink">Accounting coverage</p><p>Scope 1: fuel consumption<br />Scope 2: purchased electricity</p></div></div>
    </aside>
  );
}

export function MobileNavigation() {
  const { user } = useAuth();
  const navigation = [...links, { to: "/administration", label: user?.role === "admin" ? "Facilities & users" : "My facility", icon: Building2 }];
  return (
    <nav className="flex gap-1 overflow-x-auto border-b border-line bg-surface px-3 py-2 md:hidden" aria-label="Workspace navigation">
      {navigation.map(({ to, label, icon: Icon, end }) => (
        <NavLink key={to} to={to} end={end} className={({ isActive }) => `workspace-nav-link shrink-0 ${isActive ? "is-active" : ""}`}>
          <Icon size={18} />{label}
        </NavLink>
      ))}
    </nav>
  );
}
