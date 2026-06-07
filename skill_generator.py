"""SkillOS — Skill 生成器。

基于 antjanus/skillbox@generate-skill 的 8 阶段流程，
交互式生成符合规范的 SKILL.md 文件。
"""

import os
import re
from datetime import datetime
from pathlib import Path
from skill_parser import SkillParseResult

# Skill 类型对应的 body 模板
TEMPLATES = {
    "methodology": """# {name}

## Overview

{description}

## Core Principles

- {principle_1}
- {principle_2}

## Workflow

### Phase 1: {phase_1_name}

{phase_1_detail}

### Phase 2: {phase_2_name}

{phase_2_detail}

### Phase 3: Verify

{verify_detail}

## Examples

### Example: {example_title}

✅ Desired

{example_desired}

Why it works: {example_why}.

### Counter-example

❌ Anti-pattern

{example_anti}

Why it fails: {example_fail}.

## Gotchas

- **Symptom:** {gotcha_1_symptom}
- **Cause:** {gotcha_1_cause}
- **Fix:** {gotcha_1_fix}
""",

    "technical": """# {name}

## Overview

{description}

## Quick Start

```bash
{quick_start_command}
```

## How It Works

{how_it_works}

## Quick Reference

| Feature | Usage | Notes |
|---------|-------|-------|
| {ref_1} | {ref_1_usage} | {ref_1_notes} |

## Examples

### Example: {example_title}

✅ Desired

{example_desired}

## Gotchas

- **Symptom:** {gotcha_1_symptom}
- **Cause:** {gotcha_1_cause}
- **Fix:** {gotcha_1_fix}
""",

    "auditing": """# {name}

## Overview

{description}

## Scoring Rubric

| # | Dimension | Weight | Checkpoint |
|---|-----------|--------|------------|
| 1 | {rubric_1} | {rubric_1_weight} | {rubric_1_check} |

## Output Format

{output_format}

## Examples

### High Quality Example

{example_high}

### Low Quality Example

{example_low}

## Gotchas

- **Symptom:** {gotcha_1_symptom}
- **Cause:** {gotcha_1_cause}
- **Fix:** {gotcha_1_fix}
""",

    "reference": """# {name}

## Overview

{description}

## Quick Reference

{quick_reference}

## {domain_1}

{domain_1_content}
""",

    "automation": """# {name}

## Overview

{description}

## Command Surface

| Command | Purpose | Example |
|---------|---------|---------|
| {cmd_1} | {cmd_1_purpose} | {cmd_1_example} |

## Sample Invocation

```bash
{invocation}
```

## Failure Modes

| Failure | Symptom | Handling |
|---------|---------|----------|
| {fail_1} | {fail_1_symptom} | {fail_1_handling} |

## Gotchas

- **Symptom:** {gotcha_1_symptom}
- **Cause:** {gotcha_1_cause}
- **Fix:** {gotcha_1_fix}
""",
}


def generate_frontmatter(
    name: str,
    description: str,
    license_: str = "MIT",
    argument_hint: str = "",
    allowed_tools: str = "",
    metadata: dict = None,
) -> str:
    """生成 YAML frontmatter。"""
    lines = ["---"]
    lines.append(f"name: {name}")
    lines.append(f'description: "{description}"')
    lines.append(f"license: {license_}")
    if argument_hint:
        lines.append(f"argument-hint: {argument_hint}")
    if allowed_tools:
        lines.append(f"allowed-tools: {allowed_tools}")
    if metadata:
        lines.append("metadata:")
        for k, v in metadata.items():
            lines.append(f"  {k}: \"{v}\"")
    lines.append("---")
    return "\n".join(lines)


def validate_skill_name(name: str) -> tuple:
    """校验 Skill 名称是否为合法 kebab-case。

    Returns:
        (is_valid, message) — is_valid 为 True 表示合法，False 表示不合法
    """
    if not name:
        return False, "Skill 名称不能为空"
    pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
    if not re.match(pattern, name):
        return False, f"Skill 名称 '{name}' 不合法，必须为 kebab-case（小写字母+数字+连字符），如 'my-skill'"
    if len(name) > 64:
        return False, f"Skill 名称过长（{len(name)} 字符），最多 64 字符"
    return True, ""


