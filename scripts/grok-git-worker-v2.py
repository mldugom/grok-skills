#!/usr/bin/env python3
"""Resumable GitHub-backed Grok Build worker.

This v2 smoke-test runner extends the original transport with two controls:

1. `max_turns_reached` is a bounded checkpoint, not a generic failure.
2. Supervisor instructions can arrive on the original task issue before a PR
   exists; after a PR exists, PR comments become the primary instruction lane.

It reuses the same ~/.ai-galore state.json written by grok-git-worker.py, so a
partially completed task can resume the same Grok session/worktree instead of
starting over.
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
CHECKPOINT_MARKER = "<!-- ai-galore-agent-checkpoint/v1 -->"
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


def safe_slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
    return value.strip("-._") or "task"


def task_key(repo: str, issue_number: int) -> str:
    return f"{repo}#{issue_number}"


def parse_task(body: str) -> dict[str, Any] | None:
    match = TASK_RE.search(body or "")
    if not match:
        return None
    task = json.loads(match.group(1))
    if task.get("schema_version") != "ai-galore-agent-task/v1":
        raise ValueError("unsupported task schema_version")
    return task


def list_task_issues(repo: str) -> list[dict[str, Any]]:
    issues = gh_api_json(f"repos/{repo}/issues?state=open&per_page=100") or []
    out: list[dict[str, Any]] = []
    for issue in issues:
        if issue.get("pull_request"):
            continue
        body = issue.get("body") or ""
        if TASK_MARKER not in body:
            continue
        try:
            task = parse_task(body)
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
        raise ValueError(f"task repository {task['repository']!r} != queue repo {repo!r}")
    if not str(task["branch"]).startswith("grok/"):
        raise ValueError("task branch must start with 'grok/'")
    if str(task["base_ref"]).startswith("grok/"):
        raise ValueError("base_ref must not be another Grok task branch")


def ensure_worktree(repo_path: Path, base_ref: str, branch: str, worktree: Path) -> None:
    worktree.parent.mkdir(parents=True, exist_ok=True)
    if worktree.exists() and (worktree / ".git").exists():
        return
    run(["git", "fetch", "origin", base_ref], cwd=repo_path)
    local = run(["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=repo_path, check=False).returncode == 0
    remote = run(["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"], cwd=repo_path, check=False).returncode == 0
    if local:
        run(["git", "worktree", "add", str(worktree), branch], cwd=repo_path)
    elif remote:
        run(["git", "worktree", "add", "-b", branch, str(worktree), f"origin/{branch}"], cwd=repo_path)
    else:
        run(["git", "worktree", "add", "-b", branch, str(worktree), f"origin/{base_ref}"], cwd=repo_path)


def permission_args(task: dict[str, Any], defaults: dict[str, Any]) -> list[str]:
    allowed = [
        "Read", "Grep", "Edit",
        "Bash(git *)", "Bash(gh *)", "Bash(python *)", "Bash(python3 *)", "Bash(pytest *)",
    ]
    denied = [
        "Bash(rm -rf *)", "Bash(git push --force*)", "Bash(git reset --hard*)", "Bash(gh pr merge*)",
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
    max_turns_override: int | None = None,
) -> list[str]:
    task_grok = task.get("grok") or {}
    max_turns = int(max_turns_override if max_turns_override is not None else task_grok.get("max_turns", defaults.get("max_turns", 8)))
    effort = str(task_grok.get("effort", defaults.get("effort", "medium")))
    model = task_grok.get("model", defaults.get("model"))
    no_subagents = bool(task_grok.get("no_subagents", defaults.get("no_subagents", True)))
    disable_web = bool(task_grok.get("disable_web_search", defaults.get("disable_web_search", True)))
    cmd = [
        "grok", "--no-auto-update", "--cwd", str(worktree),
        "--output-format", "streaming-json", "--max-turns", str(max_turns),
        "--effort", effort, *permission_args(task, defaults),
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


def stream_process(cmd: list[str], log_path: Path) -> dict[str, Any]:
    """Run Grok and classify structured stop conditions from streaming JSON."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    outcome = {"returncode": None, "max_turns_reached": False}
    with log_path.open("a", encoding="utf-8") as log:
        log.write(json.dumps({"event": "runner_command_start", "at": utcnow(), "argv": cmd[:-1] + ["<prompt>"]}) + "\n")
        log.flush()
        proc = subprocess.Popen(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert proc.stdout is not None
        for line in proc.stdout:
            log.write(line)
            log.flush()
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") == "max_turns_reached":
                outcome["max_turns_reached"] = True
        outcome["returncode"] = proc.wait()
        log.write(json.dumps({"event": "runner_command_end", "at": utcnow(), **outcome}) + "\n")
    return outcome


def log_contains_max_turns(log_path: Path) -> bool:
    """Migrate an old runner's BLOCKED state when its log proves budget exhaustion."""
    if not log_path.exists():
        return False
    try:
        with log_path.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"type":"max_turns_reached"' in line or '"type": "max_turns_reached"' in line:
                    return True
    except OSError:
        return False
    return False


def find_pr(repo: str, branch: str) -> dict[str, Any] | None:
    prs = gh_json([
        "pr", "list", "--repo", repo, "--head", branch, "--state", "all",
        "--limit", "5", "--json", "number,url,state,title,headRefName,baseRefName",
    ]) or []
    return prs[0] if prs else None


def issue_comments(repo: str, number: int) -> list[dict[str, Any]]:
    return gh_api_json(f"repos/{repo}/issues/{number}/comments?per_page=100") or []


def newest_instruction(repo: str, number: int, after_id: int) -> dict[str, Any] | None:
    candidates = [
        c for c in issue_comments(repo, number)
        if int(c.get("id") or 0) > after_id and INSTRUCTION_MARKER in (c.get("body") or "")
    ]
    if not candidates:
        return None
    return sorted(candidates, key=lambda c: int(c.get("id") or 0))[-1]


def instruction_text(comment: dict[str, Any]) -> str:
    return (comment.get("body") or "").split(INSTRUCTION_MARKER, 1)[1].strip()


def build_prompt(task: dict[str, Any], issue_number: int) -> str:
    return f"""You are executing one bounded AI Galore task from GitHub issue #{issue_number}.

TASK SPEC (authoritative):
{json.dumps(task, indent=2, sort_keys=True)}

PRIMARY INSTRUCTION:
{task['prompt']}

OPERATING CONTRACT:
- Read and obey repository AGENTS.md/project instructions and installed Grok lifecycle skills.
- Work only on branch `{task['branch']}` based on `{task['base_ref']}` in the isolated worktree.
- Keep scope bounded. Do not start dependent work.
- Do not merge, force-push, promote protected refs, or self-certify.
- Preserve point-in-time/replay integrity for quantitative work.
- Prefer targeted verification, then one justified broader check near handoff.
- Push the task branch and open/update a PR to `{task['base_ref']}`.
- PR must reference issue #{issue_number} and contain a truthful BOT REPORT / handoff.
- If genuinely blocked, stop and report the blocker rather than improvising.
"""


def write_runtime(home: Path, key: str, state: dict[str, Any]) -> None:
    payload = {
        "schema_version": "ai-galore-worker-runtime/v2",
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
        "continuations": state.get("continuations", 0),
        "last_error": state.get("last_error"),
    }
    save_json(home / "runtime" / f"{safe_slug(key)}.json", payload)


def apply_outcome(repo: str, number: int, state: dict[str, Any], outcome: dict[str, Any]) -> None:
    rc = int(outcome.get("returncode") or 0)
    state["last_returncode"] = rc
    state["last_run_finished_at"] = utcnow()
    pr = find_pr(repo, state["branch"])
    if pr:
        state["pr_number"] = int(pr["number"])
        state["pr_url"] = pr.get("url")
    if outcome.get("max_turns_reached"):
        state["status"] = "TURN_BUDGET_EXHAUSTED"
        state["last_error"] = None
        gh_comment(
            repo, number,
            f"{CHECKPOINT_MARKER}\nTask `{state['task_id']}` reached its configured turn budget. "
            "Session/worktree/branch are preserved. Awaiting an explicit supervisor instruction; no automatic resume.",
        )
    elif rc == 0:
        state["status"] = "AWAITING_REVIEW" if state.get("pr_number") else "AWAITING_HANDOFF"
        state["last_error"] = None
        gh_comment(
            repo, number,
            f"{RESULT_MARKER}\nTask `{state['task_id']}` run completed cleanly. "
            + (f"PR: {state['pr_url']}" if state.get("pr_url") else "No PR is visible yet."),
        )
    else:
        state["status"] = "BLOCKED"
        state["last_error"] = f"Grok exited with status {rc}; inspect {state['log_path']}"
        gh_comment(repo, number, f"{RESULT_MARKER}\nTask `{state['task_id']}` blocked with exit code `{rc}`; inspect runner log.")


def run_new_task(config: dict[str, Any], home: Path, state_db: dict[str, Any], repo: str, r_cfg: dict[str, Any], issue: dict[str, Any], task: dict[str, Any]) -> None:
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
        "repository": repo, "issue_number": number, "task_id": task["task_id"],
        "branch": task["branch"], "base_ref": task["base_ref"], "worker_id": worker_id,
        "session_id": session_id, "worktree": str(worktree), "log_path": str(log_path),
        "status": "CLAIMED", "claimed_at": utcnow(), "last_instruction_comment_id": 0,
        "continuations": 0,
    }
    state_db[key] = state
    write_runtime(home, key, state)
    gh_comment(repo, number, f"{ACK_MARKER}\nWorker `{worker_id}` claimed `{task['task_id']}` at {state['claimed_at']}.")
    ensure_worktree(repo_path, str(task["base_ref"]), str(task["branch"]), worktree)
    state["status"] = "RUNNING"
    write_runtime(home, key, state)
    outcome = stream_process(
        grok_command(task, config.get("grok_defaults", {}), worktree, session_id, build_prompt(task, number), resume=False),
        log_path,
    )
    apply_outcome(repo, number, state, outcome)
    write_runtime(home, key, state)


