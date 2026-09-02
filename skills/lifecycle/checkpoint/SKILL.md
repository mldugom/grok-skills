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

Inspect git status and the relevant diff.

Determine:

- current checkout path,
- git root,
- branch or detached HEAD,
- HEAD SHA,
- whether this is primary or isolated/secondary,
- primary checkout if known safely (`.git/grok-worktree-source` when that path is a git working tree; otherwise the main worktree from `git worktree list`).

Distinguish intended session work from unrelated pre-existing changes.

Operate only on this working copy.

### 3. Verification

Run the smallest sufficient targeted verification for the intended work.

Prefer:
- targeted tests,
- relevant build/type checks,
- focused data validations,
- exact reproduction commands.

Do not launch an expensive full suite solely because a checkpoint was requested.

If verification materially fails, do not commit.

### 4. Update durable state

Update `PROJECT_STATE.md` or the repository's designated equivalent when warranted.

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

Update other documentation only when the work materially changed architecture, interfaces, operating procedures, research conclusions, or reproduction steps.

### 5. Commit

After verification and durable state updates, commit the coherent intended checkpoint work unless:

- the user says not to commit,
- there is nothing to commit,
- verification materially failed,
- the intended change set cannot be separated safely from unrelated dirty state,
- project policy forbids autonomous commits.

If committing:
- include only intended files,
- never absorb unrelated pre-existing dirty files,
- use a descriptive commit message,
- record the resulting commit SHA.

Never push by default. Push belongs to `/end`.

Do not apply, merge, cherry-pick, or delete a worktree during `/checkpoint`.

After a commit, check whether the intended primary branch is known to contain that SHA (inspect the primary checkout when its path is known). If that cannot be determined safely, report unknown.

Never imply that a worktree commit exists in the primary checkout merely because it was committed successfully.

### 6. Continue state

Return:

### CHECKPOINT CREATED
What durable state was updated.

### GIT
- commit SHA, or none,
- current checkout,
- kind: primary | isolated/secondary,
- whether the intended primary branch is known to contain the commit: yes | no | unknown,
- whether the commit has been pushed: yes | no,
- intentionally uncommitted files if any.

### COMPLETED SINCE LAST CHECKPOINT

### CURRENT OPEN ISSUES

### NEXT 3 ACTIONS

### SESSION CONTINUATION
One sentence describing the best immediate continuation task.

Do not end the session.
