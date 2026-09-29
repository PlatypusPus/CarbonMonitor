import { Activity, AlertTriangle, BarChart3, FileText, UploadCloud, SlidersHorizontal, Building2 } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const links = [
  { to: "/upload", label: "Data Intake", icon: UploadCloud },
  { to: "/dashboard", label: "Overview", icon: Activity, end: true },
  { to: "/trends", label: "Trends & Analytics", icon: BarChart3 },
  { to: "/scenarios", label: "What-if Scenarios", icon: SlidersHorizontal },
  { to: "/anomalies", label: "Anomaly Log", icon: AlertTriangle },
  { to: "/esg-report", label: "ESG Report", icon: FileText },
];

export default function Sidebar() {
  const { user } = useAuth();
  const navigation = [...links, { to: "/administration", label: user?.role === "admin" ? "Facilities & users" : "My facility", icon: Building2 }];
  return (
    <aside className="hidden w-[216px] shrink-0 flex-col border-r border-line bg-sidebar p-4 md:flex">
      <p className="px-2 py-2 text-xs font-semibold uppercase tracking-wider text-muted">
        Navigation
      </p>
      <nav className="flex flex-col gap-1">
        {navigation.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg border-l-4 py-2 pl-2 pr-3 text-sm font-medium transition-colors ${
                isActive
                  ? "border-leaf bg-[#E2EFE7] text-leaf-deep"
                  : "border-transparent text-body hover:bg-[#E5EFE9]"
              }`
            }
          >
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-surface">
              <Icon size={16} />
            </span>
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}

export function MobileNavigation() {
  const { user } = useAuth();
  const navigation = [...links, { to: "/administration", label: user?.role === "admin" ? "Facilities & users" : "My facility", icon: Building2 }];
  return (
    <nav className="flex gap-1 overflow-x-auto border-b border-line bg-sidebar px-3 py-2 md:hidden" aria-label="Workspace navigation">
      {navigation.map(({ to, label, icon: Icon, end }) => (
        <NavLink key={to} to={to} end={end} className={({ isActive }) => `flex shrink-0 items-center gap-2 rounded-lg px-3 py-2 text-xs font-semibold ${isActive ? "bg-[#E2EFE7] text-leaf-deep" : "text-body"}`}>
          <Icon size={15} />{label}
        </NavLink>
      ))}
    </nav>
  );
}
