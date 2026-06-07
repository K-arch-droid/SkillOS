#!/usr/bin/env python
"""SkillOS v1.1 — Meta Skill Operating System

管理、分析、评分、优化、生成和编排 Claude Code Skill 的超级 Meta Skill。

用法：
    python skillos.py <action> [options]

Actions:
    list        列出已安装 Skill
    registry    生成 Skill 索引
    rate        评分审查一个 Skill
    analyze     深度分析一个 Skill
    route       路由用户请求到合适 Skill
    conflicts       检测 Skill 冲突
    relationships   检测 Skill 关系图谱
    workflow        推荐工作流（Skill 执行链）
    generate        生成新 Skill
    optimize        优化一个 Skill
    install         安装 Agent adapter
    doctor          诊断 SkillOS 与 Agent adapter
    package         打包 Agent adapter
    help            显示帮助信息

示例：
    python skillos.py list --global
    python skillos.py rate ~/.claude/skills/find-skills
    python skillos.py analyze ./my-skill
    python skillos.py route "帮我写测试"
    python skillos.py conflicts --global
    python skillos.py relationships --global
    python skillos.py relationships --format mermaid
    python skillos.py workflow "帮我开发网站"
    python skillos.py generate --name my-skill --type methodology --desc "A skill for X"
    python skillos.py optimize ~/.claude/skills/my-skill
    python skillos.py install --agent codex
    python skillos.py doctor --agent codex
    python skillos.py package --agent codex -o dist/skillos-codex.zip
"""

import argparse
import shutil
import io
import json
import os
import sys
import zipfile
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 确保当前目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent))

from skill_parser import parse_skill, find_skill_md
from skill_analyzer import analyze, format_report
from skill_router import route_request, format_route_result, route_workflow, format_workflow_recommendation
from conflict_detector import (
    detect_conflicts, format_conflict_report,
    detect_relationships, format_relationship_report,
    relationships_to_mermaid, relationships_to_json,
)
from skill_registry import scan_installed_skills, generate_registry_markdown, save_registry
from skill_generator import generate_skill, validate_skill_content, validate_skill_name
from skill_optimizer import generate_optimization_plan, format_optimization_plan


PROJECT_ROOT = Path(__file__).parent.resolve()
COMMON_REFERENCE_FILES = [
    "REVIEW-CHECKLIST.md",
    "ROUTING-RULES.md",
    "SKILL-TYPES.md",
    "GOTCHAS.md",
    "ADVANCED-PATTERNS.md",
]
COMMON_TEMPLATE_FILES = ["EVAL-TEMPLATE.md"]
ADAPTER_TARGETS = {
    "codex": Path.home() / ".codex" / "skills" / "skillos",
    "claude-code": Path.home() / ".claude" / "skills" / "skillos",
    "generic": None,
}


def cmd_list(args):
    """列出已安装 Skill。"""
    scope = "global" if args.global_ else "project"
    registry = scan_installed_skills(scope)
    print(f"\n已安装 Skill ({scope} scope): 共 {len(registry.entries)} 个\n")
    print(f"{'#':<4} {'名称':<35} {'作用域':<10} {'描述'}")
    print("-" * 100)
    for i, entry in enumerate(registry.entries, 1):
        desc = entry.description[:50] + "…" if len(entry.description) > 50 else entry.description
        print(f"{i:<4} {entry.name:<35} {entry.scope:<10} {desc}")
    print()


def cmd_registry(args):
    """生成 Skill 索引。"""
    scope = "global" if args.global_ else "project"
    registry = scan_installed_skills(scope)
    output = args.output or str(Path(__file__).parent / "references" / "SKILL-REGISTRY.md")
    save_registry(registry, output)
    print(f"✅ 索引已生成 → {output}")
    print(f"📊 共 {len(registry.entries)} 个 Skill")


def cmd_rate(args):
    """评分审查一个 Skill。"""
    target = args.target
    if not target:
        print("❌ 请指定目标 Skill 路径")
        print("用法: python skillos.py rate <path/to/skill>")
        return

    parsed = parse_skill(target)
    if not parsed:
        print(f"❌ 找不到 SKILL.md: {target}")
        return

    result = analyze(parsed)
    report = format_report(result)
    print(report)

    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"\n报告已保存到: {args.output}")


