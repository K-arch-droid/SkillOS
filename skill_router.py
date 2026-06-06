"""SkillOS — Skill 智能路由器。

根据用户请求的语义，匹配最合适的 Skill。
基于 charon-fan/agent-playbook@skill-router 的路由模式。
"""

import re
from dataclasses import dataclass
from skill_parser import SkillParseResult


@dataclass
class RouteMatch:
    """一个路由匹配结果。"""
    skill_name: str
    confidence: float  # 0.0 - 1.0
    reason: str
    matched_triggers: list  # list[str]


@dataclass
class RouteResult:
    """路由结果。"""
    query: str
    matches: list  # list[RouteMatch], sorted by confidence desc
    best_match: RouteMatch  # or None


# 领域关键词 → Skill 类型/名称映射
DOMAIN_KEYWORDS = {
    "code_review": {
        "keywords": ["review", "pr", "pull request", "code review", "审查", "代码审查", "检查代码"],
        "skill_patterns": ["code-review", "review", "code-reviewer"],
    },
    "testing": {
        "keywords": ["test", "testing", "unit test", "e2e", "测试", "单元测试", "集成测试"],
        "skill_patterns": ["test", "testing", "jest", "playwright", "qa"],
    },
    "documentation": {
        "keywords": ["doc", "readme", "api doc", "文档", "说明文档", "技术文档"],
        "skill_patterns": ["doc", "documentation", "readme", "api-doc"],
    },
    "architecture": {
        "keywords": ["design", "architecture", "solution", "架构", "设计方案", "技术方案"],
        "skill_patterns": ["architect", "design", "solution"],
    },
    "deployment": {
        "keywords": ["deploy", "ci/cd", "release", "deploy", "部署", "上线", "发布"],
        "skill_patterns": ["deploy", "ci", "cd", "release"],
    },
    "security": {
        "keywords": ["security", "vulnerability", "owasp", "安全", "漏洞"],
        "skill_patterns": ["security", "audit", "vulnerability"],
    },
    "performance": {
        "keywords": ["performance", "optimize", "speed", "slow", "性能", "优化", "提速"],
        "skill_patterns": ["performance", "optimize", "speed"],
    },
    "design": {
        "keywords": ["ui", "ux", "design system", "wireframe", "设计", "界面"],
        "skill_patterns": ["design", "ui", "ux", "figma"],
    },
    "product": {
        "keywords": ["prd", "product requirements", "需求文档", "产品需求"],
        "skill_patterns": ["prd", "product", "requirements"],
    },
    "skill_management": {
        "keywords": ["skill", "find skill", "create skill", "rate skill", "optimize skill",
                     "找skill", "创建skill", "评价skill", "优化skill", "生成skill"],
        "skill_patterns": ["skill", "skillos"],
    },
    "browser": {
        "keywords": ["browser", "scrape", "web automation", "浏览器", "抓取", "自动化"],
        "skill_patterns": ["browser", "playwright", "selenium", "puppeteer"],
    },
    "git": {
        "keywords": ["commit", "branch", "merge", "git", "提交", "分支"],
        "skill_patterns": ["commit", "git", "branch"],
    },
}


def _tokenize(text: str) -> set:
    """分词并去停用词。"""
    words = set(re.findall(r"[a-z一-鿿]{2,}", text.lower()))
    stop_words = {
        "the", "this", "that", "with", "from", "for", "and", "are", "was",
        "been", "have", "has", "had", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "not", "but", "what",
        "when", "where", "how", "which", "who", "help", "please",
        "want", "need", "make", "get", "set",
    }
    return words - stop_words


def _match_skill_to_query(query_tokens: set, domain_keywords: set) -> float:
    """计算查询词与领域关键词的匹配度。"""
    if not query_tokens or not domain_keywords:
        return 0.0
    overlap = query_tokens & domain_keywords
    return len(overlap) / max(len(domain_keywords), 1)


