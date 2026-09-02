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

Never declare work landed until the intended primary branch actually contains it.

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

- current checkout path,
- git root,
- branch or detached HEAD,
- HEAD SHA,
- upstream,
- git status,
- relevant diff,
- untracked files,
- whether this is primary or isolated/secondary,
- primary checkout if known safely (`.git/grok-worktree-source` when that path is a git working tree; otherwise the main worktree from `git worktree list`).

Operate only on this working copy until a worktree landing step, if any.

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

### 7. Worktree landing

Before SESSION COMPLETE, determine whether intended session commits actually exist on the intended primary branch.

If this is already the primary checkout and the intended branch contains those commits, continue.

If this is an isolated/secondary worktree and those commits have not landed on the intended primary branch:

- do not silently cherry-pick,
- do not force,
- do not push an unintended detached/worktree state,
- do not declare SESSION COMPLETE.

A simple provably safe fast-forward may be performed only when all of:

- the intended primary checkout path is known,
- the intended primary branch is unambiguous,
- the primary checkout has no conflicting dirty state,
- session HEAD is a descendant of primary HEAD (fast-forward only; no rewrite, no merge commit).

If those hold, fetch the session SHA into the primary repository if needed, then in the primary checkout run `git merge --ff-only <sha>`. Recheck that the primary branch contains the SHA.

Otherwise stop for user confirmation and return:

### WORKTREE LANDING REQUIRED
- session checkout,
- session HEAD,
- intended primary checkout/branch if known,
- primary HEAD if known,
- whether the commit is known to exist on the intended primary branch,
- the safest next action.

Do not continue to SESSION COMPLETE from that state.

### 8. Push

Push only after intended session commits exist on the intended primary branch.

Push the intended branch only when:

- there is an intended commit to publish,
- a remote/upstream is configured,
- no project instruction forbids it,
- no unresolved safety ambiguity exists,
- HEAD is not an unintended detached/worktree state.

Never force push.

If push requires permission/confirmation under the environment, request it rather than circumventing protections.

Confirm whether the remote push succeeded.

### 9. Final handoff

Return only when intended session commits exist on the intended primary branch:

### SESSION COMPLETE

### COMPLETED
Concise list of actual accomplishments.

### VERIFICATION
Tests/checks and outcomes.

### DOCUMENTATION UPDATED

### GIT
- current checkout and kind: primary | isolated/secondary,
- branch or detached HEAD,
- commit SHA/message if created,
- whether the intended primary branch is known to contain the commit,
- push status,
- intentionally uncommitted files if any.

### OPEN ISSUES

### NEXT 3 ACTIONS

### NEXT SESSION START
A compact statement suitable for the next `/start`.

Do not begin new implementation after `/end`.
