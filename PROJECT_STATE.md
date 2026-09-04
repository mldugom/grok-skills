# Project State

## Current objective

Create a version-controlled library of reusable Grok skills and operating procedures that is safe, efficient, and economical for long-running quantitative/software projects.

## Phase

Lifecycle v1.1 + Efficiency v1.2 credit controls.

## Lifecycle status

Canonical implementations exist under `skills/lifecycle/`:

1. `/start` — reports checkout, git root, branch or detached HEAD, HEAD SHA, primary vs isolated/secondary, and a worktree warning when secondary; v1.2 also keeps bootstrap narrow and routes broad reprioritization to `/prioritize`
2. `/checkpoint` — targeted verification, durable state, local commit of intended work, no push; reports SHA, checkout kind, whether the primary branch is known to contain the commit, and whether it was pushed; v1.2 avoids redundant checkpoint-then-end closeouts
3. `/prioritize`
4. `/audit`
5. `/end` — must not declare SESSION COMPLETE until intended commits exist on the intended primary branch; otherwise WORKTREE LANDING REQUIRED. Safe fast-forward only.

## Efficiency v1.2

`policies/EFFICIENT_AGENT.md` now includes:

- one substantial epic/research question per session by default,
- bounded investigative and implementation tool-call budgets,
- context/credit thresholds around 150k / 175k / 200k / 250k,
- Plan-mode read-only discipline before approval,
- verbose-output/logging discipline,
- targeted-test discipline,
- quantitative point-in-time integrity checks,
- explicit escalation before broad autonomous expansion.

Runtime support:

- `shell/grok-safe.zsh` launches Grok with the efficiency policy, `--max-turns 6`, and `--no-subagents`.
- `scripts/configure-runtime.sh` installs the launcher source line into `~/.zshrc` and configures the Grok status line to display cwd, model, context, cost, and turn timer.

## Architecture

The repository is the source of truth.

Global Grok installation locations are deployment targets:

- `~/.grok/skills`
- `~/.grok/policies`

A Grok isolated worktree is a separate working copy. Commits there do not update the source checkout until that checkout pulls or the worktree is applied.

## Installation / validation

Install lifecycle skills and policy:

    bash scripts/install.sh

Configure runtime credit controls:

    bash scripts/configure-runtime.sh
    source ~/.zshrc

Validate installed copies:

    bash scripts/verify.sh

Validate lifecycle + efficiency contracts in-repo:

    bash tests/test_lifecycle_metadata.sh

## Immediate next work

Do not implement quantitative-research or domain skills yet.

Use Efficiency v1.2 in real project sessions and only revise it again if observed behavior exposes a concrete gap.

## Confirmed findings

The prior expensive crypto session reached roughly 293k context and 302 tool calls in five user turns. The dominant problem was broad autonomous scope within individual turns, not lifecycle-skill context size.

## Next major design phase

Strategically design the quantitative-research skill spine and its relationship to:

- data science,
- machine learning,
- portfolio construction,
- risk management,
- sports modeling,
- crypto modeling,
- front-office finance,
- analytics consulting,
- production applications.

Do not generate that broader library until the architecture has been planned deliberately.
