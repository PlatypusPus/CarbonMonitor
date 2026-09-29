import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import Anomalies from "./pages/Anomalies";
import Dashboard from "./pages/Dashboard";
import ESGReport from "./pages/ESGReport";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Onboarding from "./pages/Onboarding";
import Trends from "./pages/Trends";
import Intake from "./pages/Intake";
import Scenarios from "./pages/Scenarios";
import Administration from "./pages/Administration";
import { useAuth } from "./context/AuthContext";
import { getOnboarding } from "./lib/onboarding";

function Workspace() {
  const { user } = useAuth();
  return getOnboarding(user?.id) ? <Layout /> : <Navigate to="/onboarding" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/onboarding" element={<ProtectedRoute><Onboarding /></ProtectedRoute>} />
      <Route
        element={
          <ProtectedRoute>
            <Workspace />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/trends" element={<Trends />} />
        <Route path="/scenarios" element={<Scenarios />} />
        <Route path="/administration" element={<Administration />} />
        <Route path="/anomalies" element={<Anomalies />} />
        <Route path="/ocr" element={<Navigate to="/upload" replace />} />
        <Route path="/esg-report" element={<ESGReport />} />
        <Route path="/upload" element={<Intake />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
