#!/usr/bin/env bash
# SkillOS 安装脚本
# 用法: bash scripts/install.sh [--global]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== SkillOS v1.0 安装 ==="
echo ""

# Check Python
PYTHON_CMD=""
if command -v python &> /dev/null; then
  PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
  PYTHON_CMD="python3"
else
  echo "❌ 需要 Python 3.10+"
  echo "   下载: https://www.python.org/downloads/"
  exit 1
fi

PY_VERSION=$($PYTHON_CMD --version 2>&1)
echo "✅ Python: $PY_VERSION"

# Check npx skills
if command -v npx &> /dev/null; then
  echo "✅ npx: $(npx --version 2>/dev/null || echo 'available')"
else
  echo "⚠️  npx 不可用（部分功能需要 Node.js）"
fi

echo ""
echo "=== 安装核心依赖 Skill ==="
echo ""

CORE_SKILLS=(
  "charon-fan/agent-playbook@skill-router"
  "antjanus/skillbox@rate-skill"
  "antjanus/skillbox@generate-skill"
  "chujianyun/skills@skill-optimizer"
  "gohypergiant/agent-skills@accelint-skill-manager"
  "charon-fan/agent-playbook@workflow-orchestrator"
  "charon-fan/agent-playbook@self-improving-agent"
)

for skill in "${CORE_SKILLS[@]}"; do
  echo -n "  安装 $skill ... "
  if npx skills add "$skill" -g -y > /dev/null 2>&1; then
    echo "✅"
  else
    echo "⚠️  跳过"
  fi
done

echo ""
echo "=== 初始化 ==="
echo ""

# Create state directory
mkdir -p "$PROJECT_DIR/state"
echo '{}' > "$PROJECT_DIR/state/registry.json"
echo '[]' > "$PROJECT_DIR/state/evolution.json"
echo '[]' > "$PROJECT_DIR/state/learnings.json"
echo "✅ state/ 目录已初始化"

# Run initial scan
cd "$PROJECT_DIR"
$PYTHON_CMD skillos.py registry --global 2>/dev/null || echo "⚠️  首次扫描可稍后运行: python skillos.py registry"

echo ""
echo "=== 安装完成 ==="
echo ""
echo "使用方式:"
echo "  python skillos.py list          # 列出已安装 Skill"
echo "  python skillos.py rate <path>   # 评分审查 Skill"
echo "  python skillos.py route <query> # 路由请求"
echo "  python skillos.py help          # 查看全部命令"
echo ""
echo "详细文档: README.md"
