# 示例：检测 Skill 冲突

## 场景

你安装了很多 Skill，想知道有没有触发词冲突。

## 命令

```bash
python skillos.py conflicts --global
```

## 输出示例

```
# Skill 冲突检测报告

**扫描 Skill 数：** 22
**发现冲突数：** 12

## 冲突摘要

| 类型              | 数量 |
|-------------------|------|
| capability_duplicate | 7  |
| trigger_overlap      | 5  |

## 冲突详情

### 高严重度

**graphify-windows** <-> **graphify**
- 类型：trigger_overlap
- 详情：触发词重叠率 100%，共 36 个共同词
- 建议：让 description 的前 50 字符包含独特名词，用 'Do NOT use for…' 划清边界

### 低严重度

**google-agents-cli-scaffold** <-> **google-agents-cli-scaffold**
- 类型：capability_duplicate
- 详情：章节结构重叠率 100%，可能有重复能力
- 建议：检查是否可以合并或明确分工
```

## 如何解决冲突

1. **触发词重叠** → 修改 description，让前 50 字符包含独特名词
2. **能力重复** → 考虑合并或明确分工
3. **负面范围重叠** → 在 description 中添加 "Do NOT use for…"
