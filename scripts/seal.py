#!/usr/bin/env python3
"""封存研究主题（策略 B 专用）：执行最终编译+lint+生成研究结论摘要。

用法:
    python scripts/seal.py --domain 个人学习/蒸馏研究 [--base-dir /path/to/knowledge]
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

# 兼容中文 Windows（GBK 终端）：强制 UTF-8 输出，避免 emoji/中文 print 崩溃
if sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from config_loader import ConfigLoader
from file_ops import list_files, ensure_dir


def seal_topic(domain_dir: str, dry_run: bool = False):
    """封存研究主题

    Args:
        domain_dir: 领域（主题）根目录
    """
    loader = ConfigLoader(domain_dir)
    strategy = loader.get_strategy()

    if strategy != "B":
        print(f"⚠️  策略 {strategy} 不支持封存（仅策略 B 适用）")
        return

    domain_path = Path(domain_dir)
    today = Path(domain_dir).name  # 主题名

    print(f"🔒 封存研究主题: {domain_path.name}")
    print()

    # 1. 检查原始资料积压
    raw_dir = loader.get_full_path("原始资料")
    raw_files = list_files(raw_dir) if raw_dir.exists() else []
    if raw_files:
        print(f"  ⚠️  原始资料还有 {len(raw_files)} 个未编译文件")
        print(f"     建议先完成编译再封存")

    if dry_run:
        print(f"[dry-run] 预览：将对主题「{domain_path.name}」执行封存（生成研究结论摘要并标记 sealed），不写入任何文件。")
        return

    # 2. 生成研究结论摘要
    engine_dir = Path(__file__).parent.parent
    template = engine_dir / "templates" / "research-conclusion.md"
    template_content = template.read_text(encoding="utf-8")

    # 替换模板变量
    today_str = datetime.now().strftime("%Y-%m")
    content = template_content.replace("YYYY-MM", today_str)
    content = content.replace("主题名", domain_path.name)

    # 写入结论摘要
    conclusion_file = domain_path / f"研究结论_{today_str}.md"
    conclusion_file.write_text(content, encoding="utf-8")

    print(f"  ✅ 研究结论摘要已生成: {conclusion_file.name}")
    print(f"  📋 请填写以下章节:")
    print(f"     - 结论")
    print(f"     - 判断验证（哪些被证实/证伪）")
    print(f"     - 未解问题")
    print(f"     - 重启入口")
    print(f"     - 关联")

    # 3. 统计 wiki 规模
    notes_dir = loader.get_full_path("研究笔记")
    if notes_dir.exists():
        notes = list_files(notes_dir)
        total_words = 0
        for note in notes:
            total_words += len(note.read_text(encoding="utf-8"))
        print(f"\n  📊 wiki 规模: {len(notes)} 篇, 约 {total_words} 字")

    # 4. 标记封存
    config_path = domain_path / "config.json"
    import json
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    config["sealed"] = True
    config["sealed_date"] = today_str
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"\n  ✅ 主题已标记封存: {today_str}")
    print(f"  💡 raw 资料可压缩备份: tar czf {domain_path.name}_raw.tar.gz {raw_dir}")


def main():
    parser = argparse.ArgumentParser(description="封存研究主题（策略 B）")
    parser.add_argument("--domain", required=True, help="领域名（主题路径）")
    parser.add_argument("--base-dir", default=".", help="知识库根目录")
    parser.add_argument("--dry-run", action="store_true", help="只预览将执行的操作，不写入文件")
    args = parser.parse_args()

    domain_dir = str(Path(args.base_dir) / args.domain)
    seal_topic(domain_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
