#!/usr/bin/env python3
"""灵感库清理：扫描灵感库，提示该 promote 到哪个领域。

用法:
    python scripts/clean_inbox.py [--base-dir /path/to/knowledge]
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

# 兼容中文 Windows（GBK 终端）：强制 UTF-8 输出，避免 emoji/中文 print 崩溃
if sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from strategy_router import StrategyRouter
from file_ops import list_files


def clean_inbox(base_dir: str, engine_dir: str):
    """扫描灵感库，为每条内容建议目标领域

    Args:
        base_dir: 知识库根目录
        engine_dir: kb-engine 根目录
    """
    router = StrategyRouter(engine_dir)
    inbox_path = router.get_inbox_config().get("path", "00-灵感库").rstrip("/")
    base_path = Path(base_dir)
    inbox_dir = base_path / inbox_path

    if not inbox_dir.exists():
        print(f"ℹ️  {inbox_path}不存在")
        return

    items = list_files(inbox_dir)
    if not items:
        print(f"✅ {inbox_path}为空")
        return

    domains = router.get_all_domains()

    print(f"📥 {inbox_path}有 {len(items)} 条待处理:\n")

    for item in items:
        content = item.read_text(encoding="utf-8")

        # 提取内容用于建议领域
        # 去掉 frontmatter
        if content.startswith("---"):
            parts = content.split("---", 2)
            content_body = parts[2] if len(parts) > 2 else content
        else:
            content_body = content

        suggested = router.suggest_domain(content_body)

        # 检查文件年龄
        stat = item.stat()
        days_old = (datetime.now().timestamp() - stat.st_mtime) / 86400

        age_marker = ""
        if days_old > 30:
            age_marker = " ⚠️ 已超过30天"
        elif days_old > 7:
            age_marker = " (已超过7天)"

        raw_dir = router.get_domain_raw_dir(base_dir, suggested) if suggested else None
        if suggested and raw_dir:
            domain_hint = f" → 建议进「{suggested}」的「{raw_dir}」"
        elif suggested:
            domain_hint = f" → 建议进「{suggested}」（未找到原始目录，请手动选择）"
        else:
            domain_hint = " → 无法自动判断，请手动选择"

        print(f"  📄 {item.name}{age_marker}{domain_hint}")

    print(f"\n处理方式:")
    print(f"  1. 确认目标领域后，移动到对应领域的原始/暂存目录（见上方每条建议，如 原始流水/原始资料/收集箱）")
    print(f"  2. 无用的直接删除")
    print(f"  3. LLM 可协助判断领域归属")


def main():
    parser = argparse.ArgumentParser(description="清理灵感库")
    parser.add_argument("--base-dir", default=".", help="知识库根目录")
    parser.add_argument("--engine-dir", default=".", help="kb-engine 根目录")
    args = parser.parse_args()

    engine_dir = Path(__file__).parent.parent
    clean_inbox(args.base_dir, str(engine_dir))


if __name__ == "__main__":
    main()
