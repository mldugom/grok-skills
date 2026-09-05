# Grok Skills

Private source-of-truth repository for reusable Grok Build skills,
agent lifecycle controls, quantitative research methodology, domain
overlays, and project operating procedures.

## Design

The repository separates several concerns:

### Lifecycle

Explicit session-control commands:

- `/start` — bootstrap from durable state; report checkout, HEAD, and primary vs isolated/secondary; keep bootstrap narrow rather than reading the whole repo
- `/checkpoint` — targeted verification, persist state, commit intended work locally; never push by default; use only when the session will continue
- `/prioritize`
- `/audit`
- `/handoff` — provider-neutral implementation handoff: verify scope/tests/Git state, push/open-or-update PR, emit canonical `BOT REPORT`, then stop for Integration Owner review
- `/end` — verify, commit, land onto the intended primary branch when safe, then optionally push; otherwise WORKTREE LANDING REQUIRED

`/handoff` is deliberately separate from project governance. It standardizes how an agent reports completion; it never self-certifies, self-merges, promotes a protected ref, or releases dependent work. See `docs/agent-handoff-protocol.md`.

### Efficiency / credit controls

`policies/EFFICIENT_AGENT.md` provides the standing execution discipline:

- one substantial epic or research question per session by default,
- bounded investigative and implementation tool-call budgets,
- context/credit thresholds around 150k / 175k / 200k / 250k,
- Plan-mode read-only discipline until approval,
- no default subagent fan-out,
- targeted testing and verbose-output controls,
- point-in-time checks for quantitative historical research.

`shell/grok-safe.zsh` is the canonical `grok-safe` launcher. It injects the
policy, caps autonomous turns at 6, and disables subagents by default.

`scripts/configure-runtime.sh` also configures Grok's built-in status line
to show cwd, model, context, cost, and turn timer.

`scripts/grok-cost.py`, exposed as `grok-cost` by the shell helper, tracks
observed spend from the xAI prepaid-balance delta instead of treating the
status-line `$` value as authoritative billing. See `docs/COST_TRACKING.md`.

`scripts/grok-dashboard.py`, exposed as `grok-dashboard`, provides a reusable
local HTML operations monitor for Grok spend, project/git progress, roadmap
state, and runtime health. See `docs/GROK_DASHBOARD.md`.

### Research Methods

Reusable methodological skills such as:

- quantitative research
- temporal validation
- feature research
- model development
- Bayesian uncertainty
- robustness and stress testing

### Data

Reusable data engineering and integrity procedures.

### Finance

Portfolio construction, risk management, execution, and related
investment methodology.

### Production

Production ML, monitoring, pipelines, and data-product engineering.

### Domains

Domain-specific overlays such as:

- sports markets
- crypto markets
- front-office finance

### Consulting

Reusable analytics and quantitative consulting methodology.

### Lenses

Explicit analytical review modes such as:

- hedge-fund portfolio manager
- Taleb-style fragility / convexity review
- model-risk review
- research red team
- skeptical investment committee

## Architecture

This repository is the durable source of truth for reusable skills and provider-specific execution behavior.

    ~/repos/grok-skills
             │
             ├── skills/
             ├── policies/
             ├── shell/
             ├── scripts/
             ├── manifests/
             ├── docs/
             └── tests/
                    │
                    ▼
          installation / sync
                    │
                    ▼
             ~/.grok/skills
             ~/.grok/policies

Project control planes and dashboards stay in separate repositories. They interoperate through ordinary Git/PR metadata plus the provider-neutral `agent-handoff/v1` report contract, so a future Claude/OpenAI/local agent can replace Grok without changing the monitor.

Do not manually evolve installed copies when the corresponding source
exists in this repository. Modify the repository source, test it, then
sync/install it.

## Installation

Install lifecycle skills and the efficiency policy:

    bash scripts/install.sh

Install/update runtime credit controls and the canonical `grok-safe` shell
function (including `grok-cost` and `grok-dashboard`):

    bash scripts/configure-runtime.sh
    source ~/.zshrc

Compare installed skill/policy copies under `~/.grok` to this repository:

    bash scripts/verify.sh

Validate lifecycle metadata and lifecycle/efficiency contracts in-repo:

    bash tests/test_lifecycle_metadata.sh

## Cost tracking

Track the prepaid balance around a Grok session:

    grok-cost start 20.00 --label "crypto A0"
    grok-cost status 16.30
    grok-cost end 16.30
    grok-cost history --limit 10

The tracker stores only local session accounting under `~/.grok/cost-tracker`.
It does not store an API key or infer authoritative spend from tokens, turns,
tool calls, or the Grok status-line `$` indicator.

## Operations dashboard

Run a one-shot local HTML snapshot:

    grok-dashboard --project ~/repos/crypto-innout --open

Or keep a reusable monitor running and refreshing every 15 seconds:

    grok-dashboard --project ~/repos/crypto-innout --watch 15 --open

The dashboard serves on `127.0.0.1:8790` by default and monitors the project
runtime on port `8787` by default, so it does not collide with Crypto Innout.
Use `grok-cost status <balance>` during an active session to refresh the
manual authoritative xAI balance shown on the dashboard.

## Recommended daily workflow

For consequential work:

    cd ~/repos/<project>
    grok-safe
    # choose a normal New Session, not Resume/New Worktree unless deliberate
    /start
    # use /prioritize only if direction is unclear
    # use Plan mode only for architecture/research design/major ambiguous work
    # after approval, execute one bounded epic
    /checkpoint   # only if continuing the session
    /handoff      # when the bounded implementation is ready for integration review
    /end          # once the work unit/session is complete

Do not begin a second substantial epic after the first one is complete;
prefer `/end` and a fresh `/start`.

## Principles

- Skills should be modular rather than monolithic.
- Shared methodology belongs in shared skills.
- Domain skills should add domain-specific constraints rather than
  duplicate generic statistical methodology.
- Analytical lenses should generally be explicit/user-invoked.
- Repository instructions and durable project state should carry
  project knowledge rather than indefinitely growing chat sessions.
- Agent execution skills and project control-plane logic stay separate and communicate through versioned interfaces.
- Optimize for correctness, information value, and economic efficiency per model call.
- Avoid unnecessary agent fan-out and repeated investigation.
- Never commit Grok authentication, runtime sessions, secrets, or
  generated conversation state.

## Status

Lifecycle v1.2 adds the provider-neutral `/handoff` skill and `agent-handoff/v1` protocol on top of the prior checkpoint/worktree lifecycle controls.

Efficiency v1.3 adds credit/context/tool-call controls, a cost-visible
runtime launcher/status line, prepaid-balance reconciliation via `grok-cost`,
and the reusable `grok-dashboard` operations monitor.

Next planned design phase: quantitative research spine.
