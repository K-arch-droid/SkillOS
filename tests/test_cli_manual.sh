#!/usr/bin/env bash
# SkillOS — CLI 手动测试脚本
# 用法: cd SkillOS && bash tests/test_cli_manual.sh
# 每个测试会打印命令、执行、检查退出码

set -e
PASS=0
FAIL=0
SKILLOS="python skillos.py"

pass() { PASS=$((PASS+1)); echo "  ✅ PASS: $1"; }
fail() { FAIL=$((FAIL+1)); echo "  ❌ FAIL: $1"; }

echo "=========================================="
echo "  SkillOS v1.0 — CLI 手动功能测试"
echo "=========================================="
echo ""

# ─── Test 1: help ─────────────────────────────────────────────────────────────
echo "📋 Test 1: skillos help"
OUTPUT=$($SKILLOS help 2>&1)
if echo "$OUTPUT" | grep -q "SkillOS"; then
    pass "help 输出包含 SkillOS"
else
    fail "help 输出缺少 SkillOS"
fi
echo ""

# ─── Test 2: list ─────────────────────────────────────────────────────────────
echo "📋 Test 2: skillos list --global"
OUTPUT=$($SKILLOS list --global 2>&1)
if echo "$OUTPUT" | grep -q "已安装 Skill"; then
    pass "list 输出包含 '已安装 Skill'"
else
    fail "list 输出格式错误"
fi
echo ""

# ─── Test 3: registry ─────────────────────────────────────────────────────────
echo "📋 Test 3: skillos registry --global"
OUTPUT=$($SKILLOS registry --global 2>&1)
if echo "$OUTPUT" | grep -q "索引已生成"; then
    pass "registry 成功生成索引"
else
    fail "registry 索引生成失败"
fi
echo ""

# ─── Test 4: rate (使用内置 SKILL.md) ──────────────────────────────────────────
echo "📋 Test 4: skillos rate ."
OUTPUT=$($SKILLOS rate . 2>&1)
if echo "$OUTPUT" | grep -q "审查报告"; then
    pass "rate 输出包含审查报告"
else
    fail "rate 输出格式错误"
fi
if echo "$OUTPUT" | grep -q "评分明细"; then
    pass "rate 包含评分明细"
else
    fail "rate 缺少评分明细"
fi
echo ""

# ─── Test 5: analyze --json ────────────────────────────────────────────────────
echo "📋 Test 5: skillos analyze . --json"
OUTPUT=$($SKILLOS analyze . --json 2>&1)
# Validate JSON
if echo "$OUTPUT" | python -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    pass "analyze --json 输出合法 JSON"
else
    fail "analyze --json 输出不是合法 JSON"
fi
# Check JSON fields
if echo "$OUTPUT" | python -c "
import sys, json
d = json.load(sys.stdin)
assert 'name' in d, 'missing name'
assert 'grade' in d, 'missing grade'
assert 'score' in d, 'missing score'
assert 'categories' in d, 'missing categories'
assert len(d['categories']) == 7, f'expected 7 categories, got {len(d[\"categories\"])}'
print('OK')
" 2>&1 | grep -q "OK"; then
    pass "analyze JSON 包含全部字段和 7 个维度"
else
    fail "analyze JSON 字段不完整"
fi
echo ""

# ─── Test 6: route ────────────────────────────────────────────────────────────
echo "📋 Test 6: skillos route \"帮我写测试\""
OUTPUT=$($SKILLOS route "帮我写测试" 2>&1)
if echo "$OUTPUT" | grep -q "路由结果\|Skill\|未找到"; then
    pass "route 输出格式正确"
else
    fail "route 输出格式错误"
fi
echo ""

# ─── Test 7: conflicts ────────────────────────────────────────────────────────
echo "📋 Test 7: skillos conflicts --global"
OUTPUT=$($SKILLOS conflicts --global 2>&1)
if echo "$OUTPUT" | grep -q "冲突检测\|需要至少\|未发现"; then
    pass "conflicts 输出格式正确"
else
    fail "conflicts 输出格式错误"
fi
echo ""

