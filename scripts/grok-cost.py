#!/usr/bin/env python3
"""Track Grok spend from authoritative prepaid-balance deltas.

This deliberately does not infer billing from the Grok status-line `$` value,
context tokens, turns, or tool calls. Give it the prepaid balance shown by xAI
at session start/end and it records the exact observed delta.

Examples:
  python3 scripts/grok-cost.py start 20.00 --label "crypto A0"
  python3 scripts/grok-cost.py status 16.30
  python3 scripts/grok-cost.py end 16.30
  python3 scripts/grok-cost.py history --limit 10
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

STATE_DIR = Path(os.environ.get("GROK_COST_DIR", Path.home() / ".grok" / "cost-tracker"))
CURRENT = STATE_DIR / "current.json"
LEDGER = STATE_DIR / "sessions.csv"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def money(raw: str) -> Decimal:
    try:
        value = Decimal(raw.replace("$", "").replace(",", "").strip())
    except (InvalidOperation, AttributeError) as exc:
        raise argparse.ArgumentTypeError(f"invalid dollar balance: {raw!r}") from exc
    if value < 0:
        raise argparse.ArgumentTypeError("balance must be >= 0")
    return value.quantize(Decimal("0.0001"))


def fmt(value: Decimal) -> str:
    return f"${value.quantize(Decimal('0.0001')):,.4f}"


def load_current() -> dict:
    if not CURRENT.exists():
        raise SystemExit("No active cost session. Run: grok-cost start <balance>")
    return json.loads(CURRENT.read_text())


def write_current(data: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CURRENT.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    tmp.replace(CURRENT)


def cmd_start(args: argparse.Namespace) -> int:
    if CURRENT.exists() and not args.force:
        cur = json.loads(CURRENT.read_text())
        raise SystemExit(
            "A cost session is already active "
            f"({cur.get('label') or 'unlabeled'}, started {cur.get('started_at')}). "
            "End it first or pass --force."
        )
    state = {
        "started_at": now_iso(),
        "start_balance": str(args.balance),
        "label": args.label or "",
        "project": args.project or Path.cwd().name,
    }
    write_current(state)
    print(f"Grok cost session started: {state['label'] or state['project']}")
    print(f"  start balance  {fmt(args.balance)}")
    print("  source         xAI prepaid balance (authoritative delta)")
    return 0


def delta(state: dict, current: Decimal) -> tuple[Decimal, Decimal]:
    start = Decimal(state["start_balance"])
    spent = start - current
    if spent < 0:
        raise SystemExit(
            f"Current balance {fmt(current)} exceeds start balance {fmt(start)}. "
            "A top-up/credit occurred or the wrong balance was entered; do not treat the delta as session spend."
        )
    pct = (spent / start * Decimal("100")) if start else Decimal("0")
    return spent, pct


def print_status(state: dict, current: Decimal) -> None:
    start = Decimal(state["start_balance"])
    spent, pct = delta(state, current)
    print(f"Grok cost: {state.get('label') or state.get('project') or 'session'}")
    print(f"  start balance  {fmt(start)}")
    print(f"  current        {fmt(current)}")
    print(f"  observed spend {fmt(spent)}")
    print(f"  used           {pct.quantize(Decimal('0.01'))}%")
    print(f"  remaining      {fmt(current)}")
    print("  note           status-line $ is not used for this calculation")


def cmd_status(args: argparse.Namespace) -> int:
    state = load_current()
    if args.balance is None:
        print(f"Active: {state.get('label') or state.get('project') or 'session'}")
        print(f"  started        {state['started_at']}")
        print(f"  start balance  {fmt(Decimal(state['start_balance']))}")
        print("Pass the current xAI balance for an exact observed-spend delta:")
        print("  grok-cost status <balance>")
        return 0
    print_status(state, args.balance)
    return 0


def append_ledger(row: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    fields = [
        "started_at",
        "ended_at",
        "label",
        "project",
        "start_balance",
        "end_balance",
        "observed_spend",
    ]
    new_file = not LEDGER.exists()
    with LEDGER.open("a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        if new_file:
            writer.writeheader()
        writer.writerow({k: row.get(k, "") for k in fields})


def cmd_end(args: argparse.Namespace) -> int:
    state = load_current()
    spent, _ = delta(state, args.balance)
    print_status(state, args.balance)
    row = {
        **state,
        "ended_at": now_iso(),
        "end_balance": str(args.balance),
        "observed_spend": str(spent.quantize(Decimal("0.0001"))),
    }
    append_ledger(row)
    CURRENT.unlink(missing_ok=True)
    print(f"  ledger         {LEDGER}")
    return 0


def cmd_history(args: argparse.Namespace) -> int:
    if not LEDGER.exists():
        print("No completed cost sessions yet.")
        return 0
    with LEDGER.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    rows = rows[-args.limit :]
    if not rows:
        print("No completed cost sessions yet.")
        return 0
    print("started (UTC)               spend       end bal      project / label")
    print("--------------------------  ----------  -----------  ------------------------------")
    for row in rows:
        started = row["started_at"][:25]
        spend = fmt(Decimal(row["observed_spend"]))
        end_bal = fmt(Decimal(row["end_balance"]))
        name = row.get("label") or row.get("project") or ""
        print(f"{started:<26}  {spend:>10}  {end_bal:>11}  {name}")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Track Grok cost from xAI prepaid-balance deltas.")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("start", help="record the authoritative balance before a Grok session")
    s.add_argument("balance", type=money)
    s.add_argument("--label", default="")
    s.add_argument("--project", default="")
    s.add_argument("--force", action="store_true", help="replace an unfinished tracking session")
    s.set_defaults(func=cmd_start)

    s = sub.add_parser("status", help="show spend so far from a current balance")
    s.add_argument("balance", nargs="?", type=money)
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("end", help="close the session using the authoritative ending balance")
    s.add_argument("balance", type=money)
    s.set_defaults(func=cmd_end)

    s = sub.add_parser("history", help="show recent completed sessions")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(func=cmd_history)
    return p


def main() -> int:
    args = parser().parse_args()
    if getattr(args, "limit", 1) < 1:
        raise SystemExit("--limit must be >= 1")
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
