#!/usr/bin/env python3
"""Reusable local dashboard for Grok cost, project progress, and runtime health.

No third-party dependencies. It reads:
- ~/.grok/cost-tracker/{sessions.csv,current.json}
- git metadata for a project
- PROJECT_STATE.md and docs/22-automation-roadmap.md when present
- local process / port status

Examples:
  python3 scripts/grok-dashboard.py --project ~/repos/crypto-innout --open
  python3 scripts/grok-dashboard.py --project ~/repos/crypto-innout --watch 15
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Iterable

GROK_DIR = Path(os.environ.get("GROK_COST_DIR", Path.home() / ".grok" / "cost-tracker"))
LEDGER = GROK_DIR / "sessions.csv"
CURRENT = GROK_DIR / "current.json"
DEFAULT_OUT = Path.home() / ".grok" / "dashboard" / "index.html"


def run(cmd: list[str], cwd: Path | None = None) -> str:
    try:
        p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    return p.stdout.strip() if p.returncode == 0 else ""


def dec(raw: object, default: str = "0") -> Decimal:
    try:
        return Decimal(str(raw if raw not in (None, "") else default))
    except (InvalidOperation, ValueError):
        return Decimal(default)


def money(value: Decimal | float | int) -> str:
    return f"${Decimal(str(value)):,.2f}"


def age_text(path: Path) -> str:
    if not path.exists():
        return "missing"
    seconds = max(0, time.time() - path.stat().st_mtime)
    if seconds < 60:
        return f"{int(seconds)}s ago"
    if seconds < 3600:
        return f"{int(seconds // 60)}m ago"
    if seconds < 86400:
        return f"{seconds / 3600:.1f}h ago"
    return f"{seconds / 86400:.1f}d ago"


def load_costs() -> tuple[list[dict], dict | None]:
    rows: list[dict] = []
    if LEDGER.exists():
        try:
            with LEDGER.open(newline="") as fh:
                rows = list(csv.DictReader(fh))
        except OSError:
            rows = []
    current = None
    if CURRENT.exists():
        try:
            current = json.loads(CURRENT.read_text())
        except (OSError, json.JSONDecodeError):
            current = None
    return rows, current


def git_info(project: Path) -> dict:
    if not (project / ".git").exists() and not run(["git", "rev-parse", "--show-toplevel"], project):
        return {"branch": "—", "head": "—", "dirty": 0, "summary": "not a git repo"}
    branch = run(["git", "branch", "--show-current"], project) or "detached"
    head = run(["git", "rev-parse", "--short=8", "HEAD"], project) or "—"
    status = run(["git", "status", "--porcelain"], project)
    dirty = len([line for line in status.splitlines() if line.strip()])
    summary = run(["git", "log", "-1", "--pretty=%s"], project) or "—"
    commit_time = run(["git", "log", "-1", "--pretty=%cI"], project) or ""
    return {"branch": branch, "head": head, "dirty": dirty, "summary": summary, "commit_time": commit_time}


def section(text: str, heading: str, limit: int = 12) -> list[str]:
    lines = text.splitlines()
    start = None
    target = heading.lower().strip()
    for i, line in enumerate(lines):
        if line.lower().strip() == target:
            start = i + 1
            break
    if start is None:
        return []
    out: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        s = line.strip()
        if s:
            out.append(s)
        if len(out) >= limit:
            break
    return out


def read_project_state(project: Path) -> dict:
    path = project / "PROJECT_STATE.md"
    if not path.exists():
        return {"path": path, "text": "", "objective": [], "next": [], "stage": "—"}
    text = path.read_text(errors="replace")
    objective = section(text, "## 1. Current objective", 10)
    next_items = section(text, "## 9. Immediate next tasks (priority)", 8)
    if not next_items:
        next_items = section(text, "## Immediate next tasks", 8)
    stage_matches = re.findall(r"\bA(\d)(?:\.(\d+[a-z]?))?\b", "\n".join(objective[:4]), flags=re.I)
    stage = "—"
    if stage_matches:
        a, sub = stage_matches[0]
        stage = f"A{a}" + (f".{sub}" if sub else "")
    return {"path": path, "text": text, "objective": objective, "next": next_items, "stage": stage}


def roadmap(project: Path, state_text: str) -> list[dict]:
    path = project / "docs" / "22-automation-roadmap.md"
    if not path.exists():
        return []
    text = path.read_text(errors="replace")
    rows: list[dict] = []
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [re.sub(r"\*\*", "", c.strip()) for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not re.fullmatch(r"A\d+", cells[0]):
            continue
        rows.append({"code": cells[0], "name": cells[1], "scope": cells[2] if len(cells) > 2 else ""})
    active_num = None
    m = re.search(r"\bA(\d)(?:\.\w+)?\b", state_text)
    if m:
        active_num = int(m.group(1))
    done_codes = set(re.findall(r"\b(A\d+)\s+(?:COMPLETE|DONE|PASS)\b", state_text, flags=re.I))
    for row in rows:
        n = int(row["code"][1:])
        if row["code"] in done_codes:
            status = "done"
        elif active_num is not None and n < active_num:
            status = "done"
        elif active_num is not None and n == active_num:
            status = "active"
        else:
            status = "pending"
        row["status"] = status
    return rows


def port_listener(port: int) -> str:
    out = run(["lsof", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"])
    if out:
        lines = out.splitlines()
        return lines[-1] if len(lines) > 1 else lines[0]
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.15):
            return f"listener detected on 127.0.0.1:{port}"
    except OSError:
        return ""


def process_lines(pattern: str) -> list[str]:
    out = run(["pgrep", "-fl", pattern])
    return [x for x in out.splitlines() if x.strip()][:8] if out else []


def latest_matching(root: Path, pattern: str) -> Path | None:
    try:
        paths = list(root.glob(pattern))
    except OSError:
        return None
    return max(paths, key=lambda p: p.stat().st_mtime) if paths else None


def render(project: Path, app_port: int, process_pattern: str, refresh: int = 0) -> str:
    costs, current = load_costs()
    gi = git_info(project)
    ps = read_project_state(project)
    rm = roadmap(project, ps["text"])
    listener = port_listener(app_port)
    procs = process_lines(process_pattern)
    lock = project / "data" / "history.lock"
    db = project / "data" / "radar.sqlite"
    latest_gate = latest_matching(project / "data" / "reports", "gate_validity_*.html") if (project / "data" / "reports").exists() else None

    spends = [dec(r.get("observed_spend")) for r in costs]
    total_spend = sum(spends, Decimal("0"))
    avg_spend = total_spend / len(spends) if spends else Decimal("0")
    last_spend = spends[-1] if spends else Decimal("0")
    last_end_balance = dec(costs[-1].get("end_balance")) if costs else Decimal("0")

    active_label = "none"
    active_spend = Decimal("0")
    active_balance: Decimal | None = None
    active_checked = "not active"
    if current:
        active_label = current.get("label") or current.get("project") or "active session"
        start_bal = dec(current.get("start_balance"))
        if current.get("last_balance") is not None:
            active_balance = dec(current.get("last_balance"))
            active_spend = max(Decimal("0"), start_bal - active_balance)
            active_checked = current.get("last_checked_at") or "manual observation"
        else:
            active_balance = start_bal
            active_checked = "start balance only — run grok-cost status <balance>"

    max_spend = max(spends[-12:] or [Decimal("1")])
    bars = []
    for row, spend in zip(costs[-12:], spends[-12:]):
        width = float((spend / max_spend) * 100) if max_spend else 0.0
        label = row.get("label") or row.get("project") or "session"
        bars.append(
            f'<div class="bar-row"><div class="bar-label">{html.escape(label)}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div>'
            f'<div class="bar-value">{money(spend)}</div></div>'
        )

    objective_html = "".join(f"<li>{html.escape(x)}</li>" for x in ps["objective"][:8]) or "<li>No PROJECT_STATE objective found.</li>"
    next_html = "".join(f"<li>{html.escape(x)}</li>" for x in ps["next"][:6]) or "<li>No next-task section found.</li>"
    roadmap_html = ""
    for row in rm:
        roadmap_html += (
            f'<div class="phase {row["status"]}"><div class="phase-code">{html.escape(row["code"])}</div>'
            f'<div><strong>{html.escape(row["name"])}</strong><div class="muted">{html.escape(row["scope"])}</div></div>'
            f'<span class="pill">{row["status"]}</span></div>'
        )
    if not roadmap_html:
        roadmap_html = '<div class="muted">No automation roadmap found.</div>'

    prod_up = bool(listener and procs)
    prod_status = "UP" if prod_up else ("PARTIAL" if listener or procs else "DOWN")
    prod_class = "ok" if prod_up else ("warn" if listener or procs else "bad")
    proc_html = "<br>".join(html.escape(x) for x in procs) if procs else "no matching process"
    gate_text = f"{latest_gate.name} · {age_text(latest_gate)}" if latest_gate else "no gate report"

    refresh_meta = f'<meta http-equiv="refresh" content="{refresh}">' if refresh > 0 else ""
    generated = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    current_balance_display = money(active_balance) if active_balance is not None else (money(last_end_balance) if costs else "—")

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{refresh_meta}
<title>Grok Ops Dashboard</title>
<style>
:root{{--bg:#0b0e13;--panel:#121720;--panel2:#171d27;--text:#edf2f7;--muted:#8d99a8;--line:#263140;--good:#53d18b;--warn:#f2bf5e;--bad:#f06d6d;--accent:#76a7ff}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}}
.wrap{{max-width:1380px;margin:0 auto;padding:24px}} .top{{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;margin-bottom:18px}}
h1{{font-size:24px;margin:0}} h2{{font-size:14px;margin:0 0 12px;text-transform:uppercase;letter-spacing:.08em;color:#b8c2cf}} .muted{{color:var(--muted)}}
.grid{{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}} .card{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px;min-width:0}}
.kpis{{grid-column:span 12;display:grid;grid-template-columns:repeat(6,1fr);gap:10px;background:transparent;border:0;padding:0}} .kpi{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}}
.kpi .v{{font-size:24px;font-weight:700;margin-top:4px}} .kpi .l{{color:var(--muted);font-size:12px}} .span4{{grid-column:span 4}} .span5{{grid-column:span 5}} .span7{{grid-column:span 7}} .span8{{grid-column:span 8}} .span12{{grid-column:span 12}}
.status{{font-weight:800;letter-spacing:.06em}} .ok{{color:var(--good)}} .warn{{color:var(--warn)}} .bad{{color:var(--bad)}}
ul{{padding-left:18px;margin:0}} li{{margin:6px 0}} code{{color:#c8d8ff}} .mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px;word-break:break-word}}
.phase{{display:grid;grid-template-columns:42px 1fr auto;gap:10px;align-items:start;padding:9px 0;border-bottom:1px solid var(--line)}} .phase:last-child{{border:0}} .phase-code{{font-weight:800}} .phase.done{{opacity:.62}} .phase.active{{color:#fff}} .phase.active .phase-code{{color:var(--accent)}}
.pill{{font-size:10px;text-transform:uppercase;border:1px solid var(--line);border-radius:999px;padding:2px 7px;color:var(--muted)}}
.bar-row{{display:grid;grid-template-columns:minmax(90px,1.5fr) 3fr 58px;gap:8px;align-items:center;margin:8px 0}} .bar-label{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#c9d1dc}} .bar-track{{height:8px;background:#202836;border-radius:999px;overflow:hidden}} .bar-fill{{height:100%;background:var(--accent)}} .bar-value{{text-align:right;font-variant-numeric:tabular-nums}}
.row{{display:flex;justify-content:space-between;gap:14px;border-bottom:1px solid var(--line);padding:7px 0}} .row:last-child{{border:0}} .row span:first-child{{color:var(--muted)}}
@media(max-width:900px){{.kpis{{grid-template-columns:repeat(2,1fr)}} .span4,.span5,.span7,.span8{{grid-column:span 12}}}} @media(max-width:520px){{.wrap{{padding:14px}} .kpis{{grid-template-columns:1fr}} .top{{align-items:flex-start;flex-direction:column}}}}
</style></head><body><main class="wrap">
<div class="top"><div><h1>Grok Ops · {html.escape(project.name)}</h1><div class="muted">Reusable local monitor · generated {html.escape(generated)}</div></div><div class="mono">{html.escape(str(project))}</div></div>
<div class="grid">
<section class="kpis">
<div class="kpi"><div class="l">Total Grok spend</div><div class="v">{money(total_spend)}</div><div class="muted">{len(costs)} completed sessions</div></div>
<div class="kpi"><div class="l">Last session</div><div class="v">{money(last_spend)}</div><div class="muted">average {money(avg_spend)}</div></div>
<div class="kpi"><div class="l">Tracked balance</div><div class="v">{current_balance_display}</div><div class="muted">manual xAI balance observations</div></div>
<div class="kpi"><div class="l">Active session spend</div><div class="v">{money(active_spend)}</div><div class="muted">{html.escape(active_label)}</div></div>
<div class="kpi"><div class="l">Project stage</div><div class="v">{html.escape(ps['stage'])}</div><div class="muted">from PROJECT_STATE.md</div></div>
<div class="kpi"><div class="l">Production</div><div class="v status {prod_class}">{prod_status}</div><div class="muted">port {app_port}</div></div>
</section>
<section class="card span7"><h2>Current objective</h2><ul>{objective_html}</ul></section>
<section class="card span5"><h2>Runtime health</h2>
<div class="row"><span>App port {app_port}</span><strong class="{'ok' if listener else 'bad'}">{'LISTENING' if listener else 'FREE'}</strong></div>
<div class="row"><span>Matching process</span><strong>{len(procs)}</strong></div>
<div class="row"><span>history.lock</span><strong>{'present · ' + age_text(lock) if lock.exists() else 'absent'}</strong></div>
<div class="row"><span>radar.sqlite</span><strong>{age_text(db)}</strong></div>
<div class="row"><span>latest gate report</span><strong>{html.escape(gate_text)}</strong></div>
<div class="mono muted" style="margin-top:10px">{proc_html}</div></section>
<section class="card span7"><h2>Automation roadmap</h2>{roadmap_html}</section>
<section class="card span5"><h2>Grok cost history</h2>{''.join(bars) or '<div class="muted">No completed sessions yet.</div>'}<div class="muted" style="margin-top:10px">Active cost observation: {html.escape(active_checked)}</div></section>
<section class="card span7"><h2>Next project actions</h2><ul>{next_html}</ul></section>
<section class="card span5"><h2>Git state</h2>
<div class="row"><span>Branch</span><strong>{html.escape(gi['branch'])}</strong></div><div class="row"><span>HEAD</span><strong class="mono">{html.escape(gi['head'])}</strong></div><div class="row"><span>Dirty paths</span><strong class="{'warn' if gi['dirty'] else 'ok'}">{gi['dirty']}</strong></div><div class="muted" style="margin-top:10px">{html.escape(gi['summary'])}</div></section>
</div></main></body></html>"""


