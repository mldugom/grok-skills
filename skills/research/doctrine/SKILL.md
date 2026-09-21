---
name: doctrine
description: The methodology for AI-assisted quantitative research — how a discovery becomes a tracked candidate, how a candidate becomes evidence, and where automation is safe versus where it still needs a human. Apply this whenever proposing a factor, baseline, or model for a prediction system; deciding whether existing code counts as evidence; deciding whether an AI step should propose-and-a-human-accepts versus run automatically; or scoping new automation for a research/discovery loop. This generalizes past any one project. For align's concrete implementation of it, read references/align.md.
when-to-use:
  - propose a candidate factor, baseline, or model
  - decide if existing code counts as evidence
  - scope an AI-assisted research step
  - decide whether to automate a research/discovery loop
user-invocable: true
disable-model-invocation: false
argument-hint: "[optional project or step]"
metadata:
  author: mldugom
  short-description: Quantitative research methodology spine
---

# doctrine — Quantitative Research Methodology

## Why this exists

A research pipeline that lets an AI propose freely and a human approve loosely will
eventually mint a false positive that looks real. This isn't about distrust of AI —
it's about making sure a claim survives contact with real data before it gets spent
as evidence. Four ideas do almost all of the work.

## 1. Discovery is cheap, evidence is not

An AI proposing "here's a plausible factor / baseline / population window" from raw
structure is fast and low-risk — nothing has been committed yet. Let AI do as much
of this as it usefully can. The expensive, risk-bearing step is turning a proposal
into something the system will actually trust and act on. Keep that boundary sharp:
propose freely, commit deliberately.

## 2. A proposal becomes evidence only through the tracked pipeline

Code that was **not** produced by a tracked run — no logged proposal, no commitment
record, no pre-registration — does not count as evidence, even if it's real code,
even if it runs, even if it sits in the project's own repository. This is the single
most important rule here, and the easiest one to violate by accident: a
plausible-looking model or heuristic that was hand-built outside the tracked loop is
not validated just because it exists. Data can be reused freely; a fitted model or a
computed probability can only be trusted once it was produced through the tracked
path.

Concretely: before treating any existing model or heuristic as usable evidence, ask
"was this produced by a run the system itself logged?" If not, it's a hypothesis to
re-derive through the real pipeline, not a shortcut past it.

## 3. A commitment is sealed and never silently edited

Once a proposal is accepted and committed to, that commitment becomes effectively
immutable — a hash of its own identity and the data bounds it was based on, refused
from being overwritten in place. A disappointing result afterward never edits the
sealed commitment; it opens a new one, at a new identity. This is what turns "we
tried X and it didn't work" into a permanent, auditable fact instead of something
that quietly gets overwritten and lost.

Two different identities matter here, and they should never be confused:

- **The seal** — identifies one specific attempt: the proposal plus the exact data
  bounds and timestamp it was tested against. Retrying the same idea on fresh data
  must produce a *different* seal.
- **The stream / line-of-inquiry id** — identifies the underlying idea itself,
  independent of which data window it was tested on. Retrying the same idea on
  fresh data must produce the *same* stream id, so the system recognizes it as a
  retry, not a new idea.

A design with only one of these can't tell "we already tried this" from "this is
genuinely new."

## 4. Automate the search, not the risk — and never ahead of the guardrail

Once there's a real memory of every attempt (not just the wins), it's tempting to
let AI keep proposing and re-attempting automatically until something passes. That's
a legitimate goal — a faster discovery loop is real value. But it must not be built
before there is an actual, *enforced* limit on how many attempts a line of inquiry
gets before the statistical bar tightens (a multiple-testing correction, a throttle,
something that actually gates). A real, tested throttle function that nothing calls
is not a guardrail — it's a promise. Automating proposal generation on top of an
unenforced promise amplifies exactly the risk the guardrail was meant to prevent.
Build and wire the gate first. Automate the loop second.

## Where AI should propose and a human should accept

Three places this shows up in a well-built research pipeline, in order:

1. **What to try** — factor/baseline/population proposals from raw data structure.
2. **How to translate it** — mapping a tenant's real, messy schema toward the
   system's standard shape. Keep this mechanical: an honest AI step here declines to
   guess at an ambiguous mapping rather than inventing a plausible-looking one — an
   unmapped field flagged for a human is more valuable than a wrong guess a human
   doesn't catch.
3. **What model to fit** — given an adopted baseline and its real data, proposing a
   candidate model spec (which features, what functional form) for a human to
   review before it's fit through the tracked pipeline. This is the step most
   pipelines skip, leaving "fit a model" as unowned, ad hoc work outside the
   system's own view — which is exactly how a refuted, untracked model ends up
   mistaken for real evidence (see #2).

## When to reach for automation instead of a human step

Only once: the guardrail from #4 is real and wired, **and** the memory from #3 is
being read by something, not just written to. Before both are true, keep the loop
human-paced even if it's slower — a slow, trustworthy discovery loop beats a fast
one nobody can audit.
