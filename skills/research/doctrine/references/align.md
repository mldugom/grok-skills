# doctrine in align — concrete grounding

Real, verified detail against `mldugom/align` (formerly cloned/known as `keel` —
same repository, GitHub's canonical name is `align`) as of 2026-09-21. Read
`../SKILL.md` first; this file is where the doctrine's principles map onto real
functions and modules, not a restatement of them.

## The tracked pipeline (doctrine #2, #3)

- `align.conductor.desk.ConductorDesk.adopt(row_id, value_mechanism)` →
  `align.compass.config.write_project()` writes `[project]` plus a `[seal]` table
  into `prediction.toml`, in one atomic write.
- `align.run()` → `grade()` → `judge()` — `judge()` is the only real Verdict mint
  in the codebase. `grade()` calls `align.fees` and `align.bankroll` in the same
  step to size stakes once a candidate passes.
- Confirmed via `judge.py`'s own docstring: the tenant supplies `p_model`; align
  never fits one. This is doctrine #2's rule in code — align enforces the boundary,
  it doesn't cross it.

## The evidentiary-provenance gate, in practice

`crypto-innout`'s only existing model, `factorlab_v1_logistic`, is real, runnable
code — and refuted (ties the constant base rate on holdout accuracy, negative rank
correlation, wrong target). It was never produced through a tracked `adopt()`/
ledger/pre-registration run. It is the canonical example of what doctrine #2 means
by "don't treat untracked code as evidence, however real it looks."

## Seal vs. stream (doctrine #3)

- **Seal** — `align.compass.config.make_seal(project, bounds, sealed_at)`:
  `sha256` of the four `[project]` strings, the real census bounds on the desk, and
  a UTC timestamp. `write_project()` refuses (before opening the file) to overwrite
  an already-sealed `prediction.toml`.
- **Stream** — `align.workstream.stream_id_for(x_identity, y_identity)`:
  `"ws_" + sha256({"kind": "workstream", "x": ..., "y": ...})`. Deliberately
  excludes census bounds and timestamp — retrying the same X/Y on a fresh data
  window produces the *same* stream id, on purpose. Never collides with a seal id;
  distinct hash inputs, distinct prefix.

## Guardrail-before-automation (doctrine #4)

`align.discover.attempt_throttle` and `align.ledger.CandidateLedger.append` are
both real and tested. As of this writing, neither has a production call site —
confirmed by grepping the real source, not assumed from an earlier note. This is
exactly why no automated candidate-proposal loop should be built in align yet: the
guardrail exists as a library function, not as an enforced gate on anything. Wire a
real call site first (`adopt()` and/or `grade()` calling `ledger.append` on every
real attempt, win or refusal) before any step that generates proposals
automatically.

## Propose-then-accept, as align actually implements it

- `prior` and `posterior` propose X/Y/population-window/baseline from a raw census
  via a hosted model call (DeepSeek). Live-verified against two real tenants.
- Posterior's adapter-skeleton step (mechanical column → `ScoreRow`-field mapping)
  is deliberately conservative: live-verified at 0/10 auto-mapped on both real
  tenants, correctly declining to guess rather than inventing a plausible mapping.
  That's doctrine #`How AI should propose` point 2 working as intended — a TODO a
  human reviews beats a wrong guess a human doesn't catch.
- **A `propose-model` step (doctrine's point 3) does not exist yet.** This is
  align's current highest-leverage gap: nothing proposes a candidate model spec
  from an adopted baseline's real data. Both real tenants are stuck at the same
  wall for the same reason — `grade()`/`judge()` refuse with
  `BlockedComputeError: no_computed_baseline` because nothing has ever produced a
  tracked `p_model`.

## DataFrame-accessor discipline

Any notebook working against align should have zero local helper functions and
zero raw JSON/dict prints. Every tabular view is a real accessor on the align type
it describes — `align.tabular.as_frame()` is the shared primitive; methods like
`ConductorDesk.composition_frame()`, `compass.config.seal_frame()`,
`score.refusal_frame()` are the concrete examples. Live-verified: a
`conductor_desk_tenniskal.ipynb` walkthrough with exactly zero `def` statements and
zero `print()` calls across all of its code cells, confirmed by reading the actual
notebook source, not the report describing it.

## Bankroll composition (a smaller, concrete "compose, don't replace" example)

`align.bankroll.MAX_POSITION_FRACTION` clips a stake after the Kelly multiplier —
it composes with, and never replaces, `max_period_exposure` (a separate period-level
cap) and `grade()`'s independent 100%-of-bankroll total-ruin refusal. Three
non-overlapping guards, not one guard doing three jobs. The same "compose, don't
collapse two distinct concepts into one" instinct as the seal/stream distinction
above.
