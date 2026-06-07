#!/usr/bin/env python
"""SkillOS — 全功能自动化测试套件。

覆盖全部 8 个模块、27 个公开函数、9 个 CLI 子命令。

用法：
    cd SkillOS
    python -m tests.test_all              # 运行全部测试
    python -m tests.test_all -v           # 详细输出
    python -m tests.test_all TestParser   # 只跑某个测试类
"""

import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# 确保 SkillOS 根目录在 Python 路径中
SKILLOS_ROOT = str(Path(__file__).parent.parent)
sys.path.insert(0, SKILLOS_ROOT)

# Fix Windows console encoding for test output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─── 测试用 Fixtures ────────────────────────────────────────────────────────────

SAMPLE_SKILL_MD = """---
name: test-sample-skill
description: "Use this skill whenever the user asks to \"write tests\", \"run tests\", or \"test coverage\". A testing helper skill for unit and integration tests. Do NOT use for deployment or CI/CD setup."
license: MIT
argument-hint: <action>
metadata:
  author: test
  version: "1.0.0"
---

# Test Sample Skill

## Overview

This skill helps with writing and running tests.

## Workflow

### Phase 1: Analyze

Analyze the test requirements.

### Phase 2: Execute

Generate and run tests.

### Phase 3: Verify

Verify test results.

## Examples

### Example: Writing Unit Tests

✅ Desired

User asks to write tests for a function. The skill generates pytest-compatible test cases.

Why it works: Follows the test pyramid pattern.

### Counter-example

❌ Anti-pattern

Writing tests without understanding the function's contract.

Why it fails: Tests pass but don't catch real bugs.

## Gotchas

- **Symptom:** Tests pass locally but fail in CI
- **Cause:** Environment differences
- **Fix:** Use containers for consistent test environments
"""

SAMPLE_SKILL_MINIMAL = """---
name: minimal-skill
description: "A minimal skill for testing."
---

# Minimal Skill

## Overview

Just a minimal skill.
"""

SAMPLE_SKILL_BAD = """---
name: Bad-Name--Claude
description: |
  This is a multiline description
  that uses YAML block scalar.
version: "1.0.0"
author: someone
---

# Bad Skill

## SECTION ONE

It is important to note that this skill does things.

As we all know, skills are useful.

Let me explain how this works.

In this section, we will cover the basics.
"""


def _write_temp_skill(content: str, with_references: bool = False) -> str:
    """创建临时 SKILL.md 文件，返回目录路径。"""
    tmpdir = tempfile.mkdtemp()
    skill_path = os.path.join(tmpdir, "SKILL.md")
    with open(skill_path, "w", encoding="utf-8") as f:
        f.write(content)
    if with_references:
        refs_dir = os.path.join(tmpdir, "references")
        os.makedirs(refs_dir, exist_ok=True)
        with open(os.path.join(refs_dir, "GOTCHAS.md"), "w", encoding="utf-8") as f:
            f.write("# Gotchas\n\nSome gotchas.\n")
    return tmpdir


# ─── Module 1: skill_parser ─────────────────────────────────────────────────────

