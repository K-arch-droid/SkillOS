#!/usr/bin/env bash
# scan-skills.sh — 扫描已安装 Skill 并生成 SKILL-REGISTRY.md 索引
# 用法: bash scripts/scan-skills.sh [--global] [--output references/SKILL-REGISTRY.md]

set -euo pipefail

TMPFILE=$(mktemp)
trap 'rm -f "$TMPFILE"' EXIT

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT="${2:-$PROJECT_DIR/references/SKILL-REGISTRY.md}"
SCOPE_FLAG=""
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# 解析参数
for arg in "$@"; do
  case "$arg" in
    --global) SCOPE_FLAG="-g" ;;
    --output=*) OUTPUT="${arg#*=}" ;;
  esac
done

echo "🔍 SkillOS: 扫描已安装 Skill..."

# 获取已安装 Skill 列表（JSON 格式）
SKILLS_JSON=$(npx skills ls $SCOPE_FLAG --json 2>/dev/null || echo "[]")

# 获取纯文本格式（备用）
SKILLS_TEXT=$(npx skills ls $SCOPE_FLAG 2>/dev/null || echo "")

# 生成 Registry 头部
cat > "$OUTPUT" << 'HEADER'
# Skill Registry

> SkillOS 维护的已安装 Skill 索引。由 `scripts/scan-skills.sh` 自动生成。

## 索引格式

| 字段 | 说明 |
|------|------|
| name | Skill 名称 |
| path | 安装路径 |
| scope | 作用域：global / project |
| agents | 支持的 Agent |
| description | 一句话描述（从 SKILL.md 提取） |

---

## 已安装 Skill

HEADER

# 追加时间戳
echo "> 最后扫描时间: $TIMESTAMP" >> "$OUTPUT"
echo "" >> "$OUTPUT"

# 解析 JSON 输出（如果可用）
echo "$SKILLS_JSON" > "$TMPFILE"

PYTHON_CMD=""
if command -v python &> /dev/null; then
  PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
  PYTHON_CMD="python3"
fi

if [ -n "$PYTHON_CMD" ] && [ "$SKILLS_JSON" != "[]" ]; then
  $PYTHON_CMD - "$TMPFILE" >> "$OUTPUT" << 'PYEOF'
import json, sys, os

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    raw = f.read()

try:
    data = json.loads(raw)
    if isinstance(data, list):
        for skill in data:
            name = skill.get("name", "unknown")
            skill_path = skill.get("path", "")
            scope = skill.get("scope", "unknown")
            agents = skill.get("agents", [])
            # Try to read description from SKILL.md
            desc = "N/A"
            skill_md = os.path.join(skill_path, "SKILL.md")
            if os.path.isfile(skill_md):
                try:
                    with open(skill_md, "r", encoding="utf-8") as sf:
                        content = sf.read(4000)
                    # Extract description from frontmatter
                    if content.startswith("---"):
                        fm_end = content.find("---", 3)
                        if fm_end > 0:
                            fm = content[3:fm_end]
                            for line in fm.split("\n"):
                                if line.startswith("description:"):
                                    desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                                    break
                except Exception:
                    pass
            agent_str = ", ".join(agents) if agents else "—"
            print("### " + name)
            print("- **Path:** `" + skill_path + "`")
            print("- **Scope:** " + scope)
            print("- **Agents:** " + agent_str)
            print("- **Description:** " + desc)
            print()
    else:
        print("<!-- JSON format unexpected -->")
except json.JSONDecodeError:
    print("<!-- JSON parse failed, using text output -->")
    print()
    print("```")
    print(raw[:2000])
    print("```")
PYEOF
else
  # 回退到文本输出
  echo "```" >> "$OUTPUT"
  echo "$SKILLS_TEXT" >> "$OUTPUT"
  echo "```" >> "$OUTPUT"
  echo "" >> "$OUTPUT"
fi

# 追加核心依赖 Skill 推荐
cat >> "$OUTPUT" << 'FOOTER'

---

## 核心依赖 Skill（推荐安装）

```bash
# Skill 路由 — 智能分发用户请求
npx skills add charon-fan/agent-playbook@skill-router -g -y

# Skill 评分 — 7 维度 A-F 评分
npx skills add antjanus/skillbox@rate-skill -g -y

# Skill 生成 — 8 阶段交互式生成器
npx skills add antjanus/skillbox@generate-skill -g -y

# Skill 优化 — 审查→计划→确认→实施→校验
npx skills add chujianyun/skills@skill-optimizer -g -y

# Skill 管理 — 扫描、安装、更新
npx skills add gohypergiant/agent-skills@accelint-skill-manager -g -y

# 工作流编排 — 多 Skill 协调
npx skills add charon-fan/agent-playbook@workflow-orchestrator -g -y

# 自我改进 — 从工作中学习
npx skills add charon-fan/agent-playbook@self-improving-agent -g -y
```
FOOTER

rm -f "$TMPFILE"

echo "✅ SkillOS: 索引已生成 → $OUTPUT"
SKILL_COUNT=$(grep -c "^### " "$OUTPUT" 2>/dev/null || echo "0")
echo "📊 共扫描到 $SKILL_COUNT 个 Skill"
