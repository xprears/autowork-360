# -*- coding: utf-8 -*-
"""使用单位路径的解析与归一化。"""

import re

# 天津市 16 个区白名单
TIANJIN_DISTRICTS = [
    "和平区", "河东区", "河西区", "南开区", "河北区", "红桥区",
    "东丽区", "西青区", "津南区", "北辰区", "武清区", "宝坻区",
    "滨海新区", "宁河区", "静海区", "蓟州区",
]

# 机构大类
BRANCHES = {"业务通讯录", "应急管理"}
# 业务通讯录下的机构分类
CATEGORIES = {"各区", "横向委办局", "企事业单位", "社会侧"}

# 区划分类口径
REGION_CATEGORIES = ["市级委办局", "区应急管理局", "行政区划", "其他", "待定"]

# 街镇后缀
TOWN_SUFFIXES = ("镇", "乡", "街道", "街")

# ---- 风险村清洗规则 ----

# 风险村台账 -> 全量台账的街镇标准名（台账内写法不统一）
RISK_TOWN_ALIASES = {
    "西龙虎": "西龙虎峪镇",
    "孙各庄": "孙各庄满族乡",
    "西营门街": "西营门街道",
}

# 台账原文村名 -> 全量台账标准单位名（加字/别字，无法由规则推导）
RISK_VILLAGE_ALIASES = {
    "薄前村": "大薄前村委会",
    "北胡村": "北胡庄村村委会",
    "于台村": "于台子村委会",
    "凌沿村": "凌沿庄村委会",
    "水泉村": "北水泉村委会",
    "车道峪村": "北车道峪村委会",
    "青池岭村": "青池岭沟村委会",
    "杨庄子村": "杨庄村委会",
    "粱后庄村": "梁后庄村委会",
}

# 中文数字（含大写）-> 数值
_CN_NUMS = {
    "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9,
    "壹": 1, "贰": 2, "叁": 3, "肆": 4, "伍": 5,
    "陆": 6, "柒": 7, "捌": 8, "玖": 9,
}

_COUNT_SUFFIX_RE = re.compile(r"[（(]\d+[）)]")


def _strip_count_suffix(name):
    """去掉街镇/区名称中的计数后缀，如 西青区（22） -> 西青区。"""
    return _COUNT_SUFFIX_RE.sub("", str(name or ""))


def _strip_ws(name):
    """去除换行、回车、半角/全角空格。"""
    return str(name or "").replace("\n", "").replace("\r", "").replace(" ", "").replace("\u3000", "")


def clean_risk_district(name):
    """清洗风险村台账的区名：去计数后缀与空白。"""
    return _strip_ws(_strip_count_suffix(name))


def clean_risk_town(name):
    """清洗风险村台账的街镇名：去计数后缀，并统一为全量台账标准写法。"""
    town = _strip_ws(_strip_count_suffix(name))
    return RISK_TOWN_ALIASES.get(town, town)


def cn_to_arabic(s):
    """把字符串中的中文数字（如 拾叁街村、柒街村）转为阿拉伯数字。"""
    def repl(m):
        text = m.group(0)
        # 统一大写数字 -> 小写
        unified = (
            text.replace("拾", "十")
            .replace("壹", "一").replace("贰", "二").replace("叁", "三")
            .replace("肆", "四").replace("伍", "五").replace("陆", "六")
            .replace("柒", "七").replace("捌", "八").replace("玖", "九")
        )
        if "十" not in unified:
            # 纯个位（如 七/三）
            return str(_CN_NUMS.get(unified, 0))
        # 支持 十X / X十 / X十Y 形式
        a, _, b = unified.partition("十")
        a_val = _CN_NUMS.get(a, 0)
        b_val = _CN_NUMS.get(b, 0)
        if a == "":
            return str(10 + b_val)
        return str(a_val * 10 + b_val)

    # 连续中文数字整体匹配，避免“拾叁”被拆成 10 和 3
    return re.sub(
        r"[零一二两三四五六七八九十壹贰叁肆伍陆柒捌玖拾]+",
        repl,
        s,
    )


