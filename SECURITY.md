# Security Policy

SkillOS manages local skill files and adapter installation paths. Treat installation targets carefully.

## Reporting

Please report security issues privately through GitHub Security Advisories if available, or open an issue without sensitive details and request a private contact path.

## Scope

Security-sensitive areas include:

- Recursive file copy/delete logic
- Adapter installation targets
- Parsing untrusted `SKILL.md` files
- Shell command examples in generated or optimized skills
- Any future networked registry or marketplace integration

## Current Guarantees

- Core behavior uses the Python standard library.
- Adapter installation copies a small curated bundle instead of the full repository.
- Generated skill names are validated as kebab-case.

