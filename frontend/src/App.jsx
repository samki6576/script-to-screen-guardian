import React, { useEffect, useMemo, useState } from "react";
import Dashboard, { SceneRail } from "./components/Dashboard";
import ScriptUpload from "./components/ScriptUpload";
import RiskReport from "./components/RiskReport";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export default function App() {
  const [reports, setReports] = useState([]);
  const [selectedId, setSelectedId] = useState(null);

  // Real-time updates over WebSocket (e.g. reschedule proposals from other clients).
  useEffect(() => {
    const wsUrl = API_URL.replace(/^http/, "ws") + "/api/ws";
    let socket;
    try {
      socket = new WebSocket(wsUrl);
      socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.event === "analysis_complete") {
          setReports(msg.reports);
          setSelectedId(msg.reports[0]?.scene.id ?? null);
        }
      };
    } catch {
      // WebSocket is a nice-to-have; the app still works via plain fetch.
    }
    return () => socket && socket.close();
  }, []);

  const handleAnalyzed = (newReports) => {
    setReports(newReports);
    setSelectedId(newReports[0]?.scene.id ?? null);
  };

  const overallStatus = useMemo(() => {
    if (reports.some((r) => r.decision.overall_risk === "HIGH")) return "HIGH";
    if (reports.some((r) => r.decision.overall_risk === "MEDIUM")) return "MEDIUM";
    return "LOW";
  }, [reports]);

  const selectedReport = reports.find((r) => r.scene.id === selectedId) || null;

  return (
    <div className="app-shell">
      <SceneRail reports={reports} selectedId={selectedId} onSelect={setSelectedId} />
      <div className="main-column">
        <Dashboard reports={reports} overallStatus={overallStatus} />
        <ScriptUpload apiUrl={API_URL} onAnalyzed={handleAnalyzed} />
        <RiskReport report={selectedReport} />
      </div>
    </div>
  );
}
