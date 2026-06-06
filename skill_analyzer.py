"""SkillOS — Skill 深度分析器。

基于 rate-skill 的 7 维度评分体系，对 SKILL.md 进行完整审查。
输出 A-F 等级、加权分数、逐维度评分和具体修复建议。
"""

import re
from dataclasses import dataclass, field
from skill_parser import SkillParseResult, SkillSection

# 合法 frontmatter 顶级字段
VALID_FM_FIELDS = {
    "name", "description", "license", "compatibility", "when_to_use",
    "argument-hint", "arguments", "disable-model-invocation", "user-invocable",
    "model", "effort", "agent", "hooks", "paths", "shell", "allowed-tools", "metadata",
}

# 不应在顶级出现的字段
INVALID_TOPLEVEL_FIELDS = {"version", "author", "tags", "category"}


@dataclass
class Finding:
    """一个审查发现。"""
    priority: str  # P0 / P1 / P2
    category: str  # 对应维度名
    title: str
    reason: str
    fix: str


@dataclass
class CategoryScore:
    """单维度评分。"""
    name: str
    weight: int
    score: int  # 0-100
    weighted: float = 0.0

    def __post_init__(self):
        self.weighted = round(self.score * self.weight / 100, 1)


@dataclass
class AnalysisResult:
    """完整分析结果。"""
    skill_name: str
    skill_type: str
    overall_score: int  # 0-100
    grade: str  # A/B/C/D/F
    categories: list  # list[CategoryScore]
    strengths: list  # list[str]
    findings: list  # list[Finding]
    projected_grade: str  # 修复 P0+P1 后预估


