# SkillOS v1.1 使用指南

> 从安装到高级用法，手把手教你用 SkillOS 管理 Claude Code Skill。

---

## 目录

1. [安装与配置](#1-安装与配置)
2. [核心概念](#2-核心概念)
3. [CLI 命令速查](#3-cli-命令速查)
4. [场景实战](#4-场景实战)
5. [v1.1 新功能](#5-v11-新功能)
6. [在 Claude Code 中使用](#6-在-claude-code-中使用)
7. [常见问题](#7-常见问题)

---

## 1. 安装与配置

### 环境要求

- Python >= 3.10
- Node.js >= 18（用于 `npx skills` CLI）
- Claude Code >= 2.0.0

### 安装步骤

```bash
# 克隆项目
git clone https://github.com/K-arch-droid/SkillOS.git
cd SkillOS

# 安装依赖 Skill（可选，推荐）
bash scripts/install.sh
```

### 验证安装

```bash
python skillos.py list --global
```

如果看到已安装 Skill 列表，说明安装成功。

---

## 2. 核心概念

### SkillOS 是什么？

SkillOS 是一个 **Meta Skill** —— 管理其他 Skill 的 Skill。它不直接完成业务任务，而是：

- **发现**：搜索社区中可安装的 Skill
- **评分**：用 7 维度体系审查 Skill 质量
- **分析**：深度分析 Skill 结构和内容
- **优化**：审查 → 计划 → 确认 → 修改
- **生成**：交互式创建新 Skill
- **路由**：智能匹配用户请求到最合适的 Skill
- **关系图谱**：检测 Skill 间的 5 种关系
- **工作流推荐**：基于关系图谱构建执行链
- **冲突检测**：发现触发词和职责重叠
- **索引管理**：扫描并注册已安装 Skill

### 5 种 Skill 类型

| 类型 | 用途 | 示例 |
|------|------|------|
| **methodology** | 多阶段工作流 | code-review, prd-planner |
| **technical** | 封装 API/工具 | docx, pdf, semantic-release |
| **auditing** | 评审或检查 | rate-skill, security-review |
| **reference** | 领域参考文档 | bigquery, css-patterns |
| **automation** | 脚本自动化 | screenshot-local, deploy-script |

### 7 维度评分体系

| 维度 | 权重 | 检查内容 |
|------|------|----------|
| Description 质量 | 25 | 第三人称、指令式触发语态、≥3 个引号触发短语 |
| Frontmatter 有效性 | 20 | 字段规范、保留字检查、kebab-case |
| 长度与渐进式披露 | 15 | 正文 ≤300 行、references/ 拆分 |
| 结构匹配度 | 15 | 按类型检查必要章节 |
| 示例质量 | 10 | 正反对比（✅/❌）、具体性 |
| 简洁性 | 10 | 无冗余引入语、无常识重述 |
| 反模式规避 | 5 | 无全大写标题、无 Mega-skill |

**等级：** A (90-100) / B (80-89) / C (70-79) / D (60-69) / F (<60)

---

## 3. CLI 命令速查

SkillOS 提供 10 个子命令：

```bash
python skillos.py <command> [options]
```

| 命令 | 用途 | 常用选项 |
|------|------|----------|
| `list` | 列出已安装 Skill | `-g` 全局 / `-p` 项目 |
| `registry` | 生成 Skill 索引 | `-o <path>` 输出路径 |
| `rate` | 评分审查 | `-o <path>` 保存报告 |
| `analyze` | 深度分析 | `--json` JSON 输出 |
| `route` | 路由请求 | `-g` 全局搜索 |
| `conflicts` | 冲突检测 | `-g` / `-p` |
| `relationships` | 关系图谱 | `--json` / `--format mermaid` |
| `workflow` | 工作流推荐 | `--top-n <N>` 最多推荐数 |
| `generate` | 生成 Skill | `--name` `--type` `--desc` |
| `optimize` | 优化 Skill | `--apply` 自动应用（开发中） |

---

## 4. 场景实战

### 场景 1：查看已安装了哪些 Skill

```bash
# 查看全局 Skill
python skillos.py list --global

# 查看项目级 Skill
python skillos.py list --project
```

### 场景 2：审查自己写的 Skill 质量

```bash
# 评分审查
python skillos.py rate ./auto-email

# 深度分析（JSON 格式）
python skillos.py analyze ./auto-email --json

# 保存报告到文件
python skillos.py rate ./auto-email -o report.md
```

### 场景 3：不确定该用哪个 Skill

```bash
python skillos.py route "帮我写单元测试"
```

### 场景 4：检测 Skill 之间的冲突

```bash
python skillos.py conflicts --global
```

### 场景 5：生成一个新 Skill

```bash
python skillos.py generate --name my-api-helper --type technical --desc "Help users design REST APIs"

# 查看生成内容
python skillos.py generate --name my-api-helper --type technical --desc "Help users design REST APIs" --show
```

### 场景 6：优化一个 Skill

```bash
python skillos.py optimize ~/.claude/skills/my-skill
```

### 场景 7：更新 Skill 索引

```bash
python skillos.py registry --global
python skillos.py registry --global -o my-index.md
```

---

## 5. v1.1 新功能

### 5.1 Relationship Intelligence（关系图谱）

检测 Skill 之间的 5 种关系：

| 类型 | 来源 | 说明 |
|------|------|------|
| 冲突 (conflict) | 提取 | 触发词重叠或职责冲突 |
| 互补 (complement) | 推断 | 领域相邻、适合配合使用 |
| 协作 (collaboration) | 推断 | 产出方可作为消费方输入 |
| 引用 (reference) | 提取 | SKILL.md 正文互相引用 |
| 领域相邻 (domain_adjacency) | 推断 | 属于相邻领域 |

```bash
python skillos.py relationships --global
python skillos.py relationships --global --json
python skillos.py relationships --global --format mermaid
```

### 5.2 Workflow Routing（工作流推荐）

基于关系图谱自动构建 Skill 执行链：

```bash
python skillos.py workflow "帮我开发网站"
python skillos.py workflow "审查代码并优化性能" --top-n 3
```

---

## 6. 在 Claude Code 中使用

SkillOS 作为 SKILL.md 被 Claude Code 自动识别。在对话中直接说：

| 你说的话 | SkillOS 做什么 |
|----------|---------------|
| "找一个测试的 skill" | 搜索可安装 Skill |
| "评价一下这个 skill" | 7 维度评分审查 |
| "帮我优化这个 skill" | 审查→计划→确认→修改 |
| "创建一个新 skill" | 8 阶段交互式生成 |
| "这个任务该用什么 skill" | 智能路由推荐 |
| "帮我开发网站" | 工作流推荐（执行链） |
| "看看 skill 之间有什么关系" | 关系图谱检测 |

---

## 7. 常见问题

### Q: 路由结果不准确怎么办？

运行 `python skillos.py registry --global` 刷新索引。

### Q: 生成的 Skill 从不自动触发？

用 `python skillos.py rate <path>` 检查 description 质量，确保单行、含 ≥3 个引号触发短语、使用指令式语态。

### Q: 如何查看 Skill 间的关系？

```bash
python skillos.py relationships --global
python skillos.py relationships --global --format mermaid
```

### Q: 测试套件怎么跑？

```bash
python -m tests.test_all -v          # 全部单元测试
bash tests/test_cli_manual.sh        # CLI 集成测试
python -m tests.test_all TestParser  # 只测某个模块
```

---

## 附录：命令示例速查

```bash
# 基础操作
python skillos.py list --global
python skillos.py registry --global
python skillos.py rate ./my-skill
python skillos.py analyze . --json
python skillos.py route "帮我写测试"
python skillos.py generate --name my-skill --type methodology
python skillos.py optimize ./my-skill

# v1.1 新功能
python skillos.py conflicts --global
python skillos.py relationships --global
python skillos.py relationships --global --json
python skillos.py relationships --format mermaid
python skillos.py workflow "帮我开发网站"
python skillos.py workflow "审查代码" --top-n 3
```
