"""SkillOS — Skill 优化器。

基于 chujianyun/skills@skill-optimizer 的审查→计划→确认→实施→校验工作流。
提供自动化的 Skill 优化建议和修复。
"""

import re
from dataclasses import dataclass
from typing import Optional
from skill_parser import SkillParseResult, parse_skill
from skill_analyzer import analyze, AnalysisResult, Finding


@dataclass
class OptimizationPlan:
    """优化计划。"""
    target: str
    scope: str
    findings: list  # list[Finding]
    changes: list  # list[Change]
    estimated_grade: str


@dataclass
class Change:
    """一个具体的修改。"""
    file_path: str
    change_type: str  # modify / add / remove
    section: str
    description: str
    priority: str  # P0 / P1 / P2
    old_content: str
    new_content: str


def generate_optimization_plan(parsed: SkillParseResult) -> OptimizationPlan:
    """生成优化计划（不修改文件）。

    Args:
        parsed: 解析后的 Skill

    Returns:
        OptimizationPlan
    """
    result = analyze(parsed)
    changes = []

    # Generate concrete changes for each finding
    for finding in result.findings:
        if finding.priority in ("P0", "P1"):
            change = _finding_to_change(parsed, finding)
            if change:
                changes.append(change)

    return OptimizationPlan(
        target=parsed.frontmatter.name or parsed.path,
        scope="全文审查",
        findings=result.findings,
        changes=changes,
        estimated_grade=result.projected_grade,
    )


def _finding_to_change(parsed: SkillParseResult, finding: Finding) -> Optional[Change]:
    """将审查发现转化为具体的修改建议。"""
    fm = parsed.frontmatter

    if finding.category == "Description 质量" and "第一人称" in finding.title:
        old = fm.description
        new = re.sub(r"^I (help|assist|will)\s+", "Use this skill whenever the user wants to ", old, flags=re.IGNORECASE)
        new = re.sub(r"^I'm\s+", "This skill is for ", new, flags=re.IGNORECASE)
        if new != old:
            return Change(
                file_path=parsed.path,
                change_type="modify",
                section="frontmatter/description",
                description="将 description 从第一人称改为第三人称",
                priority="P1",
                old_content=old,
                new_content=new,
            )

    if finding.category == "Description 质量" and "多行格式" in finding.title:
        return Change(
            file_path=parsed.path,
            change_type="modify",
            section="frontmatter/description",
            description="将 description 改为单行格式",
            priority="P0",
            old_content=fm.description,
            new_content=fm.description.replace("\n", " ").strip(),
        )

    if finding.category == "长度与披露" and "超过 500" in finding.title:
        return Change(
            file_path=parsed.path,
            change_type="modify",
            section="body",
            description="拆分长章节到 references/ 目录",
            priority="P1",
            old_content=f"(当前 {parsed.body_lines} 行)",
            new_content="将 ## Gotchas 等详细内容移到 references/GOTCHAS.md，在 SKILL.md 中保留一行指针",
        )

    if finding.category == "结构匹配度" and "缺少必要章节" in finding.title:
        missing = finding.title.split("：")[-1] if "：" in finding.title else finding.title
        return Change(
            file_path=parsed.path,
            change_type="add",
            section="body",
            description=f"添加缺失的章节：{missing}",
            priority="P1",
            old_content="",
            new_content=f"## {missing.split(',')[0].strip().title()}\n\n(待填充内容)",
        )

    return None


def format_optimization_plan(plan: OptimizationPlan) -> str:
    """格式化优化计划为 Markdown。"""
    lines = [
        "# Skill 审查结论",
        "",
        "## 审查对象",
        f"- 目标 skill：{plan.target}",
        f"- 本次范围：{plan.scope}",
        "",
    ]

    # Group findings by priority
    for p in ["P0", "P1", "P2"]:
        pf = [f for f in plan.findings if f.priority == p]
        if pf:
            label = {"P0": "高优先级", "P1": "中优先级", "P2": "低优先级"}[p]
            lines.extend([f"## {label}", ""])
            for f in pf:
                lines.append(f"- **{f.title}** — {f.reason}")
            lines.append("")

    if plan.changes:
        lines.extend(["## 优化计划", ""])
        for i, change in enumerate(plan.changes, 1):
            lines.extend([
                f"### {i}. [{change.priority}] {change.description}",
                f"- 文件：`{change.file_path}`",
                f"- 类型：{change.change_type}",
                f"- 位置：{change.section}",
                "",
            ])
            if change.old_content and change.new_content:
                lines.extend([
                    "```diff",
                    f"- {change.old_content[:100]}",
                    f"+ {change.new_content[:100]}",
                    "```",
                    "",
                ])

    lines.extend([
        "---",
        f"## 修复 P0+P1 后预估等级：{plan.estimated_grade}",
        "",
        "> 仅当用户明确回复「按计划执行」「开始修改」「确认修改」后才能实施修改。",
    ])

    return "\n".join(lines)


def apply_description_fix(parsed: SkillParseResult, new_description: str) -> str:
    """应用 description 修复。

    Args:
        parsed: 解析后的 Skill
        new_description: 新的 description

    Returns:
        修改后的完整 SKILL.md 内容
    """
    content = parsed.path
    with open(content, "r", encoding="utf-8") as f:
        raw = f.read()

    # Replace description line in frontmatter
    lines = raw.split("\n")
    result = []
    in_frontmatter = False
    found = False

    for line in lines:
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            result.append(line)
            continue
        if in_frontmatter and line.startswith("description:"):
            result.append(f'description: "{new_description}"')
            found = True
            continue
        result.append(line)

    if not found:
        # Insert after name line
        final = []
        for line in result:
            final.append(line)
            if in_frontmatter and line.startswith("name:"):
                final.append(f'description: "{new_description}"')
        return "\n".join(final)

    return "\n".join(result)
