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
    <WorkspaceProvider><div className="workspace-shell flex min-h-screen flex-col">
      <TopBar />
      <MobileNavigation />
      <div className="flex flex-1">
        <Sidebar />
        <main id="main-content" tabIndex={-1} className="workspace-main min-w-0 flex-1 bg-canvas p-4 md:p-7 lg:p-10">
          <div className="mx-auto w-full max-w-[1440px]"><WorkspaceContent /></div>
        </main>
      </div>
    </div></WorkspaceProvider>
  );
}
