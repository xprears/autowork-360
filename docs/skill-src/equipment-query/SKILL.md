---
name: equipment-query
description: 查询、汇总和导出应急通信装备本地 SQLite 台账时使用。适用于按区、街镇、设备类型、状态、风险村、区划分类、单位关键词或基准口径统计装备数量，也适用于将查询结果导出为 Excel 明细。当 Trae、Workbuddy 或 Codex 需要在本项目内处理台账查询、汇总、口径核对或导出任务时触发。
---

# 设备台账查询

## 工作前提

1. 以项目根目录为工作目录。
2. 优先使用预置数据库 `data/equipment.db`；若文件缺失，先检查 `sources/设备台账/全量设备.xlsx` 是否存在，存在时执行：

```bash
python3 -m pip install -r requirements.txt
python3 -m equipment.ingest sources/设备台账/全量设备.xlsx --rebuild
```

   若数据库与原始台账均不存在，先提示用户提供文件或恢复预置库，不要自行猜测数据。

3. CLI 报 `ModuleNotFoundError` 时，先安装依赖。
4. 不直接修改 SQLite；查询和导出通过 `python3 -m equipment.cli` 完成。

## 查询流程

1. 确认任务类型：汇总数量、明细、风险村、区划分类、基准口径或 Excel 导出。
2. 用 CLI 查询，并按需组合过滤参数。
3. 汇总优先输出设备类型和状态；导出文件写入 `reports/` 或用户指定路径。

## 常用示例

```bash
# 宝坻区汇总
python3 -m equipment.cli --district 宝坻区 --summary

# 大钟庄镇北斗终端明细并导出
python3 -m equipment.cli --district 宝坻区 --town 大钟庄镇 --device-type 北斗终端 --export reports/结果.xlsx

# 仅风险村或排除风险村
python3 -m equipment.cli --risk-only --summary
python3 -m equipment.cli --exclude-risk --summary

# 区划分类
python3 -m equipment.cli --region-category 区应急管理局 --summary

# 基准汇总（数量口径，如无人机）
python3 -m equipment.cli --benchmark --device-type 无人机
```

## 参数与数据说明

- 完整 CLI 参数见 `references/cli.md`；参数不确定时先运行 `python3 -m equipment.cli --help`。
- 表结构与口径注意点见 `references/data.md`，仅在核对字段、风险村差异或基准口径时读取。
- 风险村以 `risk_villages` 表为准；与全量台账存在已知差异时，按用户已确认口径说明。

## 安全要求

- 仅本地运行，不访问外网。
- 不读取或提交 `sources/`、根目录 `*.xlsx`、`reports/` 中的敏感内容。
- 不把 `data/equipment.db` 或查询结果复制到外部服务；若要提交 Git，只能提交已确认脱敏的预置库并获得用户同意。
