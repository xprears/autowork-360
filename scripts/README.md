# scripts —— 辅助脚本

本目录为阶段 B/C 辅助脚本预留，当前已有：

- 阶段 C：`make_test_report_template.py` 将《应急通信装备测试报告》原始 docx 转换为固定模板。
- 阶段 C：`install_emergency_test_reports_skill.py` 将 `docs/skill-src/emergency-test-reports` 安装为 Codex skill（默认安装至 `~/.codex/skills/emergency-test-reports`）。

规划落点：

- 阶段 B：测试回传数据导入与自动对账脚本；
- 阶段 C：基于模板的测试报告自动生成脚本；
- 阶段 D：脱敏与外部 AI 查询适配脚本。
