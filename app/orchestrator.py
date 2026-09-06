"""
Orchestrator

Runs the full multi-agent workflow:

  Script Supervisor -> (Location Scout + Logistics Agent, in parallel per
  scene) -> Studio Head -> risk report

Also persists each report to ClickHouse (best-effort — the demo still works
if ClickHouse isn't reachable) so /api/dashboard-data and Grafana can query
real history.
"""

from __future__ import annotations
import asyncio
import logging
from datetime import date, datetime, timedelta

from app.agents.script_supervisor import ScriptSupervisorAgent
from app.agents.location_scout import LocationScoutAgent
from app.agents.logistics_agent import LogisticsAgent
from app.agents.studio_head import StudioHeadAgent
from app.database.clickhouse_client import get_clickhouse_client
from app.models import ProductionRiskReport, Scene

logger = logging.getLogger("orchestrator")


class ProductionOrchestrator:
    def __init__(self):
        self.script_supervisor = ScriptSupervisorAgent()
        self.location_scout = LocationScoutAgent()
        self.logistics_agent = LogisticsAgent()
        self.studio_head = StudioHeadAgent()

    async def _assess_scene(self, scene: Scene, shoot_date: str) -> ProductionRiskReport:
        loop = asyncio.get_event_loop()
        location, logistics = await asyncio.gather(
            loop.run_in_executor(None, self.location_scout.assess, scene, shoot_date),
            loop.run_in_executor(None, self.logistics_agent.assess, scene, shoot_date),
        )
        decision = self.studio_head.decide(scene, location, logistics)

        try:
            get_clickhouse_client().log_risk_report(
                scene.id, decision.overall_risk.value, decision.cost_impact,
                datetime.utcnow().isoformat(),
            )
        except Exception as exc:  # pragma: no cover
            logger.warning("Could not log risk report to ClickHouse: %s", exc)

        return ProductionRiskReport(
            scene=scene, location=location, logistics=logistics, decision=decision
        )

    async def run(self, script_text: str, shoot_start_date: str | None = None) -> list[ProductionRiskReport]:
        shoot_date = shoot_start_date or (date.today() + timedelta(days=7)).isoformat()
        analysis = self.script_supervisor.analyze(script_text)
        reports = await asyncio.gather(
            *(self._assess_scene(scene, shoot_date) for scene in analysis.scenes)
        )
        return list(reports)


_orchestrator: ProductionOrchestrator | None = None


def get_orchestrator() -> ProductionOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ProductionOrchestrator()
    return _orchestrator
