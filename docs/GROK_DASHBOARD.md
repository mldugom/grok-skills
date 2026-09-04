# Grok Ops Dashboard

Reusable local HTML monitor for Grok work and project operations. It has no third-party Python dependencies and is intentionally separate from project virtual environments.

## What it shows

- completed Grok spend from `~/.grok/cost-tracker/sessions.csv`;
- active Grok cost session and the latest manually observed xAI balance;
- git branch, HEAD, latest commit, and dirty-path count;
- current objective and next actions from `PROJECT_STATE.md`;
- A0–A9 roadmap rows from `docs/22-automation-roadmap.md` when present;
- project runtime process status;
- monitored application port status (8787 by default);
- `data/history.lock`, `data/radar.sqlite`, and latest gate-validity report freshness when present.

The dashboard never infers authoritative spend from tokens or the Grok status-line `$` counter.

## Install / refresh

```bash
cd ~/repos/grok-skills
git pull origin main
source ~/.zshrc
```

If `grok-dashboard` is not yet available in the current shell, run:

```bash
source ~/repos/grok-skills/shell/grok-safe.zsh
```

## Crypto Innout

One-shot HTML snapshot:

```bash
grok-dashboard --project ~/repos/crypto-innout --open
```

Recommended continuously refreshing local dashboard:

```bash
grok-dashboard \
  --project ~/repos/crypto-innout \
  --app-port 8787 \
  --process alpha \
  --watch 15 \
  --open
```

This serves the dashboard on:

```text
http://127.0.0.1:8790/
```

The monitored project remains on its own port, e.g. Crypto Innout on `:8787`; the Grok dashboard uses `:8790` by default so the two do not conflict.

## Cost refresh

xAI balance is still a manual authoritative observation. During an active session, update it with:

```bash
grok-cost status 8.42
```

That command now persists the latest observed balance and timestamp in the local current-session file so the dashboard can display active-session spend. It does not query or store an API key.

## Reuse on another project

```bash
grok-dashboard --project ~/repos/another-project --watch 30 --open
```

Override the monitored process or project port when needed:

```bash
grok-dashboard \
  --project ~/repos/another-project \
  --process my-service \
  --app-port 8501 \
  --watch 20 \
  --open
```

Project-specific panels degrade gracefully when `PROJECT_STATE.md`, the A-roadmap, `radar.sqlite`, or gate-validity reports do not exist.
