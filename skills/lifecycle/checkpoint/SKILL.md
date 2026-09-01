---
name: checkpoint
description: Create a durable mid-session project checkpoint without ending the working session.
when-to-use:
  - checkpoint project
  - save current state
  - record progress
user-invocable: true
disable-model-invocation: true
argument-hint: "[optional checkpoint note]"
metadata:
  author: mldugom
  short-description: Persist current project state
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
- branch,
- current project-state documentation.

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

### 5. Commit behavior

Do NOT automatically commit unless:

- the user explicitly requests a commit, OR
- project standing instructions explicitly establish checkpoint commits as expected behavior.

If committing:
- inspect diff first,
- include only intended files,
- never absorb unrelated pre-existing dirty files,
- use a descriptive commit message.

### 6. Continue state

Return:

### CHECKPOINT CREATED
What durable state was updated.

### COMPLETED SINCE LAST CHECKPOINT

### CURRENT OPEN ISSUES

### NEXT 3 ACTIONS

### SESSION CONTINUATION
One sentence describing the best immediate continuation task.

Do not end the session.
