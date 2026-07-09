#!/usr/bin/env python3
"""初始化新领域：读取策略模板，生成 config.json，创建目录。

用法:
    python scripts/init_domain.py --domain 育儿 --strategy A [--base-dir /path/to/knowledge] [--yes]
    python scripts/init_domain.py --domain 育儿 --season-transition  # 换季
    python scripts/init_domain.py --domain 育儿 --strategy A --dry-run  # 只打印计划
"""

import argparse
import json
import shutil
import sys
from pathlib import Path

# 兼容中文 Windows（GBK 终端）：emoji/中文 print 会 UnicodeEncodeError，强制 UTF-8 输出
if sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from file_ops import ensure_dir


# 每个策略的完整目录结构 + 编译规则。
# 与 strategies/*.md 保持一致；模板里的目录块有缺失（如 A 缺外部政策、C 缺过期判断、
# D 缺外部扫描、E 缺提交记录等），此处补全，保证 compile_rules 引用的逻辑名都有目录。
# 改策略模板的目录/规则时，需同步此处。
STRATEGY_CONFIG = {
    "A": {
        "directories": {
            "原始资料": {"path": "原始资料", "purpose": "输入", "maintainer": "manual", "writable": False},
            "观察记录": {"path": "观察记录", "purpose": "个案记录", "maintainer": "manual", "writable": False},
            "学习资料": {"path": "学习资料", "purpose": "待编译资料", "maintainer": "manual", "writable": False},
            "成长日志": {"path": "成长日志", "purpose": "按月记录", "maintainer": "human", "writable": False},
            "知识卡片": {"path": "知识卡片", "purpose": "编译后的卡片", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "知识卡片/.草稿"},
            "阶段重点": {"path": "阶段重点", "purpose": "当前阶段里程碑", "maintainer": "human", "writable": False},
            "远期观察": {"path": "远期观察", "purpose": "远期内容", "maintainer": "observe_only", "writable": False},
            "外部政策": {"path": "外部政策", "purpose": "政策/外部规则", "maintainer": "manual", "writable": False},
        },
        "compile_rules": [
            {"input": "观察记录", "output": "成长日志", "rule": "不编译成通识，按周期归档"},
            {"input": "学习资料", "output": "知识卡片", "rule": "编译成卡片，带 source_level 和阶段标记"},
            {"input": "外部政策", "output": "远期观察", "rule": "编译成观察笔记，标只看不练"},
        ],
    },
    "B": {
        "directories": {
            "原始资料": {"path": "原始资料", "purpose": "研究原料", "maintainer": "manual", "writable": False},
            "研究笔记": {"path": "研究笔记", "purpose": "编译产出", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "研究笔记/.草稿"},
        },
        "compile_rules": [
            {"input": "原始资料", "output": "研究笔记", "rule": "编译成结构化笔记，建立反向链接"},
        ],
    },
    "C": {
        "directories": {
            "原始资料": {"path": "原始资料", "purpose": "输入", "maintainer": "manual", "writable": False},
            "框架": {"path": "框架", "purpose": "长线框架", "maintainer": "human", "writable": False},
            "认知": {"path": "认知", "purpose": "编译产出", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "认知/.草稿"},
            "归档": {"path": "归档", "purpose": "过期判断归档", "maintainer": "llm_full", "writable": True},
            "过期判断": {"path": "过期判断", "purpose": "待归档判断", "maintainer": "manual", "writable": False},
        },
        "compile_rules": [
            {"input": "原始资料", "output": "认知", "rule": "提取要点+标记时效日期，不保留原文"},
            {"input": "过期判断", "output": "归档", "rule": "超过设定周期的判断移入归档"},
        ],
    },
    "D": {
        "directories": {
            "收集箱": {"path": "收集箱", "purpose": "LLM自动生成草稿", "maintainer": "llm_full", "writable": True},
            "待尝试": {"path": "待尝试", "purpose": "排队", "maintainer": "human", "writable": False},
            "尝试记录": {"path": "尝试记录", "purpose": "人写的实测记录", "maintainer": "human", "writable": False},
            "沉淀": {"path": "沉淀", "purpose": "最终判断+原理", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "沉淀/.草稿"},
            "我的成果": {"path": "我的成果", "purpose": "自研成果", "maintainer": "human", "writable": False},
            "外部扫描": {"path": "外部扫描", "purpose": "扫描来源", "maintainer": "manual", "writable": False},
        },
        "compile_rules": [
            {"input": "外部扫描", "output": "收集箱", "rule": "LLM 从 README 提取标称能力，生成草稿"},
            {"input": "尝试记录", "output": "沉淀", "rule": "人写尝试记录后，提炼最终判断和原理"},
        ],
    },
    "E": {
        "directories": {
            "原始流水": {"path": "原始流水", "purpose": "自动采集", "maintainer": "auto", "writable": True},
            "提交记录": {"path": "提交记录", "purpose": "自动拉取提交", "maintainer": "auto", "writable": True},
            "缺陷记录": {"path": "缺陷记录", "purpose": "自动拉取缺陷", "maintainer": "auto", "writable": True},
            "会议纪要": {"path": "会议纪要", "purpose": "会议记录", "maintainer": "manual", "writable": False},
            "每日记录": {"path": "每日记录", "purpose": "每日记录", "maintainer": "manual", "writable": False},
            "周报": {"path": "周报", "purpose": "周报", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "周报/.草稿"},
            "月报": {"path": "月报", "purpose": "月报", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "月报/.草稿"},
            "年报": {"path": "年报", "purpose": "年报", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "年报/.草稿"},
            "项目": {"path": "项目", "purpose": "项目跟踪", "maintainer": "human", "writable": False},
            "项目决策": {"path": "项目/决策记录", "purpose": "项目决策记录，AI下次先读", "maintainer": "human", "writable": False},
            "项目反馈": {"path": "项目/反馈记录", "purpose": "不满意产出，AI下次先读避免重复犯错", "maintainer": "llm_full", "writable": True},
            "指标": {"path": "指标", "purpose": "KPI追踪", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "指标/.草稿"},
            "经验": {"path": "经验", "purpose": "踩坑模式", "maintainer": "llm_draft_human_review", "writable": True, "draft_dir": "经验/.草稿"},
            "附件": {"path": "附件", "purpose": "非md附件", "maintainer": "manual", "writable": False},
            "配置": {"path": "配置", "purpose": "规则配置", "maintainer": "manual", "writable": False},
        },
        "compile_rules": [
            {"input": "原始流水", "output": "周报", "rule": "按周编译，生成周报草稿"},
            {"input": "周报", "output": "月报", "rule": "按月汇总周报，生成月报草稿"},
            {"input": "缺陷记录", "output": "经验", "rule": "提炼踩坑模式，进经验草稿区"},
            {"input": "原始流水", "output": "指标", "rule": "按指标定义提取数据，更新追踪表"},
        ],
    },
}


