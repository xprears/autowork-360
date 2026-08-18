# -*- coding: utf-8 -*-
"""风险村台账导入与范围查询测试。"""

import argparse
import tempfile
import unittest
from pathlib import Path

import openpyxl

from equipment.db import get_connection
from equipment.risk_ingest import ingest_risk_xlsx
from equipment.cli import query_detail


class TestRiskIngest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = get_connection(Path(self.tmp.name) / "test.db")
        self._seed_devices()

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _seed_devices(self):
        rows = [
            ("西青区", "杨柳青镇", "十三街村委会"),
            ("西青区", "杨柳青镇", "七街村委会"),
            ("蓟州区", "西龙虎峪镇", "柳官庄村委会"),
            ("蓟州区", "孙各庄满族乡", "丈烟台村委会"),
            ("宁河区", "桥北街道", "大薄前村委会"),
            ("河东区", "天津铁厂街道", ""),
        ]
        for district, town, unit_name in rows:
            self.db.execute(
                """
                INSERT INTO devices (device_type, unit_path, district, town, unit_name)
                VALUES ('北斗终端', ?, ?, ?, ?)
                """,
                (
                    f"天津市/业务通讯录/各区/{district}/{town}/{unit_name}",
                    district,
                    town,
                    unit_name or None,
                ),
            )
        self.db.commit()

    def _make_risk_xlsx(self, path):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "风险村台账"
        ws.append(["区", "街镇", "通信保障重点村名称", "风险类型", "联系人"])
        # 区/街镇为合并单元格风格：仅每组首行有值
        ws.append(["西青区（22）", "杨柳青镇（14）", "拾叁街村", "洪涝", "甲"])
        ws.append([None, None, "柒街村", "洪涝", "乙"])
        ws.append(["蓟州区（124）", "西龙虎（6）", "柳官庄村", "夹边沟", "丙"])
        ws.append([None, "孙各庄（6）", "丈烟台村", "夹边沟", "丁"])
        ws.append(["宁河区（26）", "桥北街道（4）", "薄前村", "洪涝", "戊"])
        ws.append(["河东区（1）", "天津铁厂街道（1）", "天津铁厂街道", "边远", "己"])
        ws.append(["宝坻区（15）", "无此镇（1）", "无此村", "洪涝", "庚"])
        wb.save(path)

    def test_ingest_risk_xlsx(self):
        xlsx = Path(self.tmp.name) / "风险村台账.xlsx"
        self._make_risk_xlsx(xlsx)
        stats = ingest_risk_xlsx(xlsx, self.db)

        # 6 个可匹配村入库，1 个失败
        self.assertEqual(stats["total"], 6)
        self.assertEqual(len(stats["failed"]), 1)
        self.assertEqual(stats["matched_units"], 6)

        rows = self.db.execute(
            "SELECT district, town, village_name, source_row FROM risk_villages ORDER BY district, town"
        ).fetchall()
        self.assertEqual(len(rows), 6)

        # 街镇别名：西龙虎 -> 西龙虎峪镇
        liuguan = [r for r in rows if r["village_name"] == "柳官庄村委会"][0]
        self.assertEqual(liuguan["town"], "西龙虎峪镇")

        # 加字别名：薄前村 -> 大薄前村委会
        boqian = [r for r in rows if r["village_name"] == "大薄前村委会"][0]
        self.assertEqual(boqian["town"], "桥北街道")

        # 街镇级特例：天津铁厂街道
        tiechang = [r for r in rows if r["village_name"] == "天津铁厂街道"][0]
        self.assertEqual(tiechang["town"], "天津铁厂街道")

        # 杨柳青街村：中文数字已转阿拉伯
        self.assertIn("十三街村委会", {r["village_name"] for r in rows})
        self.assertIn("七街村委会", {r["village_name"] for r in rows})

        # 别名表保存台账原文
        aliases = self.db.execute(
            "SELECT alias_town, alias_name FROM risk_village_aliases ORDER BY alias_name"
        ).fetchall()
        alias_names = {a["alias_name"] for a in aliases}
        self.assertIn("拾叁街村", alias_names)
        self.assertIn("柒街村", alias_names)
        self.assertIn("薄前村", alias_names)
        self.assertIn("柳官庄村", alias_names)
        self.assertEqual(len(aliases), 6)

    def test_cli_risk_range_query(self):
        xlsx = Path(self.tmp.name) / "风险村台账.xlsx"
        self._make_risk_xlsx(xlsx)
        ingest_risk_xlsx(xlsx, self.db)

        def make_args(**kwargs):
            defaults = dict(
                district=None, town=None, device_type=None, status=None,
                org_branch=None, org_category=None, region_category=None,
                unit=None, tag=None,
                risk_only=False, exclude_risk=False, limit=None,
            )
            defaults.update(kwargs)
            return argparse.Namespace(**defaults)

        risk_rows = query_detail(self.db, make_args(risk_only=True))
        self.assertEqual(len(risk_rows), 6)

        non_risk_rows = query_detail(self.db, make_args(exclude_risk=True))
        self.assertEqual(len(non_risk_rows), 0)

        # 叠加区条件：仅风险村 + 西青区
        xq_risk = query_detail(self.db, make_args(risk_only=True, district="西青区"))
        self.assertEqual(len(xq_risk), 2)

    def test_reingest_no_duplicate(self):
        xlsx = Path(self.tmp.name) / "风险村台账.xlsx"
        self._make_risk_xlsx(xlsx)
        ingest_risk_xlsx(xlsx, self.db)
        ingest_risk_xlsx(xlsx, self.db)
        count = self.db.execute("SELECT COUNT(*) FROM risk_villages").fetchone()[0]
        self.assertEqual(count, 6)
        alias_count = self.db.execute("SELECT COUNT(*) FROM risk_village_aliases").fetchone()[0]
        self.assertEqual(alias_count, 6)


if __name__ == "__main__":
    unittest.main()
