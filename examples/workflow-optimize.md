# 示例：优化一个现有 Skill

## 场景

你发现 `auto-email` Skill 触发不太准，想优化它。

## 命令

```bash
python skillos.py optimize ./auto-email
```

## 输出示例

```
# Skill 审查结论

## 审查对象
- 目标 skill：auto-email
- 本次范围：全文审查

## 高优先级
- (无 P0 问题)

## 中优先级
- **Description 缺少指令式触发语态** — 被动描述降低激活可靠性
- **只有 1 个引号触发短语（需要 ≥3）** — 触发短语不足导致激活不稳定
- **缺少反模式示例** — 反模式帮助避免常见错误

## 低优先级
- (无 P2 问题)

## 不改动项
- 正文长度合理
- Frontmatter 字段规范

## 优化计划

### 1. [P1] 将 description 从第一人称改为第三人称
- 文件：`./auto-email/SKILL.md`
- 类型：modify
- 位置：frontmatter/description

### 2. [P1] 添加缺失的章节：examples, gotchas
- 文件：`./auto-email/SKILL.md`
- 类型：add
- 位置：body

---
## 修复 P0+P1 后预估等级：A (95/100)

> 仅当用户明确回复「按计划执行」「开始修改」「确认修改」后才能实施修改。
```

## 工作流

```
优化进度：
- [x] 步骤 1：Scope（确定范围）
- [x] 步骤 2：Review（审查目标 skill）
- [x] 步骤 3：Plan（输出优化计划并等待确认）
- [ ] 步骤 4：Implement（确认后实施）
- [ ] 步骤 5：Verify（校验结果）
```

## 下一步

确认计划后，手动修改 SKILL.md，然后重新运行 `rate` 验证改进效果。
