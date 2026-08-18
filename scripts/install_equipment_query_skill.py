#!/usr/bin/env python3
"""将设备台账查询 skill 安装到目标工具的 skills 目录。"""

import argparse
import shutil
import sys
from pathlib import Path


SKILL_NAME = "equipment-query"


def resolve_target(value):
    if value:
        return Path(value).expanduser() / SKILL_NAME
    home = Path.home()
    return home / ".codex" / "skills" / SKILL_NAME


def main():
    parser = argparse.ArgumentParser(description="安装设备台账查询 skill")
    parser.add_argument(
        "--target",
        help="目标工具的 skills 父目录，例如 ~/.codex/skills 或 Trae/Workbuddy 的 skills 目录；默认 ~/.codex/skills",
    )
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
    print("[提示] 若 Trae 或 Workbuddy 不支持该 skill 目录，可在项目 AGENTS.md 中直接引用 skill 源文件。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
