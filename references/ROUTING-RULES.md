# Routing Rules

> SkillOS 的路由决策规则。当用户发起请求时，按此规则链匹配最合适的 Skill 或 SkillOS 子流程。

## 路由优先级

从高到低匹配，首个命中即执行：

### 1. 显式调用（最高优先级）

用户直接命名 Skill：
- "用 X skill" / "调用 X" / "/X" → 直接调用命名的 Skill
- 不经过路由分析

### 2. Skill 管理请求 → SkillOS 子流程

| 用户意图 | 触发短语 | 路由目标 |
|----------|---------|----------|
| 查找 Skill | "有没有X的skill"、"找skill"、"search skill" | `npx skills find` + SkillOS 解析 |
| 评分 Skill | "评价这个skill"、"给skill打分"、"rate skill" | rate-skill 工作流 |
| 生成 Skill | "创建skill"、"生成skill"、"写一个skill" | generate-skill 工作流 |
| 优化 Skill | "优化skill"、"改进skill"、"重构skill" | skill-optimizer 工作流 |
| 审查 Skill | "审查skill"、"review skill"、"检查skill质量" | AnalyzeSkills 流程 |
| 组合 Skill | "组合skill"、"编排workflow"、"多skill协作" | workflow-orchestrator |
| 查看已安装 | "已安装哪些skill"、"skill列表" | `npx skills ls` |

### 3. 任务型请求 → 路由到匹配 Skill

通过语义分析匹配用户任务与已注册 Skill：

| 任务领域 | 关键词示例 | 推荐 Skill 类型 |
|----------|-----------|----------------|
| 代码审查 | "review"、"检查代码"、"PR" | code-reviewer |
| 测试 | "写测试"、"test"、"单元测试" | test-automator |
| 文档 | "写文档"、"README"、"API文档" | documentation-engineer |
| 架构 | "设计方案"、"架构"、"技术方案" | architecting-solutions |
| 部署 | "部署"、"CI/CD"、"上线" | deployment-engineer |
| 安全 | "安全审查"、"漏洞"、"OWASP" | security-auditor |
| 性能 | "优化性能"、"提速"、"慢" | performance-engineer |
| 设计 | "UI"、"UX"、"设计系统" | product-designer |
| 产品 | "PRD"、"需求文档"、"产品需求" | prd-planner |

### 4. 兜底（最低优先级）

无匹配 Skill → 使用 Claude 通用能力直接处理。

## 路由决策流程

```
用户请求
  │
  ├─ 显式命名 Skill？ ──是──→ 直接调用
  │
  ├─ Skill 管理请求？ ──是──→ SkillOS 子流程
  │
  ├─ 语义匹配 Skill？ ──是──→ 推荐 Skill + 确认
  │
  └─ 无匹配 ──→ 通用处理
```

## 多 Skill 组合规则

当一个任务需要多个 Skill 协作时：

1. **串行依赖**：前一个 Skill 的输出是后一个的输入
   - 例：api-designer → api-documenter → test-automator
2. **并行独立**：多个 Skill 互不依赖
   - 例：security-auditor + performance-engineer 同时审查
3. **编排模式**：创建临时 workflow 文件协调执行顺序
   - 参考 workflow-orchestrator 的模式

## 冲突处理

当两个 Skill 触发词重叠时：

1. 优先选择 description 中触发词更具体的 Skill
2. 如果无法区分，询问用户选择
3. 记录冲突到 SKILL-REGISTRY.md 的 conflicts 字段
