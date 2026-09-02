# Project State

## Current objective

Create a version-controlled library of reusable Grok skills and
operating procedures.

## Phase

Phase 1 — lifecycle layer — complete.
Lifecycle v1.1 — checkpoint commits and worktree-awareness.

## Lifecycle status

Canonical implementations exist under `skills/lifecycle/`:

1. `/start` — reports workspace kind (primary checkout, git-linked worktree, Grok isolated worktree)
2. `/checkpoint` — updates durable state and commits intended work; does not push
3. `/prioritize`
4. `/audit`
5. `/end` — commit/push remain end-of-session; worktree-aware

They are installed to `~/.grok/skills/` via `scripts/install.sh`.
`scripts/verify.sh` confirmed the installed copies and
`policies/EFFICIENT_AGENT.md` match this repository.

In-repo metadata and v1.1 contract validation does not use `~/.grok`:

    bash tests/test_lifecycle_metadata.sh

## Architecture

The repository is the source of truth.

Global Grok installation locations are deployment targets:

- `~/.grok/skills`
- `~/.grok/policies`

A Grok isolated worktree is a separate working copy. Commits there do not
update the source checkout until that checkout pulls or the worktree is
applied.

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
