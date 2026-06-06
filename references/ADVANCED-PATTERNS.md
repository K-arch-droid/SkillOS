# SkillOS 高级模式

> 超越基础 Skill 管理的高级用法。

## 1. 批量评分

对所有已安装 Skill 进行批量评分：

```bash
# Linux/Mac
for skill in ~/.claude/skills/*/; do
  echo "--- $(basename "$skill") ---"
  python skillos.py rate "$skill" 2>/dev/null
  echo ""
done

# 输出 CSV 格式
python -c "
from skill_parser import parse_skill
from skill_analyzer import analyze
from pathlib import Path
import os, csv, sys

home = Path.home()
writer = csv.writer(sys.stdout)
writer.writerow(['name', 'type', 'grade', 'score', 'p0', 'p1', 'p2'])

for d in (home / '.claude' / 'skills').iterdir():
    if not d.is_dir(): continue
    p = parse_skill(str(d))
    if not p: continue
    r = analyze(p)
    p0 = sum(1 for f in r.findings if f.priority == 'P0')
    p1 = sum(1 for f in r.findings if f.priority == 'P1')
    p2 = sum(1 for f in r.findings if f.priority == 'P2')
    writer.writerow([r.skill_name, r.skill_type, r.grade, r.overall_score, p0, p1, p2])
" > skill-report.csv
```

## 2. Skill 质量趋势

追踪一个 Skill 的评分变化：

```bash
# 首次评分
python skillos.py rate ./my-skill > rate-v1.txt

# 修改后再次评分
python skillos.py rate ./my-skill > rate-v2.txt

# 对比
diff rate-v1.txt rate-v2.txt
```

## 3. 自动化 CI 集成

在 CI 中检查 Skill 质量：

```yaml
# .github/workflows/skill-check.yml
name: Skill Quality Check
on: [push, pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Rate Skills
        run: |
          for skill_dir in skills/*/; do
            python skillos.py rate "$skill_dir"
          done
```

## 4. Skill 模板自定义

修改 `templates/SKILL-TEMPLATE.md` 来自定义生成模板：

```bash
# 使用自定义模板
python skillos.py generate --name my-skill --type methodology
# 然后编辑生成的文件
```

## 5. 冲突自动解决

```bash
# 检测冲突并输出修复建议
python skillos.py conflicts --global 2>&1 | grep "建议" | sort -u
```

## 6. Skill 依赖图

```python
"""生成 Skill 依赖关系图。"""
from skill_parser import parse_skill, find_skill_md
from conflict_detector import extract_triggers
from pathlib import Path

skills = []
for p in find_skill_md(str(Path.home() / '.claude' / 'skills')):
    parsed = parse_skill(p)
    if parsed:
        skills.append(parsed)

# 输出 Mermaid 图
print("graph LR")
for i, s in enumerate(skills):
    name = s.frontmatter.name or f"skill_{i}"
    for j, other in enumerate(skills):
        if i == j:
            continue
        other_name = other.frontmatter.name or f"skill_{j}"
        triggers_a = extract_triggers(s)
        triggers_b = extract_triggers(other)
        overlap = len(triggers_a & triggers_b)
        if overlap > 5:
            print(f"  {name} -->|{overlap} shared| {other_name}")
```

## 7. 扩展评分维度

在 `skill_analyzer.py` 中添加自定义维度：

```python
def _analyze_custom(result, parsed):
    """自定义维度：国际化支持（5 分）。"""
    score = 100
    body = parsed.body
    # 检查是否有中文/英文双语
    has_cn = bool(re.search(r'[一-鿿]', body))
    has_en = bool(re.search(r'[a-zA-Z]{3,}', body))
    if has_cn and has_en:
        score = 100  # 双语支持
    elif has_cn:
        score = 60   # 仅中文
    elif has_en:
        score = 80   # 仅英文
    result.categories.append(CategoryScore("国际化", 5, score))
```
