---
name: skillos
description: Use this skill whenever an agent needs to manage, rate, route, optimize, generate, compare, or compose skills. SkillOS is an agent-skill lifecycle manager, not a domain implementation skill.
license: MIT
metadata:
  adapter: generic
---

# SkillOS Generic Adapter

Point your agent at the SkillOS CLI:

```bash
python "{{SKILLOS_ROOT}}/skillos.py" <action> [options]
```

Supported actions: `list`, `registry`, `rate`, `analyze`, `route`, `conflicts`, `relationships`, `workflow`, `generate`, and `optimize`.

Use SkillOS for skill lifecycle management only. Route business tasks to domain-specific skills.
