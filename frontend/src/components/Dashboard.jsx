import React from "react";

export default function Dashboard({ reports, selectedId, onSelect, overallStatus }) {
  return (
    <>
      <div className="masthead">
        <div>
          <h1>Script-to-Screen Guardian</h1>
          <div className="subtitle">Live production risk monitoring — {reports.length} scene{reports.length === 1 ? "" : "s"} tracked</div>
        </div>
        {reports.length > 0 && (
          <div className="status-gauge">
            <div>Production status</div>
            <div className={`value ${overallStatus}`}>{overallStatus}</div>
          </div>
        )}
      </div>
    </>
  );
}

export function SceneRail({ reports, selectedId, onSelect }) {
  return (
    <nav className="scene-rail">
      <div className="brand-lockup">
        <img className="brand-logo" src="/logo.png" alt="Script-to-Screen Guardian logo" />
        <div className="brand-name">SCRIPT TO SCREEN<br />GUARDIAN</div>
      </div>
      <div className="rail-title">SCENE BINDER</div>
      {reports.length === 0 && (
        <div style={{ padding: "0 20px", fontSize: 13, color: "var(--parchment-dim)" }}>
          No scenes analyzed yet.
        </div>
      )}
      {reports.map((r) => (
        <button
          key={r.scene.id}
          className={`scene-tab ${r.scene.id === selectedId ? "active" : ""}`}
          onClick={() => onSelect(r.scene.id)}
        >
          <span>{r.scene.id}</span>
          <span className={`risk-dot ${r.decision.overall_risk}`} />
        </button>
      ))}
    </nav>
  );
}
