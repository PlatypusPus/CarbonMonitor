import { Activity, AlertTriangle, BarChart3, FileCheck, FileText } from "lucide-react";
import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Live Monitor", icon: Activity, end: true },
  { to: "/trends", label: "Trends & Analytics", icon: BarChart3 },
  { to: "/anomalies", label: "Anomaly Log", icon: AlertTriangle },
  { to: "/cross-verify", label: "Cross-Verification", icon: FileCheck },
  { to: "/esg-report", label: "ESG Report", icon: FileText },
];

export default function Sidebar() {
  return (
    <aside className="flex w-[216px] shrink-0 flex-col border-r border-line bg-sidebar p-4">
      <p className="px-2 py-2 text-xs font-semibold uppercase tracking-wider text-muted">
        Navigation
      </p>
      <nav className="flex flex-col gap-1">
        {links.map(({ to, label, icon: Icon, end }) => (
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
      <div className="mt-auto rounded-lg border border-dashed border-line p-3 text-xs text-muted">
        <p className="font-semibold uppercase tracking-wider">System</p>
        <p className="mt-1">All sensors reporting</p>
      </div>
    </aside>
  );
}