def load_strategy_template(engine_dir: Path, strategy: str) -> str:
    """加载策略模板内容（保留接口，供未来解析使用）"""
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


def generate_directory_config(engine_dir: Path, domain: str, strategy: str) -> dict:
    """按策略生成完整目录配置（目录结构 + 编译规则）"""
    cfg = STRATEGY_CONFIG.get(strategy)
    if not cfg:
        raise ValueError(f"未配置策略: {strategy}")
    return {
        "domain": domain,
        "strategy": strategy,
        "directories": cfg["directories"],
        "compile_rules": cfg["compile_rules"],
    }


def create_directories(base_dir: Path, domain: str, config: dict):
    """根据配置创建目录结构"""
    domain_dir = base_dir / domain
    for logical_name, dir_config in config["directories"].items():
        dir_path = domain_dir / dir_config["path"]
        ensure_dir(dir_path)
        if dir_config.get("draft_dir"):
            ensure_dir(domain_dir / dir_config["draft_dir"])
    print(f"✅ 目录已创建: {domain_dir}")


def main():
    parser = argparse.ArgumentParser(description="初始化新知识库领域")
    parser.add_argument("--domain", required=True, help="领域名（如 育儿）")
    parser.add_argument("--strategy", required=True, choices=["A", "B", "C", "D", "E"], help="策略类型")
    parser.add_argument("--base-dir", default=".", help="知识库根目录（默认当前目录）")
    parser.add_argument("--season-transition", action="store_true", help="执行换季操作")
    parser.add_argument("--yes", action="store_true", help="跳过确认，直接创建目录与配置")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不写入文件/不创建目录")
    args = parser.parse_args()

    engine_dir = Path(__file__).parent.parent
    base_dir = Path(args.base_dir)
    domain_dir = base_dir / args.domain

    if args.season_transition:
        print(f"🔄 执行换季: {args.domain}")
        print("1. 新建下一阶段重点文件")
        print("2. 更新索引")
        print("3. 标记旧阶段")
        print("请参考 rules/season-transition.md 手动完成")
        return

    config = generate_directory_config(engine_dir, args.domain, args.strategy)

    if args.dry_run:
        print(f"[dry-run] 将为领域「{args.domain}」(策略 {args.strategy}) 生成 config.json：")
        print(f"[dry-run] 目录结构 ({len(config['directories'])} 个):")
        for name, d in config["directories"].items():
            writable = "✏️" if d.get("writable") else "🔒"
            print(f"   {writable} {name} → {d['path']}")
        print(f"[dry-run] 编译规则 ({len(config['compile_rules'])} 条):")
        for r in config["compile_rules"]:
            print(f"   {r['input']} → {r['output']}: {r['rule']}")
        return

    if domain_dir.exists():
        print(f"⚠️  领域已存在: {domain_dir}")
        if not args.yes:
            print(f"如需覆盖重建，请加 --yes 参数。")
            return

    ensure_dir(domain_dir)
    config_path = domain_dir / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"✅ 目录配置已生成: {config_path}")
    print(f"📋 策略: {args.strategy}")
    print(f"📁 目录结构:")
    for name, d in config["directories"].items():
        writable = "✏️" if d.get("writable") else "🔒"
        print(f"   {writable} {name} → {d['path']}")

    if args.yes:
        create_directories(base_dir, args.domain, config)
    else:
        print(f"\n目录配置已生成但未创建目录。加 --yes 创建目录，或用 /kb build 流入内容。")


if __name__ == "__main__":
    main()