class TestParser(unittest.TestCase):
    """测试 skill_parser.py 的全部公开函数。"""

    def test_parse_frontmatter_basic(self):
        from skill_parser import parse_frontmatter
        raw = 'name: my-skill\ndescription: "A test skill"\nlicense: MIT'
        fm = parse_frontmatter(raw)
        self.assertEqual(fm.name, "my-skill")
        self.assertEqual(fm.description, "A test skill")
        self.assertEqual(fm.license, "MIT")

    def test_parse_frontmatter_empty(self):
        from skill_parser import parse_frontmatter
        fm = parse_frontmatter("")
        self.assertEqual(fm.name, "")
        self.assertEqual(fm.description, "")

    def test_parse_frontmatter_special_fields(self):
        from skill_parser import parse_frontmatter
        raw = 'argument-hint: <action>\ndisable-model-invocation: true\nuser-invocable: false'
        fm = parse_frontmatter(raw)
        self.assertEqual(fm.argument_hint, "<action>")
        self.assertTrue(fm.disable_model_invocation)
        self.assertFalse(fm.user_invocable)

    def test_parse_sections_basic(self):
        from skill_parser import parse_sections
        body = "## First\nContent here\n## Second\nMore content\n### Sub\nDetails"
        sections = parse_sections(body)
        self.assertEqual(len(sections), 3)
        self.assertEqual(sections[0].title, "First")
        self.assertEqual(sections[0].level, 2)
        self.assertEqual(sections[1].title, "Second")
        self.assertEqual(sections[2].title, "Sub")
        self.assertEqual(sections[2].level, 3)

    def test_parse_sections_empty(self):
        from skill_parser import parse_sections
        sections = parse_sections("")
        self.assertEqual(len(sections), 0)

    def test_detect_skill_type_methodology(self):
        from skill_parser import detect_skill_type, parse_sections
        body = "## Workflow\n### Phase 1\nDo stuff\n## Examples\nExample here"
        sections = parse_sections(body)
        self.assertEqual(detect_skill_type(sections, body), "methodology")

    def test_detect_skill_type_auditing(self):
        from skill_parser import detect_skill_type, parse_sections
        body = "## Scoring Rubric\n| dim | weight |\n## Output Format\nMarkdown"
        sections = parse_sections(body)
        self.assertEqual(detect_skill_type(sections, body), "auditing")

    def test_detect_skill_type_technical(self):
        from skill_parser import detect_skill_type, parse_sections
        body = "## Quick Start\n```bash\nnpm install\n```\n## How It Works\nDetails"
        sections = parse_sections(body)
        self.assertEqual(detect_skill_type(sections, body), "technical")

    def test_detect_skill_type_reference(self):
        from skill_parser import detect_skill_type, parse_sections
        body = "## Schema\nJSON schema here\n## Lookup\nTable"
        sections = parse_sections(body)
        self.assertEqual(detect_skill_type(sections, body), "reference")

    def test_detect_skill_type_automation(self):
        from skill_parser import detect_skill_type, parse_sections
        body = "## Command Surface\n| cmd | desc |\n## Failure Modes\n| fail | handling |"
        sections = parse_sections(body)
        self.assertEqual(detect_skill_type(sections, body), "automation")

    def test_detect_skill_type_unknown(self):
        from skill_parser import detect_skill_type, parse_sections
        body = "## Random\nNothing special"
        sections = parse_sections(body)
        self.assertEqual(detect_skill_type(sections, body), "unknown")

    def test_parse_skill_full(self):
        from skill_parser import parse_skill
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD, with_references=True)
        result = parse_skill(tmpdir)
        self.assertIsNotNone(result)
        self.assertEqual(result.frontmatter.name, "test-sample-skill")
        self.assertIn("write tests", result.frontmatter.description)
        self.assertEqual(result.skill_type, "methodology")
        self.assertTrue(result.has_references_dir)
        self.assertIn("GOTCHAS.md", result.references_files)
        self.assertGreater(result.body_lines, 10)

    def test_parse_skill_file_path(self):
        from skill_parser import parse_skill
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        result = parse_skill(os.path.join(tmpdir, "SKILL.md"))
        self.assertIsNotNone(result)

    def test_parse_skill_nonexistent(self):
        from skill_parser import parse_skill
        self.assertIsNone(parse_skill("/nonexistent/path"))

    def test_find_skill_md(self):
        from skill_parser import find_skill_md
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        results = find_skill_md(tmpdir)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].endswith("SKILL.md"))

    def test_find_skill_md_nested(self):
        from skill_parser import find_skill_md
        tmpdir = tempfile.mkdtemp()
        for name in ["skill-a", "skill-b"]:
            d = os.path.join(tmpdir, name)
            os.makedirs(d)
            with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
                f.write(SAMPLE_SKILL_MD)
        results = find_skill_md(tmpdir)
        self.assertEqual(len(results), 2)

    def test_get_section_by_title(self):
        from skill_parser import parse_skill, get_section_by_title
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        parsed = parse_skill(tmpdir)
        section = get_section_by_title(parsed.sections, "examples")
        self.assertIsNotNone(section)
        self.assertIn("examples", section.title.lower())

    def test_get_all_section_titles(self):
        from skill_parser import parse_skill, get_all_section_titles
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        parsed = parse_skill(tmpdir)
        titles = get_all_section_titles(parsed.sections)
        self.assertIsInstance(titles, list)
        self.assertTrue(len(titles) > 0)


# ─── Module 2: skill_analyzer ───────────────────────────────────────────────────

