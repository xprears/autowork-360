# -*- coding: utf-8 -*-
"""台账导入与查询冒烟测试。"""

import argparse
import tempfile
import unittest
from pathlib import Path

import openpyxl

from equipment.db import get_connection
from equipment.ingest import ingest_xlsx, rebuild_db
from equipment.cli import query_detail


class TestIngest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = get_connection(Path(self.tmp.name) / "test.db")

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def _make_xlsx(self, path):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "北斗终端"
        ws.append(["序号", "*设备类型", "*使用单位"])
        ws.append([1, "北斗终端", "天津市/业务通讯录/各区/宝坻区/大钟庄镇/凌沿庄村委会"])
        ws.append([2, "北斗终端", "天津市/业务通讯录/各区/宝坻区/大钟庄镇/刘庄村村民委员会"])
        ws2 = wb.create_sheet("指挥车")
        ws2.append(["序号", "*设备类型", "*设备名称", "品牌", "设备型号", "卫星网络信息", "*使用单位"])
        ws2.append([1, "指挥车", "静海区通信指挥车", "考斯特", None, None,
                    "天津市/应急管理/市应急管理局/静海区应急管理局"])
        wb.save(path)

    def test_ingest_and_query(self):
        xlsx = Path(self.tmp.name) / "台账.xlsx"
        self._make_xlsx(xlsx)
        stats = ingest_xlsx(xlsx, self.db)
        self.assertEqual(stats["total"], 3)

        rows = self.db.execute(
            "SELECT * FROM devices WHERE district = '宝坻区' ORDER BY unit_name"
        ).fetchall()
        self.assertEqual(len(rows), 2)
        # 村民委员会 已归一化为 村委会
        self.assertEqual(rows[1]["unit_name"], "刘庄村村委会")
        # 属地街镇/村 归行政区划
        self.assertEqual(rows[0]["region_category"], "行政区划")

        rows = self.db.execute(
            "SELECT * FROM devices WHERE device_type = '指挥车'"
        ).fetchall()
        self.assertEqual(rows[0]["district"], "静海区")
        self.assertEqual(rows[0]["unit_name"], "静海区应急管理局")
        self.assertEqual(rows[0]["region_category"], "区应急管理局")

    def test_query_by_region_category(self):
        xlsx = Path(self.tmp.name) / "台账.xlsx"
        self._make_xlsx(xlsx)
        ingest_xlsx(xlsx, self.db)
        args = argparse.Namespace(
            region_category="区应急管理局",
            district=None,
            town=None,
            device_type=None,
            status=None,
            org_branch=None,
            org_category=None,
            unit=None,
            tag=None,
            risk_only=False,
            exclude_risk=False,
            limit=None,
        )
        rows = query_detail(self.db, args)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["district"], "静海区")

    def test_reingest_no_duplicate(self):
        xlsx = Path(self.tmp.name) / "台账.xlsx"
        self._make_xlsx(xlsx)
        ingest_xlsx(xlsx, self.db)
        ingest_xlsx(xlsx, self.db)
        count = self.db.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
        self.assertEqual(count, 3)

    def test_rebuild_clears_devices(self):
        xlsx = Path(self.tmp.name) / "台账.xlsx"
        self._make_xlsx(xlsx)
        ingest_xlsx(xlsx, self.db)
        rebuild_db(self.db)
        count = self.db.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
        self.assertEqual(count, 0)
        # 重建后可再次正常导入
        stats = ingest_xlsx(xlsx, self.db)
        self.assertEqual(stats["total"], 3)


if __name__ == "__main__":
    unittest.main()
