# -*- coding: utf-8 -*-
"""将台账 xlsx 导入 SQLite 全量数据库。"""

import argparse
from pathlib import Path

import openpyxl

from equipment.db import SCHEMA, get_connection
from equipment.normalize import parse_unit_path

# 表头列名映射：去掉星号后与数据库字段对应
COLUMN_MAP = {
    "序号": None,
    "设备类型": "device_type",
    "使用单位": "unit_path",
    "设备名称": "device_name",
    "品牌": "brand",
    "设备型号": "model",
    "卫星网络信息": "satellite_info",
}

UPSERT_SQL = """
INSERT INTO devices (
    device_type, device_name, brand, model, satellite_info,
    unit_path, org_branch, org_category, region_category,
    district, town, unit_name, unit_parent,
    status, source_file, source_sheet, source_row, updated_at
) VALUES (
    :device_type, :device_name, :brand, :model, :satellite_info,
    :unit_path, :org_branch, :org_category, :region_category,
    :district, :town, :unit_name, :unit_parent,
    COALESCE(:status, '待测试'), :source_file, :source_sheet, :source_row,
    datetime('now', 'localtime')
)
ON CONFLICT(source_file, source_sheet, source_row) DO UPDATE SET
    device_type = excluded.device_type,
    device_name = excluded.device_name,
    brand = excluded.brand,
    model = excluded.model,
    satellite_info = excluded.satellite_info,
    unit_path = excluded.unit_path,
    org_branch = excluded.org_branch,
    org_category = excluded.org_category,
    region_category = excluded.region_category,
    district = excluded.district,
    town = excluded.town,
    unit_name = excluded.unit_name,
    unit_parent = excluded.unit_parent,
    updated_at = datetime('now', 'localtime')
"""


def _clean_header(cell):
    """清洗表头：去星号、去空白。"""
    if cell is None:
        return None
    return str(cell).replace("*", "").strip()


def ingest_xlsx(xlsx_path, conn):
    """将 xlsx 中所有 Sheet 导入 devices 表，返回导入统计。"""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    source_file = Path(xlsx_path).name
    stats = {"sheets": {}, "total": 0, "empty_unit": 0, "skipped_sheets": []}

    for ws in wb.worksheets:
        rows = ws.iter_rows(values_only=True)
        header = next(rows, None)
        if not header:
            continue

        # 建立 列序号 -> 字段名 映射
        col_map = {}
        for idx, cell in enumerate(header):
            key = _clean_header(cell)
            if key in COLUMN_MAP and COLUMN_MAP[key]:
                col_map[idx] = COLUMN_MAP[key]

        # 跳过汇总/说明类 Sheet：无“使用单位”列的不视为设备明细表
        if "unit_path" not in col_map.values():
            stats["skipped_sheets"].append(ws.title)
            continue

        sheet_count = 0
        for row_idx, row in enumerate(rows, start=2):
            if not any(c is not None and str(c).strip() != "" for c in row):
                continue

            values = {field: None for field in COLUMN_MAP.values() if field}
            for idx, field in col_map.items():
                if idx < len(row):
                    values[field] = row[idx]

            unit_path = values["unit_path"]
            parsed = parse_unit_path(unit_path)
            if not unit_path or not str(unit_path).strip():
                stats["empty_unit"] += 1

            values.update(parsed)
            values.update(
                {
                    "source_file": source_file,
                    "source_sheet": ws.title,
                    "source_row": row_idx,
                    "status": "待测试",
                }
            )
            conn.execute(UPSERT_SQL, values)
            sheet_count += 1

        stats["sheets"][ws.title] = sheet_count
        stats["total"] += sheet_count

    conn.commit()
    return stats


def rebuild_db(conn):
    """清空设备表并重建 Schema，用于按最新台账全量重构数据库。

    仅重建 devices 表（台账数据来源），保留 unit_tags 等用户维护的表。
    """
    conn.execute("DROP TABLE IF EXISTS devices")
    conn.executescript(SCHEMA)
    conn.commit()


def main():
    parser = argparse.ArgumentParser(description="将台账 xlsx 导入 SQLite 数据库")
    parser.add_argument("xlsx", help="台账 Excel 文件路径")
    parser.add_argument("--db", default=None, help="数据库路径（默认 data/equipment.db）")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="先清空设备表再导入，用于按最新台账全量重构数据库",
    )
    args = parser.parse_args()

    conn = get_connection(args.db)
    if args.rebuild:
        rebuild_db(conn)
    stats = ingest_xlsx(args.xlsx, conn)
    print(f"导入完成：共 {stats['total']} 条记录，空使用单位 {stats['empty_unit']} 条")
    for sheet, count in stats["sheets"].items():
        print(f"  - {sheet}: {count} 条")
    conn.close()


if __name__ == "__main__":
    main()
