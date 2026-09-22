# Git Agent Transport v2 smoke procedure

This is a bounded smoke/hardening layer on top of `GIT_AGENT_TRANSPORT.md`.
It exists because the first real KTR0 run proved that GitHub task delivery,
worktree creation, repo reads and Grok Build edits worked, but the configured
8-turn budget was reported as a generic exit-code failure before PR handoff.

## Required semantics

`max_turns_reached` is an expected control event:

```text
RUNNING
  -> TURN_BUDGET_EXHAUSTED
  -> supervisor instruction required
  -> RUNNING_CONTINUATION
```

The worker must preserve the existing Grok session ID, worktree, task branch,
log and task issue. It must not auto-resume or silently raise the task budget.

Before a PR exists, tagged supervisor instructions are read from the original
task issue. After a PR exists, the PR conversation is primary and the task
issue remains a fallback.

Default continuation budget is 4 turns unless the task/config explicitly sets
`continuation_max_turns`.

## KTR0 recovery smoke test

The v2 runner reuses the existing `~/.ai-galore/state.json` created by v1 and
migrates a `BLOCKED` state to `TURN_BUDGET_EXHAUSTED` when the existing JSONL
log contains Grok's structured `max_turns_reached` event.

After pulling the transport branch:

```bash
cd ~/repos/grok-skills
git pull --ff-only
python3 scripts/grok-git-worker-v2.py doctor
python3 scripts/grok-git-worker-v2.py status
python3 scripts/grok-git-worker-v2.py once
```

For KTR0, an `ai-galore-agent-instruction/v1` continuation has already been
placed on LDPS issue #3. The expected result is that `once` resumes the same
KTR0 Grok session/worktree with a four-turn continuation rather than creating
a new task.

Success means either:

1. KTR0 reaches a pushed branch + PR + truthful handoff, or
2. it reaches another `TURN_BUDGET_EXHAUSTED` checkpoint cleanly.

A second turn-budget checkpoint is not permission for an automatic third run.
The Integration Owner reviews why more budget is needed.

## No API billing requirement

This path uses the locally authenticated Grok Build CLI. It does not require an
xAI API key or introduce direct xAI API billing as part of the transport.