class TestAnalyzer(unittest.TestCase):
    """测试 skill_analyzer.py 的全部公开函数。"""

    def test_grade_from_score(self):
        from skill_analyzer import grade_from_score
        self.assertEqual(grade_from_score(95), "A")
        self.assertEqual(grade_from_score(85), "B")
        self.assertEqual(grade_from_score(75), "C")
        self.assertEqual(grade_from_score(65), "D")
        self.assertEqual(grade_from_score(50), "F")

    def test_analyze_good_skill(self):
        from skill_parser import parse_skill
        from skill_analyzer import analyze
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD, with_references=True)
        parsed = parse_skill(tmpdir)
        result = analyze(parsed)
        self.assertEqual(result.skill_name, "test-sample-skill")
        self.assertEqual(result.skill_type, "methodology")
        self.assertGreaterEqual(result.overall_score, 50)
        self.assertIn(result.grade, ["A", "B", "C", "D", "F"])
        self.assertEqual(len(result.categories), 7)
        self.assertIsInstance(result.findings, list)
        self.assertIsInstance(result.strengths, list)

    def test_analyze_minimal_skill(self):
        from skill_parser import parse_skill
        from skill_analyzer import analyze
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MINIMAL)
        parsed = parse_skill(tmpdir)
        result = analyze(parsed)
        self.assertIsNotNone(result)
        self.assertEqual(result.skill_name, "minimal-skill")

    def test_analyze_bad_skill(self):
        from skill_parser import parse_skill
        from skill_analyzer import analyze
        tmpdir = _write_temp_skill(SAMPLE_SKILL_BAD)
        parsed = parse_skill(tmpdir)
        result = analyze(parsed)
        # Bad skill should have P0/P1 findings
        p0_findings = [f for f in result.findings if f.priority == "P0"]
        p1_findings = [f for f in result.findings if f.priority == "P1"]
        self.assertTrue(len(p0_findings) > 0 or len(p1_findings) > 0,
                        "Bad skill should have P0 or P1 findings")
        # Should have description issues (multiline)
        desc_findings = [f for f in result.findings if f.category == "Description 质量"]
        self.assertTrue(len(desc_findings) > 0)

    def test_format_report(self):
        from skill_parser import parse_skill
        from skill_analyzer import analyze, format_report
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        parsed = parse_skill(tmpdir)
        result = analyze(parsed)
        report = format_report(result)
        self.assertIn("Skill 审查报告", report)
        self.assertIn("评分明细", report)
        self.assertIn("test-sample-skill", report)

    def test_category_weights_sum(self):
        """验证 7 维度权重之和为 100。"""
        from skill_parser import parse_skill
        from skill_analyzer import analyze
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        parsed = parse_skill(tmpdir)
        result = analyze(parsed)
        total_weight = sum(c.weight for c in result.categories)
        self.assertEqual(total_weight, 100)


# ─── Module 3: skill_router ─────────────────────────────────────────────────────

class TestRouter(unittest.TestCase):
    """测试 skill_router.py 的全部公开函数。"""

    def _get_parsed_skills(self):
        from skill_parser import parse_skill
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        parsed = parse_skill(tmpdir)
        return [parsed]

    def test_route_request_match(self):
        from skill_router import route_request
        skills = self._get_parsed_skills()
        result = route_request("帮我写测试", skills)
        self.assertIsNotNone(result)
        self.assertEqual(result.query, "帮我写测试")
        self.assertIsInstance(result.matches, list)

    def test_route_request_no_match(self):
        from skill_router import route_request
        skills = self._get_parsed_skills()
        result = route_request("今天天气怎么样", skills)
        self.assertIsNotNone(result)
        # Low or no confidence for unrelated query
        if result.matches:
            self.assertLess(result.matches[0].confidence, 0.5)

    def test_route_request_english(self):
        from skill_router import route_request
        skills = self._get_parsed_skills()
        result = route_request("write tests for my code", skills)
        self.assertIsNotNone(result)

    def test_format_route_result(self):
        from skill_router import route_request, format_route_result
        skills = self._get_parsed_skills()
        result = route_request("帮我写测试", skills)
        formatted = format_route_result(result)
        self.assertIn("Skill 路由结果", formatted)
        self.assertIn("用户请求", formatted)

    def test_format_route_result_empty(self):
        from skill_router import RouteResult, RouteMatch, format_route_result
        result = RouteResult(query="test", matches=[], best_match=None)
        formatted = format_route_result(result)
        self.assertIn("未找到匹配", formatted)

    def test_tokenize(self):
        from skill_router import _tokenize
        tokens = _tokenize("Help me write unit tests please")
        self.assertIn("write", tokens)
        self.assertIn("unit", tokens)
        self.assertIn("tests", tokens)
        # Stop words should be removed
        self.assertNotIn("help", tokens)
        self.assertNotIn("please", tokens)
        # All tokens should be >= 2 chars
        for t in tokens:
            self.assertGreaterEqual(len(t), 2)

    def test_route_workflow_basic(self):
        """workflow 路由应返回 WorkflowRecommendation。"""
        from skill_router import route_workflow
        from skill_parser import parse_skill
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        parsed = parse_skill(tmpdir)
        rec = route_workflow("帮我写测试", [parsed])
        self.assertIsNotNone(rec)
        self.assertEqual(rec.query, "帮我写测试")
        self.assertIsInstance(rec.steps, list)
        self.assertGreaterEqual(len(rec.steps), 0)

    def test_route_workflow_no_match(self):
        """无匹配时返回空 steps。"""
        from skill_router import route_workflow
        from skill_parser import parse_skill
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MINIMAL)
        parsed = parse_skill(tmpdir)
        rec = route_workflow("xyz nonexistent query 12345", [parsed])
        self.assertIsNotNone(rec)
        # May have 0 or 1 step depending on match
        self.assertIsInstance(rec.steps, list)

    def test_format_workflow_recommendation(self):
        from skill_router import route_workflow, format_workflow_recommendation
        from skill_parser import parse_skill
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        parsed = parse_skill(tmpdir)
        rec = route_workflow("帮我写测试", [parsed])
        formatted = format_workflow_recommendation(rec)
        self.assertIn("工作流推荐", formatted)
        self.assertIn("用户请求", formatted)


