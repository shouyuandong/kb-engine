#!/usr/bin/env python3
"""GitHub 更新检测（策略 D 专用）：用 gh CLI 批量查已追踪 repo 的最近提交/release。

用法:
    python scripts/check_updates.py --domain 技能追踪 [--base-dir /path/to/knowledge]
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_gh(api_path: str) -> dict:
    """执行 gh api 命令

    Args:
        api_path: API 路径（如 repos/owner/repo/commits）

    Returns:
        JSON 响应
    """
    try:
        result = subprocess.run(
            ["gh", "api", api_path, "--jq", "."],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if result.returncode != 0:
            return None
        import json
        return json.loads(result.stdout)
    except Exception as e:
        print(f"  ⚠️  gh 命令失败: {e}")
        return None


def check_repo_updates(owner_repo: str) -> dict:
    """检查单个 repo 的更新

    Args:
        owner_repo: owner/repo 格式

    Returns:
        {latest_commit_date, latest_commit_msg, latest_release, releases}
    """
    info = {}

    # 最近提交
    commits = run_gh(f"repos/{owner_repo}/commits?per_page=1")
    if commits and len(commits) > 0:
        commit = commits[0]
        info["latest_commit_date"] = commit.get("commit", {}).get("committer", {}).get("date", "")
        info["latest_commit_msg"] = commit.get("commit", {}).get("message", "").split("\n")[0]

    # 最近 release
    releases = run_gh(f"repos/{owner_repo}/releases?per_page=3")
    if releases:
        info["releases"] = []
        for r in releases[:3]:
            info["releases"].append({
                "tag": r.get("tag_name", ""),
                "date": r.get("published_at", ""),
                "name": r.get("name", ""),
            })

    return info


def extract_repo_urls(settled_dir: Path) -> list:
    """从沉淀目录的文件中提取 GitHub repo URL

    Args:
        settled_dir: 沉淀目录路径

    Returns:
        [(owner/repo, 文件名), ...]
    """
    repos = []
    for md_file in settled_dir.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        # 从 frontmatter 提取 url
        if "url:" in content:
            for line in content.split("\n"):
                if "url:" in line and "github.com" in line:
                    url = line.split("url:")[1].strip().strip('"').strip("'")
                    # 提取 owner/repo
                    parts = url.replace("https://github.com/", "").split("/")
                    if len(parts) >= 2:
                        owner_repo = f"{parts[0]}/{parts[1]}"
                        repos.append((owner_repo, md_file.name))
                        break
    return repos


def main():
    parser = argparse.ArgumentParser(description="GitHub 更新检测（策略 D）")
    parser.add_argument("--domain", required=True, help="领域名")
    parser.add_argument("--base-dir", default=".", help="知识库根目录")
    args = parser.parse_args()

    domain_dir = Path(args.base_dir) / args.domain
    settled_dir = domain_dir / "沉淀"

    if not settled_dir.exists():
        print("ℹ️  沉淀目录不存在")
        return

    repos = extract_repo_urls(settled_dir)
    if not repos:
        print("ℹ️  未找到已追踪的 GitHub repo")
        return

    print(f"🔍 检查 {len(repos)} 个 repo 的更新:\n")

    for owner_repo, filename in repos:
        print(f"  📦 {owner_repo} ({filename})")
        info = check_repo_updates(owner_repo)

        if info.get("latest_commit_date"):
            print(f"     最近提交: {info['latest_commit_date'][:10]} {info.get('latest_commit_msg', '')}")

        if info.get("releases"):
            latest = info["releases"][0]
            print(f"     最近发布: {latest['tag']} ({latest['date'][:10]})")
        print()

    print("💡 提示: 对照尝试记录中的吐槽点，判断是否值得重试")


if __name__ == "__main__":
    main()
