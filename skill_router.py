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
        "skill_patterns": ["code-review", "review", "code-reviewer", "graphify", "codeconductor"],
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
        "skill_patterns": ["skillos", "skill-creator", "skill-installer", "skill"],
    },
    "browser": {
        "keywords": ["browser", "scrape", "web automation", "浏览器", "抓取", "自动化"],
        "skill_patterns": ["browser", "playwright", "selenium", "puppeteer"],
    },
    "git": {
        "keywords": ["commit", "branch", "merge", "git", "提交", "分支"],
        "skill_patterns": ["commit", "git", "branch"],
    },
    "frontend": {
        "keywords": ["网站", "前端", "web app", "next.js", "react", "网页", "页面", "webapp"],
        "skill_patterns": ["react", "nextjs", "frontend", "webapp", "web"],
    },
    "skill_creation": {
        "keywords": ["生成 skill", "创建 skill", "新 skill", "写一个 skill", "新建 skill", "generate skill", "create skill"],
        "skill_patterns": ["skillos", "skill-creator", "generate", "skill"],
    },
    "api": {
        "keywords": ["api", "接口", "接口文档", "rest", "restful", "endpoint"],
        "skill_patterns": ["api", "rest", "endpoint", "openapi"],
    },
}


# 中文短语 → 领域映射（用于短语级匹配）
_PHRASE_DOMAIN_MAP = {
    "单元测试": "testing",
    "集成测试": "testing",
    "写测试": "testing",
    "测试代码": "testing",
    "审查代码": "code_review",
    "代码审查": "code_review",
    "检查代码": "code_review",
    "代码检查": "code_review",
    "api文档": "documentation",
    "接口文档": "documentation",
    "写文档": "documentation",
    "技术文档": "documentation",
    "开发网站": "frontend",
    "做网站": "frontend",
    "建网站": "frontend",
    "前端开发": "frontend",
    "部署项目": "deployment",
    "部署到": "deployment",
    "上线部署": "deployment",
    "生产环境": "deployment",
    "安全审查": "security",
    "安全检查": "security",
    "性能优化": "performance",
    "优化性能": "performance",
    "提速": "performance",
    "产品需求": "product",
    "需求文档": "product",
    "生成skill": "skill_creation",
    "生成一个新skill": "skill_creation",
    "创建skill": "skill_creation",
    "创建一个skill": "skill_creation",
    "新skill": "skill_creation",
    "写一个skill": "skill_creation",
    "api接口": "api",
    "设计接口": "api",
    "设计api": "api",
    "浏览器": "browser",
    "网页抓取": "browser",
    "找skill": "skill_management",
    "skill管理": "skill_management",
    "skill列表": "skill_management",
    "检测冲突": "skill_management",
    "推荐工作流": "skill_management",
    "skill工作流": "skill_management",
    "评价skill": "skill_management",
    "优化skill": "skill_management",
}


DOMAIN_SKILL_BOOSTS = {
    "skill_creation": {"skillos": 0.35, "skill-creator": 0.25},
    "skill_management": {"skillos": 0.35, "skill-creator": 0.2, "skill-installer": 0.2},
    "code_review": {"graphify": 0.25, "codeconductor": 0.2},
    "performance": {"graphify": 0.15, "codeconductor": 0.15},
    "documentation": {"word": 0.2, "docx": 0.2, "graphify": 0.15, "prd": 0.1},
    "api": {"word": 0.2, "docx": 0.2, "graphify": 0.15, "prd": 0.1},
    "deployment": {"google-agents-cli-scaffold": 0.15, "tencent-novnc-chromium-cdp": 0.15},
}


GENERIC_SKILL_NAMES = {
    "self-improvement",
    "self-improving + proactive agent",
}


