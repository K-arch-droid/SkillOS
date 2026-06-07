"""SkillOS — Relationship Intelligence Engine。

检测 Skill 之间的多种关系：冲突、互补、协作、引用、领域相邻。
这是社区目前没有成熟方案的领域，SkillOS 自主设计。
"""

import re
import json
from dataclasses import dataclass, field
from skill_parser import SkillParseResult


# ── 原有数据结构（向后兼容） ──────────────────────────────────

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


# ── 新增数据结构（Relationship Intelligence） ──────────────────

@dataclass
class Relationship:
    """两个 Skill 之间的关系。"""
    relation_type: str  # conflict / complement / collaboration / reference / domain_adjacency
    source: str  # extracted / inferred
    confidence: float  # 0.0 - 1.0
    skill_a: str
    skill_b: str
    reason: str


@dataclass
class RelationshipReport:
    """Skill 关系图谱报告。"""
    total_skills: int
    relationships: list  # list[Relationship]
    summary: dict  # relation_type -> count


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
    # Deduplicate by name
    seen_names = set()
    unique_skills = []
    for s in skills:
        name = (s.frontmatter.name or "").lower()
        if name and name not in seen_names:
            seen_names.add(name)
            unique_skills.append(s)
        elif not name:
            unique_skills.append(s)
    skills = unique_skills

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


# ── Relationship Intelligence ─────────────────────────────────

# 领域相邻关系映射（哪些领域天然互补）
DOMAIN_ADJACENCY = {
    "code_review": ["testing", "security", "architecture"],
    "testing": ["code_review", "deployment", "security"],
    "documentation": ["architecture", "product"],
    "architecture": ["code_review", "documentation", "deployment"],
    "deployment": ["testing", "security", "architecture"],
    "security": ["code_review", "testing", "deployment"],
    "performance": ["code_review", "architecture"],
    "design": ["product", "documentation"],
    "product": ["design", "documentation", "architecture"],
    "skill_management": [],
    "browser": ["testing"],
    "git": ["code_review", "deployment"],
}

# 协作关系：(产出方能力, 消费方能力) → 推断置信度
COLLABORATION_PATTERNS = [
    ({"generate", "create", "scaffold", "build"}, {"review", "audit", "check", "inspect"}, 0.78),
    ({"generate", "create", "build", "code"}, {"test", "testing", "verify", "validate"}, 0.82),
    ({"test", "testing", "verify"}, {"deploy", "release", "ci", "cd"}, 0.75),
    ({"design", "architect", "plan"}, {"code", "implement", "build", "develop"}, 0.70),
    ({"analyze", "audit", "review", "rate"}, {"optimize", "improve", "fix", "refactor"}, 0.80),
    ({"document", "write", "readme"}, {"deploy", "release", "publish"}, 0.65),
]


def _get_skill_capabilities(parsed: SkillParseResult) -> set:
    """从 Skill 的 name + description 中提取能力关键词。"""
    text = f"{parsed.frontmatter.name} {parsed.frontmatter.description}".lower()
    words = set(re.findall(r"[a-z]{3,}", text))
    stop_words = {
        "the", "this", "that", "with", "from", "for", "and", "are", "was",
        "use", "skill", "user", "whenever", "claude", "code", "help",
    }
    return words - stop_words


def _get_skill_domain(parsed: SkillParseResult) -> set:
    """返回 Skill 匹配到的领域集合。"""
    from skill_router import DOMAIN_KEYWORDS
    text = f"{parsed.frontmatter.name} {parsed.frontmatter.description}".lower()
    matched_domains = set()
    for domain, config in DOMAIN_KEYWORDS.items():
        for kw in config["keywords"]:
            if kw in text:
                matched_domains.add(domain)
                break
        else:
            for pattern in config["skill_patterns"]:
                if pattern in text:
                    matched_domains.add(domain)
                    break
    return matched_domains


def _extract_referenced_skills(parsed: SkillParseResult) -> set:
    """从 SKILL.md 正文中提取被引用的其他 Skill 名称。"""
    text = parsed.body
    refs = set()
    refs.update(re.findall(r"@([a-z][a-z0-9-]*)", text.lower()))
    refs.update(re.findall(r"([a-z][a-z0-9-]*)\.md", text.lower()))
    quoted = re.findall(r'"([a-z][a-z0-9-]*)"', text.lower())
    refs.update(q for q in quoted if len(q) > 3)
    noise = {"skill", "skills", "example", "output", "input", "error", "none", "true", "false"}
    refs -= noise
    return refs