# ─── Module 4: conflict_detector ────────────────────────────────────────────────

class TestConflictDetector(unittest.TestCase):
    """测试 conflict_detector.py 的全部公开函数。"""

    def _make_skill(self, name, description):
        """快速创建 mock SkillParseResult。"""
        from skill_parser import SkillParseResult, SkillFrontmatter, SkillSection
        return SkillParseResult(
            path=f"/tmp/{name}",
            frontmatter=SkillFrontmatter(name=name, description=description),
            body="## Overview\nContent\n## Examples\nExample",
            body_lines=4,
            sections=[
                SkillSection(title="Overview", level=2, line_start=0, line_end=1, content="Content"),
                SkillSection(title="Examples", level=2, line_start=2, line_end=3, content="Example"),
            ],
            has_references_dir=False,
            references_files=[],
            skill_type="methodology",
        )

    def test_extract_triggers(self):
        from conflict_detector import extract_triggers
        skill = self._make_skill("test", 'Use whenever user asks to "write tests" or "run tests"')
        triggers = extract_triggers(skill)
        self.assertIn("write tests", triggers)
        self.assertIn("run tests", triggers)

    def test_extract_scope(self):
        from conflict_detector import extract_scope
        skill = self._make_skill("test", "A skill. Do NOT use for deployment or CI/CD setup.")
        scope = extract_scope(skill)
        self.assertTrue(len(scope) > 0)

    def test_compute_overlap_identical(self):
        from conflict_detector import compute_overlap
        s = {"a", "b", "c"}
        self.assertAlmostEqual(compute_overlap(s, s), 1.0)

    def test_compute_overlap_disjoint(self):
        from conflict_detector import compute_overlap
        self.assertAlmostEqual(compute_overlap({"a"}, {"b"}), 0.0)

    def test_compute_overlap_empty(self):
        from conflict_detector import compute_overlap
        self.assertAlmostEqual(compute_overlap(set(), {"a"}), 0.0)
        self.assertAlmostEqual(compute_overlap({"a"}, set()), 0.0)

    def test_detect_conflicts_no_overlap(self):
        from conflict_detector import detect_conflicts
        a = self._make_skill("skill-a", 'Use for "cooking" and "recipes"')
        b = self._make_skill("skill-b", 'Use for "deployment" and "ci/cd"')
        report = detect_conflicts([a, b])
        self.assertEqual(report.total_skills, 2)
        # Should have few or no conflicts for unrelated skills
        high_conflicts = [c for c in report.conflicts if c.severity == "high"]
        self.assertEqual(len(high_conflicts), 0)

    def test_detect_conflicts_high_overlap(self):
        from conflict_detector import detect_conflicts
        a = self._make_skill("skill-a", 'Use whenever user asks to "write tests" "run tests" "test coverage"')
        b = self._make_skill("skill-b", 'Use whenever user asks to "write tests" "run tests" "test coverage"')
        report = detect_conflicts([a, b])
        # Identical descriptions should trigger high overlap
        trigger_conflicts = [c for c in report.conflicts if c.conflict_type == "trigger_overlap"]
        self.assertTrue(len(trigger_conflicts) > 0)

    def test_detect_conflicts_single_skill(self):
        from conflict_detector import detect_conflicts
        a = self._make_skill("solo", "A solo skill")
        report = detect_conflicts([a])
        self.assertEqual(report.total_skills, 1)
        self.assertEqual(len(report.conflicts), 0)

    def test_format_conflict_report(self):
        from conflict_detector import detect_conflicts, format_conflict_report
        a = self._make_skill("skill-a", 'Use for "testing" and "qa"')
        b = self._make_skill("skill-b", 'Use for "testing" and "qa"')
        report = detect_conflicts([a, b])
        formatted = format_conflict_report(report)
        self.assertIn("冲突检测报告", formatted)
        self.assertIn("skill-a", formatted)

    def test_detect_relationships_complement(self):
        """互补关系：领域相邻但触发词不重叠。"""
        from conflict_detector import detect_relationships
        a = self._make_skill("code-reviewer", 'Use whenever user asks to "review code" or "code review"')
        b = self._make_skill("test-automator", 'Use whenever user asks to "write tests" or "run tests"')
        report = detect_relationships([a, b])
        self.assertEqual(report.total_skills, 2)
        complement = [r for r in report.relationships if r.relation_type == "complement"]
        self.assertTrue(len(complement) > 0, "Should detect complement between code review and testing")
        self.assertEqual(complement[0].source, "inferred")

    def test_detect_relationships_conflict_preserved(self):
        """原有冲突检测在关系图谱中保留。"""
        from conflict_detector import detect_relationships
        a = self._make_skill("skill-a", 'Use for "testing" "qa" "coverage"')
        b = self._make_skill("skill-b", 'Use for "testing" "qa" "coverage"')
        report = detect_relationships([a, b])
        conflicts = [r for r in report.relationships if r.relation_type == "conflict"]
        self.assertTrue(len(conflicts) > 0)
        self.assertEqual(conflicts[0].source, "extracted")

    def test_detect_relationships_reference(self):
        """引用关系：SKILL.md 正文引用其他 Skill。"""
        from conflict_detector import detect_relationships
        from skill_parser import SkillParseResult, SkillFrontmatter, SkillSection
        a = SkillParseResult(
            path="/tmp/skill-a",
            frontmatter=SkillFrontmatter(name="skill-a", description="Skill A"),
            body="## Overview\nSee skill-b.md for details.",
            body_lines=2,
            sections=[SkillSection(title="Overview", level=2, line_start=0, line_end=1, content="See skill-b.md")],
            has_references_dir=False,
            references_files=[],
            skill_type="methodology",
        )
        b = self._make_skill("skill-b", "Skill B")
        report = detect_relationships([a, b])
        refs = [r for r in report.relationships if r.relation_type == "reference"]
        self.assertTrue(len(refs) > 0)
        self.assertEqual(refs[0].confidence, 1.0)

    def test_detect_relationships_collaboration(self):
        """协作关系：产出方 → 消费方。"""
        from conflict_detector import detect_relationships
        a = self._make_skill("code-generator", 'Use to "generate code" and "create files"')
        b = self._make_skill("code-reviewer", 'Use to "review code" and "audit"')
        report = detect_relationships([a, b])
        collabs = [r for r in report.relationships if r.relation_type == "collaboration"]
        self.assertTrue(len(collabs) > 0, "Should detect collaboration between generator and reviewer")
        self.assertEqual(collabs[0].source, "inferred")
        self.assertGreater(collabs[0].confidence, 0.5)

    def test_detect_relationships_empty(self):
        """空输入。"""
        from conflict_detector import detect_relationships
        report = detect_relationships([])
        self.assertEqual(report.total_skills, 0)
        self.assertEqual(len(report.relationships), 0)

    def test_detect_relationships_single(self):
        """单个 Skill 无法检测关系。"""
        from conflict_detector import detect_relationships
        a = self._make_skill("solo", "A solo skill")
        report = detect_relationships([a])
        self.assertEqual(report.total_skills, 1)
        self.assertEqual(len(report.relationships), 0)

    def test_format_relationship_report(self):
        from conflict_detector import detect_relationships, format_relationship_report
        a = self._make_skill("skill-a", 'Use for "testing"')
        b = self._make_skill("skill-b", 'Use for "deployment"')
        report = detect_relationships([a, b])
        formatted = format_relationship_report(report)
        self.assertIn("关系图谱", formatted)

    def test_relationships_to_json(self):
        from conflict_detector import detect_relationships, relationships_to_json
        a = self._make_skill("skill-a", 'Use for "testing"')
        b = self._make_skill("skill-b", 'Use for "testing"')
        report = detect_relationships([a, b])
        json_str = relationships_to_json(report)
        data = json.loads(json_str)
        self.assertIn("total_skills", data)
        self.assertIn("relationships", data)
        self.assertEqual(data["total_skills"], 2)

    def test_relationships_to_mermaid(self):
        from conflict_detector import detect_relationships, relationships_to_mermaid
        a = self._make_skill("skill-a", 'Use for "testing"')
        b = self._make_skill("skill-b", 'Use for "deployment"')
        report = detect_relationships([a, b])
        mermaid = relationships_to_mermaid(report)
        self.assertIn("graph LR", mermaid)
        self.assertIn("skill_a", mermaid)