def cmd_analyze(args):
    """深度分析一个 Skill。"""
    target = args.target
    if not target:
        print("❌ 请指定目标 Skill 路径")
        return

    parsed = parse_skill(target)
    if not parsed:
        print(f"❌ 找不到 SKILL.md: {target}")
        return

    result = analyze(parsed)
    report = format_report(result)

    if args.json_output:
        data = {
            "name": result.skill_name,
            "type": result.skill_type,
            "grade": result.grade,
            "score": result.overall_score,
            "categories": [
                {"name": c.name, "score": c.score, "weight": c.weight, "weighted": c.weighted}
                for c in result.categories
            ],
            "strengths": result.strengths,
            "findings": [
                {"priority": f.priority, "category": f.category, "title": f.title,
                 "reason": f.reason, "fix": f.fix}
                for f in result.findings
            ],
            "projected_grade": result.projected_grade,
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(report)


def cmd_route(args):
    """路由用户请求到合适 Skill。"""
    query = " ".join(args.query) if args.query else ""
    if not query:
        print("❌ 请提供用户请求")
        print("用法: python skillos.py route \"帮我写测试\"")
        return

    # Scan installed skills: None=both, True=global, False=project
    if args.global_ is None:
        scope = "both"
    elif args.global_:
        scope = "global"
    else:
        scope = "project"
    if scope == "both":
        registry = scan_installed_skills("global")
        project_registry = scan_installed_skills("project")
        all_skills = registry.entries + project_registry.entries
    else:
        registry = scan_installed_skills(scope)
        all_skills = registry.entries

    # Get parsed skills
    parsed_skills = [e.parsed for e in all_skills if e.parsed]

    if not parsed_skills:
        print("未找到已安装的 Skill。请先运行: python skillos.py registry")
        return

    result = route_request(query, parsed_skills)
    print(format_route_result(result))


def cmd_conflicts(args):
    """检测 Skill 冲突。"""
    scope = "global" if args.global_ else "project"
    registry = scan_installed_skills(scope)
    parsed_skills = [e.parsed for e in registry.entries if e.parsed]

    if len(parsed_skills) < 2:
        print("需要至少 2 个 Skill 才能检测冲突")
        return

    report = detect_conflicts(parsed_skills)
    print(format_conflict_report(report))


def cmd_workflow(args):
    """推荐工作流（Skill 执行链）。"""
    query = " ".join(args.query) if args.query else ""
    if not query:
        print("❌ 请提供用户请求")
        print('用法: python skillos.py workflow "帮我开发网站"')
        return

    if args.global_ is None:
        scope = "both"
    elif args.global_:
        scope = "global"
    else:
        scope = "project"
    if scope == "both":
        registry = scan_installed_skills("global")
        project_registry = scan_installed_skills("project")
        all_skills = registry.entries + project_registry.entries
    else:
        registry = scan_installed_skills(scope)
        all_skills = registry.entries

    parsed_skills = [e.parsed for e in all_skills if e.parsed]

    if not parsed_skills:
        print("未找到已安装的 Skill。请先运行: python skillos.py registry")
        return

    top_n = args.top_n or 5
    rec = route_workflow(query, parsed_skills, top_n=top_n)
    print(format_workflow_recommendation(rec))


def cmd_relationships(args):
    """检测 Skill 关系图谱。"""
    scope = "global" if args.global_ else "project"
    registry = scan_installed_skills(scope)
    parsed_skills = [e.parsed for e in registry.entries if e.parsed]

    if len(parsed_skills) < 2:
        print("需要至少 2 个 Skill 才能检测关系")
        return

    report = detect_relationships(parsed_skills)

    if args.json_output:
        print(relationships_to_json(report))
    elif args.format == "mermaid":
        print(relationships_to_mermaid(report))
    else:
        print(format_relationship_report(report))


def cmd_generate(args):
    """生成新 Skill。"""
    name = args.name
    if not name:
        print("❌ 请指定 Skill 名称")
        print("用法: python skillos.py generate --name my-skill --type methodology --desc \"...\"")
        return

    # Validate skill name
    is_valid, msg = validate_skill_name(name)
    if not is_valid:
        print(f"❌ {msg}")
        return

    desc = args.desc or f"A skill for {name}"
    skill_type = args.type or "methodology"
    output_dir = args.output or str(Path.cwd() / name)

    content = generate_skill(
        name=name,
        description=desc,
        skill_type=skill_type,
        output_dir=output_dir,
    )

    if not content:
        print(f"❌ 生成失败：Skill 名称 '{name}' 不合法")
        return

    issues = validate_skill_content(content)
    if issues:
        print("⚠️  验证发现以下问题：")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"✅ Skill 已生成 → {output_dir}/SKILL.md")
        print(f"✅ 评估集已生成 → {output_dir}/references/EVAL.md")

    if args.show:
        print("\n" + "=" * 60)
        print(content)


