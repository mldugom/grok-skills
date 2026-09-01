---
name: prioritize
description: Holistically reassess project priorities, sequencing, complexity, blockers, and highest-value next work.
when-to-use:
  - reprioritize project
  - reassess roadmap
  - decide what to do next
user-invocable: true
disable-model-invocation: true
argument-hint: "[optional objective or constraint]"
metadata:
  author: mldugom
  short-description: Re-evaluate project priorities
---

# /prioritize — Holistic Project Reassessment

Use this when direction needs to be reconsidered rather than merely continuing the existing task list.

This is a decision exercise, not an implementation exercise.

## Objective

Re-evaluate the project from first principles using current evidence.

Do not assume that:
- the existing roadmap is correct,
- unfinished work deserves completion,
- previously prioritized work remains valuable,
- complexity already introduced should be preserved.

## Assess

### Mission
- What is the actual project objective?
- What outcome creates value?
- What does success look like now?

### Evidence
- What has actually been proven?
- What remains hypothesis?
- What results materially changed our understanding?
- What negative findings should change direction?

### Architecture
- Does current architecture serve the objective?
- What is unnecessary?
- What is missing?
- What is premature?
- What creates operational fragility?

### Current work
Classify existing work into:
- essential,
- useful,
- optional,
- obsolete,
- distracting.

### Dependencies
Identify:
- hard blockers,
- sequencing constraints,
- external dependencies,
- data dependencies,
- infrastructure prerequisites.

### Risk
Assess:
- correctness risk,
- technical risk,
- model/research risk,
- operational risk,
- production risk,
- schedule risk,
- unnecessary complexity.

### Opportunity cost
Ask:
- What are we doing that should stop?
- What work provides little information or value?
- What more valuable problem is being postponed?

## Prioritization framework

Use this conceptual ranking:

    expected impact
    × confidence
    × urgency
    × information value
    --------------------------------
    effort × dependency burden × risk

Do not pretend these quantities are precise if they are not.

## For quantitative / financial projects

When applicable, distinguish:

- research value,
- predictive value,
- economic value,
- portfolio value,
- production value.

A statistically interesting result is not automatically economically useful.

## Output

### OBJECTIVE
Current project objective in one concise statement.

### WHAT MATTERS NOW
The few facts that should drive current prioritization.

### KEEP
Work that remains justified.

### DO NEXT
Highest-value immediate work.

### DEFER
Useful but currently premature work.

### STOP
Work that should no longer consume resources.

### MISSING FROM ROADMAP
Important work not currently represented.

### TOP 5 PRIORITIES

For each provide:
1. priority,
2. rationale,
3. expected value,
4. dependency,
5. principal risk,
6. definition of done.

### RECOMMENDED NEXT SESSION
One bounded next unit of work.

Do not modify code or documentation unless the user separately asks you to implement the resulting priorities.
