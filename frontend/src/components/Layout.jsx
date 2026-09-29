import { Outlet } from "react-router-dom";

import Sidebar, { MobileNavigation } from "./Sidebar";
import TopBar from "./TopBar";
import { WorkspaceProvider, useWorkspace } from "../context/WorkspaceContext";

function WorkspaceContent() {
  const { facilityId } = useWorkspace();
  return <Outlet key={facilityId || "all"} />;
}

export default function Layout() {
  return (
    <WorkspaceProvider><div className="flex min-h-screen flex-col">
      <TopBar />
      <MobileNavigation />
      <div className="flex flex-1">
        <Sidebar />
        <main className="min-w-0 flex-1 overflow-auto bg-[#FBFCFB] p-4 md:p-8">
          <WorkspaceContent />
        </main>
      </div>
    </div></WorkspaceProvider>
  );
}
