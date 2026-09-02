# Project State

## Current objective

Create a version-controlled library of reusable Grok skills and
operating procedures.

## Phase

Lifecycle v1.1 — checkpoint commits and worktree-awareness.

## Lifecycle status

Canonical implementations exist under `skills/lifecycle/`:

1. `/start` — reports checkout, git root, branch or detached HEAD, HEAD SHA, primary vs isolated/secondary, and a worktree warning when secondary
2. `/checkpoint` — targeted verification, durable state, local commit of intended work, no push; reports SHA, checkout kind, whether the primary branch is known to contain the commit, and whether it was pushed
3. `/prioritize`
4. `/audit`
5. `/end` — must not declare SESSION COMPLETE until intended commits exist on the intended primary branch; otherwise WORKTREE LANDING REQUIRED. Safe fast-forward only.

`policies/EFFICIENT_AGENT.md` includes Worktree discipline.

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

## Confirmed findings

`bash tests/test_lifecycle_metadata.sh` is CLEAN for v1.1 contracts.

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