def migrate_old_state(home: Path, key: str, state: dict[str, Any]) -> bool:
    if state.get("status") != "BLOCKED" or not state.get("log_path"):
        return False
    if not log_contains_max_turns(Path(state["log_path"])):
        return False
    state["status"] = "TURN_BUDGET_EXHAUSTED"
    state["last_error"] = None
    state.setdefault("continuations", 0)
    write_runtime(home, key, state)
    return True


def resume_from_instruction(config: dict[str, Any], home: Path, key: str, state: dict[str, Any], task: dict[str, Any], comment: dict[str, Any], source: str) -> None:
    text = instruction_text(comment)
    cid = int(comment.get("id") or 0)
    if not text:
        state["last_instruction_comment_id"] = cid
        return
    continuation_turns = int((task.get("grok") or {}).get("continuation_max_turns", config.get("grok_defaults", {}).get("continuation_max_turns", 4)))
    prompt = f"""A supervisor sent this durable GitHub instruction through the {source}:

{text}

Continue the SAME bounded task, SAME worktree, SAME branch, and SAME Grok session.
Use this continuation only for the requested correction/completion and directly required verification.
Do not broaden scope, merge, force-push, self-certify, or start dependent work.
Update the PR/BOT REPORT/handoff truthfully when done. If the instruction conflicts with the frozen task contract, stop and report the conflict.
"""
    state["status"] = "RUNNING_CONTINUATION"
    state["last_instruction_comment_id"] = cid
    state["continuations"] = int(state.get("continuations") or 0) + 1
    write_runtime(home, key, state)
    outcome = stream_process(
        grok_command(
            task, config.get("grok_defaults", {}), Path(state["worktree"]), state["session_id"], prompt,
            resume=True, max_turns_override=continuation_turns,
        ),
        Path(state["log_path"]),
    )
    apply_outcome(state["repository"], int(state["issue_number"]), state, outcome)
    write_runtime(home, key, state)


