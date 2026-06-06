# 示例：生成一个新 Skill

## 场景

你想创建一个自动发送邮件的 Skill。

## 命令

```bash
python skillos.py generate \
  --name auto-email \
  --type methodology \
  --desc "Automated email sending with templates. Use whenever the user wants to send email, compose message, or automate mailing."
```

## 输出

```
✅ Skill 已生成 → ./auto-email/SKILL.md
✅ 评估集已生成 → ./auto-email/references/EVAL.md
```

## 生成的文件结构

```
auto-email/
├── SKILL.md              # 核心 Skill 文件
└── references/
    └── EVAL.md           # 20 条测试查询（10 应触发 + 10 不应触发）
```

## 生成的 SKILL.md 示例

```markdown
---
name: auto-email
description: "Automated email sending with templates. Use whenever the user wants to send email, compose message, or automate mailing."
license: MIT
---

# auto-email

## Overview

Automated email sending with templates. Use whenever the user wants to send email, compose message, or automate mailing.

## Core Principles

- auto-email 只做一件事
- 先审查再修改

## Workflow

### Phase 1: Analyze

分析输入

### Phase 2: Execute

执行操作

### Phase 3: Verify

确认结果正确

## Examples

### Example: 正确用法

✅ Desired

用户请求 → Skill 响应

Why it works: 遵循了正确流程.

### Counter-example

❌ Anti-pattern

跳过必要步骤

Why it fails: 缺少验证导致错误.

## Gotchas

- **Symptom:** 操作失败
- **Cause:** 缺少必要参数
- **Fix:** 检查输入并补充参数
```

## 下一步

1. 编辑 SKILL.md，填充实际内容
2. 运行 `python skillos.py rate ./auto-email` 验证质量
3. 将目录复制到 `~/.claude/skills/` 安装
