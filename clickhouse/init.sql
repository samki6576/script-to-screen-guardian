-- Script-to-Screen Guardian — ClickHouse schema
-- Run against a ClickHouse instance (self-hosted or ClickHouse Cloud):
--   clickhouse-client --multiquery < clickhouse/init.sql

CREATE DATABASE IF NOT EXISTS production_db;

USE production_db;

CREATE TABLE IF NOT EXISTS equipment_inventory
(
    equipment_name String,
    category       String,
    status         String,      -- 'available' | 'booked_until_YYYY-MM-DD' | 'maintenance_scheduled'
    location       String,
    updated_at     DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY equipment_name;

CREATE TABLE IF NOT EXISTS crew_schedules
(
    crew_member     String,
    role            String,
    shoot_date      Date,
    is_available    UInt8,       -- 0 = conflict, 1 = available
    conflict_reason String,
    updated_at      DateTime DEFAULT now()
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (shoot_date, crew_member);

CREATE TABLE IF NOT EXISTS maintenance_logs
(
    equipment_name String,
    maintenance_date Date,
    notes          String,
    logged_at      DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (equipment_name, maintenance_date);

CREATE TABLE IF NOT EXISTS risk_reports
(
    scene_id     String,
    risk_level   String,
    cost_impact  String,
    created_at   DateTime
)
ENGINE = MergeTree
ORDER BY created_at;
