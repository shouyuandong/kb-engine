#!/usr/bin/env python3
"""策略路由器：根据内容或领域，判断该用哪个策略。

读取 config/strategy-index.yml，返回策略类型。
"""

import yaml
from pathlib import Path
from typing import Optional


class StrategyRouter:
    def __init__(self, engine_dir: str):
        """初始化

        Args:
            engine_dir: kb-engine 根目录路径
        """
        self.engine_dir = Path(engine_dir)
        self.index_path = self.engine_dir / "config" / "strategy-index.yml"
        self.index = self._load_index()

    def _load_index(self) -> dict:
        """加载策略索引"""
        if not self.index_path.exists():
            raise FileNotFoundError(f"策略索引不存在: {self.index_path}")
        with open(self.index_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_strategy(self, domain: str) -> str:
        """通过领域名获取策略类型

        Args:
            domain: 领域名（如 "育儿"）

        Returns:
            策略类型（如 "A"）
        """
        domains = self.index.get("domains", {})
        if domain not in domains:
            raise KeyError(f"领域 '{domain}' 不在策略索引中")
        return domains[domain]

    def get_strategy_template(self, strategy: str) -> Path:
        """获取策略模板文件路径

        Args:
            strategy: 策略类型（如 "A"）

        Returns:
            模板文件路径
        """
        templates = self.index.get("strategy_templates", {})
        if strategy not in templates:
            raise KeyError(f"策略 '{strategy}' 没有对应的模板")
        return self.engine_dir / templates[strategy]

    def get_all_domains(self) -> dict:
        """获取所有领域→策略映射"""
        return self.index.get("domains", {})

    def get_inbox_config(self) -> dict:
        """获取灵感库配置"""
        return self.index.get("inbox", {})

    def get_domain_raw_dir(self, base_dir: str, domain: str) -> Optional[str]:
        """读取某领域的 config.json，返回其「原始/暂存」目录的逻辑名。

        用于将灵感库条目 promote 到具体领域时的目标目录提示。
        优先级关键词匹配：原始 > 流水 > 收集箱 > 尝试记录，命中第一个即返回。

        Args:
            base_dir: 知识库根目录
            domain: 领域名

        Returns:
            逻辑目录名（如 "原始流水"），无配置时返回 None
        """
        cfg_path = Path(base_dir) / domain / "config.json"
        if not cfg_path.exists():
            return None
        try:
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return None
        dirs = data.get("directories", {})
        if not dirs:
            return None
        for kw in ("原始", "流水", "收集箱", "尝试记录"):
            for name in dirs:
                if kw in name:
                    return name
        # 兜底：返回第一个目录
        return next(iter(dirs), None)

    def suggest_domain(self, content: str) -> Optional[str]:
        """根据内容建议领域（简单关键词匹配，LLM 可覆盖此逻辑）

        Args:
            content: 内容文本

        Returns:
            建议的领域名，或 None
        """
        # 简单关键词匹配，实际使用时 LLM 会做更智能的判断
        keyword_map = {
            "育儿": ["孩子", "宝宝", "育儿", "启蒙", "教育"],
            "交易": ["股票", "交易", "信号", "板块", "研报"],
            "个人学习": ["论文", "研究", "学习", "技术"],
            "技能追踪": ["skill", "工具", "github", "开源"],
            "工作": ["项目", "bug", "会议", "周报", "kpi"],
        }

        content_lower = content.lower()
        for domain, keywords in keyword_map.items():
            if any(kw in content_lower for kw in keywords):
                return domain
        return None
