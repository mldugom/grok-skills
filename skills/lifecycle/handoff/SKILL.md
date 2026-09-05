---
name: handoff
description: Emit a machine- and human-readable implementation handoff through Git/PR state without self-certifying or self-promoting work.
when-to-use:
  - implementation complete
  - ready for review
  - bot report
  - handoff work
user-invocable: true
disable-model-invocation: false
argument-hint: "[optional PR/task context]"
metadata:
  author: mldugom
  short-description: Standard agent-to-integration handoff
---

# /handoff — Agent Implementation Handoff

Use this skill when a bounded implementation or design slice is ready for Integration Owner review.

This protocol is intentionally provider-neutral. A Grok, Claude, OpenAI, local, or future agent can follow the same contract. The skill controls *how the agent reports completion*; it does not control project-specific certification rules.

## Core rule

**Implementation complete != certified != merged != live.**

An agent hands work off. Integration Owners decide whether to correct, certify, merge/promote, deploy, or release dependent work.

## Preconditions

Before declaring a handoff:

1. Confirm the assigned scope and stop condition.
2. Inspect current branch, HEAD SHA, upstream, and working-tree status.
3. Verify the task was based on the requested base/ref when one was specified.
4. Run the required focused verification and any required full suite.
5. Do not hide failures, skipped required checks, dirty unrelated files, or unresolved contract deviations.
6. Push the intended branch normally. Never force-push unless the human explicitly requested it.
7. Open or update a pull request when the project workflow uses PRs.

## BOT REPORT contract

Emit the following structure in the PR body/comment and, when requested, the coordinating chat:

```text
BOT REPORT

Agent: <stable agent id/name>
Role: <persistent role>
Task: <bounded task id + title>
Status: READY_FOR_INTEGRATION_REVIEW | BLOCKED | PARTIAL

Repository: <owner/repo>
Branch: <branch>
Base: <base branch/ref>
Base SHA: <sha if known>
Head SHA: <exact sha>
PR: <number/url or NONE>

Scope completed:
- ...

Files/areas changed:
- ...

Verification:
- <command> -> <result>
- <command> -> <result>

Contract checks:
- production/economic semantics changed? YES/NO
- migrations/schema changed? YES/NO
- network/runtime behavior changed? YES/NO
- research estimand/identifiability changed? YES/NO
- known deviations from task contract? NONE/<details>

Risks / review focus:
- ...

Blocked or dependent work NOT started:
- ...

STOP.
Await Integration Owner decision.
```

## Status semantics

- `READY_FOR_INTEGRATION_REVIEW`: requested implementation/design is complete enough for review; this is not approval.
- `BLOCKED`: cannot complete without a human decision, missing dependency, inaccessible resource, or contract conflict.
- `PARTIAL`: useful work exists, but the assigned stop condition has not been satisfied.

Never use `DONE`, `CERTIFIED`, `MERGED`, `PROMOTED`, or `LIVE` unless the repository's Integration Owners have actually performed/approved that state transition.

## Git event semantics

For projects using an agent monitor, these events are the durable handoff surface:

- branch push = work changed; not necessarily complete,
- PR opened/ready = review candidate,
- PR synchronize = new candidate SHA; prior review may be stale,
- `BOT REPORT` PR comment/body = explicit agent handoff,
- review/certification comment = Integration Owner state,
- merge/promotion = separate human-controlled transition.

## Safety

Never:

- merge your own PR unless explicitly authorized,
- advance protected/certified refs,
- release a dependent task merely because your tests are green,
- modify project economics/strategy outside assigned scope,
- invent test output or Git state,
- write secrets into reports,
- treat a dashboard/status monitor as more authoritative than Git.

## Provider-neutral interface

The stable integration boundary is the report schema above plus ordinary Git metadata. Provider-specific prompt techniques, tool instructions, or reasoning conventions stay inside the agent/skill implementation and are not required by the monitor.

See `docs/agent-handoff-protocol.md` for the repository-independent protocol.