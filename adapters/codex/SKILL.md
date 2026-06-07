---
name: skillos
description: Use this skill whenever the user asks to "list skills", "rate skill", "optimize skill", "generate skill", "skill conflicts", "skill relationships", "skill workflow", "查看 skill 列表", "评价 skill", "优化 skill", "生成 skill", "skill 冲突", or "skill 工作流". SkillOS manages skills; do NOT use for ordinary implementation tasks except to recommend the right skill.
license: MIT
argument-hint: <action> [target-or-request]
metadata:
  adapter: codex
---

# SkillOS for Codex

## Overview

SkillOS manages skills: discovery, listing, registry generation, rating, analysis, optimization planning, generation, routing, conflict detection, relationships, and workflow recommendations.

Use the installed SkillOS CLI:

```powershell
python "{{SKILLOS_ROOT}}\skillos.py" <action> [options]
```

## Command Routing

| Intent | Command |
|---|---|
| List global skills | `list --global` |
| List project skills | `list --project` |
| Update global index | `registry --global` |
| Save index to a path | `registry --global -o <path>` |
| Rate a skill | `rate <path>` |
| Save rating report | `rate <path> -o <report.md>` |
| Analyze a skill | `analyze <path>` |
| JSON analysis | `analyze <path> --json` |
| Recommend a skill | `route "<request>"` |
| Detect conflicts | `conflicts --global` or `conflicts --project` |
| Show relationships | `relationships --global` |
| JSON relationships | `relationships --global --json` |
| Mermaid relationships | `relationships --global --format mermaid` |
| Recommend workflow | `workflow "<request>" [--top-n N]` |
| Generate a skill | `generate --name <kebab-name> --type <type> --desc "<description>"` |
| Show generated content | `generate --name <name> --type <type> --show` |
| Optimize a skill | `optimize <path>` |

## Operating Rules

- Prefer the CLI over reimplementing SkillOS logic in chat.
- For optimization, output the plan first. Do not modify the target skill unless the user explicitly confirms execution.
- For generation, require a kebab-case skill name.
- For project-level operations, run commands from the target project directory.
- If CLI output conflicts with expectations, report the actual output and likely mismatch.
- Keep business tasks routed to domain skills; SkillOS only manages and recommends skills.

## References

Load only when needed:

- `references/REVIEW-CHECKLIST.md` for the 7-dimension rating system.
- `references/ROUTING-RULES.md` for routing and confidence behavior.
- `references/SKILL-TYPES.md` for skill templates.
- `references/GOTCHAS.md` for failure modes and fixes.
- `references/ADVANCED-PATTERNS.md` for composition patterns.
- `templates/EVAL-TEMPLATE.md` when generating evaluation queries.

## Examples

### Desired

User asks: "查看全局 skill 列表"

Run:

```powershell
python "{{SKILLOS_ROOT}}\skillos.py" list --global
```

### Anti-pattern

User asks: "帮我写 React 页面"

Do not use SkillOS to implement the page. Route or recommend a frontend skill.

