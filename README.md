# SkillOS v1.1

**Meta Skill Operating System** — 管理所有 Skill 的 Skill。

> SkillOS 不直接完成业务任务。它管理完成任务的 Skill。

---

## 它能做什么

| 能力 | 说明 | 命令 |
|------|------|------|
| **发现** | 搜索可安装的社区 Skill | `python skillos.py route "帮我写测试"` |
| **评分** | 7 维度 A-F 等级审查 | `python skillos.py rate ./my-skill` |
| **分析** | JSON 深度分析（含维度得分） | `python skillos.py analyze . --json` |
| **优化** | 审查→计划→确认→修改工作流 | `python skillos.py optimize ./my-skill` |
| **生成** | 5 种类型模板，8 阶段交互式生成 | `python skillos.py generate --name my-skill` |
| **冲突检测** | 触发词/职责/能力重叠检测 | `python skillos.py conflicts --global` |
| **关系图谱** | 5 种关系类型（冲突/互补/协作/引用/领域相邻） | `python skillos.py relationships --global` |
| **工作流推荐** | 基于关系图谱的 Serial Workflow 推荐 | `python skillos.py workflow "帮我开发网站"` |
| **路由** | 智能匹配用户请求到最合适的 Skill | `python skillos.py route "审查 PR"` |
| **索引** | 扫描已安装 Skill 生成注册表 | `python skillos.py registry --global` |

## 使用指南

详细使用指南请参见 [USAGE-GUIDE.md](USAGE-GUIDE.md)，包含安装配置、场景实战、v1.1 新功能详解和常见问题。

## 快速开始

### 环境要求

- Python >= 3.10
- Node.js >= 18（用于 `npx skills` CLI）
- Claude Code >= 2.0.0

### 安装

```bash
git clone https://github.com/K-arch-droid/SkillOS.git
cd SkillOS
```

### 安装依赖 Skill（可选）

```bash
bash scripts/install.sh
```

### 使用 CLI

```bash
# 列出已安装 Skill
python skillos.py list --global

# 评分审查
python skillos.py rate ~/.claude/skills/find-skills

# 深度分析（JSON 输出）
python skillos.py analyze . --json

# 路由用户请求
python skillos.py route "帮我写测试"

# 检测冲突
python skillos.py conflicts --global

# 关系图谱
python skillos.py relationships --global
python skillos.py relationships --json
python skillos.py relationships --format mermaid

# 工作流推荐
python skillos.py workflow "帮我开发网站"

# 生成新 Skill
python skillos.py generate --name my-skill --type methodology --desc "A skill for X"

# 优化 Skill
python skillos.py optimize ~/.claude/skills/my-skill
```

### 在 Claude Code 中使用

SkillOS 会作为 SKILL.md 被 Claude Code 自动识别：

- "找一个测试的 skill" → 搜索可安装 Skill
- "评价一下这个 skill" → 7 维度评分审查
- "帮我优化这个 skill" → 审查→计划→确认→修改
- "创建一个新 skill" → 8 阶段交互式生成
- "这个任务该用什么 skill" → 智能路由推荐

## 评分体系

基于 `antjanus/skillbox@rate-skill` 的 7 维度评分体系：

| 维度 | 权重 | 检查内容 |
|------|------|---------|
| Description 质量 | 25 | 第三人称、指令式触发语态、≥3 个引号触发短语、负面范围 |
| Frontmatter 有效性 | 20 | 字段规范、保留字检查、kebab-case |
| 长度与渐进式披露 | 15 | 正文 ≤300 行软上限、references/ 拆分 |
| 结构匹配度 | 15 | 按类型检查必要章节（workflow/examples/gotchas 等） |
| 示例质量 | 10 | 正反对比（✅/❌）、具体性 |
| 简洁性 | 10 | 无冗余引入语、无常识重述 |
| 反模式规避 | 5 | 无全大写标题、无 Mega-skill、无 Windows 路径 |

**等级：** A (90-100) / B (80-89) / C (70-79) / D (60-69) / F (<60)

## 项目结构

