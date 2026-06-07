# SkillOS

**SkillOS is a Meta Skill Operating System for AI agents.** It helps agents manage other skills: list, route, rate, analyze, optimize, generate, compare, detect conflicts, map relationships, and recommend skill workflows.

[![CI](https://github.com/K-arch-droid/SkillOS/actions/workflows/ci.yml/badge.svg)](https://github.com/K-arch-droid/SkillOS/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Adapters](https://img.shields.io/badge/adapters-Codex%20%7C%20Claude%20Code%20%7C%20Generic-purple)
![Tests](https://img.shields.io/badge/tests-110%20passing-brightgreen)

SkillOS is intentionally not a replacement for domain skills. It does not write your React app, design your database, or deploy production infrastructure. It helps your agent choose, evaluate, create, and compose the right skills for those jobs.

## Why SkillOS Exists

As agents gain more skills, the hard problem becomes skill operations:

- Which skill should handle this request?
- Are two skills fighting over the same trigger words?
- Is a skill well written enough to auto-trigger reliably?
- What order should several skills run in?
- How do I install the same skill manager into Codex, Claude Code, or another agent without hand-copying random files?

SkillOS provides a deterministic CLI plus lightweight Agent adapters so every user can deploy the same capability without guessing what to copy.

## Two Installation Modes

SkillOS has two distinct surfaces:

1. **Core CLI**: the full Python project in this repository.
2. **Agent adapter**: a small `SKILL.md` package installed into an agent's skill directory. The adapter teaches the agent how to call the Core CLI.

Do not copy the whole repository into an agent skill folder. Use `install` so SkillOS installs only the files that each agent needs.

## Quick Start

```bash
git clone https://github.com/K-arch-droid/SkillOS.git
cd SkillOS
python skillos.py doctor
```

Install SkillOS into an agent:

```bash
# Codex
python skillos.py install --agent codex

# Claude Code
python skillos.py install --agent claude-code

# Generic agent / custom target
python skillos.py install --agent generic --target /path/to/agent/skills/skillos
```

Verify the adapter:

```bash
python skillos.py doctor --agent codex
```

Preview without writing files:

```bash
python skillos.py install --agent codex --dry-run
```

## Supported Agents

| Agent | Status | Install command | Default target |
|---|---|---|---|
| Codex | Supported | `python skillos.py install --agent codex` | `~/.codex/skills/skillos` |
| Claude Code | Supported | `python skillos.py install --agent claude-code` | `~/.claude/skills/skillos` |
| Generic agent | Supported | `python skillos.py install --agent generic --target <path>` | User supplied |

Each adapter is generated from `adapters/<agent>/` and bundled with the shared `references/` and `templates/` files it needs.

## Core Commands

| Capability | Command |
|---|---|
| List installed skills | `python skillos.py list --global` |
| List project skills | `python skillos.py list --project` |
| Generate registry | `python skillos.py registry --global` |
| Rate a skill | `python skillos.py rate ./my-skill` |
| Deep analysis | `python skillos.py analyze ./my-skill --json` |
| Route a request | `python skillos.py route "帮我写单元测试"` |
| Detect conflicts | `python skillos.py conflicts --global` |
| Relationship graph | `python skillos.py relationships --global --format mermaid` |
| Recommend workflow | `python skillos.py workflow "代码审查和性能优化"` |
| Generate a skill | `python skillos.py generate --name api-helper --type technical --desc "API helper"` |
| Optimize a skill | `python skillos.py optimize ./my-skill` |
| Install adapter | `python skillos.py install --agent codex` |
| Diagnose install | `python skillos.py doctor --agent codex` |
| Package adapter | `python skillos.py package --agent codex -o dist/skillos-codex.zip` |

## What Gets Installed Into an Agent

An Agent adapter contains:

```text
skillos/
├── SKILL.md
├── agents/openai.yaml          # Codex only
├── references/
│   ├── REVIEW-CHECKLIST.md
│   ├── ROUTING-RULES.md
│   ├── SKILL-TYPES.md
│   ├── GOTCHAS.md
│   └── ADVANCED-PATTERNS.md
└── templates/
    └── EVAL-TEMPLATE.md
```

The adapter does **not** copy the full source tree, test suite, `.git`, runtime state, generated registries, or development artifacts. It points back to the Core CLI path resolved during installation.

## Rating System

SkillOS rates skills with seven weighted dimensions:

| Dimension | Weight | Checks |
|---|---:|---|
| Description quality | 25 | Directive trigger language, quoted trigger phrases, negative scope |
| Frontmatter validity | 20 | Required fields, legal fields, kebab-case name |
| Length and disclosure | 15 | Body size, `references/` split |
| Structural fit | 15 | Required sections for methodology/technical/auditing/reference/automation |
| Example quality | 10 | Positive and negative examples |
| Conciseness | 10 | No filler or generic prose |
| Anti-pattern avoidance | 5 | No known skill design anti-patterns |

Grades: `A (90-100)`, `B (80-89)`, `C (70-79)`, `D (60-69)`, `F (<60)`.

## Project Structure

```text
SkillOS/
├── skillos.py                  # CLI entry point
├── skill_parser.py             # SKILL.md parser
├── skill_analyzer.py           # 7-dimension rating engine
├── skill_router.py             # Request-to-skill router
├── skill_registry.py           # Installed skill scanner and registry
├── skill_generator.py          # Skill generator and templates
├── skill_optimizer.py          # Review-to-plan optimizer
├── conflict_detector.py        # Conflict and relationship intelligence
├── adapters/                   # Agent-specific install surfaces
│   ├── codex/
│   ├── claude-code/
│   └── generic/
├── references/                 # Shared rating/routing/design references
├── templates/                  # Skill and eval templates
├── tests/                      # Unit and CLI tests
└── SKILL.md                    # Project-level skill instructions
```

## Development

Run the full test suite:

```bash
python -m tests.test_all
```

Package an adapter:

```bash
python skillos.py package --agent codex -o dist/skillos-codex.zip
```

Check a local adapter install in a temporary directory:

```bash
python skillos.py install --agent codex --target ./tmp/skillos
python skillos.py doctor --agent codex --target ./tmp/skillos
```

## Design Principles

- **Adapter, not migration**: each agent receives a lightweight adapter, not the whole repository.
- **CLI is canonical**: deterministic operations happen in Python, not in prompt text.
- **Progressive disclosure**: `SKILL.md` stays small; references load only when needed.
- **Composition over fusion**: SkillOS composes skills instead of merging them into mega-skills.
- **Safe optimization**: `optimize` plans first and only modifies after explicit confirmation.

## License

MIT
