#!/usr/bin/env bash
# SkillOS CLI 包装器
# 用法: bash scripts/skillos.sh <action> [options]
#
# 等价于: python skillos.py <action> [options]
# 适用于不想直接调用 python 的场景

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

PYTHON_CMD=""
if command -v python &> /dev/null; then
  PYTHON_CMD="python"
elif command -v python3 &> /dev/null; then
  PYTHON_CMD="python3"
else
  echo "Error: Python not found" >&2
  exit 1
fi

exec $PYTHON_CMD "$PROJECT_DIR/skillos.py" "$@"
