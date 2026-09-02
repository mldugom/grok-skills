---
name: checkpoint
description: Create a durable mid-session project checkpoint, including a commit of intended work, without ending the working session.
when-to-use:
  - checkpoint project
  - save current state
  - record progress
user-invocable: true
disable-model-invocation: true
argument-hint: "[optional checkpoint note]"
metadata:
  author: mldugom
  short-description: Persist and commit current project state
---

# /checkpoint — Durable Mid-Session Checkpoint

Use this during a long session when useful work has accumulated but the session should continue.

## Objective

Transfer important state from ephemeral conversation context into durable repository state.

## Procedure

### 1. Summarize work completed

Identify:
- changes made,
- decisions made,
- evidence obtained,
- tests/verification performed,
- unresolved issues,
- assumptions still in force.

### 2. Review repository state

Inspect:
- git status,
- relevant diff,
- branch and upstream,
- current project-state documentation,
- workspace kind: primary checkout, git-linked worktree, or Grok isolated worktree.

If this is a Grok isolated worktree or git-linked worktree, record the source checkout (`cat .git/grok-worktree-source` when present, otherwise `git worktree list`).

Operate only on this working copy. Do not silently edit or commit from the source checkout or another worktree.

### 3. Update durable state

Update `PROJECT_STATE.md` or the repository's designated equivalent when appropriate.

Keep it concise and current.

It should capture:

- current objective,
- current architecture/state,
- completed work,
- important decisions,
- confirmed findings,
- open issues,
- immediate next tasks,
- reproduction commands when material.

Do not dump chat history or terminal transcripts into project state.

### 4. Documentation consistency

Update other documentation only when the work materially changed:
- architecture,
- interfaces,
- operating procedures,
- research conclusions,
- reproduction steps.

Do not perform cosmetic documentation rewrites.

### 5. Commit

After durable state is updated, commit intended session work unless:

- the user says not to commit,
- there is nothing to commit,
- the resulting state should not be committed,
- project policy forbids autonomous commits,
- unrelated dirty state cannot be safely separated.

If committing:
- inspect the diff first,
- include only intended files,
- never absorb unrelated pre-existing dirty files,
- use a descriptive commit message.

If this working copy is an isolated worktree, commit here. State that the source checkout is unchanged. Do not apply, merge, or delete the worktree.

Do not push. Push belongs to `/end`.

### 6. Continue state

Return:

### CHECKPOINT CREATED
What durable state was updated.

### GIT
- workspace kind and source checkout if different,
- commit hash/message if created,
- intentionally uncommitted files if any.

### COMPLETED SINCE LAST CHECKPOINT

### CURRENT OPEN ISSUES

### NEXT 3 ACTIONS

### SESSION CONTINUATION
One sentence describing the best immediate continuation task.

Do not end the session.