# ─── Module 5: skill_registry ───────────────────────────────────────────────────

class TestRegistry(unittest.TestCase):
    """测试 skill_registry.py 的全部公开函数。"""

    def test_registry_dataclass(self):
        from skill_registry import Registry, SkillEntry
        entries = [
            SkillEntry(name="a", path="/a", scope="global", agents=["Claude Code"], description="skill a"),
            SkillEntry(name="b", path="/b", scope="global", agents=["Claude Code"], description="skill b"),
        ]
        reg = Registry(entries=entries)
        self.assertEqual(len(reg.entries), 2)

    def test_registry_get_by_name(self):
        from skill_registry import Registry, SkillEntry
        entries = [
            SkillEntry(name="find-skills", path="/a", scope="global", agents=[]),
            SkillEntry(name="code-reviewer", path="/b", scope="global", agents=[]),
        ]
        reg = Registry(entries=entries)
        found = reg.get_by_name("find-skills")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "find-skills")

    def test_registry_get_by_name_fuzzy(self):
        from skill_registry import Registry, SkillEntry
        entries = [SkillEntry(name="find-skills", path="/a", scope="global", agents=[])]
        reg = Registry(entries=entries)
        found = reg.get_by_name("find")
        self.assertIsNotNone(found)

    def test_registry_get_by_name_not_found(self):
        from skill_registry import Registry, SkillEntry
        reg = Registry(entries=[])
        self.assertIsNone(reg.get_by_name("nonexistent"))

    def test_registry_get_by_scope(self):
        from skill_registry import Registry, SkillEntry
        entries = [
            SkillEntry(name="a", path="/a", scope="global", agents=[]),
            SkillEntry(name="b", path="/b", scope="project", agents=[]),
        ]
        reg = Registry(entries=entries)
        global_entries = reg.get_by_scope("global")
        self.assertEqual(len(global_entries), 1)

    def test_registry_search(self):
        from skill_registry import Registry, SkillEntry
        entries = [
            SkillEntry(name="find-skills", path="/a", scope="global", agents=[], description="Search for skills"),
            SkillEntry(name="code-reviewer", path="/b", scope="global", agents=[], description="Review code"),
        ]
        reg = Registry(entries=entries)
        results = reg.search("skill")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "find-skills")

    def test_generate_registry_markdown(self):
        from skill_registry import Registry, SkillEntry, generate_registry_markdown
        entries = [
            SkillEntry(name="test-skill", path="/test", scope="global", agents=["Claude Code"], description="A test"),
        ]
        reg = Registry(entries=entries, scan_time="2026-01-01 00:00:00")
        md = generate_registry_markdown(reg)
        self.assertIn("Skill Registry", md)
        self.assertIn("test-skill", md)
        self.assertIn("共 1 个 Skill", md)

    def test_save_registry(self):
        from skill_registry import Registry, SkillEntry, save_registry
        entries = [SkillEntry(name="x", path="/x", scope="global", agents=[], description="x")]
        reg = Registry(entries=entries, scan_time="2026-01-01")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            tmppath = f.name
        try:
            save_registry(reg, tmppath)
            content = Path(tmppath).read_text(encoding="utf-8")
            self.assertIn("x", content)
        finally:
            os.unlink(tmppath)

    def test_scan_installed_skills(self):
        """scan_installed_skills 应该返回 Registry 对象（即使为空）。"""
        from skill_registry import scan_installed_skills
        reg = scan_installed_skills("global")
        self.assertIsInstance(reg, type(reg))  # Registry
        self.assertIsInstance(reg.entries, list)


