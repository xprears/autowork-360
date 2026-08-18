# -*- coding: utf-8 -*-
"""按范围查询台账并支持导出 Excel。"""

import argparse
from pathlib import Path

import openpyxl

from equipment.db import DEFAULT_DB, get_connection
from equipment.normalize import REGION_CATEGORIES

# 明细导出的中文表头
DETAIL_COLUMNS = [
    ("id", "ID"),
    ("device_type", "设备类型"),
    ("device_name", "设备名称"),
    ("brand", "品牌"),
    ("model", "设备型号"),
    ("satellite_info", "卫星网络信息"),
    ("unit_path", "使用单位（原始）"),
    ("org_branch", "机构大类"),
    ("org_category", "机构分类"),
    ("region_category", "区划分类"),
    ("district", "区"),
    ("town", "街镇"),
    ("unit_name", "单位"),
    ("unit_parent", "上级单位"),
    ("status", "测试状态"),
    ("last_test_date", "最近测试日期"),
    ("test_round", "测试批次"),
    ("fault_desc", "故障描述"),
    ("repair_status", "维修状态"),
    ("source_file", "来源文件"),
    ("source_sheet", "来源Sheet"),
    ("source_row", "来源行"),
]


def build_where(args):
    """根据命令行过滤条件构建 WHERE 子句与参数。"""
    conds, params = [], []
    mappings = [
        ("district", "district"),
        ("town", "town"),
        ("device_type", "device_type"),
        ("status", "status"),
        ("org_branch", "org_branch"),
        ("org_category", "org_category"),
        ("region_category", "region_category"),
    ]
    for arg, col in mappings:
        val = getattr(args, arg)
        if val:
            conds.append(f"{col} = ?")
            params.append(val)
    if getattr(args, "unit", None):
        conds.append("unit_name LIKE ?")
        params.append(f"%{args.unit}%")
    if getattr(args, "tag", None):
        conds.append("unit_name IN (SELECT unit_name FROM unit_tags WHERE tag = ?)")
        params.append(args.tag)
    risk_cond = (
        "EXISTS ("
        "SELECT 1 FROM risk_villages rv "
        "WHERE rv.district = devices.district AND rv.town = devices.town "
        "AND (COALESCE(devices.unit_name, '') = rv.village_name "
        "OR (COALESCE(devices.unit_name, '') = '' AND devices.town = rv.village_name))"
        ")"
    )
    if getattr(args, "risk_only", False):
        conds.append(risk_cond)
    if getattr(args, "exclude_risk", False):
        conds.append(f"NOT {risk_cond}")
    where = " WHERE " + " AND ".join(conds) if conds else ""
    return where, params


def query_summary(conn, args):
    """按设备类型与状态汇总数量。"""
    where, params = build_where(args)
    sql = f"""
        SELECT device_type, status, COUNT(*) AS cnt
        FROM devices{where}
        GROUP BY device_type, status
        ORDER BY device_type, status
    """
    return conn.execute(sql, params).fetchall()


def query_detail(conn, args):
    """查询明细记录。"""
    where, params = build_where(args)
    sql = f"""
        SELECT {", ".join(c for c, _ in DETAIL_COLUMNS)}
        FROM devices{where}
        ORDER BY device_type, district, town, unit_name, unit_path
    """
    if args.limit:
        sql += f" LIMIT {int(args.limit)}"
    return conn.execute(sql, params).fetchall()


def query_risk_list(conn):
    """查询风险村清单（区/街镇/村名/来源行）。"""
    return conn.execute(
        """
        SELECT district, town, village_name, source_row
        FROM risk_villages
        ORDER BY district, town, village_name
        """
    ).fetchall()


def query_benchmark_summary(conn, district=None, device_type=None, metric=None):
    """查询基准统计表（设备类型 + 统计单位 + 口径）。"""
    conds, params = [], []
    if district:
        conds.append("district = ?")
        params.append(district)
    if device_type:
        conds.append("device_type = ?")
        params.append(device_type)
    if metric:
        conds.append("metric = ?")
        params.append(metric)
    where = " WHERE " + " AND ".join(conds) if conds else ""
    sql = f"""
        SELECT device_type, district, metric, count AS cnt
        FROM equipment_benchmark{where}
        ORDER BY device_type, district, metric
    """
    return conn.execute(sql, params).fetchall()


def print_risk_list(rows):
    """终端打印风险村清单。"""
    if not rows:
        print("风险村表为空")
        return
    print(f"{'区':<8}{'街镇':<14}{'村/单位':<18}{'来源行':>6}")
    print("-" * 48)
    for r in rows:
        print(
            f"{(r['district'] or ''):<8}{(r['town'] or ''):<14}"
            f"{(r['village_name'] or ''):<18}{(r['source_row'] or ''):>6}"
        )
    print("-" * 48)
    print(f"共 {len(rows)} 个风险村")


def print_summary(rows):
    """终端打印汇总表。"""
    if not rows:
        print("无匹配记录")
        return
    total = 0
    print(f"{'设备类型':<16}{'测试状态':<8}{'数量':>6}")
    print("-" * 32)
    for row in rows:
        total += row["cnt"]
        print(f"{row['device_type']:<16}{row['status']:<8}{row['cnt']:>6}")
    print("-" * 32)
    print(f"{'合计':<24}{total:>6}")


