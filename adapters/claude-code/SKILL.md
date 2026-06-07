---
name: skillos
description: Use this skill whenever the user asks to "list skills", "rate skill", "optimize skill", "generate skill", "skill conflicts", "skill relationships", "skill workflow", "查看 skill 列表", "评价 skill", "优化 skill", "生成 skill", "skill 冲突", or "skill 工作流". SkillOS manages skills; do NOT use for ordinary implementation tasks except to recommend the right skill.
license: MIT
argument-hint: <action> [target-or-request]
metadata:
  adapter: claude-code
---

# SkillOS for Claude Code

SkillOS is a meta skill manager. Use the installed CLI:

```bash
python "{{SKILLOS_ROOT}}/skillos.py" <action> [options]
```

## Command Routing

- List skills: `list --global` or `list --project`
- Build registry: `registry --global [-o <path>]`
- Rate/analyze: `rate <path>`, `analyze <path> [--json]`
- Route: `route "<request>"`
- Conflicts: `conflicts --global` or `conflicts --project`
- Relationships: `relationships --global [--json|--format mermaid]`
- Workflow: `workflow "<request>" [--top-n N]`
- Generate: `generate --name <kebab-name> --type <type> --desc "<description>"`
- Optimize: `optimize <path>`

## Rules

- Use SkillOS only for skill lifecycle management and skill recommendations.
- Do not use it to implement ordinary domain tasks.
- For optimization, produce a plan and wait for explicit confirmation before modifying files.
- For details, read the bundled `references/` files only when needed.

## Examples

Desired: for "评价这个 skill", run `rate <path>`.

Anti-pattern: for "写一个 API endpoint", recommend an API/backend skill instead of using SkillOS.