def write_dashboard(args: argparse.Namespace) -> Path:
    project = Path(args.project).expanduser().resolve()
    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(project, args.app_port, args.process, args.watch if args.watch else 0))
    return out


def serve_watch(args: argparse.Namespace) -> int:
    out = write_dashboard(args)
    root = out.parent

    class Handler(SimpleHTTPRequestHandler):
        def log_message(self, fmt: str, *vals: object) -> None:
            return

    handler = lambda *a, **kw: Handler(*a, directory=str(root), **kw)  # noqa: E731
    server = ThreadingHTTPServer(("127.0.0.1", args.dashboard_port), handler)
    stop = threading.Event()

    def regenerate() -> None:
        while not stop.wait(args.watch):
            try:
                write_dashboard(args)
            except Exception as exc:  # dashboard must not kill the server
                print(f"grok-dashboard: refresh failed: {exc}", file=sys.stderr)

    threading.Thread(target=regenerate, daemon=True, name="dashboard-refresh").start()
    url = f"http://127.0.0.1:{args.dashboard_port}/"
    print(f"Grok dashboard: {url}")
    print(f"Monitoring: {Path(args.project).expanduser().resolve()}")
    print(f"Refresh: {args.watch}s · Ctrl+C to stop")
    if args.open:
        webbrowser.open(url)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Reusable local Grok/project operations dashboard.")
    p.add_argument("--project", default=str(Path.cwd()), help="project repo to monitor")
    p.add_argument("--output", default=str(DEFAULT_OUT), help="generated HTML path")
    p.add_argument("--app-port", type=int, default=8787, help="project runtime port to monitor")
    p.add_argument("--process", default="alpha", help="pgrep pattern for project runtime")
    p.add_argument("--open", action="store_true", help="open dashboard in the default browser")
    p.add_argument("--watch", type=int, default=0, metavar="SECONDS", help="regenerate and serve continuously")
    p.add_argument("--dashboard-port", type=int, default=8790, help="local dashboard server port with --watch")
    return p


def main() -> int:
    args = parser().parse_args()
    if args.watch < 0:
        raise SystemExit("--watch must be >= 0")
    if not (1 <= args.app_port <= 65535 and 1 <= args.dashboard_port <= 65535):
        raise SystemExit("ports must be 1..65535")
    if args.watch:
        return serve_watch(args)
    out = write_dashboard(args)
    print(out)
    if args.open:
        webbrowser.open(out.as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
