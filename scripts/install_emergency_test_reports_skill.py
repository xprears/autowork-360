#!/usr/bin/env python3
"""将应急通信测试简报 skill 安装到 Codex 的 skills 目录。"""

import argparse
import shutil
import sys
from pathlib import Path


SKILL_NAME = "emergency-test-reports"


def resolve_target(value):
    if value:
        return Path(value).expanduser() / SKILL_NAME
    home = Path.home()
    codex_home = Path(home / ".codex")
    return codex_home / "skills" / SKILL_NAME


def main():
    parser = argparse.ArgumentParser(description="安装应急通信测试简报 skill")
    parser.add_argument("--target", help="自定义 Codex skills 目录，默认 ~/.codex/skills")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    source_dir = project_root / "docs" / "skill-src" / SKILL_NAME
    target_dir = resolve_target(args.target)

    if not source_dir.is_dir():
        print(f"[错误] 未找到 skill 源目录：{source_dir}")
        return 1

    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, target_dir, dirs_exist_ok=True)
    print(f"[完成] 已安装 skill 至：{target_dir}")
    print("[提示] 重启 Codex 会话后，对话中说“生成日报/周报/测试进度”即可触发。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
