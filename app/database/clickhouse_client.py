"""
Thin async-friendly wrapper around the ClickHouse client.

Uses `clickhouse-connect`, which speaks HTTP(S) to ClickHouse and works well
with both self-hosted and ClickHouse Cloud instances.
"""

from __future__ import annotations
import logging
import threading
import clickhouse_connect

from app.config import get_settings

logger = logging.getLogger("clickhouse_client")

_thread_local = threading.local()


class ClickHouseClient:
    def __init__(self):
        settings = get_settings()
        self._client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_database,
        )

    def ping(self) -> bool:
        try:
            return self._client.command("SELECT 1") == 1
        except Exception as exc:  # pragma: no cover
            logger.error("ClickHouse ping failed: %s", exc)
            return False

    def query(self, sql: str, parameters: dict | None = None):
        result = self._client.query(sql, parameters=parameters or {})
        return [dict(zip(result.column_names, row)) for row in result.result_rows]

    def insert(self, table: str, rows: list[list], column_names: list[str]):
        self._client.insert(table, rows, column_names=column_names)

    def get_equipment_availability(self, equipment_names: list[str]) -> dict[str, str]:
        if not equipment_names:
            return {}
        rows = self.query(
            """
            SELECT equipment_name, status
            FROM equipment_inventory
            WHERE equipment_name IN {names:Array(String)}
            """,
            {"names": equipment_names},
        )
        found = {row["equipment_name"]: row["status"] for row in rows}
        # Anything not in the table is treated as unknown/unavailable rather than
        # silently assumed available.
        for name in equipment_names:
            found.setdefault(name, "unknown")
        return found

    def get_crew_conflicts(self, shoot_date: str) -> list[dict]:
        return self.query(
            """
            SELECT crew_member, role, conflict_reason
            FROM crew_schedules
            WHERE shoot_date = {shoot_date:String} AND is_available = 0
            """,
            {"shoot_date": shoot_date},
        )

    def log_risk_report(self, scene_id: str, risk_level: str, cost_impact: str, timestamp: str):
        self.insert(
            "risk_reports",
            [[scene_id, risk_level, cost_impact, timestamp]],
            ["scene_id", "risk_level", "cost_impact", "created_at"],
        )


def get_clickhouse_client() -> ClickHouseClient:
    client = getattr(_thread_local, "client", None)
    if client is None:
        client = ClickHouseClient()
        _thread_local.client = client
    return client