def print_benchmark_summary(rows):
    """终端打印基准统计表。"""
    if not rows:
        print("基准汇总表无匹配记录")
        return
    total = 0
    print(f"{'设备类型':<16}{'统计单位/区':<12}{'口径':<8}{'数量':>6}")
    print("-" * 46)
    for row in rows:
        total += row["cnt"]
        print(
            f"{row['device_type']:<16}{row['district']:<12}"
            f"{row['metric']:<8}{row['cnt']:>6}"
        )
    print("-" * 46)
    print(f"{'合计':<36}{total:>6}")


def print_detail(rows):
    """终端打印明细（精简列）。"""
    if not rows:
        print("无匹配记录")
        return
    print(f"{'设备类型':<14}{'区':<8}{'街镇':<12}{'单位':<16}{'状态':<6}{'来源':<12}")
    print("-" * 70)
    for r in rows:
        print(
            f"{r['device_type']:<14}{(r['district'] or ''):<8}"
            f"{(r['town'] or ''):<12}{(r['unit_name'] or ''):<16}"
            f"{(r['status'] or ''):<6}{(r['source_file'] or ''):<12}"
        )


def export_excel(conn, args, out_path):
    """将汇总与明细导出为 Excel 工作簿。"""
    summary_rows = query_summary(conn, args)
    detail_rows = query_detail(conn, args)

    wb = openpyxl.Workbook()

    ws_summary = wb.active
    ws_summary.title = "汇总"
    ws_summary.append(["设备类型", "测试状态", "数量"])
    total = 0
    for row in summary_rows:
        ws_summary.append([row["device_type"], row["status"], row["cnt"]])
        total += row["cnt"]
    ws_summary.append(["合计", "", total])

    ws_detail = wb.create_sheet("明细")
    ws_detail.append([label for _, label in DETAIL_COLUMNS])
    for row in detail_rows:
        ws_detail.append([row[col] for col, _ in DETAIL_COLUMNS])

    wb.save(out_path)
    return len(detail_rows)


def main():
    parser = argparse.ArgumentParser(
        description="按范围查询装备台账，支持汇总与导出 Excel"
    )
    parser.add_argument("--db", default=None, help=f"数据库路径（默认 {DEFAULT_DB}）")
    parser.add_argument("--district", help="区（如 宝坻区）")
    parser.add_argument("--town", help="街镇（如 大钟庄镇）")
    parser.add_argument("--device-type", help="设备类型（如 北斗终端）")
    parser.add_argument("--status", help="测试状态（待测试/正常/故障/维修中/已修复）")
    parser.add_argument("--org-branch", help="机构大类（业务通讯录/应急管理）")
    parser.add_argument("--org-category", help="机构分类（各区/横向委办局/企事业单位/社会侧/市应急管理局）")
    parser.add_argument(
        "--region-category",
        choices=REGION_CATEGORIES,
        help="区划分类（市级委办局/区应急管理局/行政区划/其他/待定）",
    )
    parser.add_argument("--unit", help="单位名称关键词（如 凌沿庄）")
    parser.add_argument("--tag", help="按标签过滤（如 风险村，标签表需先维护）")
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="按《应急装备数量统计（内部）》基准汇总表查询（设备类型+区+口径）",
    )
    parser.add_argument(
        "--metric",
        choices=["总数", "市局配发", "区局自购", "配置总数", "可用数量"],
        help="基准口径（仅与 --benchmark 一起使用）",
    )
    risk_group = parser.add_mutually_exclusive_group()
    risk_group.add_argument("--risk-only", action="store_true", help="仅查询风险村（以 risk_villages 表为准）")
    risk_group.add_argument("--exclude-risk", action="store_true", help="排除风险村，查询其余范围")
    parser.add_argument("--risk-list", action="store_true", help="列出风险村清单")
    parser.add_argument("--summary", action="store_true", help="只输出汇总数量")
    parser.add_argument("--detail", action="store_true", help="同时输出明细")
    parser.add_argument("--limit", type=int, default=None, help="明细最大条数")
    parser.add_argument("--export", help="导出 Excel 文件路径")
    args = parser.parse_args()

    conn = get_connection(args.db)

    if args.benchmark:
        print_benchmark_summary(
            query_benchmark_summary(
                conn,
                district=args.district,
                device_type=args.device_type,
                metric=args.metric,
            )
        )
        conn.close()
        return

    if args.risk_list:
        print_risk_list(query_risk_list(conn))
        conn.close()
        return

    if not args.summary and not args.detail and not args.export:
        args.summary = True

    if args.summary:
        print_summary(query_summary(conn, args))
    if args.detail or (args.export and not args.summary):
        print_detail(query_detail(conn, args))
    if args.export:
        count = export_excel(conn, args, args.export)
        print(f"已导出 Excel：{args.export}（明细 {count} 条）")

    conn.close()


if __name__ == "__main__":
    main()
