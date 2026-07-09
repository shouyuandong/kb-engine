#!/usr/bin/env python3
"""生成报告（策略 E 专用）：从原始流水生成周/月/年报。

用法:
    python scripts/generate_report.py --domain 工作 --type weekly [--base-dir /path/to/knowledge]
    python scripts/generate_report.py --domain 工作 --type monthly
    python scripts/generate_report.py --domain 工作 --type yearly
"""

import argparse
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


def get_week_range(date: datetime = None) -> tuple:
    """获取当前周的起止日期（周一到周日）"""
    if date is None:
        date = datetime.now()
    monday = date - timedelta(days=date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_month_range(date: datetime = None) -> tuple:
    """获取当前月的起止日期"""
    if date is None:
        date = datetime.now()
    first = date.replace(day=1)
    if date.month == 12:
        last = date.replace(day=31)
    else:
        last = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
    return first, last


def get_year_range(date: datetime = None) -> tuple:
    """获取当前年的起止日期"""
    if date is None:
        date = datetime.now()
    return date.replace(month=1, day=1), date.replace(month=12, day=31)


def collect_raw_files(domain_dir: Path, start: datetime, end: datetime) -> list:
    """收集指定日期范围内的原始流水文件"""
    files = []
    raw_dir = domain_dir / "原始流水"
    if not raw_dir.exists():
        return files

    for md_file in raw_dir.rglob("*.md"):
        stat = md_file.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        if start <= mtime <= end:
            files.append(md_file)
    return files


def generate_weekly(domain_dir: str):
    """生成周报"""
    loader = ConfigLoader(domain_dir)
    start, end = get_week_range()

    week_num = start.isocalendar()[1]
    year = start.year
    report_name = f"{year}-W{week_num:02d}"
    report_dir = loader.get_full_path("周报")
    draft_dir = loader.get_draft_dir("周报")

    # 检查是否已存在
    report_file = report_dir / f"{report_name}.md"
    if report_file.exists():
        print(f"⚠️  周报已存在: {report_file.name}")
        return

    # 收集原始流水
    raw_files = collect_raw_files(Path(domain_dir), start, end)

    print(f"📝 生成周报: {report_name}")
    print(f"   日期范围: {start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}")
    print(f"   原始流水: {len(raw_files)} 个文件")

    # 读取模板
    engine_dir = Path(__file__).parent.parent
    template = engine_dir / "templates" / "weekly-report.md"
    template_content = template.read_text(encoding="utf-8")

    # 收集流水内容（给 LLM 编译用）
    raw_content = ""
    for f in raw_files:
        raw_content += f"\n\n--- {f.name} ---\n"
        raw_content += f.read_text(encoding="utf-8")

    # 写入草稿区
    output_dir = draft_dir if draft_dir else report_dir
    ensure_dir(output_dir)
    draft_file = output_dir / f"{report_name}.md"

    # 替换模板变量
    content = template_content.replace("YYYY-Wxx", report_name)
    content = content.replace("YYYY-MM-DD", datetime.now().strftime("%Y-%m-%d"))

    draft_file.write_text(content, encoding="utf-8")
    print(f"   ✅ 草稿已生成: {draft_file}")
    print(f"   📋 LLM 请根据以下原始流水编译周报正文:")
    print(f"   （{len(raw_files)} 个文件的流水内容已收集，交给 LLM 编译）")


def generate_monthly(domain_dir: str):
    """生成月报"""
    loader = ConfigLoader(domain_dir)
    start, end = get_month_range()

    report_name = f"{start.strftime('%Y-%m')}"
    report_dir = loader.get_full_path("月报")
    draft_dir = loader.get_draft_dir("月报")

    report_file = report_dir / f"{report_name}.md"
    if report_file.exists():
        print(f"⚠️  月报已存在: {report_file.name}")
        return

    # 收集本月周报
    weekly_dir = loader.get_full_path("周报")
    weekly_files = [f for f in list_files(weekly_dir) if report_name[:7] in f.name]

    print(f"📝 生成月报: {report_name}")
    print(f"   本月周报: {len(weekly_files)} 篇")

    output_dir = draft_dir if draft_dir else report_dir
    ensure_dir(output_dir)
    draft_file = output_dir / f"{report_name}.md"

    engine_dir = Path(__file__).parent.parent
    template = engine_dir / "templates" / "monthly-report.md"
    content = template.read_text(encoding="utf-8")
    content = content.replace("YYYY-MM", report_name)
    content = content.replace("YYYY-MM-DD", datetime.now().strftime("%Y-%m-%d"))

    draft_file.write_text(content, encoding="utf-8")
    print(f"   ✅ 草稿已生成: {draft_file}")


def generate_yearly(domain_dir: str):
    """生成年报"""
    loader = ConfigLoader(domain_dir)
    start, end = get_year_range()

    report_name = f"{start.strftime('%Y')}"
    report_dir = loader.get_full_path("年报")
    draft_dir = loader.get_draft_dir("年报")

    report_file = report_dir / f"{report_name}.md"
    if report_file.exists():
        print(f"⚠️  年报已存在: {report_file.name}")
        return

    # 收集本年月报
    monthly_dir = loader.get_full_path("月报")
    monthly_files = [f for f in list_files(monthly_dir) if report_name in f.name]

    print(f"📝 生成年报: {report_name}")
    print(f"   本年月报: {len(monthly_files)} 篇")

    output_dir = draft_dir if draft_dir else report_dir
    ensure_dir(output_dir)
    draft_file = output_dir / f"{report_name}.md"

    engine_dir = Path(__file__).parent.parent
    template = engine_dir / "templates" / "yearly-report.md"
    content = template.read_text(encoding="utf-8")
    content = content.replace("YYYY", report_name)
    content = content.replace("YYYY-MM-DD", datetime.now().strftime("%Y-%m-%d"))

    draft_file.write_text(content, encoding="utf-8")
    print(f"   ✅ 草稿已生成: {draft_file}")


def main():
    parser = argparse.ArgumentParser(description="生成周期报告（策略 E）")
    parser.add_argument("--domain", required=True, help="领域名")
    parser.add_argument("--type", required=True, choices=["weekly", "monthly", "yearly"], help="报告类型")
    parser.add_argument("--base-dir", default=".", help="知识库根目录")
    args = parser.parse_args()

    domain_dir = str(Path(args.base_dir) / args.domain)

    if args.type == "weekly":
        generate_weekly(domain_dir)
    elif args.type == "monthly":
        generate_monthly(domain_dir)
    elif args.type == "yearly":
        generate_yearly(domain_dir)


if __name__ == "__main__":
    main()
