#!/usr/bin/env python3
"""GitHub-backed transport between a supervisor and local Grok Build workers.

The durable queue is ordinary GitHub Issues.  A task issue contains an
`ai-galore-agent-task/v1` JSON envelope.  This process polls configured repos,
claims one bounded task at a time, creates an isolated git worktree, runs Grok
Build headlessly with a named session, and watches the resulting PR for
`ai-galore-agent-instruction/v1` comments to resume that same session.

Design goals:
- no xAI API key required when the local Grok CLI is already logged in;
- GitHub remains the durable cross-provider message bus;
- no custom server/database/queue;
- safe-by-default headless permissions (`dontAsk` + explicit allow rules);
- one worker / one substantial task by default to control usage;
- agents never merge or self-certify.

Requires local `git`, `gh`, and `grok` commands.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

TASK_MARKER = "<!-- ai-galore-agent-task/v1 -->"
ACK_MARKER = "<!-- ai-galore-agent-ack/v1 -->"
INSTRUCTION_MARKER = "<!-- ai-galore-agent-instruction/v1 -->"
RESULT_MARKER = "<!-- ai-galore-agent-result/v1 -->"
TASK_RE = re.compile(
    re.escape(TASK_MARKER) + r".*?```json\s*(\{.*?\})\s*```",
    re.DOTALL | re.IGNORECASE,
)

DEFAULT_CONFIG = Path("~/.ai-galore/worker.json").expanduser()
DEFAULT_HOME = Path("~/.ai-galore").expanduser()


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def require_command(name: str) -> None:
    if not shutil.which(name):
        raise RuntimeError(f"required command not found on PATH: {name}")


def gh_json(args: list[str]) -> Any:
    cp = run(["gh", *args])
    text = cp.stdout.strip()
    return json.loads(text) if text else None


def gh_api_json(path: str) -> Any:
    return gh_json(["api", path])


def gh_comment(repo: str, number: int, body: str) -> None:
    run(["gh", "issue", "comment", str(number), "--repo", repo, "--body", body])


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def parse_task(body: str) -> dict[str, Any] | None:
    match = TASK_RE.search(body or "")
    if not match:
        return None
    task = json.loads(match.group(1))
    if task.get("schema_version") != "ai-galore-agent-task/v1":
        raise ValueError("unsupported task schema_version")
    return task


def task_key(repo: str, issue_number: int) -> str:
    return f"{repo}#{issue_number}"


def safe_slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return value.strip("-._") or "task"


def repo_cfg(config: dict[str, Any], repo: str) -> dict[str, Any] | None:
    for item in config.get("repositories", []):
        if item.get("repository") == repo and item.get("enabled", True):
            return item
    return None


def list_task_issues(repo: str) -> list[dict[str, Any]]:
    issues = gh_api_json(f"repos/{repo}/issues?state=open&per_page=100") or []
    out: list[dict[str, Any]] = []
    for issue in issues:
        if issue.get("pull_request"):
            continue
        if TASK_MARKER not in (issue.get("body") or ""):
            continue
        try:
            task = parse_task(issue.get("body") or "")
        except Exception as exc:
            print(f"WARN {repo}#{issue.get('number')}: invalid task envelope: {exc}", file=sys.stderr)
            continue
        if task:
            out.append({"issue": issue, "task": task})
    return out


def validate_task(task: dict[str, Any], repo: str) -> None:
    required = ["task_id", "repository", "base_ref", "branch", "prompt"]
    missing = [name for name in required if not task.get(name)]
    if missing:
        raise ValueError(f"missing required task fields: {', '.join(missing)}")
    if task["repository"] != repo:
        raise ValueError(f"task repository {task['repository']!r} does not match queue repo {repo!r}")
    if not str(task["branch"]).startswith("grok/"):
        raise ValueError("task branch must start with 'grok/'")
    if str(task["base_ref"]).startswith("grok/"):
        raise ValueError("base_ref must be an integration ref, not another Grok task branch")


def ensure_worktree(repo_path: Path, base_ref: str, branch: str, worktree: Path) -> None:
    worktree.parent.mkdir(parents=True, exist_ok=True)
    if worktree.exists() and (worktree / ".git").exists():
        return

    run(["git", "fetch", "origin", base_ref], cwd=repo_path)
    local_branch = run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        cwd=repo_path,
        check=False,
    ).returncode == 0
    remote_branch = run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        cwd=repo_path,
        check=False,
    ).returncode == 0

    if local_branch:
        run(["git", "worktree", "add", str(worktree), branch], cwd=repo_path)
    elif remote_branch:
        run(["git", "worktree", "add", "-b", branch, str(worktree), f"origin/{branch}"], cwd=repo_path)
    else:
        run(["git", "worktree", "add", "-b", branch, str(worktree), f"origin/{base_ref}"], cwd=repo_path)


def build_prompt(task: dict[str, Any], issue_number: int) -> str:
    scope = task.get("scope") or []
    forbidden = task.get("forbidden") or []
    exit_criteria = task.get("exit_criteria") or []
    return f"""You are executing one bounded AI Galore task from GitHub issue #{issue_number}.

