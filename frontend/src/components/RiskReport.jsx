import React from "react";

export default function RiskReport({ report }) {
  if (!report) {
    return <div className="empty-state">Select a scene from the binder to view its continuity report.</div>;
  }

  const { scene, location, logistics, decision } = report;

  return (
    <div className="report-card">
      <h2>{scene.id} — {scene.location}</h2>
      <span className={`risk-banner ${decision.overall_risk}`}>
        {decision.overall_risk} RISK
      </span>

      <div className="report-section">
        <h3>Scene breakdown</h3>
        <div className="field-row">
          <div className="field">
            <div className="label">Characters</div>
            <div className="value">{scene.characters.join(", ") || "—"}</div>
          </div>
          <div className="field">
            <div className="label">Props</div>
            <div className="value">{scene.props.join(", ") || "—"}</div>
          </div>
          <div className="field">
            <div className="label">Special requirements</div>
            <div className="value">{scene.special_requirements.join(", ") || "none"}</div>
          </div>
        </div>
      </div>

      <div className="report-section">
        <h3>Location scout</h3>
        <div className="field-row">
          <div className="field">
            <div className="label">Proposed location</div>
            <div className="value">{location.location_found}</div>
          </div>
          <div className="field">
            <div className="label">Permit</div>
            <div className="value">{location.permit_status}</div>
          </div>
          <div className="field">
            <div className="label">Weather</div>
            <div className="value">{location.weather_forecast}</div>
          </div>
        </div>
        {location.alternative_dates.length > 0 && (
          <p style={{ marginTop: 10 }}>
            Alternative dates: {location.alternative_dates.join(", ")}
          </p>
        )}
      </div>

      <div className="report-section">
        <h3>Logistics &amp; gear</h3>
        <ul>
          {Object.entries(logistics.availability).map(([item, status]) => (
            <li key={item}>{item}: {status}</li>
          ))}
        </ul>
        <p style={{ marginTop: 8 }}>
          Crew available: {logistics.crew_available ? "yes" : "no — conflicts found"}
        </p>
      </div>

      <div className="report-section">
        <h3>Studio head recommendation</h3>
        <ul>
          {decision.recommendations.map((rec, i) => (
            <li key={i}>{rec}</li>
          ))}
        </ul>
        <p style={{ marginTop: 8 }}>Estimated cost impact: {decision.cost_impact}</p>
      </div>
    </div>
  );
}
