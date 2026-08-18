# 智能体（Agent）协作规则与项目要求

> [!IMPORTANT]
> **核心约束：全中文沟通**
> 1. 本项目的所有对外沟通、输出、技术文档、项目日志及代码注释均必须使用 **中文**。
> 2. **每次启动新对话或新任务时，AI 智能体必须主动读取本文件 (`AGENTS.md`)**，以自动对齐项目上下文与基本约束。
> 3. **【快速对齐指引】**：读取本文件后，AI 智能体必须立即主动依次读取隐藏目录内的 `.project/CURRENT_STATE.yaml`（当前状态快照）与 `.project/WORK_PLAN.md`（当前工作计划），快速获取项目最新状态与下一步开发进度。

## 1. 项目边界与技术栈
- **核心环境**：Python 3.12+，本地运行
- **服务结构**：
  - 核心入口：`equipment/cli.py`（查询与导出命令行工具）
  - 台账导入：`equipment/ingest.py`（xlsx → SQLite）
  - 单位归一化：`equipment/normalize.py`（使用单位路径解析与清洗）
  - 数据库访问：`equipment/db.py`（SQLite Schema 与连接）
  - AI 查询规范：`docs/skill-src/equipment-query/SKILL.md`（Trae、Workbuddy、Codex 收到台账查询、汇总或导出需求时优先读取）
- **数据存储**：本地 SQLite 数据库（`data/equipment.db`），不依赖外部服务
- **网络与环境变量规则**：当前阶段纯本地运行，不访问外网。涉密数据（设备联系人、电话号码等）一律不允许写入任何外部服务；后续接入外部 AI 时也必须先脱敏。禁止将敏感数据提交至 Git 仓库。
- **仓库数据边界**：Git 仓库仅允许纳入已确认脱敏的预置数据库 `data/equipment.db`；原始资料、根目录统计表与导出成果一律不入库。

## 2. 项目对齐系统目录
除本文件外，其余对齐系统的文件均存放在根目录的 `.project/` 隐藏目录下：
- 快照：`.project/CURRENT_STATE.yaml`
- 计划：`.project/WORK_PLAN.md`
- 日志：`.project/PROJECT_LOG.md`
- 决策历史：`.project/decision-log/`
- 技术文档：`.project/docs/`

## 3. 读写与修改规范
- **配置防泄漏**：绝对禁止将敏感配置文件或涉密数据提交至仓库。
- **注释与修改安全**：修改代码时必须保留无关的代码注释与说明。
- **架构变更**：重大重构或数据库 Schema 变更，必须先在 `.project/decision-log/` 中创建记录并与用户对齐。

## 4. 工作流规范
1. **对齐**：与用户充分讨论，了解改动目标。
2. **计划**：对于非微调类任务，必须先创建/更新实施计划文档并取得用户批准。
3. **执行**：按计划有序改动，每次实质性推进后，需更新 `.project/PROJECT_LOG.md`。
4. **验证**：修改代码后应在本地或测试环境中运行验证，确认无报错日志。
5. **自动 Git 提交**：若用户在对话中明确表达修改无误（例如回复“没有问题”、“确认”、“通过”、“OK”等），智能体应主动执行 `git add` 与 `git commit`（提交信息需简明扼要说明修改内容），随后主动询问用户是否需要执行 `git push`。
6. **自动版本管理**：在每次对话的开发/修改任务完成后，智能体应主动分析是否需要修改版本号（采用 x.y.z 格式，其中 x 代表重大更新，y 代表小更新，z 是 bug 修复）。如果需要，应直接更新 `.project/CURRENT_STATE.yaml` 中的 `current_version`、`README.md` 及其他相关文件中的版本号，并在回复中对用户进行反馈说明。
7. **AI 助手任务触发**：收到“查询台账、汇总、导出装备明细、核对口径”类任务时，先读取 `docs/skill-src/equipment-query/SKILL.md`；日常查询使用预置库 `data/equipment.db`，不要手工修改 SQLite 数据。