def detect_relationships(skills: list) -> RelationshipReport:
    """检测一组 Skill 之间的所有关系。

    Args:
        skills: list of SkillParseResult

    Returns:
        RelationshipReport
    """
    # Deduplicate by name to avoid self-conflict from duplicate entries
    seen_names = set()
    unique_skills = []
    for s in skills:
        name = (s.frontmatter.name or "").lower()
        if name and name not in seen_names:
            seen_names.add(name)
            unique_skills.append(s)
        elif not name:
            unique_skills.append(s)
    skills = unique_skills

    relationships = []
    n = len(skills)

    skill_meta = []
    for skill in skills:
        name = skill.frontmatter.name or ""
        skill_meta.append({
            "name": name,
            "triggers": extract_triggers(skill),
            "scope": extract_scope(skill),
            "capabilities": _get_skill_capabilities(skill),
            "domains": _get_skill_domain(skill),
            "references": _extract_referenced_skills(skill),
        })

    for i in range(n):
        for j in range(i + 1, n):
            meta_a = skill_meta[i]
            meta_b = skill_meta[j]
            name_a = meta_a["name"]
            name_b = meta_b["name"]

            # 1. Conflict
            overlap = compute_overlap(meta_a["triggers"], meta_b["triggers"])
            if overlap > 0.3:
                common = meta_a["triggers"] & meta_b["triggers"]
                relationships.append(Relationship(
                    relation_type="conflict",
                    source="extracted",
                    confidence=min(1.0, overlap),
                    skill_a=name_a,
                    skill_b=name_b,
                    reason=f"触发词重叠率 {overlap:.0%}，共 {len(common)} 个共同词",
                ))
            if meta_a["scope"] and meta_b["scope"]:
                scope_overlap = meta_a["scope"] & meta_b["scope"]
                if scope_overlap:
                    relationships.append(Relationship(
                        relation_type="conflict",
                        source="extracted",
                        confidence=0.8,
                        skill_a=name_a,
                        skill_b=name_b,
                        reason=f"负面范围重叠：{', '.join(list(scope_overlap)[:3])}",
                    ))

            # 2. Complement
            if overlap < 0.15:
                adj_domains_a = set()
                for d in meta_a["domains"]:
                    adj_domains_a.update(DOMAIN_ADJACENCY.get(d, []))
                shared_adj = adj_domains_a & meta_b["domains"]
                if shared_adj:
                    relationships.append(Relationship(
                        relation_type="complement",
                        source="inferred",
                        confidence=0.75,
                        skill_a=name_a,
                        skill_b=name_b,
                        reason=f"领域相邻：{name_a} 的领域 {meta_a['domains']} 与 {name_b} 的领域 {meta_b['domains']} 互补",
                    ))

            # 3. Reference
            if name_b in meta_a["references"] or name_a in meta_b["references"]:
                relationships.append(Relationship(
                    relation_type="reference",
                    source="extracted",
                    confidence=1.0,
                    skill_a=name_a,
                    skill_b=name_b,
                    reason="SKILL.md 正文中存在交叉引用",
                ))

            # 4. Domain Adjacency
            for d_a in meta_a["domains"]:
                for d_b in meta_b["domains"]:
                    if d_b in DOMAIN_ADJACENCY.get(d_a, []) and d_a != d_b:
                        already = any(
                            r.relation_type == "complement"
                            and {r.skill_a, r.skill_b} == {name_a, name_b}
                            for r in relationships
                        )
                        if not already:
                            relationships.append(Relationship(
                                relation_type="domain_adjacency",
                                source="inferred",
                                confidence=0.65,
                                skill_a=name_a,
                                skill_b=name_b,
                                reason=f"领域相邻：{d_a} ↔ {d_b}",
                            ))

            # 5. Collaboration
            caps_a = meta_a["capabilities"]
            caps_b = meta_b["capabilities"]
            for prod_kw, cons_kw, conf in COLLABORATION_PATTERNS:
                a_produces = bool(caps_a & prod_kw)
                b_consumes = bool(caps_b & cons_kw)
                b_produces = bool(caps_b & prod_kw)
                a_consumes = bool(caps_a & cons_kw)
                if a_produces and b_consumes:
                    relationships.append(Relationship(
                        relation_type="collaboration",
                        source="inferred",
                        confidence=conf,
                        skill_a=name_a,
                        skill_b=name_b,
                        reason=f"{name_a} 的产出可作为 {name_b} 的输入",
                    ))
                    break
                if b_produces and a_consumes:
                    relationships.append(Relationship(
                        relation_type="collaboration",
                        source="inferred",
                        confidence=conf,
                        skill_a=name_b,
                        skill_b=name_a,
                        reason=f"{name_b} 的产出可作为 {name_a} 的输入",
                    ))
                    break

    relationships = _deduplicate_relationships(relationships)

    summary = {}
    for r in relationships:
        summary[r.relation_type] = summary.get(r.relation_type, 0) + 1

    return RelationshipReport(
        total_skills=n,
        relationships=relationships,
        summary=summary,
    )


