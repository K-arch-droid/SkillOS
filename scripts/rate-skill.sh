#!/usr/bin/env bash
# rate-skill.sh — SkillOS Skill 评分包装器
# 用法: bash scripts/rate-skill.sh <path/to/SKILL.md>
#
# 功能:
#   1. 读取目标 SKILL.md
#   2. 调用 rate-skill skill 进行评分（如果已安装）
#   3. 否则使用内置检查清单进行基础审查

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CHECKLIST="$PROJECT_DIR/references/REVIEW-CHECKLIST.md"

if [ $# -eq 0 ]; then
  echo "用法: bash scripts/rate-skill.sh <path/to/SKILL.md>"
  echo ""
  echo "示例:"
  echo "  bash scripts/rate-skill.sh ./my-skill/SKILL.md"
  echo "  bash scripts/rate-skill.sh ~/.claude/skills/find-skills/SKILL.md"
  exit 1
fi

TARGET="$1"

# 如果传入的是目录，查找 SKILL.md
if [ -d "$TARGET" ]; then
  TARGET="$TARGET/SKILL.md"
fi

if [ ! -f "$TARGET" ]; then
  echo "❌ 文件不存在: $TARGET"
  exit 1
fi

echo "📋 SkillOS: 审查 $TARGET"
echo ""

# 基础检查
echo "=== 基础检查 ==="
echo ""

# 检查 frontmatter
if head -1 "$TARGET" | grep -q "^---"; then
  echo "✅ Frontmatter 存在"
else
  echo "❌ 缺少 Frontmatter (应以 --- 开头)"
fi

# 检查 description
DESC=$(sed -n '/^---$/,/^---$/p' "$TARGET" | grep "^description:" | head -1)
if [ -n "$DESC" ]; then
  DESC_LEN=${#DESC}
  echo "✅ Description 存在 ($DESC_LEN 字符)"
  if [ $DESC_LEN -gt 1024 ]; then
    echo "  ⚠️  Description 超过 1024 字符硬上限"
  elif [ $DESC_LEN -gt 230 ]; then
    echo "  ⚠️  Description 超过 230 字符软目标"
  fi
  # 检查是否多行
  if echo "$DESC" | grep -q "|"; then
    echo "  ❌ Description 使用了 YAML 块标量 (|) — 会破坏发现机制"
  fi
  # 检查第一人称
  if echo "$DESC" | grep -qi "^description:.*I "; then
    echo "  ⚠️  Description 可能使用了第一人称"
  fi
else
  echo "❌ 缺少 description 字段"
fi

# 检查 name
NAME=$(sed -n '/^---$/,/^---$/p' "$TARGET" | grep "^name:" | head -1)
if [ -n "$NAME" ]; then
  NAME_VAL=$(echo "$NAME" | sed 's/^name:\s*//')
  echo "✅ Name: $NAME_VAL"
  if echo "$NAME_VAL" | grep -qE '[A-Z]|--|anthropic|claude'; then
    echo "  ⚠️  Name 包含大写/连续连字符/保留字"
  fi
else
  echo "❌ 缺少 name 字段"
fi

# 检查行数
LINE_COUNT=$(wc -l < "$TARGET")
echo ""
echo "=== 统计 ==="
echo "总行数: $LINE_COUNT"
if [ "$LINE_COUNT" -gt 500 ]; then
  echo "⚠️  超过 500 行，建议拆分到 references/"
elif [ "$LINE_COUNT" -gt 300 ]; then
  echo "⚠️  超过 300 行软上限"
else
  echo "✅ 行数在合理范围内"
fi

# 检查必要章节
echo ""
echo "=== 章节检查 ==="
for section in "Overview" "Examples" "Gotchas" "Workflow" "Quick Start"; do
  if grep -qi "## $section" "$TARGET"; then
    echo "✅ 包含 ## $section"
  fi
done

# 检查反模式
echo ""
echo "=== 反模式检查 ==="
if grep -qE '^## [A-Z]{3,}' "$TARGET"; then
  echo "⚠️  发现全大写章节标题（可能的反模式）"
fi
if grep -qE '\\\\' "$TARGET" && ! grep -qE '```' "$TARGET"; then
  echo "⚠️  可能包含 Windows 反斜杠路径"
fi

echo ""
echo "=== 完成 ==="
echo "详细评分标准参见: $CHECKLIST"
echo "建议使用 rate-skill skill 进行完整 7 维度评分。"
