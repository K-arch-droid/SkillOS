"""SkillOS — SKILL.md 文件解析器。

解析 SKILL.md 的 frontmatter、body 结构、章节、行数等。
所有其他模块的基础依赖。
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SkillFrontmatter:
    """SKILL.md 的 YAML frontmatter 数据。"""
    name: str = ""
    description: str = ""
    license: str = ""
    argument_hint: str = ""
    allowed_tools: str = ""
    disable_model_invocation: bool = False
    user_invocable: bool = True
    model: str = ""
    effort: str = ""
    paths: str = ""
    metadata: dict = field(default_factory=dict)
    raw: str = ""


@dataclass
class SkillSection:
    """SKILL.md 中的一个章节。"""
    title: str
    level: int  # ## = 2, ### = 3
    line_start: int
    line_end: int
    content: str


@dataclass
class SkillParseResult:
    """SKILL.md 解析结果。"""
    path: str
    frontmatter: SkillFrontmatter
    body: str
    body_lines: int
    sections: list  # list[SkillSection]
    has_references_dir: bool
    references_files: list  # list[str]
    skill_type: str  # methodology / technical / auditing / reference / automation / unknown


def parse_frontmatter(raw: str) -> SkillFrontmatter:
    """解析 YAML frontmatter 字符串。"""
    fm = SkillFrontmatter(raw=raw)
    for line in raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key == "name":
            fm.name = value
        elif key == "description":
            fm.description = value
        elif key == "license":
            fm.license = value
        elif key == "argument-hint":
            fm.argument_hint = value
        elif key == "allowed-tools":
            fm.allowed_tools = value
        elif key == "disable-model-invocation":
            fm.disable_model_invocation = value.lower() == "true"
        elif key == "user-invocable":
            fm.user_invocable = value.lower() != "false"
        elif key == "model":
            fm.model = value
        elif key == "effort":
            fm.effort = value
        elif key == "paths":
            fm.paths = value
    return fm


def parse_sections(body: str) -> list:
    """从 body 中提取所有章节。"""
    sections = []
    lines = body.split("\n")
    current_title = None
    current_level = 0
    current_start = 0
    current_lines = []

    for i, line in enumerate(lines):
        match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if match:
            if current_title is not None:
                sections.append(SkillSection(
                    title=current_title,
                    level=current_level,
                    line_start=current_start,
                    line_end=i - 1,
                    content="\n".join(current_lines),
                ))
            current_level = len(match.group(1))
            current_title = match.group(2).strip()
            current_start = i
            current_lines = []
        else:
            current_lines.append(line)

    if current_title is not None:
        sections.append(SkillSection(
            title=current_title,
            level=current_level,
            line_start=current_start,
            line_end=len(lines) - 1,
            content="\n".join(current_lines),
        ))

    return sections


def detect_skill_type(sections: list, body: str) -> str:
    """根据章节结构检测 Skill 类型。"""
    titles = [s.title.lower() for s in sections]
    body_lower = body.lower()

    # Check for methodology patterns
    has_phases = any("phase" in t or "step" in t or "workflow" in t for t in titles)
    has_checklist = any("checklist" in t or "verify" in t or "verification" in t for t in titles)
    if has_phases:
        return "methodology"

    # Check for auditing patterns
    has_rubric = any("rubric" in t or "scoring" in t or "score" in t for t in titles)
    has_output_format = any("output format" in t or "report" in t for t in titles)
    if has_rubric:
        return "auditing"

    # Check for technical patterns
    has_quick_start = any("quick start" in t or "getting started" in t for t in titles)
    has_api = any("api" in t or "reference" in t or "quick reference" in t for t in titles)
    if has_quick_start or (has_api and "how it works" in body_lower):
        return "technical"

    # Check for reference patterns
    if any("schema" in t or "lookup" in t or "convention" in t for t in titles):
        return "reference"

    # Check for automation patterns
    has_command = any("command" in t or "invocation" in t or "usage" in t for t in titles)
    has_failure = any("failure" in t or "error" in t for t in titles)
    if has_command and has_failure:
        return "automation"

    return "unknown"


def parse_skill(skill_path: str) -> Optional[SkillParseResult]:
    """解析一个 SKILL.md 文件。

    Args:
        skill_path: SKILL.md 文件路径或包含 SKILL.md 的目录路径

    Returns:
        SkillParseResult 或 None（文件不存在时）
    """
    path = Path(skill_path)
    if path.is_dir():
        path = path / "SKILL.md"
    if not path.exists():
        return None

    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.split("\n")

    # Parse frontmatter
    fm = SkillFrontmatter()
    body = content
    if lines and lines[0].strip() == "---":
        fm_lines = []
        body_start = 0
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == "---":
                body_start = i + 1
                break
            fm_lines.append(line)
        fm = parse_frontmatter("\n".join(fm_lines))
        body = "\n".join(lines[body_start:])

    body_lines = len(body.strip().split("\n"))
    sections = parse_sections(body)
    skill_type = detect_skill_type(sections, body)

    # Check for references directory
    parent = path.parent
    refs_dir = parent / "references"
    has_refs = refs_dir.is_dir()
    refs_files = []
    if has_refs:
        refs_files = [f.name for f in refs_dir.iterdir() if f.is_file()]

    return SkillParseResult(
        path=str(path),
        frontmatter=fm,
        body=body,
        body_lines=body_lines,
        sections=sections,
        has_references_dir=has_refs,
        references_files=refs_files,
        skill_type=skill_type,
    )


def find_skill_md(directory: str) -> list:
    """在目录中递归查找所有 SKILL.md 文件。"""
    results = []
    for root, dirs, files in os.walk(directory):
        if "SKILL.md" in files:
            results.append(os.path.join(root, "SKILL.md"))
        # Skip node_modules and hidden dirs
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
    return results


def get_section_by_title(sections: list, title_pattern: str) -> Optional[SkillSection]:
    """按标题模糊匹配查找章节。"""
    pattern = title_pattern.lower()
    for section in sections:
        if pattern in section.title.lower():
            return section
    return None


def get_all_section_titles(sections: list) -> list:
    """获取所有章节标题。"""
    return [s.title for s in sections]