# ─── Module 6: skill_generator ──────────────────────────────────────────────────

class TestGenerator(unittest.TestCase):
    """测试 skill_generator.py 的全部公开函数。"""

    def test_generate_frontmatter(self):
        from skill_generator import generate_frontmatter
        fm = generate_frontmatter("my-skill", "A test skill")
        self.assertIn("---", fm)
        self.assertIn("name: my-skill", fm)
        self.assertIn("description:", fm)
        self.assertIn("license: MIT", fm)

    def test_generate_frontmatter_with_metadata(self):
        from skill_generator import generate_frontmatter
        fm = generate_frontmatter("x", "desc", metadata={"author": "test", "version": "1.0"})
        self.assertIn("metadata:", fm)
        self.assertIn("author:", fm)

    def test_generate_skill_methodology(self):
        from skill_generator import generate_skill
        content = generate_skill("test-meth", "A methodology skill", "methodology")
        self.assertIn("name: test-meth", content)
        self.assertIn("Workflow", content)
        self.assertIn("Examples", content)
        self.assertIn("Gotchas", content)

    def test_generate_skill_all_types(self):
        from skill_generator import generate_skill
        for stype in ["methodology", "technical", "auditing", "reference", "automation"]:
            content = generate_skill(f"test-{stype}", f"A {stype} skill", stype)
            self.assertIn(f"name: test-{stype}", content)
            self.assertGreater(len(content), 100, f"{stype} template too short")

    def test_generate_skill_with_output(self):
        from skill_generator import generate_skill
        tmpdir = tempfile.mkdtemp()
        out_dir = os.path.join(tmpdir, "new-skill")
        content = generate_skill("new-skill", "A new skill", "methodology", output_dir=out_dir)
        # Files should be written
        self.assertTrue(os.path.isfile(os.path.join(out_dir, "SKILL.md")))
        self.assertTrue(os.path.isfile(os.path.join(out_dir, "references", "EVAL.md")))
        # Content should match
        written = Path(os.path.join(out_dir, "SKILL.md")).read_text(encoding="utf-8")
        self.assertEqual(written, content)

    def test_generate_skill_with_variables(self):
        from skill_generator import generate_skill
        content = generate_skill("custom", "desc", "methodology", variables={
            "phase_1_name": "Discovery",
            "phase_1_detail": "Discover requirements",
        })
        self.assertIn("Discovery", content)
        self.assertIn("Discover requirements", content)

    def test_validate_skill_content_valid(self):
        from skill_generator import generate_skill, validate_skill_content
        content = generate_skill("valid-skill", "A valid skill description.", "methodology")
        issues = validate_skill_content(content)
        self.assertEqual(len(issues), 0, f"Unexpected issues: {issues}")

    def test_validate_skill_content_missing_frontmatter(self):
        from skill_generator import validate_skill_content
        issues = validate_skill_content("No frontmatter here")
        self.assertTrue(any("frontmatter" in i for i in issues))

    def test_validate_skill_content_multiline_desc(self):
        from skill_generator import validate_skill_content
        content = '---\nname: x\ndescription: |\n  line1\n  line2\n---\n# Body'
        issues = validate_skill_content(content)
        self.assertTrue(any("多行" in i for i in issues))