TASK SPEC (authoritative):
{json.dumps(task, indent=2, sort_keys=True)}

PRIMARY INSTRUCTION:
{task['prompt']}

OPERATING CONTRACT:
- Read and obey repository AGENTS.md / project instructions and installed Grok lifecycle skills.
- Work only on branch `{task['branch']}` based on `{task['base_ref']}` in the provided isolated worktree.
- Keep the task bounded. Do not start dependent work.
- Do not merge, promote protected refs, force-push, or self-certify.
- Preserve point-in-time / replay integrity for quantitative work.
- Prefer targeted verification, then one justified broader check near handoff.
- Push the task branch and open or update a PR to `{task['base_ref']}`.
- The PR must reference issue #{issue_number} and contain a truthful BOT REPORT / handoff with exact tests, risks, and work not started.
- If blocked by missing information, permissions, data, or a scientific ambiguity that cannot be resolved safely, stop and report the blocker rather than improvising.

DECLARED SCOPE:
{json.dumps(scope, indent=2)}

FORBIDDEN / OUT OF SCOPE:
{json.dumps(forbidden, indent=2)}

EXIT CRITERIA:
{json.dumps(exit_criteria, indent=2)}
"""


def permission_args(task: dict[str, Any], defaults: dict[str, Any]) -> list[str]:
    # Headless safety: silently deny anything not explicitly allowed.  This is
    # intentionally narrower than always-approve; tasks may add bounded rules.
    allowed = [
        "Read",
        "Grep",
        "Edit",
        "Bash(git *)",
        "Bash(gh *)",
        "Bash(python *)",
        "Bash(python3 *)",
        "Bash(pytest *)",
    ]
    denied = [
        "Bash(rm -rf *)",
        "Bash(git push --force*)",
        "Bash(git reset --hard*)",
        "Bash(gh pr merge*)",
    ]
    allowed.extend(defaults.get("allow", []))
    allowed.extend((task.get("grok") or {}).get("allow", []))
    denied.extend(defaults.get("deny", []))
    denied.extend((task.get("grok") or {}).get("deny", []))

    args = ["--permission-mode", "dontAsk"]
    for rule in dict.fromkeys(allowed):
        args.extend(["--allow", str(rule)])
    for rule in dict.fromkeys(denied):
        args.extend(["--deny", str(rule)])
    return args


def grok_command(
    task: dict[str, Any],
    defaults: dict[str, Any],
    worktree: Path,
    session_id: str,
    prompt: str,
    *,
    resume: bool,
) -> list[str]:
    task_grok = task.get("grok") or {}
    max_turns = int(task_grok.get("max_turns", defaults.get("max_turns", 8)))
    effort = str(task_grok.get("effort", defaults.get("effort", "medium")))
    model = task_grok.get("model", defaults.get("model"))
    no_subagents = bool(task_grok.get("no_subagents", defaults.get("no_subagents", True)))
    disable_web = bool(task_grok.get("disable_web_search", defaults.get("disable_web_search", True)))

    cmd = [
        "grok",
        "--no-auto-update",
        "--cwd",
        str(worktree),
        "--output-format",
        "streaming-json",
        "--max-turns",
        str(max_turns),
        "--effort",
        effort,
        *permission_args(task, defaults),
    ]
    if model:
        cmd.extend(["--model", str(model)])
    if no_subagents:
        cmd.append("--no-subagents")
    if disable_web:
        cmd.append("--disable-web-search")
    if resume:
        cmd.extend(["--resume", session_id])
    else:
        cmd.extend(["--session-id", session_id])
    cmd.extend(["-p", prompt])
    return cmd


def stream_process(cmd: list[str], log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log:
        log.write(json.dumps({"event": "runner_command_start", "at": utcnow(), "argv": cmd[:-1] + ["<prompt>"]}) + "\n")
        log.flush()
        proc = subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert proc.stdout is not None
        for line in proc.stdout:
            log.write(line)
            log.flush()
        rc = proc.wait()
        log.write(json.dumps({"event": "runner_command_end", "at": utcnow(), "returncode": rc}) + "\n")
        return rc


def find_pr(repo: str, branch: str) -> dict[str, Any] | None:
    prs = gh_json([
        "pr", "list", "--repo", repo, "--head", branch, "--state", "all",
        "--limit", "5", "--json", "number,url,state,title,headRefName,baseRefName",
    ]) or []
    return prs[0] if prs else None


def write_runtime(home: Path, key: str, state: dict[str, Any]) -> None:
    payload = {
        "schema_version": "ai-galore-worker-runtime/v1",
        "generated_at": utcnow(),
        "task_key": key,
        "repository": state.get("repository"),
        "issue_number": state.get("issue_number"),
        "task_id": state.get("task_id"),
        "branch": state.get("branch"),
        "status": state.get("status"),
        "pr_number": state.get("pr_number"),
        "pr_url": state.get("pr_url"),
        "worker_id": state.get("worker_id"),
        "last_error": state.get("last_error"),
    }
    save_json(home / "runtime" / f"{safe_slug(key)}.json", payload)


def issue_comments(repo: str, number: int) -> list[dict[str, Any]]:
    return gh_api_json(f"repos/{repo}/issues/{number}/comments?per_page=100") or []


def newest_instruction(repo: str, pr_number: int, after_id: int) -> dict[str, Any] | None:
    candidates = [
        c for c in issue_comments(repo, pr_number)
        if int(c.get("id") or 0) > after_id and INSTRUCTION_MARKER in (c.get("body") or "")
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda c: int(c.get("id") or 0))[-1]


def instruction_text(comment: dict[str, Any]) -> str:
    body = comment.get("body") or ""
    return body.split(INSTRUCTION_MARKER, 1)[1].strip()


def run_new_task(
    config: dict[str, Any],
    home: Path,
    state_db: dict[str, Any],
    repo: str,
    r_cfg: dict[str, Any],
    issue: dict[str, Any],
    task: dict[str, Any],
) -> None:
    number = int(issue["number"])
    key = task_key(repo, number)
    validate_task(task, repo)

    repo_path = Path(os.path.expanduser(str(r_cfg["path"]))).resolve()
    if not (repo_path / ".git").exists():
        raise RuntimeError(f"configured repository path is not a git checkout: {repo_path}")

    worker_id = str(config.get("worker_id") or os.uname().nodename)
    session_id = str(uuid.uuid4())
    worktree = home / "worktrees" / safe_slug(repo) / safe_slug(str(task["task_id"]))
    log_path = home / "logs" / f"{safe_slug(key)}.jsonl"

    state = {
        "repository": repo,
        "issue_number": number,
        "task_id": task["task_id"],
        "branch": task["branch"],
        "base_ref": task["base_ref"],
        "worker_id": worker_id,
        "session_id": session_id,
        "worktree": str(worktree),
        "log_path": str(log_path),
        "status": "CLAIMED",
        "claimed_at": utcnow(),
        "last_instruction_comment_id": 0,
    }
    state_db[key] = state
    write_runtime(home, key, state)

    gh_comment(
        repo,
        number,
        f"{ACK_MARKER}\nWorker `{worker_id}` claimed `{task['task_id']}` at {state['claimed_at']}. "
        "Execution is local; GitHub issue/PR state is the durable coordination record.",
    )

    ensure_worktree(repo_path, str(task["base_ref"]), str(task["branch"]), worktree)
    state["status"] = "RUNNING"
    state["started_at"] = utcnow()
    write_runtime(home, key, state)

    cmd = grok_command(
        task,
        config.get("grok_defaults", {}),
        worktree,
        session_id,
        build_prompt(task, number),
        resume=False,
    )
    rc = stream_process(cmd, log_path)
    state["last_returncode"] = rc
    state["last_run_finished_at"] = utcnow()

    pr = find_pr(repo, str(task["branch"]))
    if pr:
        state["pr_number"] = int(pr["number"])
        state["pr_url"] = pr.get("url")
        state["status"] = "AWAITING_REVIEW" if rc == 0 else "BLOCKED"
    else:
        state["status"] = "BLOCKED" if rc else "AWAITING_HANDOFF"
        state["last_error"] = None if rc == 0 else f"Grok exited with status {rc}; inspect {log_path}"

    gh_comment(
        repo,
        number,
        f"{RESULT_MARKER}\nTask `{task['task_id']}` local run finished with exit code `{rc}`. "
        + (f"PR: {state['pr_url']}" if state.get("pr_url") else "No PR is visible yet; inspect the runner log / branch."),
    )
    write_runtime(home, key, state)


def resume_from_instruction(
    config: dict[str, Any], home: Path, key: str, state: dict[str, Any], task: dict[str, Any], comment: dict[str, Any]
) -> None:
    repo = state["repository"]
    number = int(state["issue_number"])
    text = instruction_text(comment)
    if not text:
        state["last_instruction_comment_id"] = int(comment.get("id") or 0)
        return

    prompt = f"""A supervisor reviewed your current PR and sent this durable GitHub instruction.

