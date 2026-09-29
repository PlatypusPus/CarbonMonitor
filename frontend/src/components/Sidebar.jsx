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
    <aside className="workspace-sidebar hidden w-[232px] shrink-0 flex-col p-4 md:flex">
      <p className="px-3 pb-4 pt-3 text-xs font-semibold text-white/70">
        Your workspace
      </p>
      <nav aria-label="Workspace navigation" className="flex flex-col gap-1.5">
        {navigation.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex min-h-12 items-center gap-3 rounded-lg px-3 py-3 text-sm font-medium transition-colors ${
                isActive
                  ? "bg-[#DAEDE2] text-[#195A3C] shadow-sm"
                  : "text-white/80 hover:bg-white/10 hover:text-white"
              }`
            }
          >
            <span className="grid w-5 shrink-0 place-items-center">
              <Icon size={18} />
            </span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto px-3 pb-3 pt-16 text-xs leading-6 text-white/70"><p className="font-semibold text-white">Know your footprint.</p><p>Review activity. Track change.<br />Make informed decisions.</p></div>
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
