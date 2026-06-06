"""SkillOS — Skill 注册表管理。

管理已安装 Skill 的索引、扫描、查询。
对应 SKILL-REGISTRY.md 和 scan-skills.sh 的 Python 实现。
"""

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from skill_parser import parse_skill, SkillParseResult


@dataclass
class SkillEntry:
    """注册表中的一个 Skill 条目。"""
    name: str
    path: str
    scope: str  # global / project
    agents: list  # list[str]
    description: str = ""
    parsed: Optional[SkillParseResult] = None


@dataclass
class Registry:
    """Skill 注册表。"""
    entries: list  # list[SkillEntry]
    scan_time: str = ""

    def get_by_name(self, name: str) -> Optional[SkillEntry]:
        """按名称查找 Skill。"""
        name_lower = name.lower()
        for entry in self.entries:
            if entry.name.lower() == name_lower:
                return entry
        # Fuzzy match
        for entry in self.entries:
            if name_lower in entry.name.lower():
                return entry
        return None

    def get_by_scope(self, scope: str) -> list:
        """按作用域筛选。"""
        return [e for e in self.entries if e.scope == scope]

    def search(self, query: str) -> list:
        """按关键词搜索 Skill。"""
        query_lower = query.lower()
        results = []
        for entry in self.entries:
            if (query_lower in entry.name.lower() or
                    query_lower in entry.description.lower()):
                results.append(entry)
        return results


def scan_installed_skills(scope: str = "global") -> Registry:
    """扫描已安装的 Skill。

    Args:
        scope: "global" 或 "project"

    Returns:
        Registry 对象
    """
    from datetime import datetime
    entries = []

    # Try npx skills ls --json
    try:
        cmd = ["npx", "skills", "ls", "--json"]
        if scope == "global":
            cmd.insert(2, "-g")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            data = json.loads(result.stdout)
            if isinstance(data, list):
                for item in data:
                    entry = SkillEntry(
                        name=item.get("name", "unknown"),
                        path=item.get("path", ""),
                        scope=item.get("scope", scope),
                        agents=item.get("agents", []),
                    )
                    # Try to parse SKILL.md for description
                    skill_md = os.path.join(entry.path, "SKILL.md")
                    if os.path.isfile(skill_md):
                        try:
                            parsed = parse_skill(entry.path)
                            if parsed:
                                entry.description = parsed.frontmatter.description
                                entry.parsed = parsed
                        except Exception:
                            pass
                    entries.append(entry)
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        pass

    # Fallback: scan common directories
    if not entries:
        entries = _scan_directories(scope)

    return Registry(
        entries=entries,
        scan_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


def _scan_directories(scope: str) -> list:
    """直接扫描文件系统查找 Skill。"""
    entries = []
    home = Path.home()

    search_dirs = []
    if scope == "global":
        search_dirs = [
            home / ".claude" / "skills",
            home / ".agents" / "skills",
        ]
    else:
        search_dirs = [
            Path.cwd() / ".claude" / "skills",
            Path.cwd() / "skills",
        ]

    for search_dir in search_dirs:
        if not search_dir.is_dir():
            continue
        for item in search_dir.iterdir():
            if not item.is_dir():
                continue
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                parsed = parse_skill(str(item))
                entry = SkillEntry(
                    name=parsed.frontmatter.name if parsed else item.name,
                    path=str(item),
                    scope=scope,
                    agents=["Claude Code"],
                    description=parsed.frontmatter.description if parsed else "",
                    parsed=parsed,
                )
                entries.append(entry)

    return entries


def generate_registry_markdown(registry: Registry) -> str:
    """生成 SKILL-REGISTRY.md 的 Markdown 内容。"""
    lines = [
        "# Skill Registry",
        "",
        "> SkillOS 维护的已安装 Skill 索引。",
        "",
        f"> 最后扫描时间: {registry.scan_time}",
        "",
        f"**共 {len(registry.entries)} 个 Skill**",
        "",
        "| # | 名称 | 作用域 | Agent | 描述 |",
        "|---|------|--------|-------|------|",
    ]

    for i, entry in enumerate(registry.entries, 1):
        agents_str = ", ".join(entry.agents[:2])
        if len(entry.agents) > 2:
            agents_str += f" +{len(entry.agents) - 2}"
        desc = entry.description[:80] + "…" if len(entry.description) > 80 else entry.description
        desc = desc.replace("|", "\\|")  # Escape pipe for markdown table
        lines.append(f"| {i} | {entry.name} | {entry.scope} | {agents_str} | {desc} |")

    lines.extend(["", "---", ""])
    lines.append(f"由 `python skillos.py registry` 自动生成。")

    return "\n".join(lines)


def save_registry(registry: Registry, output_path: str):
    """保存注册表到文件。"""
    content = generate_registry_markdown(registry)
    Path(output_path).write_text(content, encoding="utf-8")