{text}

Continue the SAME bounded task and SAME branch. Address only this instruction and any directly required verification. Do not broaden scope, merge, force-push, or start dependent work. Update the PR and BOT REPORT/handoff truthfully when done. If the instruction conflicts with the frozen task contract, stop and explain the conflict in the PR instead of silently changing the contract.
"""
    state["status"] = "RUNNING_CORRECTION"
    write_runtime(home, key, state)
    cmd = grok_command(
        task,
        config.get("grok_defaults", {}),
        Path(state["worktree"]),
        state["session_id"],
        prompt,
        resume=True,
    )
    rc = stream_process(cmd, Path(state["log_path"]))
    state["last_instruction_comment_id"] = int(comment.get("id") or 0)
    state["last_returncode"] = rc
    state["last_run_finished_at"] = utcnow()
    pr = find_pr(repo, state["branch"])
    if pr:
        state["pr_number"] = int(pr["number"])
        state["pr_url"] = pr.get("url")
    state["status"] = "AWAITING_REVIEW" if rc == 0 else "BLOCKED"
    if rc:
        state["last_error"] = f"Grok correction exited with status {rc}; inspect {state['log_path']}"
    gh_comment(
        repo,
        number,
        f"{RESULT_MARKER}\nSupervisor instruction `{comment.get('id')}` processed with exit code `{rc}`. "
        + (f"PR: {state.get('pr_url')}" if state.get("pr_url") else "No PR visible."),
    )
    write_runtime(home, key, state)


def discover_task(config: dict[str, Any], state_db: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any], dict[str, Any]] | None:
    for r_cfg in config.get("repositories", []):
        if not r_cfg.get("enabled", True):
            continue
        repo = str(r_cfg["repository"])
        for row in sorted(list_task_issues(repo), key=lambda x: int(x["issue"]["number"])):
            key = task_key(repo, int(row["issue"]["number"]))
            if key not in state_db:
                return repo, r_cfg, row["issue"], row["task"]
    return None


def refresh_feedback(config: dict[str, Any], home: Path, state_db: dict[str, Any]) -> bool:
    for key, state in state_db.items():
        pr_number = state.get("pr_number")
        if not pr_number or state.get("status") not in {"AWAITING_REVIEW", "BLOCKED", "AWAITING_HANDOFF"}:
            continue
        repo = state["repository"]
        task_issue = next(
            (row for row in list_task_issues(repo) if int(row["issue"]["number"]) == int(state["issue_number"])),
            None,
        )
        if not task_issue:
            continue
        comment = newest_instruction(repo, int(pr_number), int(state.get("last_instruction_comment_id") or 0))
        if comment:
            resume_from_instruction(config, home, key, state, task_issue["task"], comment)
            return True
    return False


def print_status(state_db: dict[str, Any]) -> None:
    if not state_db:
        print("No Grok Git worker tasks recorded.")
        return
    print(f"{'TASK':36} {'STATE':22} {'PR':8} BRANCH")
    for key, state in sorted(state_db.items()):
        pr = f"#{state['pr_number']}" if state.get("pr_number") else "-"
        print(f"{key[:36]:36} {str(state.get('status','?'))[:22]:22} {pr:8} {state.get('branch','-')}")


def doctor(config: dict[str, Any]) -> int:
    errors: list[str] = []
    for name in ("git", "gh", "grok"):
        try:
            require_command(name)
        except Exception as exc:
            errors.append(str(exc))
    for r_cfg in config.get("repositories", []):
        if not r_cfg.get("enabled", True):
            continue
        path = Path(os.path.expanduser(str(r_cfg.get("path", "")))).resolve()
        if not (path / ".git").exists():
            errors.append(f"{r_cfg.get('repository')}: missing git checkout at {path}")
    if not errors:
        cp = run(["gh", "auth", "status"], check=False)
        if cp.returncode:
            errors.append("gh is not authenticated")
        cp = run(["grok", "version"], check=False)
        if cp.returncode:
            errors.append("grok CLI did not respond to `grok version`")
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print("OK: git, gh, Grok CLI, GitHub auth, and configured repo paths are available.")
    return 0


def load_config(path: Path) -> dict[str, Any]:
    cfg = load_json(path, None)
    if not cfg:
        raise RuntimeError(f"worker config not found: {path}")
    if cfg.get("schema_version") != "ai-galore-worker/v1":
        raise RuntimeError("worker config schema_version must be ai-galore-worker/v1")
    if not cfg.get("repositories"):
        raise RuntimeError("worker config must contain at least one repository")
    return cfg


def cycle(config: dict[str, Any], home: Path, state_path: Path) -> bool:
    state_db = load_json(state_path, {})
    if refresh_feedback(config, home, state_db):
        save_json(state_path, state_db)
        return True
    found = discover_task(config, state_db)
    if found:
        repo, r_cfg, issue, task = found
        key = task_key(repo, int(issue["number"]))
        try:
            run_new_task(config, home, state_db, repo, r_cfg, issue, task)
        except Exception as exc:
            state = state_db.setdefault(key, {
                "repository": repo,
                "issue_number": int(issue["number"]),
                "task_id": task.get("task_id"),
                "branch": task.get("branch"),
                "worker_id": config.get("worker_id"),
            })
            state["status"] = "BLOCKED"
            state["last_error"] = str(exc)
            state["last_run_finished_at"] = utcnow()
            write_runtime(home, key, state)
            try:
                gh_comment(repo, int(issue["number"]), f"{RESULT_MARKER}\nRunner blocked before clean handoff: `{exc}`")
            except Exception:
                pass
            raise
        finally:
            save_json(state_path, state_db)
        return True
    save_json(state_path, state_db)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["doctor", "once", "watch", "status"])
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--home", type=Path, default=DEFAULT_HOME)
    args = parser.parse_args()

    config = load_config(args.config.expanduser())
    home = args.home.expanduser()
    state_path = home / "state.json"

    if args.command == "doctor":
        return doctor(config)
    if args.command == "status":
        print_status(load_json(state_path, {}))
        return 0
    if doctor(config):
        return 1
    if args.command == "once":
        did_work = cycle(config, home, state_path)
        if not did_work:
            print("No queued tasks or new supervisor instructions.")
        return 0

    poll_seconds = max(10, int(config.get("poll_seconds", 30)))
    print(f"Watching GitHub task queues every {poll_seconds}s. Ctrl-C to stop.")
    try:
        while True:
            try:
                cycle(config, home, state_path)
            except Exception as exc:
                print(f"worker cycle failed: {exc}", file=sys.stderr)
            time.sleep(poll_seconds)
    except KeyboardInterrupt:
        print("Stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
