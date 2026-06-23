import { Bell, LogOut } from "lucide-react";

import { useAuth } from "../context/AuthContext";

export default function TopBar() {
  const { user, logout } = useAuth();
  const initial = user?.email?.[0]?.toUpperCase() ?? "?";

  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-line bg-surface px-6">
      <div className="flex items-center gap-2">
        <div className="grid h-8 w-8 place-items-center rounded-lg bg-leaf text-sm font-bold text-white">
          C
        </div>
        <span className="font-bold text-ink">CarbonTrace</span>
      </div>
      <div className="flex items-center gap-3">
        <button className="rounded-lg border border-line p-2 text-body transition-colors hover:bg-canvas">
          <Bell size={18} />
        </button>
        <div className="grid h-9 w-9 place-items-center rounded-full bg-mint text-sm font-semibold text-leaf-deep">
          {initial}
        </div>
        <button
          onClick={logout}
          className="rounded-lg border border-line p-2 text-body transition-colors hover:bg-canvas"
          title="Log out"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
