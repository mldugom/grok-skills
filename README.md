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
- `/end` — verify, commit, land onto the intended primary branch when safe, then optionally push; otherwise WORKTREE LANDING REQUIRED

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

This repository is the durable source of truth.

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

Do not manually evolve installed copies when the corresponding source
exists in this repository. Modify the repository source, test it, then
sync/install it.

## Installation

Install lifecycle skills and the efficiency policy:

    bash scripts/install.sh

Install/update runtime credit controls and the canonical `grok-safe` shell
function (including `grok-cost`):

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
- Optimize for correctness, information value, and economic efficiency per model call.
- Avoid unnecessary agent fan-out and repeated investigation.
- Never commit Grok authentication, runtime sessions, secrets, or
  generated conversation state.

## Status

Lifecycle v1.1 is implemented: checkpoint commits, worktree-awareness,
and worktree landing before session complete.

Efficiency v1.2 adds credit/context/tool-call controls, a cost-visible
runtime launcher/status line, and prepaid-balance reconciliation via
`grok-cost`.

Next planned design phase: quantitative research spine.