def find_task(config: dict[str, Any], repo: str, issue_number: int) -> dict[str, Any] | None:
    for row in list_task_issues(repo):
        if int(row["issue"]["number"]) == int(issue_number):
            return row["task"]
    return None


def refresh_feedback(config: dict[str, Any], home: Path, state_db: dict[str, Any]) -> bool:
    for key, state in state_db.items():
        migrate_old_state(home, key, state)
        if state.get("status") not in {"TURN_BUDGET_EXHAUSTED", "AWAITING_REVIEW", "AWAITING_HANDOFF", "BLOCKED"}:
            continue
        repo = state["repository"]
        task = find_task(config, repo, int(state["issue_number"]))
        if not task:
            continue
        after = int(state.get("last_instruction_comment_id") or 0)
        # Before PR: task issue is the only durable feedback lane.
        # After PR: PR comments are primary; task-issue comments remain a fallback.
        if state.get("pr_number"):
            comment = newest_instruction(repo, int(state["pr_number"]), after)
            if comment:
                resume_from_instruction(config, home, key, state, task, comment, "PR")
                return True
        comment = newest_instruction(repo, int(state["issue_number"]), after)
        if comment:
            resume_from_instruction(config, home, key, state, task, comment, "task issue")
            return True
    return False


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


def print_status(state_db: dict[str, Any]) -> None:
    if not state_db:
        print("No Grok Git worker tasks recorded.")
        return
    print(f"{'TASK':36} {'STATE':24} {'CONT':4} {'PR':8} BRANCH")
    for key, state in sorted(state_db.items()):
        pr = f"#{state['pr_number']}" if state.get("pr_number") else "-"
        print(f"{key[:36]:36} {str(state.get('status','?'))[:24]:24} {int(state.get('continuations') or 0):4} {pr:8} {state.get('branch','-')}")


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
    if not errors and run(["gh", "auth", "status"], check=False).returncode:
        errors.append("gh is not authenticated")
    if not errors and run(["grok", "version"], check=False).returncode:
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
    # Persist migration immediately so an old BLOCKED/max-turn state becomes resumable.
    migrated = False
    for key, state in state_db.items():
        migrated = migrate_old_state(home, key, state) or migrated
    if migrated:
        save_json(state_path, state_db)
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
                "repository": repo, "issue_number": int(issue["number"]),
                "task_id": task.get("task_id"), "branch": task.get("branch"),
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
    return migrated


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
        state_db = load_json(state_path, {})
        for key, state in state_db.items():
            migrate_old_state(home, key, state)
        save_json(state_path, state_db)
        print_status(state_db)
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
