#!/usr/bin/env python3
"""文件操作模块：移动、重命名、批量更新 [[链接]]、目录创建。

迁移和编译脚本通过本模块执行文件操作。
"""

import re
import shutil
from pathlib import Path
from typing import List, Tuple


def ensure_dir(path: Path):
    """确保目录存在，不存在则创建"""
    path.mkdir(parents=True, exist_ok=True)


def move_file(src: Path, dst: Path) -> Path:
    """移动文件

    Args:
        src: 源路径
        dst: 目标路径

    Returns:
        移动后的文件路径
    """
    ensure_dir(dst.parent)
    shutil.move(str(src), str(dst))
    return dst


def rename_dir(src: Path, dst: Path):
    """重命名目录"""
    if not src.exists():
        raise FileNotFoundError(f"源目录不存在: {src}")
    if dst.exists():
        raise FileExistsError(f"目标目录已存在: {dst}")
    src.rename(dst)


def find_wikilinks(content: str) -> List[str]:
    """找出 markdown 内容中的所有 [[wikilink]]

    Returns:
        链接列表，如 ["知识卡片/xxx", "经验/yyy"]
    """
    pattern = r'\[\[([^\]]+)\]'
    return re.findall(pattern, content)


def update_wikilinks(
    content: str,
    old_path: str,
    new_path: str
) -> Tuple[str, int]:
    """更新内容中的 wikilink 路径

    Args:
        content: markdown 内容
        old_path: 旧路径（如 "知识卡片"）
        new_path: 新路径（如 "卡片库"）

    Returns:
        (更新后的内容, 替换次数)
    """
    count = 0

    # 替换 [[old_path/xxx]] → [[new_path/xxx]]
    pattern = rf'\[\[{re.escape(old_path)}([/\]])'
    replacement = f'[[{new_path}\\1'

    new_content, count = re.subn(pattern, replacement, content)
    return new_content, count


def batch_update_links(
    root_dir: Path,
    old_path: str,
    new_path: str
) -> List[Tuple[Path, int]]:
    """批量更新目录下所有 .md 文件中的 wikilink

    Args:
        root_dir: 根目录
        old_path: 旧路径
        new_path: 新路径

    Returns:
        [(文件路径, 替换次数), ...]
    """
    updated_files = []

    for md_file in root_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            new_content, count = update_wikilinks(content, old_path, new_path)
            if count > 0:
                md_file.write_text(new_content, encoding="utf-8")
                updated_files.append((md_file, count))
        except Exception as e:
            print(f"警告: 更新 {md_file} 链接失败: {e}")

    return updated_files


def count_files(directory: Path) -> int:
    """统计目录下的文件数"""
    if not directory.exists():
        return 0
    return sum(1 for _ in directory.rglob("*") if _.is_file())


def list_files(directory: Path, pattern: str = "*.md") -> List[Path]:
    """列出目录下匹配的文件"""
    if not directory.exists():
        return []
    return list(directory.rglob(pattern))