def grade_from_score(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _analyze_description(result: AnalysisResult, parsed: SkillParseResult):
    """维度 1：Description 质量（25 分）。"""
    desc = parsed.frontmatter.description
    score = 100
    findings = []

    if not desc:
        findings.append(Finding("P0", "Description 质量", "缺少 description",
                                "Description 是 Skill 激活的唯一依据",
                                "在 frontmatter 中添加 description 字段"))
        result.categories.append(CategoryScore("Description 质量", 25, 0))
        result.findings.extend(findings)
        return

    # Multiline check
    if "\n" in desc or "|" in desc[:5] or ">" in desc[:5]:
        findings.append(Finding("P0", "Description 质量", "Description 使用多行格式",
                                "YAML 块标量 (|/>) 会破坏发现机制",
                                "改为单行字符串"))
        score = 0

    # First person check
    if re.search(r"^I\s|I'll|I am|I help|I'm", desc, re.IGNORECASE):
        findings.append(Finding("P1", "Description 质量", "Description 使用第一人称",
                                "第一人称激活率比第三人称低 20 倍 (n=650)",
                                "改为第三人称：'Use this skill whenever the user…'"))
        score = min(score, 40)

    # Directive register check
    has_directive = bool(re.search(r"Use (this skill )?whenever|ALWAYS invoke|Use when", desc, re.IGNORECASE))
    if not has_directive:
        findings.append(Finding("P1", "Description 质量", "缺少指令式触发语态",
                                "被动描述降低激活可靠性",
                                "添加 'Use this skill whenever the user…'"))
        score = min(score, 70)

    # Trigger phrases check
    quoted_triggers = re.findall(r'"([^"]+)"', desc)
    if len(quoted_triggers) < 3:
        findings.append(Finding("P1", "Description 质量",
                                f"只有 {len(quoted_triggers)} 个引号触发短语（需要 ≥3）",
                                "触发短语不足导致激活不稳定",
                                "添加 ≥3 个用户会说的自然语言短语，用引号包裹"))
        score = min(score, 60)

    # Distinctive noun in first 50 chars
    first_50 = desc[:50]
    if re.search(r"^(A skill|A tool|Helps|This skill)", first_50, re.IGNORECASE):
        findings.append(Finding("P1", "Description 质量", "前 50 字符缺少独特名词",
                                "listing-budget 截断后无法区分",
                                "将独特名词移到最前面"))
        score = min(score, 70)

    # Negative scope
    has_negative = bool(re.search(r"Do NOT|don't use|not for|不应", desc, re.IGNORECASE))
    # Not always required, just note

    # Length check
    desc_len = len(desc)
    if desc_len > 1024:
        findings.append(Finding("P0", "Description 质量", f"Description {desc_len} 字符超过 1024 硬上限",
                                "违反 agentskills.io 规范",
                                "精简到 1024 字符以内"))
        score = min(score, 50)
    elif desc_len > 500:
        findings.append(Finding("P1", "Description 质量", f"Description {desc_len} 字符超过 500",
                                "超出软目标，吃 listing budget",
                                "精简到 230 字符软目标"))
        score = min(score, 85)
    elif desc_len > 230:
        findings.append(Finding("P2", "Description 质量", f"Description {desc_len} 字符超过 230 软目标",
                                "超出软目标",
                                "可选：精简到 230 字符"))

    result.categories.append(CategoryScore("Description 质量", 25, score))
    result.findings.extend(findings)

    if score >= 90:
        result.strengths.append("Description 质量优秀：第三人称、指令式、触发词充分")


def _analyze_frontmatter(result: AnalysisResult, parsed: SkillParseResult):
    """维度 2：Frontmatter 有效性（20 分）。"""
    score = 100
    findings = []
    fm = parsed.frontmatter

    # Name validation
    if fm.name:
        if re.search(r"[A-Z]", fm.name):
            findings.append(Finding("P1", "Frontmatter 有效性", "name 包含大写字母",
                                    "name 应全小写 kebab-case",
                                    "改为小写 kebab-case"))
            score -= 15
        if "--" in fm.name:
            findings.append(Finding("P1", "Frontmatter 有效性", "name 包含连续连字符",
                                    "name 不应有连续连字符",
                                    "移除多余连字符"))
            score -= 15
        if "anthropic" in fm.name.lower() or "claude" in fm.name.lower():
            findings.append(Finding("P1", "Frontmatter 有效性", "name 包含保留字",
                                    "'anthropic' 和 'claude' 是保留字",
                                    "换一个不含保留字的 name"))
            score -= 15
    else:
        findings.append(Finding("P0", "Frontmatter 有效性", "缺少 name 字段",
                                "name 是必需字段",
                                "添加 name 字段"))
        score -= 30

    # Check for invalid top-level fields
    raw_fm = parsed.frontmatter.raw
    for line in raw_fm.split("\n"):
        if ":" not in line:
            continue
        key = line.split(":")[0].strip()
        if key in INVALID_TOPLEVEL_FIELDS:
            findings.append(Finding("P1", "Frontmatter 有效性",
                                    f"'{key}' 不应在顶级出现",
                                    f"'{key}' 应放在 metadata 内",
                                    f"将 '{key}' 移到 metadata 下"))
            score -= 15

    score = max(0, score)
    result.categories.append(CategoryScore("Frontmatter 有效性", 20, score))
    result.findings.extend(findings)

    if score >= 90:
        result.strengths.append("Frontmatter 字段规范")


def _analyze_length(result: AnalysisResult, parsed: SkillParseResult):
    """维度 3：长度与渐进式披露（15 分）。"""
    score = 100
    findings = []
    lines = parsed.body_lines

    if lines > 500:
        if not parsed.has_references_dir:
            findings.append(Finding("P0", "长度与披露",
                                    f"正文 {lines} 行超过 500 且无 references/ 目录",
                                    "ETH Zurich 研究：冗长文件降低任务成功率 ~3%",
                                    "拆分细节到 references/ 目录"))
            score = 40
        else:
            over = lines - 500
            penalty = (over // 50 + 1) * 20
            score = max(0, 100 - penalty)
            findings.append(Finding("P1", "长度与披露", f"正文 {lines} 行超过 500",
                                    "超出硬上限",
                                    "继续拆分到 references/"))
    elif lines > 300:
        over = lines - 300
        penalty = (over // 50 + 1) * 20
        score = max(0, 100 - penalty)
        findings.append(Finding("P1", "长度与披露", f"正文 {lines} 行超过 300 软上限",
                                "超出软上限",
                                "拆分到 references/"))

    # Check singular reference/ vs plural references/
    # (would need filesystem check, skip for now)

    result.categories.append(CategoryScore("长度与披露", 15, score))
    result.findings.extend(findings)

    if score >= 90:
        result.strengths.append(f"正文长度合理（{lines} 行）")


def _analyze_structure(result: AnalysisResult, parsed: SkillParseResult):
    """维度 4：结构匹配度（15 分）。"""
    score = 100
    findings = []
    titles = [s.title.lower() for s in parsed.sections]
    stype = parsed.skill_type

    required_sections = {
        "methodology": ["overview", "workflow", "examples", "gotchas"],
        "technical": ["overview", "quick start", "examples", "gotchas"],
        "auditing": ["overview", "rubric", "output format", "examples", "gotchas"],
        "reference": ["overview"],
        "automation": ["overview", "command", "failure", "gotchas"],
    }

    required = required_sections.get(stype, ["overview"])
    missing = []
    for req in required:
        if not any(req in t for t in titles):
            missing.append(req)

    if missing:
        penalty = len(missing) * 20
        score = max(0, 100 - penalty)
        findings.append(Finding("P1", "结构匹配度",
                                f"类型 '{stype}' 缺少必要章节：{', '.join(missing)}",
                                f"{stype} 类型需要这些章节",
                                f"添加 ## {missing[0].title()} 等章节"))

    result.categories.append(CategoryScore("结构匹配度", 15, score))
    result.findings.extend(findings)

    if score >= 90:
        result.strengths.append(f"结构匹配 '{stype}' 类型模板")


def _analyze_examples(result: AnalysisResult, parsed: SkillParseResult):
    """维度 5：示例质量（10 分）。"""
    score = 100
    findings = []
    body = parsed.body.lower()

    has_example = "example" in body or "示例" in body
    has_positive = "✅" in parsed.body or "desired" in body or "正确" in body
    has_negative = "❌" in parsed.body or "anti-pattern" in body or "反模式" in body or "counter" in body

    if not has_example:
        findings.append(Finding("P1", "示例质量", "缺少示例章节",
                                "示例帮助 AI 理解期望行为",
                                "添加 ## Examples 章节，含正反对比"))
        score = 40
    else:
        if not has_positive:
            findings.append(Finding("P1", "示例质量", "缺少期望行为示例",
                                    "期望示例应在前",
                                    "添加 ✅ 正确用法示例"))
            score -= 25
        if not has_negative:
            findings.append(Finding("P1", "示例质量", "缺少反模式示例",
                                    "反模式帮助避免常见错误",
                                    "添加 ❌ 反模式示例"))
            score -= 25

    # Check for Good/Bad XML tags
    if "<Good>" in parsed.body or "<Bad>" in parsed.body:
        findings.append(Finding("P2", "示例质量", "使用了 <Good>/<Bad> XML 标签",
                                "0/8 顶级 Skill 使用此格式",
                                "改用 ✅/❌ 或 ## Anti-Pattern: 标题"))
        score -= 10

    score = max(0, score)
    result.categories.append(CategoryScore("示例质量", 10, score))
    result.findings.extend(findings)

    if score >= 90:
        result.strengths.append("示例质量好：有正反对比")


def _analyze_conciseness(result: AnalysisResult, parsed: SkillParseResult):
    """维度 6：简洁性（10 分）。"""
    score = 100
    findings = []
    body = parsed.body

    # Check for verbose patterns
    verbose_patterns = [
        (r"(?i)it is important to note that", "冗余引入语"),
        (r"(?i)as we all know", "常识重述"),
        (r"(?i)in this section,? we will", "章节预告"),
        (r"(?i)let me explain", "口语化引入"),
    ]
    for pattern, label in verbose_patterns:
        if re.search(pattern, body):
            findings.append(Finding("P2", "简洁性", f"发现冗余：'{label}'",
                                    "浪费 token",
                                    "删除或精简"))
            score -= 10

    score = max(0, score)
    result.categories.append(CategoryScore("简洁性", 10, score))
    result.findings.extend(findings)

    if score >= 90:
        result.strengths.append("内容简洁，无冗余")


def _analyze_antipatterns(result: AnalysisResult, parsed: SkillParseResult):
    """维度 7：反模式规避（5 分）。"""
    score = 100
    findings = []
    body = parsed.body
    path = parsed.path

    # ALL-CAPS section headers
    caps_headers = re.findall(r"^## [A-Z\s]{5,}$", body, re.MULTILINE)
    if caps_headers:
        findings.append(Finding("P2", "反模式规避", "发现全大写章节标题",
                                "Anthropic 标记为黄旗",
                                "改为正常大小写标题"))
        score -= 20

    # Windows backslash paths (not in code blocks)
    if "\\" in body and "```" not in body[:100]:
        findings.append(Finding("P2", "反模式规避", "可能包含 Windows 反斜杠路径",
                                "跨平台兼容性问题",
                                "改为正斜杠路径"))
        score -= 20

    # Mega-skill check (too many unrelated sections)
    if len(parsed.sections) > 15:
        findings.append(Finding("P1", "反模式规避", f"章节过多（{len(parsed.sections)} 个）",
                                "可能是 Mega-skill，捆绑了不相关职责",
                                "拆分为独立 Skill"))
        score -= 20

    score = max(0, score)
    result.categories.append(CategoryScore("反模式规避", 5, score))
    result.findings.extend(findings)

    if score >= 90:
        result.strengths.append("无已知反模式")


def analyze(parsed: SkillParseResult) -> AnalysisResult:
    """对解析后的 Skill 进行完整 7 维度分析。

    Args:
        parsed: SkillParseResult 对象

    Returns:
        AnalysisResult 完整分析结果
    """
    result = AnalysisResult(
        skill_name=parsed.frontmatter.name or os.path.basename(os.path.dirname(parsed.path)),
        skill_type=parsed.skill_type,
        overall_score=0,
        grade="F",
        categories=[],
        strengths=[],
        findings=[],
        projected_grade="F",
    )

    _analyze_description(result, parsed)
    _analyze_frontmatter(result, parsed)
    _analyze_length(result, parsed)
    _analyze_structure(result, parsed)
    _analyze_examples(result, parsed)
    _analyze_conciseness(result, parsed)
    _analyze_antipatterns(result, parsed)

    # Calculate weighted total
    total = sum(c.weighted for c in result.categories)
    result.overall_score = round(total)
    result.grade = grade_from_score(result.overall_score)

    # Estimate projected grade (after fixing P0 + P1)
    p0_p1_penalty = 0
    for f in result.findings:
        if f.priority == "P0":
            p0_p1_penalty += 15
        elif f.priority == "P1":
            p0_p1_penalty += 8
    projected = min(100, result.overall_score + p0_p1_penalty)
    result.projected_grade = f"{grade_from_score(projected)} ({projected}/100)"

    return result


def format_report(result: AnalysisResult) -> str:
    """将分析结果格式化为 Markdown 报告。"""
    lines = [
        f"# Skill 审查报告：{result.skill_name}",
        "",
        f"**检测类型：** {result.skill_type}",
        f"**综合等级：** {result.grade} ({result.overall_score}/100)",
        "",
        "## 评分明细",
        "",
        "| 维度 | 得分 | 权重 | 加权 |",
        "|------|------|------|------|",
    ]
    for c in result.categories:
        lines.append(f"| {c.name} | {c.score} | {c.weight} | {c.weighted} |")

    if result.strengths:
        lines.extend(["", "## 优势"])
        for s in result.strengths:
            lines.append(f"- {s}")

    if result.findings:
        lines.extend(["", "## 发现（按优先级）"])
        for p in ["P0", "P1", "P2"]:
            pf = [f for f in result.findings if f.priority == p]
            if pf:
                for f in pf:
                    lines.extend([
                        "",
                        f"### {f.priority} — {f.title}",
                        f"**原因：** {f.reason}",
                        f"**修复：** {f.fix}",
                    ])

    lines.extend([
        "",
        f"## 修复 P0+P1 后预估等级：{result.projected_grade}",
    ])

    return "\n".join(lines)


import os  # noqa: E402 (needed at module level for analyze())