def clean_risk_village_name(name):
    """清洗风险村台账的村名：去空白、中文数字转阿拉伯（如 拾叁街村 -> 十三街村）。"""
    return cn_to_arabic(_strip_ws(name))


def clean_risk_alias(name):
    """清洗台账原文别名：去计数后缀与空白，保留原文写法（如 拾叁街村、西龙虎）。"""
    return _strip_ws(_strip_count_suffix(name))


def normalize_unit_name(name):
    """归一化单位名：村民委员会统一为村委会，并去除多余空白。"""
    if not name:
        return None
    name = str(name).strip()
    if name.endswith("村民委员会"):
        name = name[: -len("村民委员会")] + "村委会"
    return name or None


def classify_region(parsed):
    """按区划口径归类使用单位。

    返回 REGION_CATEGORIES 之一：
    - 区应急管理局：路径含「区应急管理局」（含各区局内设机构、执法大队等）
    - 市级委办局：横向委办局，以及应急管理大类下除区应急管理局外的市局直属单位
    - 行政区划：业务通讯录·各区（区/街镇/村等属地单位）
    - 其他：企事业单位、社会侧
    - 待定：使用单位为空的记录等无法归类的记录
    """
    path = parsed.get("unit_path") or ""
    branch = parsed.get("org_branch")
    category = parsed.get("org_category")
    if "区应急管理局" in path:
        return "区应急管理局"
    if category == "横向委办局":
        return "市级委办局"
    if branch == "应急管理":
        return "市级委办局"
    if category == "各区":
        return "行政区划"
    if category in ("企事业单位", "社会侧"):
        return "其他"
    return "待定"


def _is_town_like(seg):
    """判断段落是否为街镇（镇/乡/街道/街 结尾）。"""
    return seg.endswith(TOWN_SUFFIXES)


def _is_structural(seg, district=None, town=None):
    """判断段落是否为结构段（市、机构大类、机构分类、区、街镇）。"""
    if seg in ("天津市",) or seg in BRANCHES or seg in CATEGORIES or seg == "市应急管理局":
        return True
    if district and seg == district:
        return True
    if town and seg == town:
        return True
    return False


def parse_unit_path(path):
    """将斜杠分隔的使用单位路径解析为结构化字段。

    返回字典：unit_path / org_branch / org_category / region_category /
    district / town / unit_name / unit_parent。原始路径完整保留，便于追溯。
    """
    empty = {
        "unit_path": "",
        "org_branch": None,
        "org_category": None,
        "region_category": "待定",
        "district": None,
        "town": None,
        "unit_name": None,
        "unit_parent": None,
    }
    if not path:
        return empty

    parts = [p.strip() for p in str(path).split("/") if p.strip()]
    if not parts:
        return empty

    result = dict(empty)
    result["unit_path"] = "/".join(parts)

    # 机构大类：一般为第 2 段
    if len(parts) >= 2:
        result["org_branch"] = parts[1]

    # 机构分类
    if result["org_branch"] == "业务通讯录":
        for seg in parts:
            if seg in CATEGORIES:
                result["org_category"] = seg
                break
    elif result["org_branch"] == "应急管理" and "市应急管理局" in parts:
        result["org_category"] = "市应急管理局"

    # 区：匹配 16 区白名单，支持“北辰区应急管理局”这类含区名的段
    for seg in parts:
        for d in TIANJIN_DISTRICTS:
            if seg == d or seg.startswith(d):
                result["district"] = d
                break
        if result["district"]:
            break

    # 街镇：镇/乡/街道/街 结尾的段
    for seg in parts:
        if _is_town_like(seg):
            result["town"] = seg
            break

    # 单位名：最后一个非结构段；村民委员会统一为村委会
    last = parts[-1]
    if not _is_structural(last, result["district"], result["town"]) and not _is_town_like(last):
        result["unit_name"] = normalize_unit_name(last)
        # 父级单位：往前找最近的非结构段（如 中国电信天津分公司/电信静海分公司）
        for seg in reversed(parts[:-1]):
            if not _is_structural(seg, result["district"], result["town"]) and not _is_town_like(seg):
                result["unit_parent"] = seg
                break

    result["region_category"] = classify_region(result)
    return result
