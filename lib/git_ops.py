#!/usr/bin/env python3
"""git 操作封装：wiki 层版本管理。

所有 git 操作通过本模块执行，确保提交信息格式统一。
"""

import subprocess
from pathlib import Path
from typing import List, Optional


class GitOps:
    def __init__(self, repo_dir: str):
        self.repo_dir = Path(repo_dir)

    def _run(self, *args: str) -> str:
        """执行 git 命令"""
        result = subprocess.run(
            ["git"] + list(args),
            cwd=str(self.repo_dir),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if result.returncode != 0:
            raise RuntimeError(f"git {args} 失败: {result.stderr}")
        return result.stdout.strip()

    def add(self, paths: List[str] = None):
        """添加文件到暂存区

        Args:
            paths: 文件路径列表，None 表示添加全部
        """
        if paths:
            for p in paths:
                self._run("add", p)
        else:
            self._run("add", "-A")

    def commit(self, message: str):
        """提交

        Args:
            message: 提交信息
        """
        self._run("commit", "-m", message)

    def diff(self, path: str = None) -> str:
        """查看差异

        Args:
            path: 文件路径，None 表示全部
        """
        if path:
            return self._run("diff", path)
        return self._run("diff")

    def log(self, count: int = 10, grep: str = None) -> str:
        """查看提交历史

        Args:
            count: 条数
            grep: 过滤关键词
        """
        args = ["log", f"--oneline", f"-{count}"]
        if grep:
            args.extend(["--grep", grep])
        return self._run(*args)

    def checkout(self, target: str, paths: List[str] = None):
        """检出

        Args:
            target: commit hash 或分支名
            paths: 限定路径列表
        """
        args = ["checkout", target]
        if paths:
            args.append("--")
            args.extend(paths)
        self._run(*args)

    def status(self) -> str:
        """查看状态"""
        return self._run("status", "--short")

    def has_changes(self) -> bool:
        """是否有未提交的变更"""
        return bool(self.status())

    def add_and_commit(self, message: str, paths: List[str] = None):
        """添加并提交（便捷方法）

        Args:
            message: 提交信息
            paths: 文件路径列表
        """
        self.add(paths)
        if self.has_changes():
            self.commit(message)

    def get_file_at_commit(self, file_path: str, commit: str = "HEAD") -> str:
        """获取某个 commit 时的文件内容

        Args:
            file_path: 文件路径
            commit: commit hash，默认 HEAD

        Returns:
            文件内容
        """
        result = subprocess.run(
            ["git", "show", f"{commit}:{file_path}"],
            cwd=str(self.repo_dir),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if result.returncode != 0:
            raise RuntimeError(f"git show 失败: {result.stderr}")
        return result.stdout