# ─── Test 8: generate ─────────────────────────────────────────────────────────
echo "📋 Test 8: skillos generate"
TEMP_DIR=$(mktemp -d)
OUTPUT=$($SKILLOS generate --name test-gen-skill --type methodology --desc "A test generated skill" -o "$TEMP_DIR/test-gen-skill" 2>&1)
if [ -f "$TEMP_DIR/test-gen-skill/SKILL.md" ]; then
    pass "generate 创建了 SKILL.md"
else
    fail "generate 未创建 SKILL.md"
fi
if [ -f "$TEMP_DIR/test-gen-skill/references/EVAL.md" ]; then
    pass "generate 创建了 references/EVAL.md"
else
    fail "generate 未创建 EVAL.md"
fi
# Verify generated content
GEN_CONTENT=$(cat "$TEMP_DIR/test-gen-skill/SKILL.md")
if echo "$GEN_CONTENT" | grep -q "name: test-gen-skill"; then
    pass "生成的 SKILL.md 包含正确的 name"
else
    fail "生成的 SKILL.md name 错误"
fi
if echo "$GEN_CONTENT" | grep -q "description:"; then
    pass "生成的 SKILL.md 包含 description"
else
    fail "生成的 SKILL.md 缺少 description"
fi
echo ""

# ─── Test 9: optimize ─────────────────────────────────────────────────────────
echo "📋 Test 9: skillos optimize ."
OUTPUT=$($SKILLOS optimize . 2>&1)
if echo "$OUTPUT" | grep -q "审查结论"; then
    pass "optimize 输出包含审查结论"
else
    fail "optimize 输出格式错误"
fi
echo ""

# ─── Test 10: rate with output file ───────────────────────────────────────────
echo "📋 Test 10: skillos rate . -o report.md"
OUTPUT=$($SKILLOS rate . -o "$TEMP_DIR/report.md" 2>&1)
if [ -f "$TEMP_DIR/report.md" ]; then
    pass "rate -o 生成了报告文件"
    if grep -q "审查报告" "$TEMP_DIR/report.md"; then
        pass "报告文件内容正确"
    else
        fail "报告文件内容错误"
    fi
else
    fail "rate -o 未生成报告文件"
fi
echo ""

# ─── Test 11: generate all types ──────────────────────────────────────────────
echo "📋 Test 11: generate 全部 5 种类型"
for TYPE in methodology technical auditing reference automation; do
    TYPE_DIR="$TEMP_DIR/type-$TYPE"
    OUTPUT=$($SKILLOS generate --name "test-$TYPE" --type "$TYPE" --desc "Test $TYPE skill" -o "$TYPE_DIR" 2>&1)
    if [ -f "$TYPE_DIR/SKILL.md" ]; then
        pass "generate --type $TYPE 成功"
    else
        fail "generate --type $TYPE 失败"
    fi
done
echo ""

# ─── Test 12: 错误处理 ─────────────────────────────────────────────────────────
echo "📋 Test 12: 错误处理"
OUTPUT=$($SKILLOS rate /nonexistent/path 2>&1)
if echo "$OUTPUT" | grep -q "找不到"; then
    pass "rate 不存在的路径 → 正确报错"
else
    fail "rate 不存在路径未报错"
fi

OUTPUT=$($SKILLOS route 2>&1)
if echo "$OUTPUT" | grep -q "请提供"; then
    pass "route 无参数 → 正确提示"
else
    fail "route 无参数未提示"
fi

OUTPUT=$($SKILLOS generate 2>&1)
if echo "$OUTPUT" | grep -q "请指定"; then
    pass "generate 无 name → 正确提示"
else
    fail "generate 无 name 未提示"
fi
echo ""

# ─── 清理 ─────────────────────────────────────────────────────────────────────
rm -rf "$TEMP_DIR"

# ─── 汇总 ─────────────────────────────────────────────────────────────────────
echo "=========================================="
echo "  测试结果汇总"
echo "=========================================="
echo "  ✅ 通过: $PASS"
echo "  ❌ 失败: $FAIL"
echo "  总计:   $((PASS + FAIL))"
echo ""

if [ $FAIL -eq 0 ]; then
    echo "🎉 全部测试通过！"
    exit 0
else
    echo "⚠️  有 $FAIL 个测试失败，请检查。"
    exit 1
fi
