"""SkillOS — Skill 冲突检测器。

检测多个 Skill 之间的触发词冲突、职责重叠、重复能力等问题。
这是社区目前没有成熟方案的领域，SkillOS 自主设计。
"""

import re
from dataclasses import dataclass, field
from skill_parser import SkillParseResult


@dataclass
class Conflict:
    """一个冲突记录。"""
    conflict_type: str  # trigger_overlap / scope_duplication / capability_duplicate
    severity: str  # high / medium / low
    skill_a: str
    skill_b: str
    detail: str
    suggestion: str


@dataclass
class ConflictReport:
    """冲突检测报告。"""
    total_skills: int
    conflicts: list  # list[Conflict]
    summary: dict  # type -> count


def extract_triggers(parsed: SkillParseResult) -> set:
    """从 description 中提取触发关键词。"""
    desc = parsed.frontmatter.description.lower()
    # Extract quoted phrases
    quoted = set(re.findall(r'"([^"]+)"', parsed.frontmatter.description))
    # Extract key nouns and verbs
    words = set(re.findall(r"\b[a-z]{3,}\b", desc))
    # Remove common stop words
    stop_words = {
        "the", "this", "that", "with", "from", "for", "and", "are", "was",
        "were", "been", "being", "have", "has", "had", "does", "did", "will",
        "would", "could", "should", "may", "might", "can", "shall", "not",
        "but", "what", "when", "where", "how", "which", "who", "whom",
        "use", "skill", "user", "whenever", "asks", "wants", "need",
    }
    keywords = words - stop_words
    return keywords | {q.lower() for q in quoted}


def extract_scope(parsed: SkillParseResult) -> set:
    """从 description 的 'Do NOT' 部分提取负面范围。"""
    desc = parsed.frontmatter.description
    scope = set()
    # Find "Do NOT use for" or similar patterns
    match = re.search(r"Do NOT (?:use|invoke).*?for\s+(.+?)(?:\.|$)", desc, re.IGNORECASE)
    if match:
        scope_text = match.group(1)
        scope = set(re.findall(r"\b[a-z]{3,}\b", scope_text.lower()))
    return scope


def compute_overlap(set_a: set, set_b: set) -> float:
    """计算两个集合的重叠率（Jaccard 系数）。"""
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


def detect_conflicts(skills: list) -> ConflictReport:
    """检测一组 Skill 之间的冲突。

    Args:
        skills: list of SkillParseResult

    Returns:
        ConflictReport
    """
    conflicts = []
    n = len(skills)

    for i in range(n):
        for j in range(i + 1, n):
            a = skills[i]
            b = skills[j]
            name_a = a.frontmatter.name or f"skill_{i}"
            name_b = b.frontmatter.name or f"skill_{j}"

            triggers_a = extract_triggers(a)
            triggers_b = extract_triggers(b)
            overlap = compute_overlap(triggers_a, triggers_b)

            # Trigger overlap
            if overlap > 0.3:
                severity = "high" if overlap > 0.5 else "medium"
                common = triggers_a & triggers_b
                conflicts.append(Conflict(
                    conflict_type="trigger_overlap",
                    severity=severity,
                    skill_a=name_a,
                    skill_b=name_b,
                    detail=f"触发词重叠率 {overlap:.0%}，共 {len(common)} 个共同词：{', '.join(list(common)[:5])}",
                    suggestion="让 description 的前 50 字符包含独特名词，用 'Do NOT use for…' 划清边界",
                ))

            # Scope duplication — both have "Do NOT" pointing to each other's domain
            scope_a = extract_scope(a)
            scope_b = extract_scope(b)
            if scope_a and scope_b:
                scope_overlap = scope_a & scope_b
                if scope_overlap:
                    conflicts.append(Conflict(
                        conflict_type="scope_duplication",
                        severity="medium",
                        skill_a=name_a,
                        skill_b=name_b,
                        detail=f"负面范围重叠：{', '.join(list(scope_overlap)[:5])}",
                        suggestion="明确各自排除范围，避免互相引用",
                    ))

            # Capability duplicate — very similar section structures
            sections_a = {s.title.lower() for s in a.sections if s.level == 2}
            sections_b = {s.title.lower() for s in b.sections if s.level == 2}
            section_overlap = compute_overlap(sections_a, sections_b)
            if section_overlap > 0.5 and len(sections_a) > 3:
                conflicts.append(Conflict(
                    conflict_type="capability_duplicate",
                    severity="low",
                    skill_a=name_a,
                    skill_b=name_b,
                    detail=f"章节结构重叠率 {section_overlap:.0%}，可能有重复能力",
                    suggestion="检查是否可以合并或明确分工",
                ))

    # Build summary
    summary = {}
    for c in conflicts:
        summary[c.conflict_type] = summary.get(c.conflict_type, 0) + 1

    return ConflictReport(
        total_skills=n,
        conflicts=conflicts,
        summary=summary,
    )


def format_conflict_report(report: ConflictReport) -> str:
    """格式化冲突报告为 Markdown。"""
    lines = [
        "# Skill 冲突检测报告",
        "",
        f"**扫描 Skill 数：** {report.total_skills}",
        f"**发现冲突数：** {len(report.conflicts)}",
        "",
    ]

    if not report.conflicts:
        lines.append("未发现冲突。")
        return "\n".join(lines)

    lines.append("## 冲突摘要")
    lines.append("")
    lines.append("| 类型 | 数量 |")
    lines.append("|------|------|")
    for ctype, count in report.summary.items():
        lines.append(f"| {ctype} | {count} |")

    lines.extend(["", "## 冲突详情"])

    for severity in ["high", "medium", "low"]:
        sev_conflicts = [c for c in report.conflicts if c.severity == severity]
        if not sev_conflicts:
            continue
        label = {"high": "高", "medium": "中", "low": "低"}[severity]
        lines.extend(["", f"### {label}严重度"])
        for c in sev_conflicts:
            lines.extend([
                "",
                f"**{c.skill_a}** <-> **{c.skill_b}**",
                f"- 类型：{c.conflict_type}",
                f"- 详情：{c.detail}",
                f"- 建议：{c.suggestion}",
            ])

    return "\n".join(lines)
