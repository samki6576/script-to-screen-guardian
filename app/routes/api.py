"""
API routes for Script-to-Screen Guardian.
"""

from __future__ import annotations
import json
import logging

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.database.clickhouse_client import get_clickhouse_client
from app.models import ProductionRiskReport, RescheduleRequest, ScriptUploadRequest
from app.orchestrator import get_orchestrator

logger = logging.getLogger("api")
router = APIRouter(prefix="/api")

# In-memory cache of the most recent run — good enough for a hackathon demo;
# swap for ClickHouse-backed reads in a production deployment.
_latest_reports: list[ProductionRiskReport] = []
_ws_clients: list[WebSocket] = []


async def _broadcast(payload: dict):
    stale = []
    for ws in _ws_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            stale.append(ws)
    for ws in stale:
        _ws_clients.remove(ws)


@router.post("/upload-script")
async def upload_script(request: ScriptUploadRequest):
    if not request.script_text.strip():
        raise HTTPException(status_code=400, detail="script_text cannot be empty")

    global _latest_reports
    orchestrator = get_orchestrator()
    _latest_reports = await orchestrator.run(request.script_text, request.shoot_start_date)

    payload = {"event": "analysis_complete", "reports": [r.model_dump() for r in _latest_reports]}
    await _broadcast(payload)
    return payload


@router.get("/production-status")
async def production_status():
    if not _latest_reports:
        return {"status": "no_data", "scenes_analyzed": 0}
    high = sum(1 for r in _latest_reports if r.decision.overall_risk == "HIGH")
    medium = sum(1 for r in _latest_reports if r.decision.overall_risk == "MEDIUM")
    return {
        "status": "HIGH" if high else "MEDIUM" if medium else "LOW",
        "scenes_analyzed": len(_latest_reports),
        "high_risk_scenes": high,
        "medium_risk_scenes": medium,
    }


@router.get("/risks")
async def get_risks():
    return {"reports": [r.model_dump() for r in _latest_reports]}


@router.post("/reschedule")
async def reschedule(request: RescheduleRequest):
    matched = next((r for r in _latest_reports if r.scene.id == request.scene_id), None)
    if not matched:
        raise HTTPException(status_code=404, detail=f"No report found for {request.scene_id}")

    result = {
        "scene_id": request.scene_id,
        "proposed_date": request.proposed_date,
        "reason": request.reason,
        "status": "proposed",
    }
    await _broadcast({"event": "reschedule_proposed", **result})
    return result


@router.get("/dashboard-data")
async def dashboard_data():
    """Grafana-friendly aggregate view, backed by ClickHouse history when available."""
    try:
        ch = get_clickhouse_client()
        history = ch.query(
            "SELECT scene_id, risk_level, cost_impact, created_at "
            "FROM risk_reports ORDER BY created_at DESC LIMIT 50"
        )
    except Exception as exc:
        logger.warning("Falling back to in-memory dashboard data: %s", exc)
        history = [
            {
                "scene_id": r.scene.id,
                "risk_level": r.decision.overall_risk,
                "cost_impact": r.decision.cost_impact,
                "created_at": None,
            }
            for r in _latest_reports
        ]
    return {"history": history}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.append(websocket)
    try:
        while True:
            # Keep the connection open; clients don't need to send anything.
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)