```
SkillOS/
├── skillos.py              # CLI 主入口（10 个子命令）
├── skill_parser.py         # SKILL.md 解析器（基础模块）
├── skill_analyzer.py       # 7 维度分析引擎
├── skill_router.py         # 智能路由器（4 层加权匹配）
├── skill_registry.py       # Skill 注册表管理
├── skill_generator.py      # Skill 生成器（5 种类型模板）
├── skill_optimizer.py      # Skill 优化器
├── conflict_detector.py    # 冲突检测器（Jaccard 系数）
├── SKILL.md                # Claude Code 读取的调度器
├── README.md               # 本文件
├── USAGE-GUIDE.md          # 使用指南
├── _meta.json              # 元数据
├── LICENSE                 # MIT
├── references/             # 参考文档
│   ├── SKILL-REGISTRY.md   # 已安装 Skill 索引
│   ├── ROUTING-RULES.md    # 路由规则
│   ├── REVIEW-CHECKLIST.md # 评分标准
│   ├── SKILL-TYPES.md      # 5 种类型模板
│   ├── GOTCHAS.md          # 常见陷阱
│   └── ADVANCED-PATTERNS.md
├── scripts/                # Shell 脚本
├── templates/              # Skill/Eval 模板
├── examples/               # 工作流示例
├── state/                  # 运行时状态
├── hooks/                  # 事件钩子
├── tests/                  # 测试套件
│   ├── test_all.py         # 80 个单元测试
│   └── test_cli_manual.sh  # 24 个 CLI 测试
└── 项目说明.txt            # 完整技术文档
```

## 测试

```bash
# 运行全部单元测试（94 个）
python -m tests.test_all -v

# 运行 CLI 集成测试（24 个）
bash tests/test_cli_manual.sh

# 只测某个模块
python -m tests.test_all TestParser
python -m tests.test_all TestAnalyzer
python -m tests.test_all TestRouter
```

## 设计决策

### 为什么不自己写 10 个子 Skill？

社区已有成熟 Skill，SkillOS 是编排层，不是替代品：

| 子功能 | 现成 Skill |
|--------|-----------|
| Skill 路由 | `charon-fan/agent-playbook@skill-router` |
| Skill 评分 | `antjanus/skillbox@rate-skill` |
| Skill 生成 | `antjanus/skillbox@generate-skill` |
| Skill 优化 | `chujianyun/skills@skill-optimizer` |
| 工作流编排 | `charon-fan/agent-playbook@workflow-orchestrator` |
| 自我改进 | `charon-fan/agent-playbook@self-improving-agent` |

### 路由算法

4 层加权匹配：

1. **触发词匹配** (40%) — description 中的引号短语
2. **关键词重叠** (30%) — 分词后 Jaccard 相似度
3. **名称匹配** (10%) — skill name 与查询的重叠
4. **领域匹配** (20%) — 12 个领域的关键词映射

### 冲突检测

社区目前没有成熟的 Skill 冲突检测方案。SkillOS 自主设计：

- **触发词重叠** — Jaccard 系数 > 0.3 触发警告
- **职责重叠** — 双方的 "Do NOT" 范围有交集
- **能力重复** — 章节结构重叠率 > 0.5

### Relationship Intelligence

升级冲突检测为全面的关系图谱引擎，支持 5 种关系类型：

| 类型 | 来源 | 置信度 |
|------|------|--------|
| 冲突 (conflict) | 提取 | 基于 Jaccard 系数 |
| 互补 (complement) | 推断 | 0.75 |
| 协作 (collaboration) | 推断 | 0.65-0.82 |
| 引用 (reference) | 提取 | 1.0 |
| 领域相邻 (domain_adjacency) | 推断 | 0.65 |

输出支持 Markdown / JSON / Mermaid 三种格式。

### Workflow Routing

基于关系图谱构建 Serial Workflow 推荐：

1. Route 获取 Top N 匹配 Skill
2. Relationship Intelligence 检测协作关系
3. 拓扑排序生成执行链（产出方 → 消费方）

## 许可

MIT
