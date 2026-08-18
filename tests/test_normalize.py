# -*- coding: utf-8 -*-
"""使用单位归一化与风险村清洗规则测试。"""

import unittest

from equipment.normalize import (
    clean_risk_district,
    clean_risk_town,
    clean_risk_village_name,
    cn_to_arabic,
    normalize_unit_name,
    parse_unit_path,
)


class TestNormalizeUnitName(unittest.TestCase):
    def test_village_committee_normalization(self):
        self.assertEqual(normalize_unit_name("刘庄村村民委员会"), "刘庄村村委会")
        self.assertEqual(normalize_unit_name("凌沿庄村委会"), "凌沿庄村委会")


class TestParseUnitPath(unittest.TestCase):
    def test_village_path(self):
        r = parse_unit_path("天津市/业务通讯录/各区/宝坻区/大钟庄镇/凌沿庄村委会")
        self.assertEqual(r["org_branch"], "业务通讯录")
        self.assertEqual(r["org_category"], "各区")
        self.assertEqual(r["region_category"], "行政区划")
        self.assertEqual(r["district"], "宝坻区")
        self.assertEqual(r["town"], "大钟庄镇")
        self.assertEqual(r["unit_name"], "凌沿庄村委会")

    def test_district_bureau_department(self):
        r = parse_unit_path("天津市/应急管理/市应急管理局/北辰区应急管理局/应急指挥调度科")
        self.assertEqual(r["org_branch"], "应急管理")
        self.assertEqual(r["org_category"], "市应急管理局")
        self.assertEqual(r["region_category"], "区应急管理局")
        self.assertEqual(r["district"], "北辰区")
        self.assertEqual(r["unit_name"], "应急指挥调度科")
        self.assertEqual(r["unit_parent"], "北辰区应急管理局")

    def test_town_only(self):
        r = parse_unit_path("天津市/业务通讯录/各区/宝坻区/史各庄镇")
        self.assertEqual(r["town"], "史各庄镇")
        self.assertIsNone(r["unit_name"])

    def test_street(self):
        r = parse_unit_path("天津市/业务通讯录/各区/西青区/西营门街")
        self.assertEqual(r["town"], "西营门街")

    def test_municipal_bureau(self):
        r = parse_unit_path("天津市/应急管理/市应急管理局")
        self.assertEqual(r["org_category"], "市应急管理局")
        self.assertEqual(r["region_category"], "市级委办局")
        self.assertIsNone(r["district"])
        self.assertIsNone(r["unit_name"])

    def test_enterprise(self):
        r = parse_unit_path("天津市/业务通讯录/企事业单位/中国电信天津分公司/电信静海分公司")
        self.assertEqual(r["org_category"], "企事业单位")
        self.assertEqual(r["region_category"], "其他")
        self.assertEqual(r["unit_name"], "电信静海分公司")
        self.assertEqual(r["unit_parent"], "中国电信天津分公司")

    def test_empty_path(self):
        r = parse_unit_path("")
        self.assertEqual(r["unit_path"], "")
        self.assertEqual(r["region_category"], "待定")
        self.assertIsNone(r["district"])

    def test_region_categories(self):
        # 横向委办局（含市级消防等）归市级委办局
        r = parse_unit_path("天津市/业务通讯录/横向委办局/天津市消防救援总队")
        self.assertEqual(r["region_category"], "市级委办局")
        # 区应急管理局内设执法大队仍归区应急管理局
        r = parse_unit_path(
            "天津市/应急管理/市应急管理局/滨海新区应急管理局/"
            "滨海新区应急管理综合行政执法支队/古林街道应急管理执法大队"
        )
        self.assertEqual(r["region_category"], "区应急管理局")
        # 社会侧归其他
        r = parse_unit_path("天津市/业务通讯录/社会侧/红十字会")
        self.assertEqual(r["region_category"], "其他")


class TestRiskClean(unittest.TestCase):
    """风险村台账清洗规则。"""

    def test_clean_district(self):
        self.assertEqual(clean_risk_district("西青区（22）"), "西青区")
        self.assertEqual(clean_risk_district("蓟州区\n（124）"), "蓟州区")

    def test_clean_town_alias(self):
        self.assertEqual(clean_risk_town("西龙虎（6）"), "西龙虎峪镇")
        self.assertEqual(clean_risk_town("孙各庄（6）"), "孙各庄满族乡")
        self.assertEqual(clean_risk_town("西营门街（1）"), "西营门街道")
        self.assertEqual(clean_risk_town("杨柳青镇（14）"), "杨柳青镇")

    def test_cn_to_arabic(self):
        self.assertEqual(cn_to_arabic("拾叁街村"), "13街村")
        self.assertEqual(cn_to_arabic("柒街村"), "7街村")
        self.assertEqual(cn_to_arabic("十三街村委会"), "13街村委会")

    def test_clean_village_name(self):
        self.assertEqual(clean_risk_village_name("拾叁街村"), "13街村")
        self.assertEqual(clean_risk_village_name("粱后庄村"), "粱后庄村")


if __name__ == "__main__":
    unittest.main()
