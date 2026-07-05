#!/usr/bin/env python3
"""初始化新领域：读取策略模板，生成 _目录配置.json，创建目录。

用法:
    python scripts/init_domain.py --domain 育儿 --strategy A [--base-dir /path/to/knowledge]
    python scripts/init_domain.py --domain 育儿 --season-transition  # 换季
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

# 添加 lib 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from file_ops import ensure_dir


def load_strategy_template(engine_dir: Path, strategy: str) -> str:
    """加载策略模板内容"""
    template_path = engine_dir / "strategies" / f"{strategy}-continuous-accumulation.md"
    # 尝试匹配策略名
    mapping = {
        "A": "A-continuous-accumulation.md",
        "B": "B-topic-research.md",
        "C": "C-time-decay.md",
        "D": "D-queue-tracking.md",
        "E": "E-periodic-operation.md",
    }
    filename = mapping.get(strategy)
    if not filename:
        raise ValueError(f"未知策略: {strategy}")
    template_path = engine_dir / "strategies" / filename
    if not template_path.exists():
        raise FileNotFoundError(f"策略模板不存在: {template_path}")
    return template_path.read_text(encoding="utf-8")


def generate_directory_config(
    engine_dir: Path,
    domain: str,
    strategy: str
) -> dict:
    """从模板生成目录配置"""
    template_path = engine_dir / "config" / "directory-config-template.json"
    with open(template_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    config["domain"] = domain
    config["strategy"] = strategy
    # 删除注释字段
    config.pop("_comment", None)
    config.pop("_maintainer_values", None)

    # 根据策略设置默认目录结构
    default_dirs = {
        "A": {
            "原始资料": {"path": "原始资料", "purpose": "输入", "maintainer": "manual", "writable": False},
            "成长日志": {"path": "成长日志", "purpose": "按月记录", "maintainer": "human", "writable": False},
            "知识卡片": {"path": "知识卡片", "purpose": "编译后的卡片", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "知识卡片/.草稿"},
            "阶段重点": {"path": "阶段重点", "purpose": "当前阶段里程碑", "maintainer": "human", "writable": False},
            "远期观察": {"path": "远期观察", "purpose": "远期内容", "maintainer": "observe_only", "writable": False},
        },
        "B": {
            "原始资料": {"path": "原始资料", "purpose": "研究原料", "maintainer": "manual", "writable": False},
            "研究笔记": {"path": "研究笔记", "purpose": "编译产出", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "研究笔记/.草稿"},
        },
        "C": {
            "原始资料": {"path": "原始资料", "purpose": "输入", "maintainer": "manual", "writable": False},
            "框架": {"path": "框架", "purpose": "长线框架", "maintainer": "human", "writable": False},
            "认知": {"path": "认知", "purpose": "编译产出", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "认知/.草稿"},
            "归档": {"path": "归档", "purpose": "过期判断", "maintainer": "llm_full", "writable": True},
        },
        "D": {
            "收集箱": {"path": "收集箱", "purpose": "LLM自动生成草稿", "maintainer": "llm_full", "writable": True},
            "待尝试": {"path": "待尝试", "purpose": "排队", "maintainer": "human", "writable": False},
            "尝试记录": {"path": "尝试记录", "purpose": "人写的实测记录", "maintainer": "human", "writable": False},
            "沉淀": {"path": "沉淀", "purpose": "最终判断+原理", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "沉淀/.草稿"},
            "我的成果": {"path": "我的成果", "purpose": "自研成果", "maintainer": "human", "writable": False},
        },
        "E": {
            "原始流水": {"path": "原始流水", "purpose": "自动采集", "maintainer": "auto", "writable": True},
            "周报": {"path": "周报", "purpose": "周报", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "周报/.草稿"},
            "月报": {"path": "月报", "purpose": "月报", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "月报/.草稿"},
            "年报": {"path": "年报", "purpose": "年报", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "年报/.草稿"},
            "项目": {"path": "项目", "purpose": "项目跟踪", "maintainer": "human", "writable": False},
            "指标": {"path": "指标", "purpose": "KPI追踪", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "指标/.草稿"},
            "经验": {"path": "经验", "purpose": "踩坑模式", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "经验/.草稿"},
            "附件": {"path": "附件", "purpose": "非md附件", "maintainer": "manual", "writable": False},
            "配置": {"path": "配置", "purpose": "规则配置", "maintainer": "manual", "writable": False},
        },
    }

    config["directories"] = default_dirs.get(strategy, {})
    return config


def create_directories(base_dir: Path, domain: str, config: dict):
    """根据配置创建目录结构"""
    domain_dir = base_dir / domain
    for logical_name, dir_config in config["directories"].items():
        dir_path = domain_dir / dir_config["path"]
        ensure_dir(dir_path)
        # 创建草稿区
        if dir_config.get("draft_dir"):
            ensure_dir(domain_dir / dir_config["draft_dir"])
    print(f"✅ 目录已创建: {domain_dir}")


def main():
    parser = argparse.ArgumentParser(description="初始化新知识库领域")
    parser.add_argument("--domain", required=True, help="领域名（如 育儿）")
    parser.add_argument("--strategy", required=True, choices=["A", "B", "C", "D", "E"], help="策略类型")
    parser.add_argument("--base-dir", default=".", help="知识库根目录（默认当前目录）")
    parser.add_argument("--season-transition", action="store_true", help="执行换季操作")
    args = parser.parse_args()

    engine_dir = Path(__file__).parent.parent
    base_dir = Path(args.base_dir)
    domain_dir = base_dir / args.domain

    if args.season_transition:
        # 换季操作
        print(f"🔄 执行换季: {args.domain}")
        print("1. 新建下一阶段重点文件")
        print("2. 更新索引")
        print("3. 标记旧阶段")
        print("请参考 rules/season-transition.md 手动完成")
        return

    if domain_dir.exists():
        print(f"⚠️  领域已存在: {domain_dir}")
        response = input("覆盖？(y/n): ")
        if response.lower() != "y":
            return

    # 生成目录配置
    config = generate_directory_config(engine_dir, args.domain, args.strategy)

    # 保存配置
    ensure_dir(domain_dir)
    config_path = domain_dir / "_目录配置.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"✅ 目录配置已生成: {config_path}")
    print(f"📋 策略: {args.strategy}")
    print(f"📁 目录结构:")
    for name, d in config["directories"].items():
        writable = "✏️" if d.get("writable") else "🔒"
        print(f"   {writable} {name} → {d['path']}")

    print(f"\n确认目录结构后，运行以下命令创建目录:")
    print(f"  python scripts/init_domain.py --domain {args.domain} --strategy {args.strategy} --confirm")

    # 简化：直接创建
    response = input("\n立即创建目录？(y/n): ")
    if response.lower() == "y":
        create_directories(base_dir, args.domain, config)


if __name__ == "__main__":
    main()
