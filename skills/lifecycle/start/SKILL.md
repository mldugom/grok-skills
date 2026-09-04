---
name: start
description: Bootstrap a fresh Grok session from durable repository state with minimal rediscovery.
when-to-use:
  - start work
  - resume project
  - understand current project state
user-invocable: true
disable-model-invocation: true
argument-hint: "[optional session objective]"
metadata:
  author: mldugom
  short-description: Bootstrap project state efficiently
---

# /start — Session Bootstrap

Use this command at the beginning of a new working session.

The objective is to establish the minimum sufficient understanding of the repository without performing a broad rediscovery exercise.

## Principles

- Repository state is authoritative.
- Durable project documentation should be preferred over conversation reconstruction.
- Read narrowly before exploring broadly.
- Do not implement anything during bootstrap unless the user explicitly combines `/start` with an implementation request.
- Do not repeat investigation already resolved by current project documentation.
- Distinguish verified facts from inference.
- `/start` is a bootstrap, not a full audit, roadmap review, or implementation phase.
- Even when the user asks to be "fully aware" of a large project, prefer current durable state and the active work queue over reading all docs/code.
- If the user's real need is broad reprioritization, complete the minimal bootstrap and recommend `/prioritize`; do not turn `/start` itself into repository-wide archaeology.
- Default to one substantial epic or research question for the session. Do not silently combine several major workstreams into one execution window.

## Bootstrap sequence

### 1. Establish repository identity

Determine:

- current checkout path,
- git root,
- branch or detached HEAD,
- HEAD SHA,
- upstream if any,
- clean/dirty git state,
- recent commits,
- uncommitted or untracked files,
- whether this is the primary checkout or a Grok/secondary worktree.

Treat as **isolated/secondary** when any of these hold:

- git root is under `$GROK_HOME/worktrees` or `~/.grok/worktrees`,
- `.git/grok-worktree-source` exists,
- `.git` is a file, or `git rev-parse --git-dir` differs from `--git-common-dir`.

Otherwise treat as **primary**, unless evidence shows this is not the user's ordinary checkout.

Record the primary checkout only when it can be determined safely:

- contents of `.git/grok-worktree-source` if that path is an existing git working tree,
- otherwise the main worktree from `git worktree list` when this is a git-linked worktree.

Do not guess a primary path from a username, host, or hardcoded home directory. If unknown, say unknown.

Operate only on this working copy. Do not silently edit, commit, or push from the primary checkout or another worktree.

Do not modify anything.

### 2. Read standing instructions

Locate and read the applicable instruction hierarchy, including when present:

- `AGENTS.md`
- nested `AGENTS.md`
- project-level `.grok` configuration
- relevant repository instructions
- applicable project documentation.

Do not exhaustively read every documentation file.

### 3. Read durable project state

Prefer, in order when available:

- `PROJECT_STATE.md`
- current handoff/state document,
- active work queue / roadmap summary,
- architecture overview only when needed,
- recent decision log only when needed.

Read only enough material to reconstruct current state.

### 4. Inspect recent repository activity

Review:

- recent commits,
- current diff,
- recently touched relevant files.

Use recent activity to validate whether project-state documentation is current.

If documentation conflicts with code or git history, identify the discrepancy.

### 5. Determine current objective

If the user supplied an objective with `/start`, treat it as the candidate session objective.

Otherwise infer the most likely immediate objective from durable state and recent activity.

Do not invent one when uncertainty is material.

If several substantial objectives were supplied, rank or separate them but recommend one bounded session objective rather than implementing all of them immediately.

### 6. Minimal architecture verification

Inspect only the files necessary to validate the execution path relevant to the current objective.

Do NOT:

- perform repository-wide archaeology by default,
- read every source file,
- read every documentation file,
- run expensive jobs,
- rerun historical experiments,
- launch full test suites,
- spawn subagents merely to understand the repo.

If project documentation is inadequate, state what is missing before substantially expanding investigation.

## Output

Return:

### CURRENT STATE
Concise description of what presently exists.

### WORKSPACE
- current checkout path,
- git root,
- branch or detached HEAD,
- HEAD SHA,
- kind: primary | isolated/secondary,
- primary checkout if known safely, else unknown,
- clean or dirty.

If this is isolated/secondary, also return:

### WORKTREE WARNING
Commits in this checkout may not yet exist in the user's primary checkout. State the primary path when known. Do not treat this checkout's HEAD as primary-branch state.

### CURRENT OBJECTIVE
What the project/session appears to be trying to accomplish.

### RECENT CHANGES
Material recent repository changes relevant to current work.

### OPEN ISSUES
Known blockers, bugs, uncertainty, or unfinished work.

### RISKS / INCONSISTENCIES
Documentation drift, dirty state, conflicting implementations, or anything likely to cause mistakes.

### TOP 3 NEXT ACTIONS
Ranked by value and dependency order.

### RECOMMENDED SESSION TASK
One bounded task that represents the best next unit of work.

### CONTEXT QUALITY
State one of:
- GOOD — durable state is sufficient.
- PARTIAL — some additional inspection is needed.
- POOR — repository state/documentation is inadequate.

Stop after bootstrap unless the user explicitly requested work beyond `/start`.
