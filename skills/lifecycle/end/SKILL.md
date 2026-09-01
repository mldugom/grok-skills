---
name: end
description: Close a working session cleanly by verifying changes, updating durable project state, reviewing git state, and optionally committing/pushing intended work.
when-to-use:
  - end session
  - wrap up work
  - finish work session
user-invocable: true
disable-model-invocation: true
argument-hint: "[optional commit/push instruction]"
metadata:
  author: mldugom
  short-description: Close session with durable handoff
---

# /end — Session Closeout

Use this when the current work session should be closed cleanly.

The objective is to leave the repository in a reproducible state so a future `/start` can resume efficiently.

## Safety

Never:

- silently include unrelated pre-existing dirty files,
- discard uncommitted work,
- rewrite history,
- force push,
- merge branches,
- delete branches,
- push secrets,
- hide failing verification.

Commit and push only intended session work.

If there is ambiguity about whether a file belongs to the current work, leave it out and identify it.

## Procedure

### 1. Reconstruct this session's work

Determine:

- what was requested,
- what was actually changed,
- what decisions were made,
- what remains unfinished.

Do not claim work that was not completed.

### 2. Inspect repository state

Check:

- repository root,
- branch,
- upstream,
- git status,
- relevant diff,
- untracked files.

Identify pre-existing versus session-created changes when reasonably possible.

### 3. Verification

Run the smallest sufficient verification for the work completed.

Prefer:

- targeted tests,
- relevant build/type checks,
- focused data validations,
- exact reproduction commands.

Do not launch an expensive full suite solely because the session is ending unless it is required for confidence.

Report failures honestly.

### 4. Documentation

Update durable documentation when warranted.

Prioritize:

- `PROJECT_STATE.md`,
- relevant README sections,
- architecture docs,
- research/decision logs,
- operating/runbook documentation.

`PROJECT_STATE.md` should reflect current truth, not session chronology.

Capture:

- current objective,
- current implementation state,
- important decisions,
- confirmed findings/results,
- unresolved issues,
- next actions,
- important reproduction commands.

### 5. Final diff review

Before committing:

- inspect the diff,
- remove accidental temporary changes where safe,
- confirm generated artifacts are intentionally included,
- ensure unrelated files are excluded,
- check for obvious credentials/secrets.

### 6. Commit

If the working session produced intended repository changes, create a descriptive commit unless:

- the user says not to commit,
- verification reveals a state that should not be committed,
- project policy forbids autonomous commits,
- unrelated dirty state cannot be safely separated.

Do not use vague commit messages such as "updates".

### 7. Push

Push the current branch only when:

- there is an intended commit to publish,
- a remote/upstream is configured,
- no project instruction forbids it,
- no unresolved safety ambiguity exists.

Never force push.

If push requires permission/confirmation under the environment, request it rather than circumventing protections.

Confirm whether the remote push succeeded.

### 8. Final handoff

Return:

### SESSION COMPLETE

### COMPLETED
Concise list of actual accomplishments.

### VERIFICATION
Tests/checks and outcomes.

### DOCUMENTATION UPDATED

### GIT
- branch,
- commit hash/message if created,
- push status,
- intentionally uncommitted files if any.

### OPEN ISSUES

### NEXT 3 ACTIONS

### NEXT SESSION START
A compact statement suitable for the next `/start`.

Do not begin new implementation after `/end`.
