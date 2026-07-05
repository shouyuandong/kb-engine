#!/usr/bin/env python3
"""健康检查：按策略执行 lint，找出不一致/过期/积压/缺失。

用法:
    python scripts/lint.py --all [--base-dir /path/to/knowledge]
    python scripts/lint.py --domain 育儿 [--base-dir /path/to/knowledge]
    python scripts/lint.py --domain 育儿 --check season  # 只检查换季
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from config_loader import ConfigLoader
from file_ops import list_files


def lint_domain(domain_dir: str, check_only: str = None) -> list:
    """对单个领域执行 lint

    Args:
        domain_dir: 领域根目录
        check_only: 只检查某项（如 "season"）

    Returns:
        问题列表
    """
    loader = ConfigLoader(domain_dir)
    strategy = loader.get_strategy()
    issues = []

    if strategy == "A":
        issues.extend(lint_strategy_a(loader, check_only))
    elif strategy == "B":
        issues.extend(lint_strategy_b(loader, check_only))
    elif strategy == "C":
        issues.extend(lint_strategy_c(loader, check_only))
    elif strategy == "D":
        issues.extend(lint_strategy_d(loader, check_only))
    elif strategy == "E":
        issues.extend(lint_strategy_e(loader, check_only))

    return issues


def lint_strategy_a(loader: ConfigLoader, check_only: str = None) -> list:
    """策略 A lint"""
    issues = []

    if check_only and check_only != "season":
        return issues

    # 检查卡片缺 source_level
    cards_dir = loader.get_full_path("知识卡片")
    for card in list_files(cards_dir):
        content = card.read_text(encoding="utf-8")
        if "source_level" not in content:
            issues.append(f"⚠️  卡片缺 source_level: {card.name}")
        if "verified: true" not in content and "verified: false" not in content:
            issues.append(f"⚠️  卡片缺 verified 标记: {card.name}")

    # 检查换季
    if not check_only or check_only == "season":
        stage_dir = loader.get_full_path("阶段重点")
        for stage_file in list_files(stage_dir):
            content = stage_file.read_text(encoding="utf-8")
            if "已度过" not in content:
                stat = stage_file.stat()
                days_old = (datetime.now().timestamp() - stat.st_mtime) / 86400
                if days_old > 180:
                    issues.append(f"📅 阶段重点超过180天未更新，考虑换季: {stage_file.name}")

    return issues


def lint_strategy_b(loader: ConfigLoader, check_only: str = None) -> list:
    """策略 B lint"""
    issues = []

    # 检查活跃超期
    domain_dir = loader.domain_dir
    notes_dir = loader.get_full_path("研究笔记")
    if notes_dir.exists():
        stat = notes_dir.stat()
        days_old = (datetime.now().timestamp() - stat.st_mtime) / 86400
        if days_old > 90:
            issues.append(f"📅 研究主题超过90天未更新，考虑封存")

    # 检查封存摘要完整性
    for f in list_files(domain_dir, "*结论*.md"):
        content = f.read_text(encoding="utf-8")
        for section in ["## 结论", "## 未解问题", "## 重启入口"]:
            if section not in content:
                issues.append(f"⚠️  封存摘要缺 {section}: {f.name}")

    return issues


def lint_strategy_c(loader: ConfigLoader, check_only: str = None) -> list:
    """策略 C lint"""
    issues = []

    # 检查过期未归档
    cognition_dir = loader.get_full_path("认知")
    for f in list_files(cognition_dir):
        content = f.read_text(encoding="utf-8")
        if "created:" in content:
            # 简单检查日期
            lines = content.split("\n")
            for line in lines:
                if "created:" in line:
                    date_str = line.split("created:")[1].strip()
                    try:
                        created = datetime.strptime(date_str[:10], "%Y-%m-%d")
                        if (datetime.now() - created).days > 14:
                            issues.append(f"📅 判断超过14天未归档: {f.name}")
                    except ValueError:
                        pass
                    break

    return issues


def lint_strategy_d(loader: ConfigLoader, check_only: str = None) -> list:
    """策略 D lint"""
    issues = []

    # 检查收集箱积压
    inbox_dir = loader.get_full_path("收集箱")
    for f in list_files(inbox_dir):
        stat = f.stat()
        days_old = (datetime.now().timestamp() - stat.st_mtime) / 86400
        if days_old > 30:
            issues.append(f"📥 收集箱积压超过30天: {f.name}")

    # 检查待尝试卡住
    queue_dir = loader.get_full_path("待尝试")
    for f in list_files(queue_dir):
        stat = f.stat()
        days_old = (datetime.now().timestamp() - stat.st_mtime) / 86400
        if days_old > 14:
            issues.append(f"⏳ 待尝试超过14天未处理: {f.name}")

    return issues


def lint_strategy_e(loader: ConfigLoader, check_only: str = None) -> list:
    """策略 E lint"""
    issues = []

    # 检查报告缺失（简化版）
    for report_type in ["周报", "月报"]:
        report_dir = loader.get_full_path(report_type)
        if report_dir.exists():
            files = list_files(report_dir)
            if len(files) == 0:
                issues.append(f"📭 {report_type} 为空，可能缺失报告")

    # 检查经验是否提炼
    bug_dir = loader.get_full_path("原始流水")
    if bug_dir:
        for subdir in bug_dir.iterdir():
            if subdir.name == "缺陷记录" and subdir.is_dir():
                bug_count = len(list_files(subdir))
                exp_dir = loader.get_full_path("经验")
                exp_count = len(list_files(exp_dir)) if exp_dir.exists() else 0
                if bug_count > 10 and exp_count < bug_count * 0.3:
                    issues.append(f"💡 缺陷记录 {bug_count} 条，但经验只有 {exp_count} 条，建议提炼")

    return issues


def main():
    parser = argparse.ArgumentParser(description="知识库健康检查")
    parser.add_argument("--domain", help="领域名（不指定则检查全部）")
    parser.add_argument("--base-dir", default=".", help="知识库根目录")
    parser.add_argument("--all", action="store_true", help="检查所有领域")
    parser.add_argument("--check", help="只检查某项（如 season）")
    args = parser.parse_args()

    base_dir = Path(args.base_dir)

    if args.all:
        # 检查所有领域
        for item in base_dir.iterdir():
            if item.is_dir() and (item / "_目录配置.json").exists():
                print(f"\n🔍 检查: {item.name}")
                issues = lint_domain(str(item), args.check)
                if issues:
                    for issue in issues:
                        print(f"   {issue}")
                else:
                    print("   ✅ 无问题")
    elif args.domain:
        domain_dir = base_dir / args.domain
        print(f"\n🔍 检查: {args.domain}")
        issues = lint_domain(str(domain_dir), args.check)
        if issues:
            for issue in issues:
                print(f"   {issue}")
        else:
            print("   ✅ 无问题")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