def cmd_optimize(args):
    """优化一个 Skill。"""
    target = args.target
    if not target:
        print("❌ 请指定目标 Skill 路径")
        return

    parsed = parse_skill(target)
    if not parsed:
        print(f"❌ 找不到 SKILL.md: {target}")
        return

    plan = generate_optimization_plan(parsed)
    print(format_optimization_plan(plan))

    if args.apply:
        print("\n⚠️  自动应用功能开发中。请手动按照优化计划修改。")


def _adapter_dir(agent: str) -> Path:
    return PROJECT_ROOT / "adapters" / agent


def _default_target(agent: str) -> Path:
    target = ADAPTER_TARGETS.get(agent)
    if target is None:
        raise ValueError("generic adapter requires --target")
    return target


def _render_adapter_text(text: str) -> str:
    return text.replace("{{SKILLOS_ROOT}}", str(PROJECT_ROOT))


def _copy_rendered_tree(source: Path, target: Path):
    for item in source.rglob("*"):
        rel = item.relative_to(source)
        dest = target / rel
        if item.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if item.suffix.lower() in {".md", ".yaml", ".yml", ".json", ".txt"}:
            dest.write_text(_render_adapter_text(item.read_text(encoding="utf-8")), encoding="utf-8")
        else:
            shutil.copy2(item, dest)


def _copy_common_bundle(target: Path):
    refs_target = target / "references"
    refs_target.mkdir(parents=True, exist_ok=True)
    for name in COMMON_REFERENCE_FILES:
        shutil.copy2(PROJECT_ROOT / "references" / name, refs_target / name)

    templates_target = target / "templates"
    templates_target.mkdir(parents=True, exist_ok=True)
    for name in COMMON_TEMPLATE_FILES:
        shutil.copy2(PROJECT_ROOT / "templates" / name, templates_target / name)


def install_adapter(agent: str, target: str = None, dry_run: bool = False) -> Path:
    """Install an Agent adapter skill without copying the full project."""
    if agent not in ADAPTER_TARGETS:
        raise ValueError(f"unsupported agent: {agent}")

    source = _adapter_dir(agent)
    if not source.is_dir():
        raise FileNotFoundError(f"adapter not found: {source}")

    target_path = Path(target).expanduser() if target else _default_target(agent)
    target_path = target_path.resolve()

    if dry_run:
        return target_path

    target_path.mkdir(parents=True, exist_ok=True)
    _copy_rendered_tree(source, target_path)
    _copy_common_bundle(target_path)
    return target_path


def cmd_install(args):
    """安装 Agent adapter。"""
    try:
        target = install_adapter(args.agent, args.target, dry_run=args.dry_run)
    except Exception as exc:
        print(f"❌ 安装失败：{exc}")
        return

    print(f"Agent: {args.agent}")
    print(f"Target: {target}")
    if args.dry_run:
        print("Dry run: 未写入文件")
        return

    print(f"✅ SkillOS adapter 已安装 → {target}")
    print(f"验证: python {PROJECT_ROOT / 'skillos.py'} doctor --agent {args.agent} --target \"{target}\"")


