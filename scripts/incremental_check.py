#!/usr/bin/env python3
"""增量检测：算 raw 文件 md5，比对上次，输出变化列表。

用法:
    python scripts/incremental_check.py --domain 育儿 [--base-dir /path/to/knowledge]
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import List


def md5sum(filepath: Path) -> str:
    """计算文件的 md5"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def load_hashes(cache_path: Path) -> dict:
    """加载上次的 md5 哈希记录"""
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_hashes(cache_path: Path, hashes: dict):
    """保存 md5 哈希记录"""
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(hashes, f, ensure_ascii=False, indent=2)


def check_changed_files(domain_dir: str) -> List[Path]:
    """检查领域内哪些 raw 文件变了

    Args:
        domain_dir: 领域根目录

    Returns:
        变更文件列表
    """
    domain_path = Path(domain_dir)
    cache_path = domain_path / ".cache" / "md5_hashes.json"
    raw_dir = domain_path / "原始资料"

    if not raw_dir.exists():
        # 策略 D 没有"原始资料"，检查"收集箱"
        raw_dir = domain_path / "收集箱"
        if not raw_dir.exists():
            return []

    last_hashes = load_hashes(cache_path)
    current_hashes = {}
    changed = []

    # 遍历 raw 目录下所有 .md 文件
    for md_file in raw_dir.rglob("*.md"):
        rel_path = str(md_file.relative_to(domain_path))
        current_hash = md5sum(md_file)
        current_hashes[rel_path] = current_hash

        if rel_path not in last_hashes or last_hashes[rel_path] != current_hash:
            changed.append(md_file)

    # 检查被删除的文件
    for old_path in last_hashes:
        if old_path not in current_hashes:
            print(f"  🗑️  文件已删除: {old_path}")

    # 保存当前哈希
    save_hashes(cache_path, current_hashes)

    return changed


def main():
    parser = argparse.ArgumentParser(description="增量检测：md5 比对")
    parser.add_argument("--domain", required=True, help="领域名")
    parser.add_argument("--base-dir", default=".", help="知识库根目录")
    args = parser.parse_args()

    domain_dir = Path(args.base_dir) / args.domain
    changed = check_changed_files(str(domain_dir))

    if changed:
        print(f"📦 {len(changed)} 个文件变更:")
        for f in changed:
            print(f"   {f.relative_to(domain_dir)}")
    else:
        print("✅ 无变更")


if __name__ == "__main__":
    main()
