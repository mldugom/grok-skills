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

## Bootstrap sequence

### 1. Establish repository identity

Determine:

- repository root,
- current working directory,
- current branch,
- upstream branch if any,
- clean/dirty git state,
- recent commits,
- whether there are uncommitted or untracked files,
- workspace kind.

Classify this working copy as one of:

- **primary checkout** — the user's ordinary clone,
- **git-linked worktree** — `.git` is a file, or `git rev-parse --git-dir` differs from `--git-common-dir`,
- **Grok isolated worktree** — path under `~/.grok/worktrees/`, or `.git/grok-worktree-source` exists.

When this is not the primary checkout, record the source path (`cat .git/grok-worktree-source` when present, otherwise `git worktree list`).

Operate only on this working copy. Do not silently edit, commit, or push from the source checkout or another worktree.

A commit or push here does not update a different source checkout until that checkout pulls or the user applies the worktree.

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
- roadmap or task timeline,
- architecture overview,
- recent decision log.

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

### 6. Minimal architecture verification

Inspect only the files necessary to validate the execution path relevant to the current objective.

Do NOT:

- perform repository-wide archaeology by default,
- read every source file,
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
- working copy path,
- kind: primary checkout | git-linked worktree | grok isolated worktree,
- source checkout if different,
- branch and upstream,
- clean or dirty.

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