def cmd_doctor(args):
    """诊断 SkillOS 与 Agent adapter 安装。"""
    checks = []

    checks.append(("Python", sys.version.split()[0], sys.version_info >= (3, 10)))
    checks.append(("SkillOS root", str(PROJECT_ROOT), PROJECT_ROOT.is_dir()))
    checks.append(("CLI entry", str(PROJECT_ROOT / "skillos.py"), (PROJECT_ROOT / "skillos.py").is_file()))
    checks.append(("References", str(PROJECT_ROOT / "references"), all((PROJECT_ROOT / "references" / n).is_file() for n in COMMON_REFERENCE_FILES)))
    checks.append(("Templates", str(PROJECT_ROOT / "templates"), all((PROJECT_ROOT / "templates" / n).is_file() for n in COMMON_TEMPLATE_FILES)))

    if args.agent:
        try:
            target = Path(args.target).expanduser().resolve() if args.target else _default_target(args.agent)
            checks.append((f"{args.agent} adapter source", str(_adapter_dir(args.agent)), _adapter_dir(args.agent).is_dir()))
            checks.append((f"{args.agent} install target", str(target), target.is_dir()))
            checks.append(("Installed SKILL.md", str(target / "SKILL.md"), (target / "SKILL.md").is_file()))
        except Exception as exc:
            checks.append((f"{args.agent} adapter", str(exc), False))

    ok = True
    for label, detail, passed in checks:
        ok = ok and passed
        mark = "✅" if passed else "❌"
        print(f"{mark} {label}: {detail}")

    if ok:
        print("✅ Doctor passed")
    else:
        print("❌ Doctor found issues")


def cmd_package(args):
    """打包 Agent adapter zip。"""
    if args.agent not in ADAPTER_TARGETS:
        print(f"❌ 不支持的 agent: {args.agent}")
        return
    source = _adapter_dir(args.agent)
    if not source.is_dir():
        print(f"❌ 找不到 adapter: {source}")
        return

    out = Path(args.output or (PROJECT_ROOT / "dist" / f"skillos-{args.agent}.zip")).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in source.rglob("*"):
            if item.is_file():
                arc = Path("skillos") / item.relative_to(source)
                content = item.read_text(encoding="utf-8") if item.suffix.lower() in {".md", ".yaml", ".yml", ".json", ".txt"} else None
                if content is not None:
                    zf.writestr(str(arc).replace("\\", "/"), content)
                else:
                    zf.write(item, str(arc).replace("\\", "/"))
        for name in COMMON_REFERENCE_FILES:
            zf.write(PROJECT_ROOT / "references" / name, f"skillos/references/{name}")
        for name in COMMON_TEMPLATE_FILES:
            zf.write(PROJECT_ROOT / "templates" / name, f"skillos/templates/{name}")

    print(f"✅ Adapter package 已生成 → {out}")


def cmd_help(args):
    """显示帮助信息。"""
    print(__doc__)


