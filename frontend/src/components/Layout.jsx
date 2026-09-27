import { Outlet } from "react-router-dom";

import Sidebar, { MobileNavigation } from "./Sidebar";
import TopBar from "./TopBar";

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <TopBar />
      <MobileNavigation />
      <div className="flex flex-1">
        <Sidebar />
        <main className="min-w-0 flex-1 overflow-auto bg-[#FBFCFB] p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