SELF_IMPROVEMENT_TERMS = {
    "自我改进", "持续改进", "记忆", "纠正", "学习", "反思",
    "self improvement", "learn", "memory", "correction",
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
    query_compact = re.sub(r"\s+", "", query_lower)
    matches = []

    for skill in available_skills:
        name = skill.frontmatter.name or ""
        desc = skill.frontmatter.description or ""
        name_lower = name.lower()
        desc_lower = desc.lower()

        # Extract skill's trigger keywords
        skill_triggers = set(re.findall(r'"([^"]+)"', desc))
        skill_tokens = _tokenize(desc)
        skill_name_tokens = set(re.findall(r"[a-z]+", name_lower))

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

        # Score 2: Keyword overlap with description (token + substring)
        keyword_overlap = len(query_tokens & skill_tokens) / max(len(query_tokens), 1)
        # 中文子串匹配：query 中是否包含 skill 描述里的中文词
        cn_keywords_in_desc = re.findall(r'[一-鿿]{2,}', desc)
        for kw in cn_keywords_in_desc:
            if kw in query_lower:
                keyword_overlap = max(keyword_overlap, 0.5)
                break

        # Score 3: Name match
        name_score = len(query_tokens & skill_name_tokens) / max(len(skill_name_tokens), 1)

        # Score 4: Domain keyword match (token + phrase-level)
        domain_score = 0
        matched_domain = None

        # 4a: 短语级匹配（中文短语直接包含在 query 中）
        for phrase, domain in _PHRASE_DOMAIN_MAP.items():
            phrase_compact = re.sub(r"\s+", "", phrase.lower())
            if phrase.lower() in query_lower or phrase_compact in query_compact:
                config = DOMAIN_KEYWORDS.get(domain, {})
                for pattern in config.get("skill_patterns", []):
                    if pattern in name_lower or pattern in desc_lower:
                        domain_score = max(domain_score, 0.85)
                        matched_domain = domain
                        break

        # 4b: Token 级匹配
        for domain, config in DOMAIN_KEYWORDS.items():
            domain_tokens = set(config["keywords"])
            if query_tokens & domain_tokens:
                for pattern in config["skill_patterns"]:
                    if pattern in name_lower or pattern in desc_lower:
                        domain_score = max(domain_score, 0.8)
                        matched_domain = domain
                        break

        # Weighted total — phrase-level domain match is a strong signal for Chinese queries
        if matched_domain:
            confidence = min(1.0, (
                trigger_score * 0.2 +
                keyword_overlap * 0.2 +
                name_score * 0.1 +
                domain_score * 0.5
            ))
        else:
            confidence = min(1.0, (
                trigger_score * 0.4 +
                keyword_overlap * 0.3 +
                name_score * 0.1 +
                domain_score * 0.2
            ))

        if matched_domain:
            for pattern, boost in DOMAIN_SKILL_BOOSTS.get(matched_domain, {}).items():
                if pattern in name_lower or pattern in desc_lower:
                    confidence = min(1.0, confidence + boost)
                    break

        if name_lower in GENERIC_SKILL_NAMES and matched_domain not in {"skill_management", "skill_creation"}:
            if not any(term in query_lower for term in SELF_IMPROVEMENT_TERMS):
                confidence *= 0.45

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


# ── Workflow Routing ──────────────────────────────────────────

@dataclass
class WorkflowStep:
    """工作流中的一个步骤。"""
    skill_name: str
    role: str  # producer / consumer / transformer / independent / single
    reason: str


@dataclass
class WorkflowRecommendation:
    """工作流推荐结果。"""
    query: str
    steps: list  # list[WorkflowStep]
    confidence: float
    reasoning: str


# 预定义任务模板（当路由无匹配时兜底）
_WORKFLOW_TEMPLATES = {
    "code_review_performance": {
        "triggers": ["代码审查和性能优化", "审查代码和性能优化", "代码审查与性能优化", "review and performance"],
        "steps": [
            ("graphify", "producer", "分析代码结构与热点"),
            ("codeconductor", "transformer", "提出架构与性能优化建议"),
            ("javascript-testing-patterns", "consumer", "补充回归测试验证优化"),
        ],
        "confidence": 0.68,
    },
    "website": {
        "triggers": ["网站", "开发网站", "做网站", "建网站", "前端开发", "web app", "webapp", "website"],
        "steps": [
            ("prd-planner", "producer", "规划产品需求"),
            ("product-designer", "transformer", "设计 UI/UX"),
            ("react-nextjs-development", "transformer", "实现前端"),
            ("webapp-testing", "consumer", "端到端测试"),
        ],
        "confidence": 0.7,
    },
    "testing": {
        "triggers": ["写测试", "单元测试", "测试代码", "测试", "test", "testing"],
        "steps": [
            ("javascript-testing-patterns", "producer", "编写测试"),
            ("webapp-testing", "consumer", "运行 E2E 测试"),
        ],
        "confidence": 0.65,
    },
    "code_review": {
        "triggers": ["审查代码", "代码审查", "review", "检查代码", "代码检查"],
        "steps": [
            ("graphify", "producer", "分析代码架构"),
            ("javascript-testing-patterns", "consumer", "验证测试覆盖"),
        ],
        "confidence": 0.6,
    },
    "new_project": {
        "triggers": ["新项目", "搭建项目", "创建项目", "项目初始化", "new project"],
        "steps": [
            ("google-agents-cli-scaffold", "producer", "搭建项目脚手架"),
            ("graphify", "transformer", "构建代码知识图谱"),
            ("webapp-testing", "consumer", "验证项目可用"),
        ],
        "confidence": 0.65,
    },
    "skillos_management": {
        "triggers": ["先检测冲突，再推荐工作流", "检测冲突再推荐工作流", "检测 skill 冲突", "推荐 skill 工作流"],
        "steps": [
            ("skillos", "producer", "检测 Skill 冲突"),
            ("skillos", "consumer", "推荐 Skill 执行链"),
        ],
        "confidence": 0.95,
    },
}


def _workflow_from_template(query: str, reason_suffix: str = "路由无直接匹配") -> WorkflowRecommendation:
    query_lower = query.lower()
    query_compact = re.sub(r"\s+", "", query_lower)
    for template_name, template in _WORKFLOW_TEMPLATES.items():
        for trigger in template["triggers"]:
            trigger_compact = re.sub(r"\s+", "", trigger.lower())
            if trigger.lower() in query_lower or trigger_compact in query_compact:
                steps = [
                    WorkflowStep(skill_name=skill_name, role=role, reason=reason)
                    for skill_name, role, reason in template["steps"]
                ]
                return WorkflowRecommendation(
                    query=query,
                    steps=steps,
                    confidence=template["confidence"],
                    reasoning=f"基于任务模板 '{template_name}' 推荐（{reason_suffix}）",
                )
    return None


def route_workflow(query: str, available_skills: list, top_n: int = 5) -> WorkflowRecommendation:
    """根据用户请求推荐 Serial Workflow（Skill 执行链）。

    流程：
    1. 用 route_request() 获取 Top N 匹配 Skill
    2. 用 detect_relationships() 获取 Skill 间关系
    3. 基于 collaboration 关系构建 Serial 执行链
    4. 如果路由无匹配，尝试任务模板兜底

    Args:
        query: 用户的自然语言请求
        available_skills: list of SkillParseResult
        top_n: 最多推荐的 Skill 数

    Returns:
        WorkflowRecommendation
    """
    # 延迟导入避免循环依赖
    from conflict_detector import detect_relationships

    # Step 1: 获取 Top N 匹配
    route_result = route_request(query, available_skills)

    template_rec = _workflow_from_template(query, "模板优先匹配")
    if template_rec and (not route_result.best_match or route_result.best_match.confidence <= template_rec.confidence):
        return template_rec

    # 如果路由无匹配，尝试任务模板兜底
    if not route_result.matches:
        template_rec = _workflow_from_template(query)
        if template_rec:
            return template_rec

        return WorkflowRecommendation(
            query=query,
            steps=[],
            confidence=0.0,
            reasoning="未找到匹配的 Skill",
        )

    top_skills_names = [m.skill_name for m in route_result.matches[:top_n]]
    top_skills_conf = {m.skill_name: m.confidence for m in route_result.matches[:top_n]}

    # 获取对应的 parsed skills
    skill_map = {}
    for s in available_skills:
        name = s.frontmatter.name or ""
        if name in top_skills_names:
            skill_map[name] = s

    matched_skills = [skill_map[n] for n in top_skills_names if n in skill_map]

    if len(matched_skills) < 2:
        single = matched_skills[0] if matched_skills else None
        name = single.frontmatter.name if single else top_skills_names[0]
        return WorkflowRecommendation(
            query=query,
            steps=[WorkflowStep(skill_name=name, role="single", reason="单一 Skill 即可完成")],
            confidence=top_skills_conf.get(name, 0.5),
            reasoning="任务复杂度较低，单个 Skill 即可处理",
        )

    # Step 2: 检测关系
    rel_report = detect_relationships(matched_skills)

    # Step 3: 构建 Serial 执行链
    collab_edges = []
    for r in rel_report.relationships:
        if r.relation_type == "collaboration" and r.skill_a in top_skills_names and r.skill_b in top_skills_names:
            collab_edges.append((r.skill_a, r.skill_b, r.confidence, r.reason))

    if collab_edges:
        ordered = _topo_sort_workflow(collab_edges, top_skills_names)
        steps = []
        for i, name in enumerate(ordered):
            if i == 0:
                role = "producer"
            elif i == len(ordered) - 1:
                role = "consumer"
            else:
                role = "transformer"
            reason = ""
            for a, b, conf, r in collab_edges:
                if a == name or b == name:
                    reason = r
                    break
            steps.append(WorkflowStep(skill_name=name, role=role, reason=reason or "参与工作流"))

        avg_conf = sum(c for _, _, c, _ in collab_edges) / len(collab_edges)
        return WorkflowRecommendation(
            query=query,
            steps=steps,
            confidence=round(avg_conf, 2),
            reasoning=f"基于 {len(collab_edges)} 条协作关系构建 Serial 工作流",
        )
    else:
        steps = []
        for name in top_skills_names:
            conf = top_skills_conf.get(name, 0.5)
            steps.append(WorkflowStep(
                skill_name=name,
                role="independent",
                reason=f"路由置信度 {conf:.0%}",
            ))
        best_conf = max(top_skills_conf.values()) if top_skills_conf else 0.5
        return WorkflowRecommendation(
            query=query,
            steps=steps,
            confidence=round(best_conf, 2),
            reasoning="未发现协作关系，各 Skill 可独立执行或按需组合",
        )


def _topo_sort_workflow(edges: list, all_names: list) -> list:
    """基于 collaboration 边做简单拓扑排序，返回执行顺序。"""
    successors = {n: set() for n in all_names}
    predecessors = {n: set() for n in all_names}
    for a, b, _, _ in edges:
        successors[a].add(b)
        predecessors[b].add(a)

    queue = [n for n in all_names if not predecessors[n]]
    result = []
    visited = set()

    while queue:
        queue.sort(key=lambda n: all_names.index(n))
        node = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        result.append(node)
        for succ in successors[node]:
            predecessors[succ].discard(node)
            if not predecessors[succ]:
                queue.append(succ)

    for n in all_names:
        if n not in visited:
            result.append(n)

    return result


def format_workflow_recommendation(rec: WorkflowRecommendation) -> str:
    """格式化工作流推荐为 Markdown。"""
    lines = [
        "# 工作流推荐",
        "",
        f"**用户请求：** {rec.query}",
        f"**整体置信度：** {rec.confidence:.0%}",
        f"**推理依据：** {rec.reasoning}",
        "",
    ]

    if not rec.steps:
        lines.append("未找到合适的 Skill 组合。")
        return "\n".join(lines)

    lines.append("## 执行链")
    lines.append("")

    for i, step in enumerate(rec.steps):
        role_label = {
            "producer": "产出方",
            "consumer": "消费方",
            "transformer": "中间处理",
            "independent": "独立执行",
            "single": "单独执行",
        }.get(step.role, step.role)
        lines.append(f"**{i+1}. {step.skill_name}** ({role_label})")
        lines.append(f"   {step.reason}")
        if i < len(rec.steps) - 1:
            lines.append("")
            lines.append("   ↓")

    return "\n".join(lines)
