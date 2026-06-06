# SkillOS Gotchas

> SkillOS 使用和 Skill 管理中的常见陷阱，基于社区最佳实践和已知问题整理。

---

## Skill 发现与激活

### Multiline description 是隐形杀手
- **症状：** Skill 安装后永远不会自动触发
- **原因：** YAML `|` 块标量解析正常，但发现机制看不到（anthropics/skills #9817）
- **修复：** description 必须是单行字符串，不用 `|` 或 `>`

### 前 50 字符决定命运
- **症状：** 安装 >15 个 Skill 后某些 Skill 失效
- **原因：** listing-budget 截断机制，每条 description 只显示前 ~1% context 的份额
- **修复：** 独特名词放最前面，"A skill for…" 这种泛化开头会被截断到无法区分

### 第一人称降低激活率
- **症状：** "I'll help you…" 描述的 Skill 激活不稳定
- **原因：** 实证研究（n=650, p<0.0001）显示第三人称激活率高 20 倍
- **修复：** 改为 "Use this skill whenever the user…" 或 "{名词短语}. Use when…"

---

## Skill 设计

### 一个 Skill 一个 Job
- **症状：** Mega-skill 安装后触发混乱、上下文膨胀
- **原因：** 捆绑不相关职责导致 description 过长、触发歧义
- **修复：** 拆分为独立 Skill，每个 Skill 只做一件事

### ALL-CAPS "IRON LAW" 无实证支持
- **症状：** 用全大写强调规则，但 AI 不一定更遵守
- **原因：** Anthropic skill-creator 标记为黄旗："if possible, reframe and explain the reasoning"
- **修复：** 用 "Quality Signals" + "Anti-Patterns" 结构替代，解释原因而非吼叫

### 否定指令需要正面配对
- **症状：** "DO NOT X" 规则被频繁违反
- **原因：** LLM 对否定的处理能力较弱（arXiv 2503.22395）
- **修复：** 每条 "不要做 X" 配对 "应该做 Y"，例如："不要直接改文件，应该先出计划等确认"

---

## Skill 依赖

### 外部依赖必须可安装
- **症状：** Skill 要求的 CLI/服务找不到
- **原因：** Skill 未附带安装指令
- **修复：** 在 SKILL.md 中写明安装命令，例如 `npm install -g xxx`

### 版本锁定不现实
- **症状：** 试图用 semver 锁定 Skill 版本
- **原因：** Skill 生态没有统一版本管理，`npx skills update` 是粗粒度的
- **修复：** 依赖声明用 "需要 X Skill" 而非 "需要 X@1.2.3"

---

## Skill 冲突

### 触发词重叠
- **症状：** 两个 Skill 总是抢同一个用户请求
- **原因：** description 中关键词高度重叠
- **修复：** 让 description 的前 50 字符包含独特名词，用 "Do NOT use for…" 划清边界

### 同级 Skill 抢触发
- **症状：** 同一个 repo 下的多个 Skill 互相干扰
- **原因：** 安装时全部注册，description 语义相近
- **修复：** 同仓库 Skill 的 description 要互相引用排除范围

---

## Skill 优化

### 不要在审查后直接改文件
- **症状：** 审查结论和修改混在一起，用户无法确认
- **原因：** 跳过了"出计划等确认"步骤
- **修复：** 先输出审查报告 + 优化计划，等用户明确确认后再实施

### 不要为了全面而扩大改动面
- **症状：** 用户只想改 description，结果整个 SKILL.md 被重写
- **原因：** 审查时发现了更多问题，擅自升级任务范围
- **修复：** 围绕用户指定的方向做，超出范围的列为"额外建议"

---

## Token 经济

### 300 行是软上限
- **症状：** SKILL.md 超过 300 行后任务成功率下降 ~3%、步骤数增加 >20%
- **原因：** ETH Zurich 研究（arXiv 2602.11988）发现冗长上下文文件降低表现
- **修复：** 正文控制在 300 行内，细节拆到 references/

### 不要重述通用知识
- **症状：** Skill 里解释 "什么是 REST API" 或 "为什么需要测试"
- **原因：** Claude 已经知道这些，写了只会浪费 token
- **修复：** 只编码不可推断的、过程性的、Skill 特定的知识
