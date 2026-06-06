# Skill Type Templates

> 基于 `antjanus/skillbox@generate-skill` 的类型模板系统。生成新 Skill 时，根据类型选择对应模板。

## 类型识别

| 类型 | 特征 | 典型用途 |
|------|------|---------|
| **methodology** | 多阶段工作流 + 检查清单 | code-review, track-session, prd-planner |
| **technical** | 封装 API/格式/工具 | docx, pdf, semantic-release |
| **auditing** | 评审或检查制品 | rate-skill, security-review |
| **reference** | 领域 schema/惯例/查找表 | bigquery, css-patterns |
| **automation** | 封装脚本或外部命令 | screenshot-local, deploy-script |

---

## methodology 模板

```markdown
# {Skill Name}

## Overview
{一句话说明这个 Skill 做什么，为什么需要它}

## Core Principles
- {原则 1}
- {原则 2}

## Workflow

### Phase 1: {阶段名}
{具体任务说明}

### Phase 2: {阶段名}
{具体任务说明}

### Phase N: {验证}
{如何确认完成}

## Examples

### ✅ 正确用法
{具体示例}

### ❌ 反模式
{具体反例 + 为什么不行}

## Gotchas
- **症状：** {现象}
- **原因：** {根因}
- **修复：** {解决方法}
```

---

## technical 模板

```markdown
# {Skill Name}

## Overview
{技术能力说明}

## Quick Start
\`\`\`bash
{最小可运行示例}
\`\`\`

## How It Works
{核心机制说明}

## Quick Reference

| 功能 | 用法 | 说明 |
|------|------|------|
| ... | ... | ... |

## Examples
{具体使用示例}

## Gotchas
{常见陷阱}
```

---

## auditing 模板

```markdown
# {Skill Name}

## Overview
{审查什么、产出什么}

## Scoring Rubric

| # | 维度 | 权重 | 检查点 |
|---|------|------|--------|
| 1 | ... | nn | ... |

## Output Format
{输出格式规范}

## Examples

### 高质量示例
{得分 A 的示例}

### 低质量示例
{得分 F 的示例}

## Gotchas
{审查时的常见误判}
```

---

## reference 模板

```markdown
# {Skill Name}

## Overview
{这个参考文档覆盖什么领域}

## Quick Reference
{最常用的查找表}

## {领域 1}
{详细内容或指向 references/{domain}.md}

## {领域 2}
{详细内容或指向 references/{domain}.md}
```

---

## automation 模板

```markdown
# {Skill Name}

## Overview
{自动化什么操作}

## Command Surface

| 命令 | 用途 | 示例 |
|------|------|------|
| ... | ... | ... |

## Sample Invocation
\`\`\`bash
{完整调用示例}
\`\`\`

## Failure Modes
| 失败场景 | 表现 | 处理 |
|----------|------|------|
| ... | ... | ... |

## Gotchas
{脚本使用的常见问题}
```

---

## 渐进式披露规则

当 SKILL.md 超过 300 行时：

1. 识别最大的可拆分章节
2. 移到 `references/{TOPIC}.md`（复数目录）
3. 在 SKILL.md 中保留一行指针：
   ```markdown
   详细 {TOPIC} 参见 [references/{TOPIC}.md](references/{TOPIC}.md)。
   ```
4. 引用文件最多一层嵌套

---

## 评估集（Eval Set）

生成 Skill 时必须附带 20 条测试查询：

- 10 条 **应触发** — 应该匹配此 Skill 的用户短语
- 10 条 **不应触发** — 相邻 Skill 或无关请求

保存到 `references/EVAL.md`，用于验证 description 的激活准确性。