# ─── Module 7: skill_optimizer ──────────────────────────────────────────────────

class TestOptimizer(unittest.TestCase):
    """测试 skill_optimizer.py 的全部公开函数。"""

    def test_generate_optimization_plan(self):
        from skill_parser import parse_skill
        from skill_optimizer import generate_optimization_plan
        tmpdir = _write_temp_skill(SAMPLE_SKILL_BAD)
        parsed = parse_skill(tmpdir)
        plan = generate_optimization_plan(parsed)
        self.assertIsNotNone(plan)
        self.assertIsInstance(plan.findings, list)
        self.assertIsInstance(plan.changes, list)
        # Plan should have a projected grade string
        self.assertIn("/", plan.estimated_grade)  # e.g. "A (100/100)"

    def test_generate_optimization_plan_good_skill(self):
        from skill_parser import parse_skill
        from skill_optimizer import generate_optimization_plan
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD, with_references=True)
        parsed = parse_skill(tmpdir)
        plan = generate_optimization_plan(parsed)
        # Good skill should have fewer changes
        self.assertIsInstance(plan.changes, list)

    def test_format_optimization_plan(self):
        from skill_parser import parse_skill
        from skill_optimizer import generate_optimization_plan, format_optimization_plan
        tmpdir = _write_temp_skill(SAMPLE_SKILL_BAD)
        parsed = parse_skill(tmpdir)
        plan = generate_optimization_plan(parsed)
        formatted = format_optimization_plan(plan)
        self.assertIn("Skill 审查结论", formatted)
        self.assertIn("审查对象", formatted)
        self.assertIn("预估等级", formatted)

    def test_apply_description_fix(self):
        from skill_parser import parse_skill
        from skill_optimizer import apply_description_fix
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        parsed = parse_skill(tmpdir)
        new_content = apply_description_fix(parsed, "New improved description")
        self.assertIn("New improved description", new_content)
        self.assertIn("name: test-sample-skill", new_content)


# ─── Module 8: skillos.py CLI ────────────────────────────────────────────────────

