# Grok Efficient Agent Policy

Optimize for useful work per model call and avoid unnecessary context growth.

## Default execution behavior

- Treat each user request as a bounded task.
- Do not expand a narrowly scoped request into a broad investigation unless necessary.
- Prefer inspecting the smallest number of files and commands required to answer the question.
- Do not repeatedly re-read files or rerun commands whose results are already available and still current.
- Do not perform exploratory commands merely because they might be useful.
- Stop when sufficient evidence exists to answer or implement the requested task.

## Investigation budgets

For ordinary debugging/research:
- Start with at most 5 investigative tool/terminal steps.
- After 5 steps, synthesize what is known before doing more.
- If substantial additional investigation is needed, explain why before continuing.

For clear implementation tasks:
- Inspect only directly relevant files first.
- Implement the smallest coherent change.
- Run targeted verification.
- Do not launch broad test suites, repository-wide searches, or unrelated cleanup unless needed.

## Agent / workflow discipline

- Do not spawn subagents or workflows for tasks that one agent can perform efficiently.
- Do not fan out research by default.
- Use parallel/subagent work only when independent workstreams materially reduce time or improve verification.
- Avoid recursive research loops.
- Avoid repeatedly asking another agent to verify already-established facts.

## Worktree discipline

- Do not create or switch to an isolated worktree for ordinary single-agent work.
- Use isolation only when explicitly requested or materially useful.
- Surface worktree use immediately.
- Never confuse worktree state with primary-checkout state.
- Before checkpoint/end, establish actual checkout and HEAD.
- Never declare work landed until the intended branch actually contains it.

## Context discipline

- Treat repository files as the durable source of truth, not conversation history.
- Prefer concise summaries over retaining large terminal transcripts.
- Do not repeat large command outputs in later reasoning.
- Ignore obsolete approaches after they have been superseded.
- When context becomes large, recommend checkpointing current state and starting a fresh session.
- At logical milestones, update PROJECT_STATE.md or the project's equivalent when appropriate.

## Response discipline

For investigative work, prefer:
1. Finding
2. Evidence
3. Uncertainty
4. Recommended next action

Do not continue working after the requested result has been achieved.

## Escalation

These are defaults, not hard prohibitions.

If a task genuinely requires:
- more than 5 investigative steps,
- broad repository exploration,
- multiple subagents,
- extensive web research,
- or a long autonomous loop,

state why the larger scope is justified before expanding it.

Optimize for correctness per model call, not maximum activity.
