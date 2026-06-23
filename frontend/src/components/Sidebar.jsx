import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/trends", label: "Trends" },
  { to: "/anomalies", label: "Anomalies" },
  { to: "/cross-verify", label: "Cross-Verify" },
  { to: "/esg-report", label: "ESG Report" },
];

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-slate-200 bg-sidebar p-6">
      <h1 className="mb-8 text-xl font-bold text-leaf">CarbonTrace</h1>
      <nav className="flex flex-col gap-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              `rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive ? "bg-leaf text-white" : "text-slate-600 hover:bg-white"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
