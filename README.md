# 应急通信装备台账管理与测试支撑系统

面向市、区、街镇、村多级应急通信装备测试场景的本地台账管理与测试支撑系统：将分散的 Excel 台账导入本地 SQLite 全量数据库，按区、街镇、设备类型、状态等条件快速查询、汇总并导出，为后续测试回传对账、报告生成与外部 AI 查询提供统一数据底座。

## 设计初衷

市、区、街镇、村各级通信装备测试任务中存在以下痛点：

- **台账分散**：装备数据分散在多个 Excel 文件中，人工翻阅多个表格才能汇总；
- **查询困难**：领导常需按特定范围（如某街镇、某类设备、风险村）查询装备情况，缺乏统一检索手段；
- **信息不对称**：测试状态、故障与维修信息回传繁琐，逐级收集效率低、重复工程多；
- **命名不规范**：使用单位路径层级不统一（如村民委员会/村委会混用），难以按区域统计。

因此，本项目以「本地化、零部署、可演进」为原则，构建一套以 SQLite 为数据核心的台账管理工具，先解决「台账入库 + 按范围查询」的核心问题，再逐步扩展测试对账、报告生成与外部 AI 能力。

## 设计需求与阶段规划

| 阶段 | 内容 | 状态 |
|---|---|---|
| 阶段 A | 台账自动汇总与按范围查询（导入、归一化、查询、导出） | ✅ 已完成 |
| 阶段 B | 接入测试回传数据，自动对账并更新设备测试状态 | ⏳ 待确认 |
| 阶段 C | 按模板生成测试报告与特定范围装备情况报告 | ⏳ 部分启动（模板与 skill 已就绪，自动生成待确认） |
| 阶段 D | 接入外部 AI（仅脱敏数据），支持自然语言查询 | ⏳ 规划中 |
| 阶段 E | 完全本地化部署（如内网 Web 页面） | ⏳ 规划中 |

## 文件夹结构

```text
自动化运维项目/
├── AGENTS.md              # 智能体协作规则与项目约束
├── README.md              # 项目总览与快速开始
├── requirements.txt       # Python 依赖清单
├── .gitignore             # 忽略本地数据库、原始资料、导出成果
├── .project/              # 项目对齐系统（快照/计划/日志/决策/技术文档）
├── equipment/             # 核心源码包（阶段 A 功能）
├── data/                  # 本地数据目录（SQLite 数据库）
├── sources/               # 原始资料输入（设备台账/测试报告/进度资料）
├── reports/               # 导出与生成成果（Excel、测试报告）
├── scripts/               # 辅助脚本（阶段 B/C 预留）
├── tests/                 # 单元测试
└── docs/                  # 公开技术文档
```

各目录职责与设计说明详见 [docs/folder-structure.md](docs/folder-structure.md)。

## 快速开始

环境要求：Python 3.12+，首次使用先安装依赖。

```bash
# 1. 安装依赖
python3 -m pip install -r requirements.txt

# 2. 导入台账（将 xlsx 导入本地 SQLite 数据库）
python3 -m equipment.ingest sources/设备台账/全量设备.xlsx

# 2.1 有新台账文件时全量重构数据库（先清空设备表再导入）
python3 -m equipment.ingest sources/设备台账/全量设备.xlsx --rebuild

# 3. 导入风险村台账（风险村是全量台账的特殊范围，189 个村）
python3 -m equipment.risk_ingest 通信保障重点村应急通信方式统计V3.xlsx

# 3.1 风险村台账更新后重建（先清空风险村表再导入）
python3 -m equipment.risk_ingest 通信保障重点村应急通信方式统计V3.xlsx --rebuild

# 3.2 导入《应急装备数量统计（内部）》基准汇总（无人机等按“设备类型+区”入库）
python3 -m equipment.benchmark_ingest 应急装备数量统计（内部）-20260722.xlsx --rebuild

# 3.3 查询基准汇总：无人机按区分布、370MHz 配发/自购/配置/可用
python3 -m equipment.cli --benchmark --device-type 无人机
python3 -m equipment.cli --benchmark --device-type 370MHz手持终端

# 4. 查询：宝坻区全部设备汇总
python3 -m equipment.cli --district 宝坻区 --summary

# 5. 查询：仅风险村设备 / 排除风险村的其余范围
python3 -m equipment.cli --risk-only --summary
python3 -m equipment.cli --exclude-risk --summary

# 6. 列出风险村清单（区/街镇/村名/来源行）
python3 -m equipment.cli --risk-list

# 7. 查询：按区划分类统计（市级委办局/区应急管理局/行政区划/其他/待定）
python3 -m equipment.cli --region-category 区应急管理局 --summary

# 8. 查询：大钟庄镇北斗终端明细并导出 Excel 到 reports/
python3 -m equipment.cli --district 宝坻区 --town 大钟庄镇 --device-type 北斗终端 --export reports/结果.xlsx
```

详细参数见 `python3 -m equipment.cli --help`。

## 固定模板与测试简报生成

- 正式测试报告模板：`sources/测试报告/应急通信装备测试报告模板.docx`，黄色高亮即待填字段；
- 日报、周报、测试进度模板：`docs/templates/`，使用说明见 `docs/测试简报模板说明.md`；
- 配套 skill：`emergency-test-reports` 已安装至 `~/.codex/skills/`，对话中直接说“生成日报/周报/测试进度”即可触发；
- 重新安装 skill：`python3 scripts/install_emergency_test_reports_skill.py`。

## 技术栈

Python 3.12+、SQLite、openpyxl（导入/导出 Excel）、pytest（测试）。

## 数据与安全

- 所有数据本地存储，不访问外网；
- 涉密数据（联系人、电话号码等）一律不录入系统；后续接入外部 AI 前必须脱敏；
- 本地数据库（`data/`）、原始资料（`sources/`）、导出成果（`reports/`）默认不进入 Git 仓库，请自行保管。

## 版本

当前版本：0.7.0（固化日报、周报、测试进度三份 Markdown 模板，并创建 emergency-test-reports skill，支撑后续自动化生成测试简报）。
