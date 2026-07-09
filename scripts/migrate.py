#!/usr/bin/env python3
"""目录结构迁移：diff 新旧 config.json，生成迁移计划，批量移动+更新链接。

用法:
    python scripts/migrate.py --domain 育儿 [--base-dir /path/to/knowledge]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

# 兼容中文 Windows（GBK 终端）：强制 UTF-8 输出，避免 emoji/中文 print 崩溃
if sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from config_loader import ConfigLoader
from file_ops import rename_dir, batch_update_links, count_files
from git_ops import GitOps


def diff_configs(old_config: dict, new_config: dict) -> List[dict]:
    """对比新旧配置，找出路径变更

    Returns:
        变更列表，每项含 logical_name, old_path, new_path
    """
    changes = []
    old_dirs = old_config.get("directories", {})
    new_dirs = new_config.get("directories", {})

    for name, new_dir in new_dirs.items():
        if name not in old_dirs:
            continue
        old_path = old_dirs[name]["path"]
        new_path = new_dir["path"]
        if old_path != new_path:
            changes.append({
                "logical_name": name,
                "old_path": old_path,
                "new_path": new_path,
                "file_count": 0,  # 后续填充
            })

    return changes


def generate_migration_plan(
    domain_dir: Path,
    changes: List[dict]
) -> str:
    """生成迁移计划文本"""
    lines = ["📋 迁移计划:\n"]

    total_files = 0
    for change in changes:
        old_dir = domain_dir / change["old_path"]
        new_dir = domain_dir / change["new_path"]
        file_count = count_files(old_dir)
        change["file_count"] = file_count
        total_files += file_count

        lines.append(f"  {change['logical_name']}:")
        lines.append(f"    {change['old_path']} → {change['new_path']}")
        lines.append(f"    文件数: {file_count}")
        lines.append("")

    lines.append(f"总计: {len(changes)} 个目录重命名, {total_files} 个文件移动")
    lines.append("同时更新所有 .md 文件中的 [[wikilink]] 链接")

    return "\n".join(lines)


def execute_migration(
    domain_dir: Path,
    changes: List[dict]
):
    """执行迁移"""
    for change in changes:
        old_dir = domain_dir / change["old_path"]
        new_dir = domain_dir / change["new_path"]

        if not old_dir.exists():
            print(f"⚠️  源目录不存在，跳过: {old_dir}")
            continue

        print(f"📦 {change['old_path']} → {change['new_path']}")
        rename_dir(old_dir, new_dir)

        # 更新所有 md 文件中的链接
        updated = batch_update_links(domain_dir, change["old_path"], change["new_path"])
        if updated:
            print(f"   更新了 {len(updated)} 个文件的链接")

    print("✅ 迁移完成")


def main():
    parser = argparse.ArgumentParser(description="目录结构迁移")
    parser.add_argument("--domain", required=True, help="领域名")
    parser.add_argument("--base-dir", default=".", help="知识库根目录")
    parser.add_argument("--execute", action="store_true", help="直接执行（跳过确认）")
    args = parser.parse_args()

    domain_dir = Path(args.base_dir) / args.domain
    config_path = domain_dir / "config.json"

    # 从 git 获取旧配置
    git = GitOps(str(Path(args.base_dir)))
    try:
        old_content = git.get_file_at_commit(str(config_path.relative_to(Path(args.base_dir))))
        old_config = json.loads(old_content)
    except Exception:
        print("⚠️  无法从 git 获取旧配置，将使用当前配置对比")
        old_config = {}

    # 读取新配置
    with open(config_path, "r", encoding="utf-8") as f:
        new_config = json.load(f)

    # diff
    changes = diff_configs(old_config, new_config)

    if not changes:
        print("✅ 无变更，无需迁移")
        return

    # 生成计划
    plan = generate_migration_plan(domain_dir, changes)
    print(plan)

    # 确认
    if not args.execute:
        response = input("\n执行迁移？(y/n): ")
        if response.lower() != "y":
            print("已取消")
            return

    # 执行
    execute_migration(domain_dir, changes)

    # git 提交
    git.add_and_commit(f"[migrate] {args.domain}: 目录结构迁移")


if __name__ == "__main__":
    main()
