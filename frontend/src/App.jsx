import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import Anomalies from "./pages/Anomalies";
import CrossVerify from "./pages/CrossVerify";
import Dashboard from "./pages/Dashboard";
import ESGReport from "./pages/ESGReport";
import Login from "./pages/Login";
import Trends from "./pages/Trends";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/trends" element={<Trends />} />
        <Route path="/anomalies" element={<Anomalies />} />
        <Route path="/cross-verify" element={<CrossVerify />} />
        <Route path="/esg-report" element={<ESGReport />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
