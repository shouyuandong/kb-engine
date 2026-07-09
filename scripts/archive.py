#!/usr/bin/env python3
"""归档过期内容（策略 C 专用）：按时效规则把过期判断移入归档区。

用法:
    python scripts/archive.py --domain 交易 [--base-dir /path/to/knowledge]
    python scripts/archive.py --domain 交易 --retention 14  # 指定保留天数
"""

import argparse
import re
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

# 兼容中文 Windows（GBK 终端）：强制 UTF-8 输出，避免 emoji/中文 print 崩溃
if sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from config_loader import ConfigLoader
from file_ops import list_files, ensure_dir


def extract_date(content: str) -> datetime:
    """从 markdown frontmatter 中提取日期"""
    # 尝试 created 字段
    match = re.search(r'created:\s*(\d{4}-\d{2}-\d{2})', content)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d")
        except ValueError:
            pass

    # 尝试 date 字段
    match = re.search(r'date:\s*(\d{4}-\d{2}-\d{2})', content)
    if match:
        try:
            return datetime.strptime(match.group(1), "%Y-%m-%d")
        except ValueError:
            pass

    return None


def archive_expired(domain_dir: str, retention_days: int = 14):
    """归档过期内容

    Args:
        domain_dir: 领域根目录
        retention_days: 保留天数，超过则归档
    """
    loader = ConfigLoader(domain_dir)
    strategy = loader.get_strategy()

    if strategy != "C":
        print(f"⚠️  策略 {strategy} 不支持自动归档（仅策略 C 适用）")
        return

    cognition_dir = loader.get_full_path("认知")
    archive_dir = loader.get_full_path("归档")

    if not cognition_dir.exists():
        print("ℹ️  认知目录不存在")
        return

    ensure_dir(archive_dir)

    cutoff_date = datetime.now() - timedelta(days=retention_days)
    archived = []

    for md_file in list_files(cognition_dir):
        content = md_file.read_text(encoding="utf-8")
        file_date = extract_date(content)

        if file_date is None:
            # 无法提取日期，跳过
            continue

        if file_date < cutoff_date:
            # 归档
            rel_path = md_file.relative_to(cognition_dir)
            dst = archive_dir / rel_path
            ensure_dir(dst.parent)
            shutil.move(str(md_file), str(dst))
            archived.append((rel_path, file_date.strftime("%Y-%m-%d")))

    if archived:
        print(f"📦 归档了 {len(archived)} 条过期内容（超过 {retention_days} 天）:")
        for path, date in archived:
            print(f"   {date} {path}")
    else:
        print("✅ 无过期内容")

    return archived


def main():
    parser = argparse.ArgumentParser(description="归档过期内容（策略 C）")
    parser.add_argument("--domain", required=True, help="领域名")
    parser.add_argument("--base-dir", default=".", help="知识库根目录")
    parser.add_argument("--retention", type=int, default=14, help="保留天数（默认14天）")
    args = parser.parse_args()

    domain_dir = str(Path(args.base_dir) / args.domain)
    archive_expired(domain_dir, args.retention)


if __name__ == "__main__":
    main()
