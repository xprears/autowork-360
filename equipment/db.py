# -*- coding: utf-8 -*-
"""SQLite 数据库连接与 Schema 定义。"""

import sqlite3
from pathlib import Path

# 数据库默认路径（相对项目根目录）
DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "equipment.db"

# 设备测试状态字典
STATUSES = ["待测试", "正常", "故障", "维修中", "已修复"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    device_type     TEXT NOT NULL,
    device_name     TEXT,
    brand           TEXT,
    model           TEXT,
    satellite_info  TEXT,
    unit_path       TEXT NOT NULL DEFAULT '',
    org_branch      TEXT,
    org_category    TEXT,
    region_category TEXT,
    district        TEXT,
    town            TEXT,
    unit_name       TEXT,
    unit_parent     TEXT,
    status          TEXT DEFAULT '待测试',
    last_test_date  TEXT,
    test_round      TEXT,
    fault_desc      TEXT,
    repair_status   TEXT,
    source_file     TEXT,
    source_sheet    TEXT,
    source_row      INTEGER,
    updated_at      TEXT DEFAULT (datetime('now', 'localtime'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_devices_source
    ON devices(source_file, source_sheet, source_row);

CREATE INDEX IF NOT EXISTS idx_devices_type ON devices(device_type);
CREATE INDEX IF NOT EXISTS idx_devices_district ON devices(district);
CREATE INDEX IF NOT EXISTS idx_devices_town ON devices(town);
CREATE INDEX IF NOT EXISTS idx_devices_status ON devices(status);

-- 标签表（预留）：用于风险村等自定义分类
CREATE TABLE IF NOT EXISTS unit_tags (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_name   TEXT NOT NULL,
    tag         TEXT NOT NULL,
    remark      TEXT,
    UNIQUE(unit_name, tag)
);

-- 风险村标准表：区/街镇/单位名与 devices 对齐，供“仅风险村/排除风险村”范围查询
CREATE TABLE IF NOT EXISTS risk_villages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    district     TEXT NOT NULL,              -- 区（与 devices.district 对齐）
    town         TEXT NOT NULL,              -- 街镇标准名（如 西龙虎峪镇、孙各庄满族乡）
    village_name TEXT NOT NULL,              -- 单位标准名（与 devices.unit_name 对齐）
    source_row   INTEGER,                    -- 来源行号（风险村台账 Excel 行）
    created_at   TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE(district, town, village_name)
);

-- 风险村别名表：台账原始写法 -> 标准名，便于更新台账后重新比对
CREATE TABLE IF NOT EXISTS risk_village_aliases (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_village_id  INTEGER NOT NULL REFERENCES risk_villages(id) ON DELETE CASCADE,
    alias_town       TEXT NOT NULL,          -- 台账原始街镇写法（如 西龙虎、孙各庄）
    alias_name       TEXT NOT NULL,          -- 台账原始村名（如 拾叁街村、粱后庄村）
    UNIQUE(alias_town, alias_name)
);

-- 基准统计表：《应急装备数量统计（内部）》按“设备类型+统计单位+口径”的汇总数。
-- 用于存放下发/自购、配置/可用等无法逐台表示的基准口径（如无人机、370MHz 可用数）。
CREATE TABLE IF NOT EXISTS equipment_benchmark (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    device_type TEXT NOT NULL,                -- 设备类型（如 无人机、370MHz手持终端）
    district    TEXT NOT NULL,                -- 统计单位/区（市行为 天津市应急管理局）
    metric      TEXT NOT NULL DEFAULT '总数', -- 口径（总数/市局配发/区局自购/配置总数/可用数量）
    count       INTEGER NOT NULL DEFAULT 0 CHECK(count >= 0),
    source_file TEXT,
    source_sheet TEXT,
    source_row  INTEGER,
    updated_at  TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE(device_type, district, metric)
);

CREATE INDEX IF NOT EXISTS idx_benchmark_type ON equipment_benchmark(device_type);
CREATE INDEX IF NOT EXISTS idx_benchmark_district ON equipment_benchmark(district);
CREATE INDEX IF NOT EXISTS idx_benchmark_metric ON equipment_benchmark(metric);
"""


def _ensure_region_category(conn):
    """旧库兼容：为 devices 表补充 region_category 列并回填历史数据。"""
    from equipment.normalize import parse_unit_path

    cols = {row["name"] for row in conn.execute("PRAGMA table_info(devices)")}
    if "region_category" not in cols:
        conn.execute("ALTER TABLE devices ADD COLUMN region_category TEXT")
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_devices_region_category"
        " ON devices(region_category)"
    )
    conn.commit()

    rows = conn.execute(
        "SELECT id, unit_path FROM devices WHERE region_category IS NULL"
    ).fetchall()
    for row in rows:
        region = parse_unit_path(row["unit_path"])["region_category"]
        conn.execute(
            "UPDATE devices SET region_category = ? WHERE id = ?",
            (region, row["id"]),
        )
    if rows:
        conn.commit()


def get_connection(db_path=None):
    """获取数据库连接，并确保 Schema 已创建。"""
    path = Path(db_path) if db_path else DEFAULT_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _ensure_region_category(conn)
    return conn
