# Grok Skills

Private source-of-truth repository for reusable Grok Build skills,
agent lifecycle controls, quantitative research methodology, domain
overlays, and project operating procedures.

## Design

The repository separates several concerns:

### Lifecycle

Explicit session-control commands:

- `/start`
- `/checkpoint`
- `/prioritize`
- `/audit`
- `/end`

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

## Principles

- Skills should be modular rather than monolithic.
- Shared methodology belongs in shared skills.
- Domain skills should add domain-specific constraints rather than
  duplicate generic statistical methodology.
- Analytical lenses should generally be explicit/user-invoked.
- Repository instructions and durable project state should carry
  project knowledge rather than indefinitely growing chat sessions.
- Optimize for correctness and information value per model call.
- Avoid unnecessary agent fan-out and repeated investigation.
- Never commit Grok authentication, runtime sessions, secrets, or
  generated conversation state.

## Status

Phase 1: lifecycle layer.

Next planned design phase: quantitative research spine.