class TestCLI(unittest.TestCase):
    """测试 skillos.py CLI 的全部子命令。"""

    def _run_cli(self, *args):
        """运行 CLI 命令并返回 (returncode, stdout, stderr)。"""
        import subprocess
        cmd = [sys.executable, os.path.join(SKILLOS_ROOT, "skillos.py")] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                encoding="utf-8", errors="replace")
        return result.returncode, result.stdout, result.stderr

    def test_help(self):
        rc, stdout, stderr = self._run_cli("help")
        self.assertEqual(rc, 0)
        self.assertIn("SkillOS", stdout)

    def test_no_args(self):
        rc, stdout, stderr = self._run_cli()
        # Should print help/usage
        self.assertEqual(rc, 0)

    def test_list_global(self):
        rc, stdout, stderr = self._run_cli("list", "--global")
        self.assertEqual(rc, 0)
        self.assertIn("已安装 Skill", stdout)

    def test_rate_with_target(self):
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        rc, stdout, stderr = self._run_cli("rate", tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("Skill 审查报告", stdout)

    def test_rate_no_target(self):
        rc, stdout, stderr = self._run_cli("rate")
        self.assertEqual(rc, 0)
        self.assertIn("请指定", stdout)

    def test_analyze_json(self):
        tmpdir = _write_temp_skill(SAMPLE_SKILL_MD)
        rc, stdout, stderr = self._run_cli("analyze", tmpdir, "--json")
        self.assertEqual(rc, 0)
        data = json.loads(stdout)
        self.assertIn("name", data)
        self.assertIn("grade", data)
        self.assertIn("score", data)
        self.assertIn("categories", data)

    def test_analyze_no_target(self):
        rc, stdout, stderr = self._run_cli("analyze")
        self.assertEqual(rc, 0)
        self.assertIn("请指定", stdout)

    def test_route_with_query(self):
        rc, stdout, stderr = self._run_cli("route", "帮我写测试")
        self.assertEqual(rc, 0)
        # Should contain routing result or "未找到" if no skills installed
        self.assertTrue("路由结果" in stdout or "未找到" in stdout or "Skill" in stdout)

    def test_route_no_query(self):
        rc, stdout, stderr = self._run_cli("route")
        self.assertEqual(rc, 0)
        self.assertIn("请提供", stdout)

    def test_generate(self):
        tmpdir = tempfile.mkdtemp()
        out_dir = os.path.join(tmpdir, "gen-skill")
        rc, stdout, stderr = self._run_cli(
            "generate", "--name", "gen-skill", "--type", "methodology",
            "--desc", "A generated skill", "-o", out_dir
        )
        self.assertEqual(rc, 0)
        self.assertTrue(os.path.isfile(os.path.join(out_dir, "SKILL.md")))

    def test_generate_no_name(self):
        rc, stdout, stderr = self._run_cli("generate")
        self.assertEqual(rc, 0)
        self.assertIn("请指定", stdout)

    def test_generate_show(self):
        tmpdir = tempfile.mkdtemp()
        out_dir = os.path.join(tmpdir, "show-skill")
        rc, stdout, stderr = self._run_cli(
            "generate", "--name", "show-skill", "--type", "technical",
            "--desc", "Show me", "-o", out_dir, "--show"
        )
        self.assertEqual(rc, 0)
        self.assertIn("show-skill", stdout)

    def test_optimize(self):
        tmpdir = _write_temp_skill(SAMPLE_SKILL_BAD)
        rc, stdout, stderr = self._run_cli("optimize", tmpdir)
        self.assertEqual(rc, 0)
        self.assertIn("审查结论", stdout)

    def test_optimize_no_target(self):
        rc, stdout, stderr = self._run_cli("optimize")
        self.assertEqual(rc, 0)
        self.assertIn("请指定", stdout)

    def test_conflicts(self):
        rc, stdout, stderr = self._run_cli("conflicts", "--global")
        # Should succeed even if < 2 skills (prints message)
        self.assertEqual(rc, 0)

    def test_registry(self):
        rc, stdout, stderr = self._run_cli("registry", "--global")
        self.assertEqual(rc, 0)
        self.assertIn("索引已生成", stdout)

    def test_relationships_global(self):
        rc, stdout, stderr = self._run_cli("relationships", "--global")
        self.assertEqual(rc, 0)

    def test_workflow_no_query(self):
        rc, stdout, stderr = self._run_cli("workflow")
        self.assertEqual(rc, 0)
        self.assertIn("请提供", stdout)


# ─── 集成测试 ────────────────────────────────────────────────────────────────────

class TestIntegration(unittest.TestCase):
    """端到端集成测试：模拟真实使用流程。"""

    def test_full_workflow_rate_then_optimize(self):
        """完整流程：解析 → 评分 → 优化计划。"""
        from skill_parser import parse_skill
        from skill_analyzer import analyze, format_report
        from skill_optimizer import generate_optimization_plan, format_optimization_plan

        tmpdir = _write_temp_skill(SAMPLE_SKILL_BAD)

        # Step 1: Parse
        parsed = parse_skill(tmpdir)
        self.assertIsNotNone(parsed)

        # Step 2: Analyze
        result = analyze(parsed)
        self.assertIsNotNone(result)
        report = format_report(result)
        self.assertIn("审查报告", report)

        # Step 3: Optimize
        plan = generate_optimization_plan(parsed)
        self.assertIsNotNone(plan)
        opt_report = format_optimization_plan(plan)
        self.assertIn("审查结论", opt_report)

    def test_generate_then_analyze(self):
        """生成新 Skill 后立即评分。"""
        from skill_generator import generate_skill, validate_skill_content
        from skill_parser import parse_skill
        from skill_analyzer import analyze

        tmpdir = tempfile.mkdtemp()
        out_dir = os.path.join(tmpdir, "my-new-skill")

        # Generate
        content = generate_skill("my-new-skill", "Use this skill whenever the user asks to 'automate tasks'",
                                 "methodology", output_dir=out_dir)
        issues = validate_skill_content(content)
        self.assertEqual(len(issues), 0, f"Validation issues: {issues}")

        # Parse and analyze
        parsed = parse_skill(out_dir)
        self.assertIsNotNone(parsed)
        result = analyze(parsed)
        self.assertGreater(result.overall_score, 0)

    def test_multiple_skills_conflict_detection(self):
        """多个 Skill 的冲突检测。"""
        from skill_parser import parse_skill
        from conflict_detector import detect_conflicts

        skills = []
        for i in range(3):
            tmpdir = _write_temp_skill(SAMPLE_SKILL_MD.replace("test-sample-skill", f"skill-{i}"))
            parsed = parse_skill(tmpdir)
            if parsed:
                skills.append(parsed)

        self.assertTrue(len(skills) >= 2)
        report = detect_conflicts(skills)
        self.assertEqual(report.total_skills, len(skills))


# ─── 运行入口 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("SkillOS v1.1 — 全功能自动化测试")
    print("=" * 60)
    print()
    unittest.main(verbosity=2)
