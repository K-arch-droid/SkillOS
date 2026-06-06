# SkillOS Hooks

SkillOS 支持事件钩子，在特定操作前后执行自定义逻辑。

## 可用事件

| 事件 | 触发时机 | 参数 |
|------|---------|------|
| `before_rate` | 评分审查前 | skill_path |
| `after_rate` | 评分审查后 | skill_path, grade, score |
| `before_generate` | 生成 Skill 前 | name, type |
| `after_generate` | 生成 Skill 后 | name, output_dir |
| `before_optimize` | 优化前 | skill_path |
| `after_optimize` | 优化后 | skill_path, changes_count |
| `before_scan` | 扫描前 | scope |
| `after_scan` | 扫描后 | scope, count |
| `on_conflict` | 发现冲突时 | conflict_type, skill_a, skill_b |

## 配置方式

在 `_meta.json` 的 `hooks` 字段中配置：

```json
{
  "hooks": {
    "after_rate": "python scripts/on_rate.py",
    "on_conflict": "echo 'Conflict detected'"
  }
}
```

## 自定义 Hook 脚本

Hook 脚本通过环境变量接收参数：

```bash
#!/usr/bin/env bash
# scripts/on_rate.sh
# 环境变量: SKILL_PATH, GRADE, SCORE

echo "Rated $SKILL_PATH: $GRADE ($SCORE/100)"

# 如果评分低于 B，自动触发优化
if [[ "$GRADE" == "C" || "$GRADE" == "D" || "$GRADE" == "F" ]]; then
  echo "Score below B, consider optimizing..."
fi
```

## 内置 Hook

### 评分后自动记录

当评分完成后，自动将结果记录到 `state/evolution.json`。

### 冲突检测后提醒

当发现高严重度冲突时，输出详细修复建议。

### 扫描后更新索引

每次扫描完成后，自动更新 `references/SKILL-REGISTRY.md`。
