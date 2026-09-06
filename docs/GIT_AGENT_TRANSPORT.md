# AI Galore Git Agent Transport v1

## Why this exists

`agent-ops-monitor` is intentionally a display/freshness layer. It was never a command queue. That is why a human still had to copy prompts between ChatGPT and Grok even when the monitor correctly displayed PR/BOT REPORT state.

This transport adds the missing control path **without building a new agent platform**:

```text
ChatGPT / human supervisor
        |
        | GitHub issue: ai-galore-agent-task/v1
        v
GitHub Issues (durable inbox)
        |
        | local poller, subscription-authenticated Grok CLI
        v
Grok Build worker in isolated git worktree
        |
        | branch + PR + BOT REPORT / handoff
        v
GitHub PR (durable outbox)
        |
        | PR comment: ai-galore-agent-instruction/v1
        v
same Grok session resumes for bounded corrections
```

GitHub provides the queue, history, identity, timestamps, comments, branches and PRs. No database, queue service, bespoke web server, xAI API key, or transcript relay is required.

## Responsibilities

### ChatGPT / Integration Owner

- Creates a bounded GitHub task issue.
- Reviews the actual branch/PR/test evidence through GitHub.
- Sends corrections through tagged PR comments.
- Owns certification, merge/promotion, scientific acceptance and live/economic decisions.

### Local Grok worker

- Polls only configured repositories.
- Claims one task at a time by default.
- Creates an isolated git worktree and deterministic task branch.
- Runs Grok Build headlessly using the locally authenticated Grok session.
- Uses a persistent Grok session ID so review feedback resumes the same task context.
- Pushes a branch and creates/updates the PR/BOT REPORT.
- Never merges or self-certifies.

### Agent Ops Monitor

- Continues to show portfolio/work/handoff/human-gate state.
- May consume the local worker runtime JSON later as a display overlay.
- Does not execute agents and does not become an orchestrator.

## Task issue contract

The issue body contains this marker and one JSON envelope:

```markdown
<!-- ai-galore-agent-task/v1 -->
```json
{
  "schema_version": "ai-galore-agent-task/v1",
  "task_id": "KTR0",
  "repository": "mldugom/ldps",
  "base_ref": "main",
  "branch": "grok/ktr0-ldps-reuse",
  "prompt": "Audit LDPS for reusable research infrastructure and run the declared parity spikes.",
  "scope": ["..."],
  "forbidden": ["merge", "start KTR2"],
  "exit_criteria": ["..."],
  "grok": {
    "effort": "medium",
    "max_turns": 8,
    "no_subagents": true,
    "disable_web_search": true,
    "allow": []
  }
}
```
```

The task issue is the immutable assignment record. If the scientific or implementation contract materially changes, create a new task or explicitly supersede the old one; do not silently rewrite history.

## Supervisor feedback contract

After reviewing the PR, ChatGPT or the Integration Owner leaves a normal top-level PR conversation comment beginning with:

```markdown
<!-- ai-galore-agent-instruction/v1 -->

Your correction here.
```

The local runner detects the new instruction and invokes Grok with `--resume <session-id>` in the same worktree. No copy/paste through the user is required.

A correction must remain inside the original bounded contract. If review reveals a new epic, create a new task instead of extending the current session indefinitely.

## Headless permission model

The runner uses Grok Build's headless `dontAsk` mode, not `--always-approve`.

Default allowed operations are deliberately narrow:

- Read
- Grep
- Edit
- `git *`
- `gh *`
- `python *` / `python3 *`
- `pytest *`

Default denies include:

- `rm -rf *`
- force push
- `git reset --hard`
- `gh pr merge`

Anything else is denied rather than prompting forever in a headless process. A task may add narrowly scoped allow rules when required.

This is a control boundary, not a security proof. Worktrees, GitHub branch protection, repository rules and human merge gates remain important.

## Cost discipline

The default is intentionally **one worker**. Run a second only for genuinely independent work.

Each task should normally use:

- one substantial epic per Grok session;
- medium or lower effort unless the task justifies more;
- `max_turns` around 6–10;
- subagents disabled;
- web search disabled unless external research is actually required;
- targeted verification before any broad suite;
- `/handoff` semantics at the end.

The runner uses the local Grok CLI. If Grok is logged in with the normal browser/device login, no xAI API key is required by this transport.

## Local setup

```bash
cd ~/repos/grok-skills
git fetch origin
# after the transport PR is merged:
git pull --ff-only origin main

mkdir -p ~/.ai-galore
cp examples/ai-galore-worker.json ~/.ai-galore/worker.json
$EDITOR ~/.ai-galore/worker.json

python3 scripts/grok-git-worker.py doctor
python3 scripts/grok-git-worker.py once
```

When the one-shot path is proven end to end:

```bash
python3 scripts/grok-git-worker.py watch
```

Do not install a launchd/background service until `once` has successfully completed a real issue -> Grok -> PR -> supervisor-comment -> Grok-resume cycle.

## Local runtime state

The worker stores only local orchestration state under `~/.ai-galore/`:

```text
state.json
logs/<task>.jsonl
runtime/<task>.json
worktrees/<repo>/<task>/
```

These files are not the scientific source of truth. GitHub issue/branch/PR state and project artifacts are authoritative.

## Why Issues instead of another queue

GitHub Issues already provide:

- durable IDs and timestamps;
- searchable history;
- comments;
- authentication/authorization;
- links to PRs;
- visibility to ChatGPT's GitHub connector;
- no new credentials or infrastructure.

The worker is therefore an adapter from an existing task ledger to Grok Build, not a new orchestration platform.

## Why not ACP yet

Grok Build also exposes ACP over stdin/stdout. ACP is useful for richer IDE/controller integration, but the first required capability is simply durable task delivery and resumable feedback. Headless named sessions already provide that with much less code.

Move to ACP only if the GitHub issue/PR transport proves too coarse for an observed workflow need.
