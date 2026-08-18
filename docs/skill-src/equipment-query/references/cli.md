# CLI 参数速查

命令行入口：`python3 -m equipment.cli [参数]`。

## 过滤参数

- `--district 区名`：按区过滤，如 `宝坻区`。
- `--town 街镇名`：按街镇过滤，如 `大钟庄镇`。
- `--device-type 设备类型`：按设备类型过滤，如 `北斗终端`。
- `--status 状态`：按测试状态过滤，如 `待测试`、`正常`、`故障`、`维修中`、`已修复`。
- `--org-branch 机构大类`：如 `业务通讯录`、`应急管理`。
- `--org-category 机构分类`：如 `各区`、`横向委办局`。
- `--region-category 区划分类`：`市级委办局`、`区应急管理局`、`行政区划`、`其他`、`待定`。
- `--unit 关键词`：按单位名称关键词模糊匹配。
- `--tag 标签`：按 `unit_tags` 标签过滤。

## 风险村参数

- `--risk-only`：仅查风险村设备。
- `--exclude-risk`：排除风险村设备。
- `--risk-list`：列出风险村清单。

`--risk-only` 与 `--exclude-risk` 互斥。

## 基准汇总参数

- `--benchmark`：查询《应急装备数量统计（内部）》基准表。
- `--metric 口径`：`总数`、`市局配发`、`区局自购`、`配置总数`、`可用数量`。

`--metric` 仅在 `--benchmark` 模式生效。

## 输出参数

- 默认输出汇总。
- `--summary`：只输出汇总。
- `--detail`：同时输出明细。
- `--limit N`：限制明细行数。
- `--export 路径`：导出 Excel，通常写入 `reports/`。
- `--db 路径`：指定数据库，默认 `data/equipment.db`。

## 常用组合

```bash
# 宝坻区全部装备汇总
python3 -m equipment.cli --district 宝坻区 --summary

# 宝坻区大钟庄镇北斗终端明细并导出
python3 -m equipment.cli --district 宝坻区 --town 大钟庄镇 --device-type 北斗终端 --export reports/北斗明细.xlsx

# 全部风险村汇总
python3 -m equipment.cli --risk-only --summary

# 各区划分类汇总
python3 -m equipment.cli --region-category 区应急管理局 --summary

# 无人机基准分布
python3 -m equipment.cli --benchmark --device-type 无人机
```
