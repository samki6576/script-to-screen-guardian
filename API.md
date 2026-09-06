# API Reference

Base URL (local): `http://localhost:8000`

All request/response bodies are JSON. Interactive docs are also available at
`/docs` (Swagger UI) once the backend is running.

---

## `POST /api/upload-script`

Runs the full multi-agent pipeline against a script and returns a risk
report per scene.

**Request**

```json
{
  "script_text": "SCENE 12 - EXT. ABANDONED WAREHOUSE - DAY\n...",
  "shoot_start_date": "2026-09-10"
}
```

`shoot_start_date` is optional — defaults to seven days from today.

**Response**

```json
{
  "event": "analysis_complete",
  "reports": [
    {
      "scene": { "id": "SCENE_12", "location": "...", "props": [...], "...": "..." },
      "location": { "scene_id": "SCENE_12", "location_found": "...", "weather_risk": "HIGH", "...": "..." },
      "logistics": { "equipment_needed": [...], "availability": {...}, "overall_risk": "MEDIUM" },
      "decision": { "overall_risk": "HIGH", "recommendations": [...], "cost_impact": "$12,500 additional" }
    }
  ]
}
```

This event is also pushed to any connected WebSocket clients.

---

## `GET /api/production-status`

Rolls all analyzed scenes up into a single traffic-light status.

```json
{
  "status": "HIGH",
  "scenes_analyzed": 4,
  "high_risk_scenes": 1,
  "medium_risk_scenes": 2
}
```

---

## `GET /api/risks`

Returns the full risk report list from the most recent analysis run.

```json
{ "reports": [ /* same shape as upload-script's reports */ ] }
```

---

## `POST /api/reschedule`

Proposes a reschedule for a given scene. Broadcasts a
`reschedule_proposed` event over WebSocket.

**Request**

```json
{
  "scene_id": "SCENE_12",
  "proposed_date": "2026-09-15",
  "reason": "Rain forecast + rain machine maintenance conflict"
}
```

**Response**

```json
{
  "scene_id": "SCENE_12",
  "proposed_date": "2026-09-15",
  "reason": "Rain forecast + rain machine maintenance conflict",
  "status": "proposed"
}
```

---

## `GET /api/dashboard-data`

Grafana-friendly aggregate of recent risk reports, read from ClickHouse's
`risk_reports` table (falls back to in-memory data if ClickHouse isn't
reachable).

```json
{
  "history": [
    { "scene_id": "SCENE_12", "risk_level": "HIGH", "cost_impact": "$12,500 additional", "created_at": "2026-09-06T10:00:00" }
  ]
}
```

---

## `WS /api/ws`

WebSocket endpoint for real-time updates. Emits:

- `{"event": "analysis_complete", "reports": [...]}` after each script upload
- `{"event": "reschedule_proposed", ...}` after each reschedule proposal

---

## `GET /health`

Basic liveness check: `{"status": "ok", "env": "development"}`.
