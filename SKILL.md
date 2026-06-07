---
name: skillos
description: Meta Skill Operating System — manages, analyzes, rates, optimizes, and generates Claude Code skills. Use whenever the user asks to "find a skill", "rate a skill", "optimize a skill", "generate a skill", "list installed skills", "check skill quality", "review this skill", "create a new skill", "improve my skill", "skill 管理", "评价 skill", "优化 skill", "生成 skill", or wants to understand, compare, or compose skills. Do NOT use for writing code or completing business tasks — those belong to domain-specific skills.
license: MIT
argument-hint: <action> [target]
metadata:
  author: SkillOS
  version: "1.1.0"
---

# SkillOS — Meta Skill Operating System

SkillOS 管理其他 Skill 的生命周期：发现、分析、评分、优化、生成、编排。

SkillOS 不直接完成业务任务。业务任务由具体 Skill 完成。

## Core Principles

- **不造轮子**：优先使用已安装的成熟 Skill，只在没有现成方案时自建
- **一个 Skill 一个 Job**：不捆绑不相关职责
- **先审查后修改**：任何优化操作必须先出计划，等用户确认后再实施
- **渐进式披露**：正文 ≤300 行，细节在 references/ 中按需加载

## Actions

SkillOS 支持以下操作（通过 argument-hint 传入或由路由自动选择）：

