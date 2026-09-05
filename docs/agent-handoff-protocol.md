# Agent Handoff Protocol v1

This document defines a provider-neutral interface between autonomous/assisted coding agents and a human-controlled integration process.

The protocol is designed to work with Grok, Claude, OpenAI, local agents, or future systems without changing the project monitor or human gate model.

## Separation of concerns

### Agent / skill layer
Owns:
- interpreting the bounded assignment,
- implementing within scope,
- running required verification,
- creating/updating the task branch and PR,
- emitting a truthful `BOT REPORT`.

Does not own:
- certification,
- merge/promotion,
- dependent-task release,
- live/economic approval.

### Git / monitor layer
Owns:
- durable work-state metadata,
- event detection,
- dashboard freshness,
- identifying review candidates and stale SHAs.

Does not own:
- scientific judgment,
- production approval,
- strategy/economic decisions.

### Human integration layer
Owns:
- task release,
- contract changes,
- correction vs acceptance,
- certification,
- merge/promotion,
- live smoke/deployment gates,
- economic/strategy decisions.

## Required handoff fields

Every completed implementation handoff should expose:

- agent id/name,
- persistent role,
- task id/title,
- handoff status,
- repository,
- branch,
- requested base/ref,
- exact head SHA,
- PR identifier when applicable,
- scope completed,
- files/areas changed,
- verification commands and results,
- explicit contract-impact flags,
- known deviations/risks,
- blocked/dependent work not started.

The canonical text representation is defined by `skills/lifecycle/handoff/SKILL.md`.

## State machine

```text
ASSIGNED
  -> IMPLEMENTING
  -> READY_FOR_INTEGRATION_REVIEW
  -> REVIEWING
      -> CORRECTION_REQUIRED -> IMPLEMENTING
      -> CERTIFIED
  -> MERGED/PROMOTED (when applicable)
  -> LIVE/VALIDATED (when a runtime/evidence gate exists)
```

`READY_FOR_INTEGRATION_REVIEW` is an agent state. `CERTIFIED`, `MERGED/PROMOTED`, and `LIVE/VALIDATED` are human/integration states.

## Monitor interoperability

A generic monitor should rely on ordinary Git/PR events and this handoff protocol, not provider-specific APIs.

Recommended events:
- branch push,
- pull request opened,
- pull request ready-for-review,
- pull request synchronize,
- issue/PR comment containing `BOT REPORT`,
- review submitted,
- pull request merged/closed.

Provider-specific skills remain replaceable. A monitor should not need to know whether the implementation was produced by Grok, Claude, OpenAI, or another tool.

## Versioning

Protocol version: `agent-handoff/v1`.

Breaking changes require a new protocol version. New optional fields may be added without breaking v1 readers.