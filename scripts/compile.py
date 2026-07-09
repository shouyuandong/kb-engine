#!/usr/bin/env python3
"""编译：读取 config.json 的 compile_rules，按规则编译 raw → 产出。

用法:
    python scripts/compile.py --domain 育儿 [--base-dir /path/to/knowledge]
    python scripts/compile.py --domain 育儿 --file raw/某文章.md
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

# 兼容中文 Windows（GBK 终端）：强制 UTF-8 输出，避免 emoji/中文 print 崩溃
if sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from config_loader import ConfigLoader
from incremental_check import check_changed_files


def compile_domain(domain_dir: str, specific_file: str = None):
    """编译领域的 raw → 产出

    Args:
        domain_dir: 领域根目录
        specific_file: 只编译指定文件（可选）
    """
    loader = ConfigLoader(domain_dir)
    rules = loader.get_compile_rules()

    if not rules:
        print("ℹ️  无编译规则")
        return

    # 增量检测：哪些 raw 文件变了
    changed = check_changed_files(domain_dir)

    if specific_file:
        changed = [f for f in changed if specific_file in str(f)]

    if not changed:
        print("✅ 无变更，跳过编译")
        return

    print(f"📦 检测到 {len(changed)} 个变更文件:")
    for f in changed:
        print(f"   {f}")

    # 按规则匹配
    for rule in rules:
        input_name = rule["input"]
        output_name = rule["output"]
        rule_desc = rule["rule"]

        input_path = loader.get_full_path(input_name)
        output_path = loader.get_full_path(output_name)

        # 检查输出目录的写权限
        if not loader.is_writable(output_name):
            print(f"⚠️  {output_name} 不可写（maintainer={loader.get_maintainer(output_name)}）")
            print(f"   LLM 只能生成草稿到: {loader.get_draft_dir(output_name)}")
            continue

        print(f"\n🔄 编译规则: {input_name} → {output_name}")
        print(f"   规则: {rule_desc}")
        print(f"   输入: {input_path}")
        print(f"   输出: {output_path}")

        # 实际编译由 LLM 执行（在 Claude Code 中，LLM 会读取此输出并执行编译）
        # 此脚本负责：检测变更、确定路径、检查权限
        # LLM 负责：读取 raw 内容、按规则编译、写入产出


def main():
    parser = argparse.ArgumentParser(description="编译知识库 raw → 产出")
    parser.add_argument("--domain", required=True, help="领域名")
    parser.add_argument("--base-dir", default=".", help="知识库根目录")
    parser.add_argument("--file", help="只编译指定文件")
    args = parser.parse_args()

    domain_dir = Path(args.base_dir) / args.domain
    compile_domain(str(domain_dir), args.file)


if __name__ == "__main__":
    main()
