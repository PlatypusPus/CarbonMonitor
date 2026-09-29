import { createContext, useContext, useState } from "react";
import { useAuth } from "./AuthContext";

const WorkspaceContext = createContext(null);

export function WorkspaceProvider({ children }) {
  const { user } = useAuth();
  const [selected, setSelected] = useState("");
  const [dates, setDates] = useState({ start_date: "", end_date: "" });
  const facilityId = user.role === "admin" ? selected : user.facility_id ?? "";
  return <WorkspaceContext.Provider value={{ facilityId, setFacilityId: setSelected, dates, setDates }}>{children}</WorkspaceContext.Provider>;
}

export const useWorkspace = () => useContext(WorkspaceContext);