def generate_skill(
    name: str,
    description: str,
    skill_type: str = "methodology",
    variables: dict = None,
    output_dir: str = None,
) -> str:
    """生成 SKILL.md 文件。

    Args:
        name: Skill 名称（kebab-case）
        description: 一句话描述
        skill_type: 类型（methodology/technical/auditing/reference/automation）
        variables: 模板变量字典
        output_dir: 输出目录（None 则只返回内容不写文件）

    Returns:
        生成的 SKILL.md 内容，如果名称不合法返回空字符串
    """
    # Validate name
    is_valid, msg = validate_skill_name(name)
    if not is_valid:
        return ""
    if variables is None:
        variables = {}

    # Set defaults for unset variables
    defaults = {
        "name": name,
        "description": description,
        "principle_1": f"{name} 只做一件事",
        "principle_2": "先审查再修改",
        "phase_1_name": "Analyze",
        "phase_1_detail": "分析输入",
        "phase_2_name": "Execute",
        "phase_2_detail": "执行操作",
        "verify_detail": "确认结果正确",
        "example_title": "正确用法",
        "example_desired": "用户请求 → Skill 响应",
        "example_why": "遵循了正确流程",
        "example_anti": "跳过必要步骤",
        "example_why_anti": "违反了核心原则",
        "example_fail": "缺少验证导致错误",
        "gotcha_1_symptom": "操作失败",
        "gotcha_1_cause": "缺少必要参数",
        "gotcha_1_fix": "检查输入并补充参数",
        "quick_start_command": f"# 使用 {name}",
        "how_it_works": "核心机制说明",
        "ref_1": "功能 1",
        "ref_1_usage": "用法",
        "ref_1_notes": "说明",
        "output_format": "输出格式说明",
        "rubric_1": "维度 1",
        "rubric_1_weight": "25",
        "rubric_1_check": "检查点",
        "example_high": "高质量示例",
        "example_low": "低质量示例",
        "quick_reference": "快速参考表",
        "domain_1": "领域 1",
        "domain_1_content": "领域内容",
        "cmd_1": "命令 1",
        "cmd_1_purpose": "用途",
        "cmd_1_example": "示例",
        "invocation": f"{name} --help",
        "fail_1": "失败场景 1",
        "fail_1_symptom": "表现",
        "fail_1_handling": "处理方式",
    }
    defaults.update(variables)

    # Generate frontmatter
    frontmatter = generate_frontmatter(name, description)

    # Get template
    template = TEMPLATES.get(skill_type, TEMPLATES["methodology"])

    # Fill template
    body = template
    for key, value in defaults.items():
        body = body.replace("{" + key + "}", str(value))

    content = frontmatter + "\n\n" + body

    # Write to file if output_dir specified
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        skill_file = out_path / "SKILL.md"
        skill_file.write_text(content, encoding="utf-8")

        # Generate eval set
        eval_content = _generate_eval_set(name, description)
        refs_dir = out_path / "references"
        refs_dir.mkdir(exist_ok=True)
        (refs_dir / "EVAL.md").write_text(eval_content, encoding="utf-8")

    return content


def _generate_eval_set(name: str, description: str) -> str:
    """生成评估集模板。"""
    return f"""# Evaluation Set: {name}

> 20 条测试查询，用于验证 description 的激活准确性。

## 应触发（Should Trigger）

1. "创建一个 {name} 的 skill"
2. "帮我做一个 {name}"
3. "我需要 {name} 功能"
4. "{description[:30]}..."
5. "有没有 {name} 相关的 skill"
6. "怎么用 {name}"
7. "{name} 怎么配置"
8. "帮我 {name}"
9. "我要 {name}"
10. "{name} skill 在哪里"

## 不应触发（Should Not Trigger）

### 相邻 Skill 应匹配

11. "帮我写代码"（应路由到 code-reviewer）
12. "部署到生产环境"（应路由到 deployment-engineer）
13. "写单元测试"（应路由到 test-automator）
14. "审查 PR"（应路由到 code-reviewer）
15. "优化性能"（应路由到 performance-engineer）

### 无关请求

16. "今天天气怎么样"
17. "帮我订个外卖"
18. "讲个笑话"
19. "翻译这段话"
20. "帮我写一封邮件"
"""


def validate_skill_content(content: str) -> list:
    """验证生成的 SKILL.md 内容是否符合规范。

    Returns:
        list of issues (empty if valid)
    """
    issues = []

    # Check frontmatter
    if not content.startswith("---"):
        issues.append("缺少 frontmatter（应以 --- 开头）")

    # Check description
    if "description:" not in content[:500]:
        issues.append("缺少 description 字段")
    elif 'description: |' in content[:500] or 'description: >' in content[:500]:
        issues.append("description 使用了多行格式（应为单行）")

    # Check name
    if "name:" not in content[:500]:
        issues.append("缺少 name 字段")

    # Check line count
    line_count = len(content.split("\n"))
    if line_count > 500:
        issues.append(f"超过 500 行上限（当前 {line_count} 行）")
    elif line_count > 300:
        issues.append(f"超过 300 行软上限（当前 {line_count} 行）")

    return issues