| Action | 说明 | 工作流 |
|--------|------|--------|
| `find` | 搜索可安装的 Skill | → [Find 流程](#find-flow) |
| `list` | 列出已安装 Skill | → [List 流程](#list-flow) |
| `rate` | 评分审查一个 Skill | → [Rate 流程](#rate-flow) |
| `optimize` | 优化一个 Skill | → [Optimize 流程](#optimize-flow) |
| `generate` | 生成新 Skill | → [Generate 流程](#generate-flow) |
| `route` | 路由用户请求到合适 Skill | → [Route 流程](#route-flow) |
| `workflow` | 推荐 Skill 执行链 | → [Workflow 流程](#workflow-flow) |
| `relationships` | 检测 Skill 关系图谱 | → [Relationships 流程](#relationships-flow) |
| `compose` | 编排多 Skill 协作 | → [Compose 流程](#compose-flow) |
| `registry` | 更新 Skill 索引 | → [Registry 流程](#registry-flow) |

如果用户请求不包含明确 action，先用 [Route 流程](#route-flow) 判断意图。

---

## Find Flow

搜索可安装的 Skill。

**步骤：**

1. 提取用户需求中的关键词
2. 运行 `npx skills find <keywords>`
3. 展示结果，说明每个 Skill 的用途和安装量
4. 如用户确认，执行 `npx skills add <package> -g -y`

**如果没有找到：**
- 尝试同义词搜索
- 建议使用 `generate` 流程创建新 Skill

---

## List Flow

列出已安装 Skill。

**步骤：**

1. 运行 `npx skills ls -g`（全局）或 `npx skills ls`（项目级）
2. 格式化输出为表格
3. 如需详细信息，读取对应 SKILL.md 的 description

---

## Rate Flow

评分审查一个 Skill。基于 [references/REVIEW-CHECKLIST.md](references/REVIEW-CHECKLIST.md) 的 7 维度体系。

**步骤：**

1. **定位目标**
   - 用户传入路径 → 读取该 SKILL.md
   - 用户传入 Skill 名称 → 在已安装目录中查找
   - 未传入 → 询问一次

2. **检测类型** — methodology / technical / auditing / reference / automation

3. **按 7 维度评分**
   - Description 质量（25）：第三人称、指令式、触发词、负面范围
   - Frontmatter 有效性（20）：字段、保留字、层级
   - 长度与披露（15）：行数、references 拆分
   - 结构匹配度（15）：类型对应章节
   - 示例质量（10）：正反对比、具体性
   - 简洁性（10）：无冗余
   - 反模式规避（5）：无已知反模式

4. **输出审查报告**（格式见 [references/REVIEW-CHECKLIST.md](references/REVIEW-CHECKLIST.md)）

5. **如果用户要求修复** → 进入 Optimize 流程

---

## Optimize Flow

优化一个 Skill。参考 `chujianyun/skills@skill-optimizer` 的工作流。

**规则：先审查、再计划、确认后才改文件。**

**步骤：**

1. **Scope** — 确认目标和优化范围。优先采用用户指定方向。
2. **Review** — 读取 SKILL.md 及其 references/，按 [REVIEW-CHECKLIST.md](references/REVIEW-CHECKLIST.md) 审查。
3. **Plan** — 输出优化计划：

   ```
   # Skill 审查结论

   ## 审查对象
   - 目标 skill：...
   - 本次范围：...

   ## 高优先级
   - [问题] 影响触发、正确性或执行稳定性

   ## 中优先级
   - [问题] 影响可维护性

   ## 低优先级
   - [问题] 体验提升

   ## 不改动项
   - ...

   # 优化计划
   1. 修改 [文件路径]
      - 变更内容：
      - 原因：
   ```

4. **等待确认** — "我看看"/"有道理"不算确认，必须是明确的执行确认。
5. **Implement** — 确认后实施修改。
6. **Verify** — 校验：frontmatter 正确、description 可独立触发、正文更短更清晰。

---

## Generate Flow

生成新 Skill。基于 `antjanus/skillbox@generate-skill` 的 8 阶段流程。

**规则：一次问一个问题，不要批量提问。**

**步骤：**

1. **Discovery**（逐个提问）
   - Skill 用途？一句话。
   - Skill 类型？methodology / technical / auditing / reference / automation
   - 触发短语？≥5 条用户会说的话
   - 负面范围？哪些相邻 Skill 不该抢触发
   - 执行强度？suggestion / guided / strict

2. **Description 草拟** — 单行、≤230 字符、第三人称、含 ≥3 个引号触发短语。展示并迭代。

3. **Frontmatter** — 只用合法字段。参见 [REVIEW-CHECKLIST.md](references/REVIEW-CHECKLIST.md) 维度 2。

4. **Body** — 根据类型选模板。参见 [references/SKILL-TYPES.md](references/SKILL-TYPES.md)。正文 <300 行。

5. **Examples** — 2-3 个 ✅ + 1 个 ❌。期望示例在前。

6. **Gotchas** — 每条：症状 + 原因 + 修复。每条否定配对正面指令。

7. **渐进式披露** — 超 300 行则拆到 references/。

8. **Eval Set** — 生成 20 条测试查询（10 应触发 + 10 不应触发）。参见 [templates/EVAL-TEMPLATE.md](templates/EVAL-TEMPLATE.md)。

**输出结构：**

```
{skill-name}/
├── SKILL.md
├── references/          # 可选：细节拆分
│   └── EVAL.md          # 评估集
├── scripts/             # 可选：确定性脚本
└── assets/              # 可选：模板资源
```

---

## Route Flow

路由用户请求到最合适的 Skill。参考 `charon-fan/agent-playbook@skill-router` 的模式。

**步骤：**

1. **意图分析** — 识别任务类型、领域、复杂度
2. **Skill 匹配** — 关键词 + 语义 + 上下文
3. **交互澄清** — 歧义时用 AskUserQuestion 提问
4. **推荐执行** — 展示推荐 Skill + 原因 + 备选

**路由规则详见** [references/ROUTING-RULES.md](references/ROUTING-RULES.md)

---

## Workflow Flow

推荐 Skill 执行链。基于 Relationship Intelligence 构建 Serial Workflow。

**步骤：**

1. 运行 `python skillos.py workflow "用户请求"` 获取推荐
2. 系统自动执行：
   - 用 Route Flow 获取 Top N 匹配 Skill
   - 用 Relationships Flow 检测 Skill 间关系
   - 基于 collaboration 关系构建执行链
3. 展示执行链，每步标注角色（产出方/消费方/独立执行）
4. 用户确认后按序执行

**CLI 用法：**

```bash
python skillos.py workflow "帮我开发网站"
python skillos.py workflow "审查代码并优化性能" --top-n 3
```

---

## Relationships Flow

检测 Skill 之间的关系图谱。覆盖 5 种关系类型：

| 类型 | 来源 | 说明 |
|------|------|------|
| 冲突 (conflict) | 提取 | 触发词重叠或职责冲突 |
| 互补 (complement) | 推断 | 领域相邻、适合配合使用 |
| 协作 (collaboration) | 推断 | 产出方可作为消费方输入 |
| 引用 (reference) | 提取 | SKILL.md 正文互相引用 |
| 领域相邻 (domain_adjacency) | 推断 | 属于相邻领域 |

**步骤：**

1. 运行 `python skillos.py relationships --global` 扫描所有 Skill
2. 系统分析每个 Skill 的触发词、领域、能力、引用
3. 输出关系图谱（Markdown / JSON / Mermaid）
4. 供 Workflow Flow 和 Compose Flow 使用

**CLI 用法：**

```bash
python skillos.py relationships --global
python skillos.py relationships --json
python skillos.py relationships --format mermaid
```

---

## Compose Flow

编排多 Skill 协作执行。不合并 Skill 内容，而是创建编排层。

**核心原则：Composition > Fusion。优先 Workflow，而不是 Merge。**

**模式：**

1. **串行依赖** — 前一个输出是后一个输入
   - 例：planner → coder → reviewer → documenter
   - 使用 `workflow` 命令自动推荐执行链
2. **并行独立** — 互不依赖，可同时执行
   - 例：security-auditor + performance-engineer
3. **条件分支** — 根据中间结果决定下一步

**步骤：**

1. 先运行 `python skillos.py workflow "任务描述"` 获取推荐
2. 确认执行链，必要时手动调整
3. 创建 workflow 描述（markdown checklist）
4. 按序调用各 Skill，传递上下文
5. 汇总结果

**禁止：合并多个 Skill 为一个 Mega Skill。**

---

## Registry Flow

更新 Skill 索引。

**步骤：**

1. 运行 `bash scripts/scan-skills.sh --global`
2. 或手动更新 [references/SKILL-REGISTRY.md](references/SKILL-REGISTRY.md)

---

## Gotchas

- **症状：** SkillOS 路由到错误的 Skill。**原因：** Skill 注册表过期。**修复：** 运行 `registry` 流程刷新索引。
- **症状：** 生成的 Skill 从不自动触发。**原因：** description 多行或触发词模糊。**修复：** 用 `rate` 流程检查 description 质量。
- **症状：** 优化后 Skill 功能丢失。**原因：** 修改面过大。**修复：** 限制优化范围，只改用户确认的部分。

## References

- [Skill Registry](references/SKILL-REGISTRY.md) — 已安装 Skill 索引
- [Routing Rules](references/ROUTING-RULES.md) — 路由决策规则
- [Review Checklist](references/REVIEW-CHECKLIST.md) — 7 维度评分标准
- [Skill Types](references/SKILL-TYPES.md) — 5 种类型模板
- [Gotchas](references/GOTCHAS.md) — 常见陷阱与修复
- [Advanced Patterns](references/ADVANCED-PATTERNS.md) — 高级用法和扩展

## State

SkillOS 在 `state/` 目录中维护运行时状态：

- `state/registry.json` — 持久化注册表
- `state/evolution.json` — Skill 演化历史
- `state/learnings.json` — 操作经验记录

## Hooks

SkillOS 支持事件钩子。详见 [hooks/HOOK.md](hooks/HOOK.md)。
