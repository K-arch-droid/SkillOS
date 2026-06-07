# Contributing to SkillOS

Thanks for improving SkillOS. Keep changes focused and testable.

## Development Setup

```bash
git clone https://github.com/K-arch-droid/SkillOS.git
cd SkillOS
python -m tests.test_all
```

SkillOS currently uses only the Python standard library for core behavior.

## Before Opening a PR

Run:

```bash
python -m tests.test_all
python skillos.py doctor
```

If your change affects an adapter, also test installation into a temporary target:

```bash
python skillos.py install --agent codex --target ./tmp/skillos
python skillos.py doctor --agent codex --target ./tmp/skillos
```

## Design Rules

- Keep the Core CLI independent from any single agent.
- Put agent-specific behavior under `adapters/<agent>/`.
- Do not copy the whole repository into an agent skill folder.
- Add regression tests for routing, workflow, conflict detection, and installer behavior.
- Optimization should plan first and only apply changes after explicit confirmation.