def main():
    parser = argparse.ArgumentParser(
        description="SkillOS v1.1 — Meta Skill Operating System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="action", help="操作类型")

    # list
    p_list = subparsers.add_parser("list", help="列出已安装 Skill")
    p_list.add_argument("-g", "--global", dest="global_", action="store_true", default=True)
    p_list.add_argument("-p", "--project", dest="global_", action="store_false")
    p_list.set_defaults(func=cmd_list)

    # registry
    p_reg = subparsers.add_parser("registry", help="生成 Skill 索引")
    p_reg.add_argument("-g", "--global", dest="global_", action="store_true", default=True)
    p_reg.add_argument("-p", "--project", dest="global_", action="store_false")
    p_reg.add_argument("-o", "--output", help="输出文件路径")
    p_reg.set_defaults(func=cmd_registry)

    # rate
    p_rate = subparsers.add_parser("rate", help="评分审查一个 Skill")
    p_rate.add_argument("target", nargs="?", help="Skill 路径")
    p_rate.add_argument("-o", "--output", help="报告输出路径")
    p_rate.set_defaults(func=cmd_rate)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="深度分析一个 Skill")
    p_analyze.add_argument("target", nargs="?", help="Skill 路径")
    p_analyze.add_argument("--json", dest="json_output", action="store_true", help="JSON 输出")
    p_analyze.set_defaults(func=cmd_analyze)

    # route
    p_route = subparsers.add_parser("route", help="路由用户请求到合适 Skill")
    p_route.add_argument("query", nargs="*", help="用户请求")
    p_route.add_argument("-g", "--global", dest="global_", action="store_true", default=None)
    p_route.add_argument("-p", "--project", dest="global_", action="store_false")
    p_route.set_defaults(func=cmd_route)

    # conflicts
    p_conf = subparsers.add_parser("conflicts", help="检测 Skill 冲突")
    p_conf.add_argument("-g", "--global", dest="global_", action="store_true", default=True)
    p_conf.add_argument("-p", "--project", dest="global_", action="store_false")
    p_conf.set_defaults(func=cmd_conflicts)

    # relationships
    p_rel = subparsers.add_parser("relationships", help="检测 Skill 关系图谱")
    p_rel.add_argument("-g", "--global", dest="global_", action="store_true", default=True)
    p_rel.add_argument("-p", "--project", dest="global_", action="store_false")
    p_rel.add_argument("--json", dest="json_output", action="store_true", help="JSON 输出")
    p_rel.add_argument("--format", choices=["markdown", "mermaid"], default="markdown", help="输出格式")
    p_rel.set_defaults(func=cmd_relationships)

    # workflow
    p_wf = subparsers.add_parser("workflow", help="推荐工作流（Skill 执行链）")
    p_wf.add_argument("query", nargs="*", help="用户请求")
    p_wf.add_argument("-g", "--global", dest="global_", action="store_true", default=None)
    p_wf.add_argument("-p", "--project", dest="global_", action="store_false")
    p_wf.add_argument("--top-n", type=int, default=5, help="最多推荐 Skill 数")
    p_wf.set_defaults(func=cmd_workflow)

    # generate
    p_gen = subparsers.add_parser("generate", help="生成新 Skill")
    p_gen.add_argument("--name", help="Skill 名称 (kebab-case)")
    p_gen.add_argument("--desc", help="一句话描述")
    p_gen.add_argument("--type", choices=["methodology", "technical", "auditing", "reference", "automation"],
                       default="methodology", help="Skill 类型")
    p_gen.add_argument("-o", "--output", help="输出目录")
    p_gen.add_argument("--show", action="store_true", help="显示生成内容")
    p_gen.set_defaults(func=cmd_generate)

    # optimize
    p_opt = subparsers.add_parser("optimize", help="优化一个 Skill")
    p_opt.add_argument("target", nargs="?", help="Skill 路径")
    p_opt.add_argument("--apply", action="store_true", help="自动应用修复（开发中）")
    p_opt.set_defaults(func=cmd_optimize)

    # install
    p_install = subparsers.add_parser("install", help="安装 SkillOS 到指定 Agent")
    p_install.add_argument("--agent", choices=sorted(ADAPTER_TARGETS.keys()), required=True, help="目标 Agent")
    p_install.add_argument("--target", help="安装目录；generic 必填，其他 Agent 可覆盖默认路径")
    p_install.add_argument("--dry-run", action="store_true", help="只显示计划，不写入文件")
    p_install.set_defaults(func=cmd_install)

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="诊断 SkillOS 和 Agent adapter 安装")
    p_doctor.add_argument("--agent", choices=sorted(ADAPTER_TARGETS.keys()), help="目标 Agent")
    p_doctor.add_argument("--target", help="安装目录")
    p_doctor.set_defaults(func=cmd_doctor)

    # package
    p_package = subparsers.add_parser("package", help="打包 Agent adapter")
    p_package.add_argument("--agent", choices=sorted(ADAPTER_TARGETS.keys()), required=True, help="目标 Agent")
    p_package.add_argument("-o", "--output", help="输出 zip 路径")
    p_package.set_defaults(func=cmd_package)

    # help
    p_help = subparsers.add_parser("help", help="显示帮助信息")
    p_help.set_defaults(func=cmd_help)

    args = parser.parse_args()
    if not args.action:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()