def _deduplicate_relationships(rels: list) -> list:
    """去重：同类型同 pair 只保留最高 confidence。"""
    best = {}
    for r in rels:
        key = (r.relation_type, frozenset({r.skill_a, r.skill_b}))
        if key not in best or r.confidence > best[key].confidence:
            best[key] = r
    return list(best.values())


def format_relationship_report(report: RelationshipReport) -> str:
    """格式化关系报告为 Markdown。"""
    lines = [
        "# Skill 关系图谱",
        "",
        f"**扫描 Skill 数：** {report.total_skills}",
        f"**发现关系数：** {len(report.relationships)}",
        "",
    ]

    if not report.relationships:
        lines.append("未发现任何关系。")
        return "\n".join(lines)

    lines.append("## 关系摘要")
    lines.append("")
    lines.append("| 类型 | 数量 | 说明 |")
    lines.append("|------|------|------|")
    type_labels = {
        "conflict": ("冲突", "触发词重叠或职责冲突"),
        "complement": ("互补", "领域相邻、适合配合使用"),
        "collaboration": ("协作", "产出方可作为消费方输入"),
        "reference": ("引用", "SKILL.md 正文互相引用"),
        "domain_adjacency": ("领域相邻", "属于相邻领域"),
    }
    for rtype, count in sorted(report.summary.items()):
        label, desc = type_labels.get(rtype, (rtype, ""))
        lines.append(f"| {label} | {count} | {desc} |")

    for rtype in ["conflict", "complement", "collaboration", "reference", "domain_adjacency"]:
        typed = [r for r in report.relationships if r.relation_type == rtype]
        if not typed:
            continue
        label, _ = type_labels.get(rtype, (rtype, ""))
        lines.extend(["", f"## {label}"])
        typed.sort(key=lambda r: r.confidence, reverse=True)
        for r in typed:
            source_tag = "📎 提取" if r.source == "extracted" else "🔮 推断"
            lines.append(f"- **{r.skill_a}** ↔ **{r.skill_b}** [{source_tag} {r.confidence:.0%}]")
            lines.append(f"  {r.reason}")

    return "\n".join(lines)


def relationships_to_mermaid(report: RelationshipReport) -> str:
    """将关系图谱导出为 Mermaid 格式。"""
    lines = ["graph LR"]

    nodes = set()
    for r in report.relationships:
        nodes.add(r.skill_a)
        nodes.add(r.skill_b)

    def clean(name):
        return re.sub(r"[^a-zA-Z0-9_]", "_", name)

    for node in sorted(nodes):
        lines.append(f"    {clean(node)}[\"{node}\"]")

    style_map = {
        "conflict": ("--", "🔴"),
        "complement": ("--", "🟢"),
        "collaboration": ("--", "🔵"),
        "reference": ("-.->", "⚪"),
        "domain_adjacency": ("--", "🟠"),
    }
    for r in report.relationships:
        style, icon = style_map.get(r.relation_type, ("--", "⚪"))
        label = f"{icon} {r.relation_type} ({r.confidence:.0%})"
        lines.append(f"    {clean(r.skill_a)} {style} |{label}| {clean(r.skill_b)}")

    return "\n".join(lines)


def relationships_to_json(report: RelationshipReport) -> str:
    """将关系图谱导出为 JSON。"""
    data = {
        "total_skills": report.total_skills,
        "summary": report.summary,
        "relationships": [
            {
                "type": r.relation_type,
                "source": r.source,
                "confidence": r.confidence,
                "skill_a": r.skill_a,
                "skill_b": r.skill_b,
                "reason": r.reason,
            }
            for r in report.relationships
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)
