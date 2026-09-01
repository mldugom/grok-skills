# Project State

## Current objective

Create a version-controlled library of reusable Grok skills and
operating procedures.

## Phase

Phase 1 — lifecycle layer — complete.

## Lifecycle status

Canonical implementations exist under `skills/lifecycle/`:

1. `/start`
2. `/checkpoint`
3. `/prioritize`
4. `/audit`
5. `/end`

They are installed to `~/.grok/skills/` via `scripts/install.sh`.
`scripts/verify.sh` confirmed the installed copies and
`policies/EFFICIENT_AGENT.md` match this repository.

In-repo metadata validation does not use `~/.grok`:

    bash tests/test_lifecycle_metadata.sh

## Architecture

The repository is the source of truth.

Global Grok installation locations are deployment targets:

- `~/.grok/skills`
- `~/.grok/policies`

## Immediate next work

Do not implement quantitative-research or domain skills yet.

## Next major design phase

Strategically design the quantitative-research skill spine and its
relationship to:

- data science,
- machine learning,
- portfolio construction,
- risk management,
- sports modeling,
- crypto modeling,
- front-office finance,
- analytics consulting,
- production applications.

Do not generate that broader library until the architecture has been
planned deliberately.
