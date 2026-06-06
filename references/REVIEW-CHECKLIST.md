# Skill Review Checklist

> 基于 `antjanus/skillbox@rate-skill` 的 7 维度评分体系和 `chujianyun/skills@skill-optimizer` 的审查框架，整合为 SkillOS 的统一审查标准。

## 评分维度（满分 100）

| # | 维度 | 权重 | 核心检查点 |
|---|------|------|-----------|
| 1 | Description 质量 | 25 | 第三人称、指令式、特征触发词、负面范围限定 |
| 2 | Frontmatter 有效性 | 20 | 字段正确、无保留字、层级正确 |
| 3 | 长度与渐进式披露 | 15 | 正文 ≤300 行、references 正确拆分 |
| 4 | 结构匹配度 | 15 | 类型对应的必含章节齐全 |
| 5 | 示例质量 | 10 | 有正反对比、具体可执行 |
| 6 | 简洁性 | 10 | 无冗余、token 经济 |
| 7 | 反模式规避 | 5 | 无已知反模式 |

等级映射：A (90-100) / B (80-89) / C (70-79) / D (60-69) / F (<60)

---

## 维度 1：Description 质量（25 分）

### 必检项

- [ ] **第三人称**：描述以名词短语或 "Use this skill whenever…" 开头
  - ❌ "I help you create skills"（第一人称，cap 40 分）
  - ✅ "Interactive SKILL.md builder. Use whenever the user asks to…"
- [ ] **指令式语态**：使用 "Use whenever…" 或 "ALWAYS invoke when…"
  - ❌ "Use when X"（被动，cap 70 分）
  - ✅ "Use this skill whenever the user wants to…"
- [ ] **特征触发词在前 50 字符**：listing-budget 截断机制下，前 50 字符必须包含独特名词
- [ ] **≥3 个具体触发短语**：用户会实际说的话，带引号
  - ❌ "helps with documents"（模糊，cap 50 分）
  - ✅ `"create a skill"`, `"generate a skill"`, `"scaffold a SKILL.md"`
- [ ] **负面范围限定**：有相邻 Skill 时必须写 "Do NOT use for…"
- [ ] **单行**：不能用 YAML `|` 或 `>` 块标量（静默破坏发现机制）
- [ ] **长度**：≤230 字符软目标，≤1024 硬上限

---

## 维度 2：Frontmatter 有效性（20 分）

### 合法顶级字段

`name`, `description`, `license`, `compatibility`, `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `model`, `effort`, `agent`, `hooks`, `paths`, `shell`, `allowed-tools`, `metadata`

### 必检项

- [ ] `name` 全小写 kebab-case，无连续连字符，不含 `anthropic`/`claude`
- [ ] `version`/`author`/`tags` 在 `metadata` 内，不在顶级
- [ ] `argument-hint` 在顶级，不在 `metadata` 内
- [ ] 无 `category` 字段（不是合法字段）

---

## 维度 3：长度与渐进式披露（15 分）

### 必检项

- [ ] SKILL.md 正文 ≤300 行（满分）
- [ ] 301-500 行：每超 50 行扣 20 分
- [ ] >500 行且无 `references/` 目录：cap 40 分
- [ ] `references/` 用复数（规范），`reference/` 扣 10 分
- [ ] 引用文件最多嵌套一层（Claude 预览读取会跳过深层文件）

---

## 维度 4：结构匹配度（15 分）

### 按类型检查

**methodology（方法论）：**
- [ ] Overview
- [ ] Workflow/Phases（分阶段，每阶段一个任务）
- [ ] Quality Signals 或 Anti-Patterns
- [ ] Examples
- [ ] Verification Checklist（可选但推荐）

**technical（技术）：**
- [ ] Overview
- [ ] Quick Start（一个最小代码块）
- [ ] How it works
- [ ] Quick Reference tables
- [ ] Examples
- [ ] Gotchas

**auditing（审计）：**
- [ ] Overview
- [ ] Scoring Rubric（表格：信号→权重→检查）
- [ ] Output Format
- [ ] Examples（高/低质量示例）
- [ ] Gotchas

**reference（参考）：**
- [ ] Overview + 导航
- [ ] 每个领域一个 `references/<domain>.md`
- [ ] SKILL.md 保持为路由器

**automation（自动化）：**
- [ ] Overview
- [ ] Command surface table
- [ ] Sample invocation
- [ ] Failure modes
- [ ] Gotchas

---

## 维度 5：示例质量（10 分）

- [ ] ≥1 组正反对比（desired vs anti-pattern）
- [ ] 期望行为展示在前（recency bias：最后也以 ✅ 结尾）
- [ ] 使用 ✅/❌ 标记或 `## Anti-Pattern:` 标题
- [ ] 不用 `<Good>`/`<Bad>` XML 标签（0/8 顶级 Skill 使用）
- [ ] 示例具体可执行，非抽象描述

---

## 维度 6：简洁性（10 分）

- [ ] 无重述通用编程知识的段落
- [ ] "why this matters" 不长于其对应的规则
- [ ] 工作流前无冗长介绍
- [ ] 术语一致（不混用 "skill"/"command"）

---

## 维度 7：反模式规避（5 分）

每个扣 20 分：

- [ ] 无 ALL-CAPS "IRON LAW" 式框架（Anthropic 标记为黄旗）
- [ ] 无 Mega-skill 捆绑不相关职责
- [ ] 目录中无多余文档（README.md/INSTALLATION.md/CHANGELOG.md 除外）
- [ ] 无 Windows 反斜杠路径
- [ ] 无魔法数字（无文档说明的常量）
- [ ] 无时效性注释（"if before August 2025…"）

---

## 审查输出模板

```markdown
# Skill 审查报告：{skill-name}

**检测类型：** {methodology | technical | reference | auditing | automation}
**综合等级：** {letter} ({score}/100)

## 评分明细

| 维度 | 得分 | 权重 | 加权 |
|------|------|------|------|
| Description 质量 | nn | 25 | nn.n |
| Frontmatter 有效性 | nn | 20 | nn.n |
| 长度与披露 | nn | 15 | nn.n |
| 结构匹配度 | nn | 15 | nn.n |
| 示例质量 | nn | 10 | nn.n |
| 简洁性 | nn | 10 | nn.n |
| 反模式规避 | nn | 5 | nn.n |

## 优势
- {具体做得好的点}

## 发现（按优先级）

### P0 — {标题}
**原因：** {一句话说明}
**修复：**
\`\`\`
{可粘贴的具体修复内容}
\`\`\`

### P1 — {标题}
...

## 修复 P0+P1 后预估等级：{letter} ({projected}/100)
```
