#!/usr/bin/env python3
"""配置加载器：解析领域的 config.json，提供路径映射接口。

所有脚本通过本模块获取实际目录路径，不直接写死路径。
策略模板用逻辑名引用目录（如 {知识卡片}），本模块负责映射到实际路径。
"""

import json
from pathlib import Path
from typing import Optional


class ConfigLoader:
    def __init__(self, domain_dir: str):
        """初始化，加载领域的 config.json

        Args:
            domain_dir: 领域根目录路径
        """
        self.domain_dir = Path(domain_dir)
        self.config_path = self.domain_dir / "config.json"
        self.config = self._load()

    def _load(self) -> dict:
        """加载 JSON 配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"目录配置不存在: {self.config_path}\n"
                f"请先运行 init_domain.py 初始化领域"
            )
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_path(self, logical_name: str) -> str:
        """通过逻辑名获取实际目录路径

        Args:
            logical_name: 逻辑名（如 "知识卡片"）

        Returns:
            实际路径（如 "知识卡片" 或 "卡片库"）
        """
        dirs = self.config.get("directories", {})
        if logical_name not in dirs:
            raise KeyError(f"逻辑名 '{logical_name}' 不在目录配置中")
        return dirs[logical_name]["path"]

    def get_full_path(self, logical_name: str) -> Path:
        """获取完整路径（领域根目录 + 实际路径）"""
        return self.domain_dir / self.get_path(logical_name)

    def get_maintainer(self, logical_name: str) -> str:
        """获取目录的维护者类型"""
        dirs = self.config.get("directories", {})
        if logical_name not in dirs:
            raise KeyError(f"逻辑名 '{logical_name}' 不在目录配置中")
        return dirs[logical_name].get("maintainer", "manual")

    def is_writable(self, logical_name: str) -> bool:
        """LLM 是否有写权限"""
        dirs = self.config.get("directories", {})
        if logical_name not in dirs:
            return False
        return dirs[logical_name].get("writable", False)

    def get_draft_dir(self, logical_name: str) -> Optional[Path]:
        """获取草稿区路径（如有）"""
        dirs = self.config.get("directories", {})
        if logical_name not in dirs:
            return None
        draft = dirs[logical_name].get("draft_dir")
        if draft:
            return self.domain_dir / draft
        return None

    def get_compile_rules(self) -> list:
        """获取编译规则列表"""
        return self.config.get("compile_rules", [])

    def get_strategy(self) -> str:
        """获取该领域的策略类型"""
        return self.config.get("strategy", "A")

    def get_all_directories(self) -> dict:
        """获取所有目录配置"""
        return self.config.get("directories", {})

    def reload(self):
        """重新加载配置（迁移后调用）"""
        self.config = self._load()
