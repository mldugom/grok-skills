# AGENTS.md

## Repository purpose

This repository defines reusable Grok skills, policies, lifecycle
commands, and installation tooling.

The repository itself is the source of truth. Installed copies under
`~/.grok` are deployment targets.

## Change discipline

- Do not modify installed copies as the canonical implementation.
- Make skill changes in this repository first.
- Keep skills modular and composable.
- Avoid duplicating methodology across domain skills.
- Explicit review/persona lenses should not silently become default
  reasoning modes.
- Validate skill metadata and installation behavior after changes.
- Never commit authentication data, runtime sessions, credentials,
  secrets, or project-specific proprietary data unless explicitly
  intended.

## Current priority

Lifecycle v1.1 is implemented and verified. Do not design the
quantitative research skill spine until that architecture has been
planned deliberately.