def route_request(query: str, available_skills: list) -> RouteResult:
    """将用户请求路由到最合适的 Skill。

    Args:
        query: 用户的自然语言请求
        available_skills: list of SkillParseResult

    Returns:
        RouteResult 匹配结果
    """
    query_tokens = _tokenize(query)
    query_lower = query.lower()
    matches = []

    for skill in available_skills:
        name = skill.frontmatter.name or ""
        desc = skill.frontmatter.description or ""

        # Extract skill's trigger keywords
        skill_triggers = set(re.findall(r'"([^"]+)"', desc))
        skill_tokens = _tokenize(desc)
        skill_name_tokens = set(re.findall(r"[a-z]+", name.lower()))

        # Score 1: Direct trigger phrase match
        trigger_score = 0
        matched_triggers = []
        for trigger in skill_triggers:
            trigger_lower = trigger.lower()
            if trigger_lower in query_lower or query_lower in trigger_lower:
                trigger_score += 1
                matched_triggers.append(trigger)
            # Partial word match
            trigger_words = _tokenize(trigger)
            overlap = query_tokens & trigger_words
            if len(overlap) >= max(1, len(trigger_words) // 2):
                trigger_score += 0.5
                matched_triggers.append(trigger)

        # Score 2: Keyword overlap with description
        keyword_overlap = len(query_tokens & skill_tokens) / max(len(query_tokens), 1)

        # Score 3: Name match
        name_score = len(query_tokens & skill_name_tokens) / max(len(skill_name_tokens), 1)

        # Score 4: Domain keyword match
        domain_score = 0
        for domain, config in DOMAIN_KEYWORDS.items():
            domain_tokens = set(config["keywords"])
            if query_tokens & domain_tokens:
                # Check if skill name matches domain patterns
                for pattern in config["skill_patterns"]:
                    if pattern in name.lower() or pattern in desc.lower():
                        domain_score = max(domain_score, 0.8)
                        break

        # Weighted total
        confidence = min(1.0, (
            trigger_score * 0.4 +
            keyword_overlap * 0.3 +
            name_score * 0.1 +
            domain_score * 0.2
        ))

        if confidence > 0.1:
            reason_parts = []
            if matched_triggers:
                reason_parts.append(f"触发词匹配：{', '.join(matched_triggers[:3])}")
            if keyword_overlap > 0.3:
                reason_parts.append(f"关键词重叠 {keyword_overlap:.0%}")
            if domain_score > 0.3:
                reason_parts.append("领域匹配")
            reason = "；".join(reason_parts) or "语义相似"

            matches.append(RouteMatch(
                skill_name=name,
                confidence=round(confidence, 2),
                reason=reason,
                matched_triggers=matched_triggers,
            ))

    # Sort by confidence descending
    matches.sort(key=lambda m: m.confidence, reverse=True)

    best = matches[0] if matches else None

    return RouteResult(
        query=query,
        matches=matches[:5],  # Top 5
        best_match=best,
    )


def format_route_result(result: RouteResult) -> str:
    """格式化路由结果为 Markdown。"""
    lines = [
        "# Skill 路由结果",
        "",
        f"**用户请求：** {result.query}",
        "",
    ]

    if not result.matches:
        lines.append("未找到匹配的 Skill。建议使用通用能力处理或创建新 Skill。")
        return "\n".join(lines)

    lines.append("## 推荐 Skill")
    lines.append("")
    lines.append("| 排名 | Skill | 置信度 | 原因 |")
    lines.append("|------|-------|--------|------|")
    for i, m in enumerate(result.matches[:5], 1):
        lines.append(f"| {i} | {m.skill_name} | {m.confidence:.0%} | {m.reason} |")

    if result.best_match:
        lines.extend([
            "",
            f"## 最佳匹配：{result.best_match.skill_name}",
            "",
            f"- 置信度：{result.best_match.confidence:.0%}",
            f"- 原因：{result.best_match.reason}",
        ])

    return "\n".join(lines)
